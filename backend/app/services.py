"""
Business logic services for better testability and separation of concerns.
"""

import re
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any


class ContentService:
    """Service for content-related business logic"""

    @staticmethod
    def sanitize_content(content: str) -> str:
        """Remove control characters except newlines and tabs"""
        return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", content)

    @staticmethod
    def sanitize_name(name: str) -> str:
        """Remove control characters from name"""
        return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", name)

    @staticmethod
    def validate_pagination_params(
        limit: Optional[int], offset: Optional[int]
    ) -> tuple[int, int]:
        """Validate and return safe pagination parameters"""
        if limit is None:
            safe_limit = 20
        else:
            safe_limit = min(max(limit, 1), 100)  # Between 1 and 100
        safe_offset = max(offset or 0, 0)  # Non-negative
        return safe_limit, safe_offset


class SessionService:
    """Service for session-related business logic"""

    @staticmethod
    def generate_default_title() -> str:
        """Generate a default session title"""
        return f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate session ID format"""
        try:
            uuid.UUID(session_id)
            return True
        except ValueError:
            return False


class MessageService:
    """Service for message-related business logic"""

    @staticmethod
    def validate_message_content(content: str) -> bool:
        """Validate message content"""
        if not content or not content.strip():
            return False
        if len(content) > 10000:  # Max 10k chars
            return False
        return True

    @staticmethod
    def get_processing_response() -> str:
        """Get standard processing response"""
        return "I'm processing your message and searching through your educational content. I'll have a response ready shortly!"


class UserService:
    """Service for user-related business logic"""

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        return len(username.strip()) >= 3 and len(username) <= 150

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        if not email or "@" not in email:
            return False
        parts = email.split("@")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return False
        return "." in parts[1]


class ContentChunkingService:
    """Service for chunking content into smaller pieces for better retrieval"""

    CHUNK_SIZE = 500  # Characters per chunk
    CHUNK_OVERLAP = 100  # Overlap between chunks

    @staticmethod
    def chunk_content(
        content_text: str, chunk_size: int = None, overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk content into smaller pieces with overlap.
        Returns list of dicts with chunk_text, start_char, end_char
        """
        if chunk_size is None:
            chunk_size = ContentChunkingService.CHUNK_SIZE
        if overlap is None:
            overlap = ContentChunkingService.CHUNK_OVERLAP

        chunks = []
        text_length = len(content_text)

        if text_length <= chunk_size:
            # Content is small enough, no need to chunk
            chunks.append(
                {
                    "chunk_text": content_text,
                    "start_char": 0,
                    "end_char": text_length,
                    "chunk_index": 0,
                }
            )
            return chunks

        # Create chunks with overlap
        start = 0
        chunk_index = 0

        while start < text_length:
            # Calculate end position
            end = min(start + chunk_size, text_length)

            # Try to find a sentence boundary near the end
            if end < text_length:
                # Look for sentence endings
                sentence_ends = [". ", "! ", "? ", "\n\n"]
                best_end = end

                for sentence_end in sentence_ends:
                    last_period = content_text.rfind(
                        sentence_end, start + chunk_size // 2, end
                    )
                    if last_period != -1:
                        best_end = last_period + len(sentence_end)
                        break

                end = best_end

            # Extract chunk
            chunk_text = content_text[start:end].strip()

            if chunk_text:  # Only add non-empty chunks
                chunks.append(
                    {
                        "chunk_text": chunk_text,
                        "start_char": start,
                        "end_char": end,
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1

            # Move to next chunk with overlap
            start = end - overlap if end < text_length else text_length

        return chunks

    @staticmethod
    def store_content_chunks(content_id: int) -> int:
        """
        Create and store chunks for a given content.
        Returns number of chunks created.
        """
        from app.models import Content, ContentChunk

        try:
            content = Content.objects.get(id=content_id)

            # Delete existing chunks
            ContentChunk.objects.filter(content=content).delete()

            # Create new chunks
            chunks = ContentChunkingService.chunk_content(content.content)
            total_chunks = len(chunks)

            for chunk_data in chunks:
                ContentChunk.objects.create(
                    content=content,
                    chunk_text=chunk_data["chunk_text"],
                    chunk_index=chunk_data["chunk_index"],
                    total_chunks=total_chunks,
                    start_char=chunk_data["start_char"],
                    end_char=chunk_data["end_char"],
                )

            return total_chunks

        except Content.DoesNotExist:
            return 0


class DebugService:
    """Service for managing debug information"""

    # In-memory storage as fallback
    _debug_storage = {}

    @staticmethod
    def store_debug_info(session_id: str, debug_info: dict) -> None:
        """Store debug info in cache for a session"""
        try:
            from django.core.cache import cache

            cache_key = f"debug_info_{session_id}"
            # Store for 1 hour
            cache.set(cache_key, debug_info, 3600)
        except Exception as e:
            # Fallback to in-memory storage if cache fails
            print(f"Warning: Cache storage failed, using in-memory storage: {e}")
            DebugService._debug_storage[session_id] = debug_info

    @staticmethod
    def get_debug_info(session_id: str) -> Optional[dict]:
        """Retrieve debug info from cache for a session"""
        try:
            from django.core.cache import cache

            cache_key = f"debug_info_{session_id}"
            return cache.get(cache_key)
        except Exception as e:
            # Fallback to in-memory storage if cache fails
            print(f"Warning: Cache retrieval failed, using in-memory storage: {e}")
            return DebugService._debug_storage.get(session_id)
