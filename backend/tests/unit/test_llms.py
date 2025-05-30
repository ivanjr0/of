"""
Unit tests for LLM-related functions.
Extensive use of mocks to avoid calling external APIs.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, Mock
from freezegun import freeze_time
from app.llms import (
    analyze_content,
    search_relevant_content,
    generate_assistant_response,
    extract_search_keywords,
)
from tests.factories import ContentFactory, ConversationSessionFactory, MessageFactory, UserFactory
from app.client_manager import client_manager
from django.test import TestCase
from django.contrib.auth.models import User
from app.models import Content, ConversationSession, Message


class TestExtractSearchKeywords(TestCase):
    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    def test_extract_keywords_success(self, mock_client, mock_available):
        # Mock response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="machine learning, algorithms, data science"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        keywords = extract_search_keywords("How does machine learning work?")

        assert keywords == ["machine learning", "algorithms", "data science"]
        mock_client.chat.completions.create.assert_called_once()

    @patch.object(client_manager, 'is_openai_available', return_value=False)
    def test_extract_keywords_no_client(self, mock_available):
        keywords = extract_search_keywords("test query")
        assert keywords == []

    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    def test_extract_keywords_error(self, mock_client, mock_available):
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        keywords = extract_search_keywords("test query")
        assert keywords == []


class TestAnalyzeContent(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.content = ContentFactory(user=self.user, processed=False)

    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    def test_analyze_content_success(self, mock_client, mock_available):
        """Test successful content analysis"""
        # Mock responses for all three API calls
        mock_responses = [
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content='{"concepts": ["python", "programming"]}'
                        )
                    )
                ]
            ),
            Mock(
                choices=[
                    Mock(message=Mock(content='{"difficulty_level": "intermediate"}'))
                ]
            ),
            Mock(
                choices=[
                    Mock(message=Mock(content='{"estimated_minutes": 45}'))
                ]
            ),
        ]
        mock_client.chat.completions.create.side_effect = mock_responses

        result = analyze_content(self.content.id)

        # Verify the result
        assert result["key_concepts"] == ["python", "programming"]
        assert result["difficulty_level"] == "intermediate"
        assert result["estimated_study_time"] == 45

        # Verify content was updated
        self.content.refresh_from_db()
        assert self.content.key_concepts == ["python", "programming"]
        assert self.content.difficulty_level == "intermediate"
        assert self.content.estimated_study_time == 45
        assert self.content.processed is True

    @patch.object(client_manager, 'is_openai_available', return_value=False)
    def test_analyze_content_no_client(self, mock_available):
        result = analyze_content(self.content.id)
        assert result is None

    def test_analyze_content_not_found(self):
        result = analyze_content(999)  # Non-existent content
        assert result is None

    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    def test_analyze_content_openai_error(self, mock_client, mock_available):
        """Test handling of OpenAI API errors"""
        # Mock OpenAI error
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            analyze_content(self.content.id)


class TestSearchRelevantContent(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.content = ContentFactory(
            user=self.user,
            name="Physics Content",
            content="This is about quantum physics",
            key_concepts=["quantum", "physics"],
            processed=True
        )

    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    @patch.object(client_manager, 'is_qdrant_available', return_value=True)
    @patch.object(client_manager, 'qdrant_client')
    @patch.object(client_manager, 'get_embeddings', return_value=[0.1] * 1536)
    def test_search_content_success(self, mock_embeddings, mock_qdrant_client, mock_qdrant_available, mock_openai_client, mock_openai_available):
        # Mock OpenAI response for keyword extraction
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="physics, quantum"))]
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Mock Qdrant search response
        mock_search_result = [
            Mock(
                payload={
                    "content_id": self.content.id,
                    "chunk_id": "1_0",
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "name": "Physics Content",
                    "content": "Quantum physics basics",
                    "key_concepts": ["quantum"],
                    "difficulty_level": "intermediate",
                },
                score=0.95,
            )
        ]
        mock_qdrant_client.search.return_value = mock_search_result

        results = search_relevant_content("quantum physics", self.user.id, limit=3)

        assert len(results) == 1
        assert results[0].id == self.content.id

    @patch.object(client_manager, 'is_openai_available', return_value=False)
    def test_search_content_no_openai(self, mock_available):
        results = search_relevant_content("test query", self.user.id)
        # Should still work but skip keyword extraction
        assert results == []

    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    @patch.object(client_manager, 'is_qdrant_available', return_value=False)
    def test_search_content_no_qdrant(self, mock_openai_client, mock_openai_available, mock_qdrant_available):
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="physics"))]
        mock_openai_client.chat.completions.create.return_value = mock_response

        results = search_relevant_content("physics", self.user.id)
        # Should work with keyword search only
        assert len(results) == 1  # The physics content should be found


class TestGenerateAssistantResponse(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.session = ConversationSessionFactory(user=self.user)
        self.user_message = MessageFactory(
            session=self.session, 
            role="user", 
            content="What is Python?"
        )

    @patch("app.services.DebugService.store_debug_info")
    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    @patch.object(client_manager, 'is_qdrant_available', return_value=False)
    def test_generate_response_success(self, mock_qdrant_available, mock_openai_client, mock_openai_available, mock_debug_service):
        # Mock search function to avoid complex setup
        mock_content_search = Mock()
        mock_content_search.name = "Test Content"
        mock_content_search.key_concepts = ["python"]
        mock_content_search.content = "This is test content about Python programming."

        # Mock OpenAI response for assistant
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="I can help you with Python programming!"))
        ]
        mock_response.usage = Mock(total_tokens=50)
        mock_openai_client.chat.completions.create.return_value = mock_response

        with patch("app.llms.search_relevant_content") as mock_search:
            mock_search.return_value = ([mock_content_search], {})

            result = generate_assistant_response(
                str(self.session.id), self.user_message.id
            )

            assert result.role == "assistant"
            assert result.content == "I can help you with Python programming!"
            assert result.token_count == 50

    @patch("app.services.DebugService.store_debug_info")
    @patch.object(client_manager, 'is_openai_available', return_value=False)
    def test_generate_response_no_client(self, mock_available, mock_debug_service):
        with patch("app.llms.search_relevant_content") as mock_search:
            mock_search.return_value = ([], {})

            result = generate_assistant_response(
                str(self.session.id), self.user_message.id
            )

            assert result.role == "assistant"
            assert "error" in result.content.lower()

    @patch("app.services.DebugService.store_debug_info")
    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    def test_generate_response_openai_error(self, mock_openai_client, mock_openai_available, mock_debug_service):
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        with patch("app.llms.search_relevant_content") as mock_search:
            mock_search.return_value = ([], {})

            result = generate_assistant_response(
                str(self.session.id), self.user_message.id
            )

            assert result.role == "assistant"
            assert "error" in result.content.lower()
