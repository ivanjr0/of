import json
from datetime import datetime
import time

from django.conf import settings
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from app.models import Content, ConversationSession, Message
from app.services import DebugService
from app.client_manager import client_manager


def extract_search_keywords(query: str) -> list[str]:
    """Extract relevant keywords from a query using LLM"""
    try:
        keyword_prompt = f"""Extract the most important keywords and search terms from this query for educational content search.
Include:
- Main topics and concepts
- Technical terms
- Subject areas
- Related synonyms that might appear in educational content

Query: {query}

Return only the keywords as a comma-separated list, no explanation needed."""

        if not client_manager.is_openai_available():
            print("OpenAI client not available, skipping keyword extraction")
            return []

        response = client_manager.openai_client.chat.completions.create(
            model=settings.SEARCH_KEYWORD_EXTRACTION_MODEL,
            messages=[{"role": "user", "content": keyword_prompt}],
            temperature=settings.SEARCH_KEYWORD_EXTRACTION_TEMPERATURE,
            max_tokens=settings.SEARCH_KEYWORD_EXTRACTION_MAX_TOKENS,
        )
        
        keywords_text = response.choices[0].message.content.strip()
        keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
        return keywords[:10]  # Limit to 10 keywords
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []


def search_relevant_content(query: str, user_id: int, limit: int = 3, include_debug: bool = False):
    """Search for relevant content using hybrid search: keyword + semantic similarity"""
    
    debug_info = {
        "query_analysis": {
            "original_query": query,
            "extracted_keywords": [],
            "embedding_model": str(client_manager.get_embedding_model()),
            "search_time_ms": 0,
            "keyword_search_time_ms": 0,
            "vector_search_time_ms": 0,
            "total_indexed_contents": 0
        },
        "relevant_passages": []
    }
    
    try:
        total_start_time = time.time()
        
        # Step 1: Extract keywords using LLM
        keywords = extract_search_keywords(query)
        debug_info["query_analysis"]["extracted_keywords"] = keywords
        
        # Step 2: PostgreSQL full-text search
        keyword_start_time = time.time()
        keyword_results = []
        
        if keywords:
            # Prepare keywords for PostgreSQL full-text search
            # Split multi-word terms and clean them for tsquery
            search_terms = []
            simple_terms = []
            
            for keyword in keywords:
                # Split multi-word terms and add individual words
                words = keyword.replace('-', ' ').split()
                for word in words:
                    # Clean word for tsquery (alphanumeric only)
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if len(clean_word) >= 2:  # Only include words with 2+ characters
                        search_terms.append(clean_word)
                
                # Also keep original term for simple text matching
                simple_terms.append(keyword.lower())
            
            # Remove duplicates and limit terms
            search_terms = list(set(search_terms))[:8]  # Limit to 8 terms
            
            # Build multiple search strategies
            search_filters = []
            
            # Strategy 1: Full-text search with individual words
            if search_terms:
                try:
                    search_query = SearchQuery(" | ".join(search_terms), search_type='raw')
                    keyword_results = Content.objects.filter(
                        user_id=user_id,
                        is_deleted=False
                    ).annotate(
                        search=SearchVector('name', 'content', 'key_concepts'),
                        rank=SearchRank(SearchVector('name', 'content', 'key_concepts'), search_query)
                    ).filter(
                        search=search_query
                    ).order_by('-rank')[:limit * 2]
                except Exception as e:
                    print(f"Full-text search failed: {e}")
                    keyword_results = []
            
            # Strategy 2: Fallback to simple text search if full-text search fails or returns no results
            if not keyword_results and simple_terms:
                # Build Q objects for text matching
                text_filters = Q()
                for term in simple_terms[:5]:  # Limit to 5 terms for performance
                    text_filters |= (
                        Q(name__icontains=term) |
                        Q(content__icontains=term) |
                        Q(key_concepts__icontains=term)
                    )
                
                keyword_results = Content.objects.filter(
                    user_id=user_id,
                    is_deleted=False
                ).filter(text_filters)[:limit * 2]
            
            # Strategy 3: Also try matching the original query
            if not keyword_results:
                keyword_results = Content.objects.filter(
                    user_id=user_id,
                    is_deleted=False
                ).filter(
                    Q(name__icontains=query[:50]) |
                    Q(content__icontains=query[:50])
                )[:limit * 2]
        
        debug_info["query_analysis"]["keyword_search_time_ms"] = round(
            (time.time() - keyword_start_time) * 1000, 2
        )
        
        # Step 3: Vector similarity search
        vector_start_time = time.time()
        vector_results = []
        
        try:
            if client_manager.is_qdrant_available():
                query_embedding = client_manager.get_embeddings(query)
                
                # Search in Qdrant
                search_result = client_manager.qdrant_client.search(
                    collection_name="content_embeddings",
                    query_vector=query_embedding,
                    query_filter=Filter(
                        must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                    ),
                    limit=limit * 2,  # Get more results for merging
                    with_payload=True,
                )
                
                # Get content IDs from vector search
                vector_content_ids = list(set([hit.payload["content_id"] for hit in search_result]))
                
                if vector_content_ids:
                    vector_results = Content.objects.filter(
                        id__in=vector_content_ids,
                        is_deleted=False
                    ).prefetch_related()
                    
                # Store vector search hits for debug info
                for hit in search_result[:limit]:
                    debug_info["relevant_passages"].append({
                        "content_id": hit.payload["content_id"],
                        "chunk_id": hit.payload.get("chunk_id", ""),
                        "chunk_index": hit.payload.get("chunk_index", 0),
                        "total_chunks": hit.payload.get("total_chunks", 1),
                        "name": hit.payload["name"],
                        "content": hit.payload["content"],
                        "score": round(hit.score, 4),
                        "key_concepts": hit.payload.get("key_concepts", []),
                        "difficulty_level": hit.payload.get("difficulty_level", "unknown"),
                    })
            else:
                print("Qdrant client not available, skipping vector search")
                
        except Exception as e:
            print(f"Vector search error: {e}")
            debug_info["query_analysis"]["error"] = str(e)
            
        debug_info["query_analysis"]["vector_search_time_ms"] = round(
            (time.time() - vector_start_time) * 1000, 2
        )
        
        # Step 4: Merge and rank results
        # Combine keyword and vector results, preferring vector scores
        all_results = {}
        
        # Add keyword results
        for idx, content in enumerate(keyword_results):
            all_results[content.id] = {
                "content": content,
                "keyword_rank": idx,
                "vector_rank": float('inf'),
                "combined_score": 0
            }
            
        # Add vector results
        for idx, content in enumerate(vector_results):
            if content.id in all_results:
                all_results[content.id]["vector_rank"] = idx
            else:
                all_results[content.id] = {
                    "content": content,
                    "keyword_rank": float('inf'),
                    "vector_rank": idx,
                    "combined_score": 0
                }
                
        # Calculate combined scores (lower rank = better)
        for content_id, result in all_results.items():
            # Weighted combination: vector search is weighted more heavily
            result["combined_score"] = (
                result["vector_rank"] * 0.7 + 
                result["keyword_rank"] * 0.3
            )
            
        # Sort by combined score and get top results
        sorted_results = sorted(
            all_results.values(), 
            key=lambda x: x["combined_score"]
        )[:limit]
        
        final_contents = [result["content"] for result in sorted_results]
        
        # Update debug info
        debug_info["query_analysis"]["total_indexed_contents"] = len(all_results)
        debug_info["query_analysis"]["search_time_ms"] = round(
            (time.time() - total_start_time) * 1000, 2
        )
        
        if include_debug:
            return final_contents, debug_info
        return final_contents
        
    except Exception as e:
        print(f"Search error: {e}")
        debug_info["query_analysis"]["error"] = str(e)
        if include_debug:
            return [], debug_info
        return []


