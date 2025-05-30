"""
Main pytest configuration and fixtures for the test suite.
Based on pytest-django documentation: https://pytest-django.readthedocs.io/en/latest/
"""

import os
import sys
from unittest.mock import MagicMock

os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

import django

django.setup()

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from faker import Faker
from app.models import Content, ConversationSession, Message
from tests.factories import UserFactory, ConversationSessionFactory

fake = Faker()

# Mock settings attributes for tests
import settings
from app.client_manager import client_manager

# Force override the client_manager attributes with mocks
client_manager._openai_client = MagicMock()
client_manager._qdrant_client = MagicMock()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This is equivalent to marking all tests with @pytest.mark.django_db
    """
    pass


@pytest.fixture
def api_client():
    """Django test client for API testing"""
    return Client()


@pytest.fixture
def test_user(db):
    """Create a test user"""
    return UserFactory(username="testuser", email="test@example.com", is_active=True)


@pytest.fixture
def admin_user(admin_user):
    """Use the built-in admin_user fixture from pytest-django"""
    return admin_user


@pytest.fixture
def test_content():
    """Create test content"""
    return Content.objects.create(
        name="Test Content",
        content="This is test educational content about Python programming.",
        processed=False,
    )


@pytest.fixture
def processed_content():
    """Create processed test content with analysis results"""
    return Content.objects.create(
        name="Processed Content",
        content="Advanced Python concepts including decorators and metaclasses.",
        processed=True,
        key_concepts=["decorators", "metaclasses", "advanced Python"],
        difficulty_level="advanced",
        estimated_study_time=45,
    )


@pytest.fixture
def test_session(test_user):
    """Create a test conversation session"""
    return ConversationSessionFactory(user=test_user, title="Test Session")


@pytest.fixture
def test_message(test_session):
    """Create a test message"""
    return Message.objects.create(
        session=test_session, role="user", content="What are Python decorators?"
    )


@pytest.fixture
def mock_openai_client(mocker):
    """Mock OpenAI client for testing"""
    mock_client = mocker.MagicMock()
    mocker.patch.object(client_manager, '_openai_client', mock_client)
    mocker.patch.object(client_manager, 'is_openai_available', return_value=True)
    return mock_client


@pytest.fixture
def mock_queue(mocker):
    """Mock queue manager for testing"""
    mock_queue_manager = mocker.patch("app.queue_manager.queue_manager")
    mock_queue_manager.enqueue.return_value = MagicMock(id="test-job-id")
    mock_queue_manager.is_available.return_value = True
    mock_queue_manager.get_queue_stats.return_value = {"status": "mocked"}
    return mock_queue_manager


@pytest.fixture
def mock_qdrant_client(mocker):
    """Mock Qdrant client for vector search testing"""
    mock_client = mocker.MagicMock()
    mocker.patch.object(client_manager, '_qdrant_client', mock_client)
    mocker.patch.object(client_manager, 'is_qdrant_available', return_value=True)
    return mock_client


@pytest.fixture
def api_headers():
    """Common API headers"""
    return {
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_content_data():
    """Sample content data for testing"""
    return {"name": fake.sentence(nb_words=4), "content": fake.text(max_nb_chars=500)}


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {"username": fake.user_name(), "email": fake.email()}


@pytest.fixture(autouse=True)
def setup_test_mocks(mocker):
    """Automatically mock external dependencies for all tests"""
    # Mock client_manager OpenAI client
    mock_client = mocker.MagicMock()
    mocker.patch.object(client_manager, '_openai_client', mock_client)
    mocker.patch.object(client_manager, 'is_openai_available', return_value=True)
    mock_client.chat.completions.create.return_value = mocker.MagicMock(
        choices=[
            mocker.MagicMock(
                message=mocker.MagicMock(
                    content='{"concepts": ["test"], "difficulty_level": "beginner", "estimated_minutes": 30}'
                )
            )
        ],
        usage=mocker.MagicMock(total_tokens=100)
    )
    
    # Mock client_manager Qdrant client
    mock_qdrant = mocker.MagicMock()
    mocker.patch.object(client_manager, '_qdrant_client', mock_qdrant)
    mocker.patch.object(client_manager, 'is_qdrant_available', return_value=True)
    mock_qdrant.upsert.return_value = None
    mock_qdrant.search.return_value = []
    
    # Mock embeddings function
    mocker.patch.object(client_manager, 'get_embeddings', return_value=[0.1] * 1536)
    mocker.patch.object(client_manager, 'get_embedding_model', return_value='openai')
    
    # Mock Redis client
    mock_redis = mocker.patch("redis.Redis")
    mock_redis.from_url.return_value = mocker.MagicMock()
