import json
import logging
import re
from typing import Dict, Any

from django.conf import settings
from qdrant_client.models import PointStruct

from app.models import Content, AnalysisResult
from app.queue_manager import queue_manager
from app.client_manager import client_manager

# Configure logging
logger = logging.getLogger(__name__)


def estimate_token_count(text: str) -> int:
    """Estimate token count using word-based approximation (roughly 0.75 tokens per word)"""
    # Remove extra whitespace and split into words
    words = len(re.findall(r"\b\w+\b", text))
    # Rough estimate: 1 word ≈ 1.33 tokens
    return int(words * 1.33)


def compute_content_features(
    content: str, key_concepts: list, difficulty_level: str
) -> Dict[str, Any]:
    """Compute features for time estimation"""
    return {
        "token_count": estimate_token_count(content),
        "content_length": len(content),
        "num_concepts": len(key_concepts),
        "key_concepts": ", ".join(key_concepts) if key_concepts else "None",
        "difficulty_level": difficulty_level,
        "content_preview": content[:300] + ("..." if len(content) > 300 else ""),
    }


def analyze_content_async(content_id: int) -> Dict[str, Any]:
    """Analyze content asynchronously using OpenAI and store results."""
    try:
        logger.info(f"Starting analysis for content {content_id}")
        content = Content.objects.get(id=content_id)
        logger.info(f"Found content: {content.name}")

        # Check if OpenAI client is available
        if not client_manager.is_openai_available():
            logger.error("OpenAI client not configured")
            raise ValueError("OpenAI client not configured")

        logger.info("OpenAI client is available")

        # Analyze key concepts (using configured model)
        logger.info("Starting key concepts analysis")
        concepts_response = client_manager.openai_client.chat.completions.create(
            model=settings.ANALYSIS_KEY_CONCEPTS_MODEL,
            messages=[
                {"role": "system", "content": settings.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": settings.KEY_CONCEPTS_PROMPT.format(content=content.content),
                },
            ],
            response_format=settings.KEY_CONCEPTS_SCHEMA,
            temperature=settings.ANALYSIS_KEY_CONCEPTS_TEMPERATURE,
            max_tokens=settings.ANALYSIS_KEY_CONCEPTS_MAX_TOKENS,
        )
        key_concepts = json.loads(concepts_response.choices[0].message.content)[
            "concepts"
        ]
        logger.info(f"Key concepts: {key_concepts}")

        # Analyze difficulty level
        logger.info("Starting difficulty analysis")
        difficulty_response = client_manager.openai_client.chat.completions.create(
            model=settings.ANALYSIS_DIFFICULTY_MODEL,
            messages=[
                {"role": "system", "content": settings.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": settings.DIFFICULTY_PROMPT.format(content=content.content),
                },
            ],
            response_format=settings.DIFFICULTY_SCHEMA,
            temperature=settings.ANALYSIS_DIFFICULTY_TEMPERATURE,
            max_tokens=settings.ANALYSIS_DIFFICULTY_MAX_TOKENS,
        )
        difficulty_level = json.loads(difficulty_response.choices[0].message.content)[
            "difficulty_level"
        ]
        logger.info(f"Difficulty level: {difficulty_level}")

        # Compute features for time estimation
        logger.info("Computing content features")
        features = compute_content_features(
            content.content, key_concepts, difficulty_level
        )
        logger.info(f"Computed features: {features}")

        # Analyze study time using computed features
        logger.info("Starting study time analysis with features")
        study_time_response = client_manager.openai_client.chat.completions.create(
            model=settings.ANALYSIS_STUDY_TIME_MODEL,
            messages=[
                {"role": "system", "content": settings.SYSTEM_PROMPT},
                {"role": "user", "content": settings.STUDY_TIME_PROMPT.format(**features)},
            ],
            response_format=settings.STUDY_TIME_SCHEMA,
            temperature=settings.ANALYSIS_STUDY_TIME_TEMPERATURE,
            max_tokens=settings.ANALYSIS_STUDY_TIME_MAX_TOKENS,
        )
        estimated_study_time = json.loads(
            study_time_response.choices[0].message.content
        )["estimated_minutes"]
        logger.info(f"Estimated study time: {estimated_study_time} minutes")

        # Store analysis results in AnalysisResult model
        logger.info("Creating AnalysisResult record")
        analysis_result = AnalysisResult.objects.create(
            content=content,
            key_concepts=key_concepts,
            difficulty_level=difficulty_level,
            estimated_study_time=estimated_study_time,
        )

        # Update content model fields for API consistency
        logger.info("Updating content model fields")
        content.key_concepts = key_concepts
        content.difficulty_level = difficulty_level
        content.estimated_study_time = estimated_study_time
        content.processed = True
        content.analysis_status = "completed"
        content.save()
        logger.info("Content updated successfully")

        # Store embeddings in Qdrant (enqueue as separate task for better performance)
        logger.info("Enqueueing embeddings task")
        queue_manager.enqueue(store_content_embeddings, content_id)

        result = {
            "status": "success",
            "content_id": content_id,
            "analysis_id": analysis_result.id,
            "key_concepts": key_concepts,
            "difficulty_level": difficulty_level,
            "estimated_study_time": estimated_study_time,
            "features": features,  # Include computed features in result
        }
        logger.info(f"Analysis completed successfully: {result}")
        return result

    except Content.DoesNotExist:
        error_msg = f"Content {content_id} not found"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"Analysis failed for content {content_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Update content status to failed
        try:
            content = Content.objects.get(id=content_id)
            content.analysis_status = "failed"
            content.save()
            logger.info(f"Updated content {content_id} status to failed")
        except Exception as save_error:
            logger.error(f"Failed to update content status: {save_error}")

        return {"status": "error", "message": error_msg}