def analyze_content(content_id):
    """Analyze content using OpenAI to extract key concepts, difficulty, and study time"""
    try:
        content = Content.objects.get(id=content_id)
    except Content.DoesNotExist:
        print(f"Error: Content with id {content_id} does not exist")
        return

    if not client_manager.is_openai_available():
        print(f"Error: OpenAI client not available for content {content_id}")
        return

    # Get key concepts
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
    key_concepts = json.loads(concepts_response.choices[0].message.content)["concepts"]

    # Get difficulty level
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

    # Estimate study time
    from app.tasks import compute_content_features

    features = compute_content_features(content.content, key_concepts, difficulty_level)
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
    estimated_study_time = json.loads(study_time_response.choices[0].message.content)[
        "estimated_minutes"
    ]

    # Update content with analysis results
    content.key_concepts = key_concepts
    content.difficulty_level = difficulty_level
    content.estimated_study_time = estimated_study_time
    content.processed = True
    content.save()

    print(f"Content {content_id} analyzed successfully")
    return {
        "key_concepts": key_concepts,
        "difficulty_level": difficulty_level,
        "estimated_study_time": estimated_study_time,
    }


def get_conversation_context(session_id: str, limit: int = 10):
    """Get recent conversation messages for context"""
    try:
        session = ConversationSession.objects.get(id=session_id)
        messages = session.messages.order_by("-timestamp")[:limit]
        # Reverse to get chronological order
        return list(reversed(messages))
    except ConversationSession.DoesNotExist:
        return []


