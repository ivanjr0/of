"""
Integration tests for chat/conversation API endpoints.
Using mocks and stubs for external dependencies.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, Mock
from django.contrib.auth.models import User
from app.auth import generate_tokens
from tests.factories import (
    UserFactory,
    ConversationSessionFactory,
    MessageFactory,
    ContentFactory,
)
from django.test import TestCase
from rest_framework.test import APIClient
from app.models import ConversationSession, Message, Content
from app.client_manager import client_manager


class TestAuthAPI:
    """Integration tests for authentication endpoints"""

    def test_signup_success(self, api_client):
        """Test successful user signup"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com", 
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = api_client.post(
            "/api/auth/signup",
            data=json.dumps(user_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]

    def test_signup_duplicate_username(self, api_client):
        """Test signup with duplicate username"""
        User.objects.create_user(username="existinguser", password="password123")

        response = api_client.post(
            "/api/auth/signup",
            data=json.dumps({
                "username": "existinguser", 
                "email": "new@example.com",
                "password": "password123"
            }),
            content_type="application/json",
        )

        assert response.status_code == 400
        assert "Username already exists" in response.json()["error"]

    def test_login_success(self, api_client):
        """Test successful login"""
        # Create user
        user = User.objects.create_user(
            username="testuser",
            password="password123",
            email="test@example.com"
        )
        
        response = api_client.post(
            "/api/auth/login",
            data=json.dumps({
                "username": "testuser",
                "password": "password123"
            }),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        response = api_client.post(
            "/api/auth/login",
            data=json.dumps({
                "username": "nonexistent",
                "password": "wrongpassword"
            }),
            content_type="application/json",
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["error"]


class TestSessionAPI:
    """Integration tests for conversation session endpoints"""

    @pytest.fixture
    def auth_headers(self, test_user):
        """Generate auth headers for test user"""
        tokens = generate_tokens(test_user)
        return {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }

    def test_create_session_success(self, api_client, test_user, auth_headers):
        """Test successful session creation"""
        response = api_client.post(
            "/api/sessions",
            data=json.dumps({"title": "New Chat Session"}),
            content_type="application/json",
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Chat Session"
        assert "id" in data
        assert data["message_count"] == 0

    def test_create_session_default_title(self, api_client, test_user, auth_headers):
        """Test session creation with default title"""
        response = api_client.post(
            "/api/sessions",
            data=json.dumps({}),
            content_type="application/json",
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"].startswith("Conversation")

    def test_list_user_sessions(self, api_client, test_user, auth_headers):
        """Test listing user's sessions"""
        # Create sessions
        sessions = ConversationSessionFactory.create_batch(3, user=test_user)
        other_user_session = ConversationSessionFactory()  # Different user

        response = api_client.get("/api/sessions", **auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Verify message count annotation
        assert all("message_count" in item for item in data)

    def test_list_sessions_pagination(self, api_client, test_user, auth_headers):
        """Test session listing with pagination"""
        ConversationSessionFactory.create_batch(15, user=test_user)

        response = api_client.get(
            "/api/sessions?limit=5&offset=5",
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_delete_session_success(self, api_client, test_session, auth_headers):
        """Test session deletion"""
        # Create auth headers for the session owner
        tokens = generate_tokens(test_session.user)
        owner_auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }
        
        response = api_client.delete(
            f"/api/sessions/{test_session.id}",
            **owner_auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify soft delete
        test_session.refresh_from_db()
        assert test_session.is_deleted is True


class TestMessageAPI:
    """Integration tests for message endpoints with mocking"""

    @pytest.fixture
    def auth_headers(self, test_user):
        """Generate auth headers for test user"""
        tokens = generate_tokens(test_user)
        return {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }

    def test_get_session_messages(self, api_client, test_session):
        """Test retrieving session messages"""
        # Create auth headers for session owner
        tokens = generate_tokens(test_session.user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }
        
        # Create messages
        messages = MessageFactory.create_batch(5, session=test_session)

        response = api_client.get(
            f"/api/sessions/{test_session.id}/messages",
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 5

        # Verify ordering by timestamp
        timestamps = [msg["timestamp"] for msg in data["messages"]]
        assert timestamps == sorted(timestamps)

    def test_get_messages_invalid_session_id(self, api_client, auth_headers):
        """Test getting messages with invalid session ID"""
        response = api_client.get(
            "/api/sessions/invalid-uuid/messages",
            **auth_headers
        )

        assert response.status_code == 400
        assert "error" in response.json()

    @patch("app.services.DebugService.store_debug_info")
    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    @patch.object(client_manager, 'is_qdrant_available', return_value=False)
    def test_send_message_success(self, mock_qdrant_available, mock_openai_client, mock_openai_available, mock_debug_service):
        """Test successful message sending with assistant response"""
        
        # Mock keyword extraction response (for search)
        mock_keyword_response = Mock()
        mock_keyword_response.choices = [Mock(message=Mock(content="python, programming"))]
        
        # Mock assistant response
        mock_assistant_response = Mock()
        mock_assistant_response.choices = [
            Mock(message=Mock(content="I can help you with Python programming! Here's what you need to know..."))
        ]
        mock_assistant_response.usage = Mock(total_tokens=150)
        
        # Configure mock to return different responses for different calls
        mock_openai_client.chat.completions.create.side_effect = [
            mock_keyword_response,  # For search keywords
            mock_assistant_response  # For assistant response
        ]

        response = self.client.post(
            f"/api/chat/{self.session.id}/messages/",
            {"content": "Tell me about Python programming"},
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        
        # Should have both user and assistant messages
        assert data["user_message"]["content"] == "Tell me about Python programming"
        assert data["user_message"]["role"] == "user"
        
        assert data["assistant_message"]["role"] == "assistant"
        assert "Python programming" in data["assistant_message"]["content"]
        assert data["assistant_message"]["token_count"] == 150

        # Verify messages were created in database
        assert self.session.messages.count() == 2
        user_msg = self.session.messages.filter(role="user").first()
        assistant_msg = self.session.messages.filter(role="assistant").first()
        
        assert user_msg.content == "Tell me about Python programming"
        assert assistant_msg.token_count == 150

    def test_send_message_empty_content(self, api_client, test_session):
        """Test sending message with empty content"""
        # Create auth headers for session owner
        tokens = generate_tokens(test_session.user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }
        
        response = api_client.post(
            f"/api/sessions/{test_session.id}/messages",
            data=json.dumps({"content": ""}),
            content_type="application/json",
            **auth_headers
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_send_message_session_not_found(self, api_client, auth_headers):
        """Test sending message to non-existent session"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = api_client.post(
            f"/api/sessions/{fake_uuid}/messages",
            data=json.dumps({"content": "Hello"}),
            content_type="application/json",
            **auth_headers
        )

        assert response.status_code == 404
        assert "error" in response.json()

    @patch("app.services.DebugService.store_debug_info")  
    @patch.object(client_manager, 'is_openai_available', return_value=False)
    def test_send_message_no_openai_client(self, mock_available, mock_debug_service):
        """Test message sending when OpenAI client is not available"""
        
        response = self.client.post(
            f"/api/chat/{self.session.id}/messages/",
            {"content": "Hello"},
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        
        # Should have error message from assistant
        assert data["assistant_message"]["role"] == "assistant"
        assert "error" in data["assistant_message"]["content"].lower()

    @patch("app.services.DebugService.store_debug_info")
    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')  
    @patch.object(client_manager, 'is_qdrant_available', return_value=False)
    def test_send_message_with_relevant_content(self, mock_qdrant_available, mock_openai_client, mock_openai_available, mock_debug_service):
        """Test that assistant uses relevant content in responses"""
        
        # Create relevant content
        Content.objects.create(
            user=self.user,
            name="Python Basics",
            content="Python is a programming language that is easy to learn and powerful.",
            key_concepts=["python", "programming"],
            difficulty_level="beginner",
            estimated_study_time=30,
            processed=True
        )

        # Mock keyword extraction to return relevant keywords
        mock_keyword_response = Mock()
        mock_keyword_response.choices = [Mock(message=Mock(content="python, programming, basics"))]
        
        # Mock assistant response
        mock_assistant_response = Mock()
        mock_assistant_response.choices = [
            Mock(message=Mock(content="Based on your Python Basics content, Python is indeed easy to learn..."))
        ]
        mock_assistant_response.usage = Mock(total_tokens=200)
        
        mock_openai_client.chat.completions.create.side_effect = [
            mock_keyword_response,
            mock_assistant_response
        ]

        response = self.client.post(
            f"/api/chat/{self.session.id}/messages/",
            {"content": "What is Python?"},
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        
        # Assistant should reference the content
        assistant_content = data["assistant_message"]["content"]
        assert "Python Basics" in assistant_content or "python" in assistant_content.lower()

    @patch("app.services.DebugService.store_debug_info")
    @patch.object(client_manager, 'is_openai_available', return_value=True)
    @patch.object(client_manager, 'openai_client')
    @patch.object(client_manager, 'is_qdrant_available', return_value=False)
    def test_send_message_openai_error(self, mock_qdrant_available, mock_openai_client, mock_openai_available, mock_debug_service):
        """Test handling of OpenAI API errors"""
        
        # Mock OpenAI to raise an error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        response = self.client.post(
            f"/api/chat/{self.session.id}/messages/",
            {"content": "Hello"},
            content_type="application/json"
        )

        assert response.status_code == 201
        data = response.json()
        
        # Should still create user message but assistant should have error message
        assert data["user_message"]["content"] == "Hello"
        assert "error" in data["assistant_message"]["content"].lower()


class TestIntegrationScenarios:
    """Full integration test scenarios with mocking"""

    @patch.object(client_manager, 'openai_client')
    @patch.object(client_manager, 'qdrant_client')
    def test_full_conversation_flow(
        self, mock_qdrant, mock_openai, api_client, test_user
    ):
        """Test complete conversation flow with mocked external services"""
        # Generate auth headers
        tokens = generate_tokens(test_user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }
        
        # Mock Qdrant search
        mock_qdrant.search.return_value = [
            MagicMock(payload={"name": "Topic", "content": "Content"}, score=0.9)
        ]

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Based on the content..."))
        ]
        mock_response.usage = MagicMock(total_tokens=50)
        mock_openai.chat.completions.create.return_value = mock_response

        # Create session
        session_response = api_client.post(
            "/api/sessions",
            data=json.dumps({"title": "Test Conversation"}),
            content_type="application/json",
            **auth_headers
        )
        session_id = session_response.json()["id"]

        # Send message
        with patch("app.api.get_llm_functions") as mock_get_llm:
            mock_get_llm.return_value = (MagicMock(), MagicMock(), MagicMock())
            
            message_response = api_client.post(
                f"/api/sessions/{session_id}/messages",
                data=json.dumps({"content": "Explain decorators"}),
                content_type="application/json",
                **auth_headers
            )

        assert message_response.status_code == 200

        # Get messages
        messages_response = api_client.get(
            f"/api/sessions/{session_id}/messages",
            **auth_headers
        )
        messages_data = messages_response.json()

        assert "messages" in messages_data
        assert len(messages_data["messages"]) >= 1
        assert messages_data["messages"][0]["content"] == "Explain decorators"

    @patch("app.tasks.analyze_content_async")
    def test_content_to_conversation_flow(
        self, mock_analyze, api_client, test_user, mock_queue
    ):
        """Test flow from content creation to using it in conversation"""
        # Generate auth headers
        tokens = generate_tokens(test_user)
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {tokens['access_token']}",
        }
        
        # Mock content analysis
        mock_analyze.return_value = None  # Async task

        # Create content
        content_response = api_client.post(
            "/api/content",
            data=json.dumps(
                {
                    "name": "Python Advanced Topics",
                    "content": "Decorators, generators, and context managers...",
                }
            ),
            content_type="application/json",
            **auth_headers
        )
        content_id = content_response.json()["id"]

        # Verify analysis was queued
        mock_queue.enqueue.assert_called()

        # Create conversation session
        session_response = api_client.post(
            "/api/sessions",
            data=json.dumps({"title": "Learning Python"}),
            content_type="application/json",
            **auth_headers
        )
        session_id = session_response.json()["id"]

        # Both services are now ready to interact
        assert content_id is not None
        assert session_id is not None