def store_content_embeddings(content_id: int) -> Dict[str, Any]:
    """Store content embeddings in Qdrant vector database."""
    import uuid
    
    try:
        content = Content.objects.get(id=content_id)

        # Import ContentChunkingService
        from app.services import ContentChunkingService

        # First, create chunks for the content
        num_chunks = ContentChunkingService.store_content_chunks(content_id)
        logger.info(f"Created {num_chunks} chunks for content {content_id}")

        # Get all chunks for this content
        from app.models import ContentChunk

        chunks = ContentChunk.objects.filter(content_id=content_id).order_by(
            "chunk_index"
        )

        points = []
        for chunk in chunks:
            # Get embeddings for each chunk
            embeddings = client_manager.get_embeddings(chunk.chunk_text)

            # Generate a UUID for this chunk
            chunk_uuid = str(uuid.uuid4())

            # Store in Qdrant with chunk information
            point = PointStruct(
                id=chunk_uuid,
                vector=embeddings,
                payload={
                    "content_id": content_id,
                    "chunk_id": f"{content_id}_{chunk.chunk_index}",  # Keep as string in payload for reference
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "user_id": content.user_id,
                    "name": content.name,
                    "content": chunk.chunk_text,  # Store chunk text
                    "full_content_preview": content.content[:200] + "..."
                    if len(content.content) > 200
                    else content.content,
                    "key_concepts": content.key_concepts,
                    "difficulty_level": content.difficulty_level,
                    "estimated_study_time": content.estimated_study_time,
                    "created_at": content.created_at.isoformat(),
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                },
            )
            points.append(point)

        # Batch upsert all points
        if points and client_manager.is_qdrant_available():
            client_manager.qdrant_client.upsert(collection_name="content_embeddings", points=points)
            logger.info(
                f"Successfully stored {len(points)} chunk embeddings for content {content_id}"
            )
        elif points:
            logger.warning("Qdrant client not available, skipping embedding storage")

        return {
            "status": "success",
            "content_id": content_id,
            "chunks_created": num_chunks,
            "embeddings_stored": len(points) if client_manager.is_qdrant_available() else 0,
        }

    except Content.DoesNotExist:
        return {"status": "error", "message": f"Content {content_id} not found"}
    except Exception as e:
        logger.error(f"Failed to store embeddings for content {content_id}: {e}")
        return {"status": "error", "message": str(e)}


def reanalyze_all_content() -> Dict[str, Any]:
    """Reanalyze all content in the database."""
    content_ids = list(Content.objects.values_list("id", flat=True))

    for content_id in content_ids:
        queue_manager.enqueue(analyze_content_async, content_id)

    return {
        "status": "success",
        "message": f"Queued {len(content_ids)} content items for reanalysis",
    }