def generate_assistant_response(session_id: str, user_message_id: int, include_debug: bool = True):
    """Generate assistant response using conversation context and relevant content"""
    debug_info = {
        "processing_info": {
            "generation_time_ms": 0,
            "model": settings.CONVERSATION_ASSISTANT_MODEL,
            "tokens_used": None,
            "context_length": 0
        }
    }
    
    start_time = time.time()
    
    try:
        session = ConversationSession.objects.get(id=session_id)
        user_message = Message.objects.get(id=user_message_id, session=session)
        
        # Search for relevant content with debug info
        relevant_content, search_debug_info = search_relevant_content(
            user_message.content, 
            session.user_id, 
            limit=3,
            include_debug=True
        )
        debug_info.update(search_debug_info)
        
        # Build context from relevant content
        context_parts = []
        if relevant_content:
            context_parts.append("Based on your educational content:")
            for idx, content in enumerate(relevant_content, 1):
                context_parts.append(f"\n{idx}. {content.name}")
                context_parts.append(f"   Key concepts: {', '.join(content.key_concepts or [])}")
                context_parts.append(f"   {content.content[:500]}...")
        
        context = "\n".join(context_parts) if context_parts else ""
        debug_info["processing_info"]["context_length"] = len(context)
        
        # Get conversation history
        conversation_messages = get_conversation_context(session_id, limit=5)
        
        # Build messages for OpenAI
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful educational assistant. You help users understand and learn from their educational content.
                
{context}

Provide clear, concise answers based on the content provided. If the content doesn't contain relevant information, acknowledge this and provide general guidance."""
            }
        ]
        
        # Add conversation history
        for msg in conversation_messages:
            if msg.id != user_message_id:  # Don't duplicate the current message
                messages.append({"role": msg.role, "content": msg.content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message.content})
        
        if not client_manager.is_openai_available():
            raise Exception("OpenAI client not available")
        
        # Generate response
        response = client_manager.openai_client.chat.completions.create(
            model=settings.CONVERSATION_ASSISTANT_MODEL,
            messages=messages,
            temperature=settings.CONVERSATION_ASSISTANT_TEMPERATURE,
            max_tokens=settings.CONVERSATION_ASSISTANT_MAX_TOKENS,
        )
        
        assistant_content = response.choices[0].message.content
        token_count = response.usage.total_tokens if hasattr(response, 'usage') else None
        
        debug_info["processing_info"]["tokens_used"] = token_count
        debug_info["processing_info"]["generation_time_ms"] = round(
            (time.time() - start_time) * 1000, 2
        )
        
        # Store debug info if debug mode is enabled
        if include_debug and session_id:
            DebugService.store_debug_info(str(session_id), debug_info)
        
        # Save assistant message
        assistant_message = Message.objects.create(
            session=session,
            role="assistant",
            content=assistant_content,
            token_count=token_count
        )
        
        return assistant_message
        
    except Exception as e:
        print(f"Error generating response: {e}")
        # Create an error message
        error_message = Message.objects.create(
            session_id=session_id,
            role="assistant",
            content="I apologize, but I encountered an error while processing your message. Please try again."
        )
        return error_message
