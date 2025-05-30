"""
Unit tests for Django models.
Using pytest-django for database access.
"""

import pytest
from django.db import IntegrityError
from app.models import Content, User, ConversationSession, Message
from tests.factories import (
    UserFactory,
    ContentFactory,
    ProcessedContentFactory,
    ConversationSessionFactory,
    MessageFactory,
)


class TestContentModel:
    """Test Content model functionality"""

    def test_content_creation(self):
        """Test basic content creation"""
        content = ContentFactory()
        assert content.name
        assert content.content
        assert not content.processed
        assert not content.is_deleted

    def test_processed_content_creation(self):
        """Test processed content with analysis results"""
        content = ProcessedContentFactory()
        assert content.processed
        assert content.key_concepts is not None
        assert content.difficulty_level in [
            "beginner",
            "intermediate",
            "advanced",
            "expert",
        ]
        assert content.estimated_study_time >= 10

    def test_content_soft_delete(self):
        """Test soft delete functionality"""
        content = ContentFactory()
        content.is_deleted = True
        content.save()

        # Test that default manager excludes deleted content
        assert Content.objects.filter(id=content.id).count() == 0
        # Test that all_objects manager includes deleted content
        assert Content.all_objects.filter(id=content.id).count() == 1

    def test_content_manager_methods(self):
        """Test custom manager methods"""
        # Create mixed content
        unprocessed = ContentFactory(processed=False)
        processed = ProcessedContentFactory(processed=True)

        # Test get_processed
        processed_contents = Content.objects.get_processed()
        assert processed in processed_contents
        assert unprocessed not in processed_contents

        # Test get_unprocessed
        unprocessed_contents = Content.objects.get_unprocessed()
        assert unprocessed in unprocessed_contents
        assert processed not in unprocessed_contents

    def test_content_ordering(self):
        """Test default ordering by created_at"""
        older = ContentFactory()
        newer = ContentFactory()

        contents = list(Content.objects.all())
        # Newer content should come first (descending order)
        assert contents[0].id == newer.id
        assert contents[1].id == older.id


class TestUserModel:
    """Test User model functionality"""

    def test_user_creation(self):
        """Test basic user creation"""
        user = UserFactory()
        assert user.username
        assert user.email
        assert user.is_active

    def test_username_uniqueness(self):
        """Test that username must be unique"""
        user1 = UserFactory(username="testuser")
        with pytest.raises(IntegrityError):
            user2 = UserFactory(username="testuser")


class TestConversationSessionModel:
    """Test ConversationSession model functionality"""

    def test_session_creation(self):
        """Test basic session creation"""
        session = ConversationSessionFactory()
        assert session.id  # Should be UUID
        assert session.user
        assert session.title
        assert not session.is_deleted

    def test_session_uuid_primary_key(self):
        """Test that session uses UUID as primary key"""
        session = ConversationSessionFactory()
        assert len(str(session.id)) == 36  # UUID4 format

    def test_session_user_relationship(self):
        """Test relationship with User model"""
        user = UserFactory()
        session = ConversationSessionFactory(user=user)

        assert session.user == user
        assert session in user.sessions.all()

    def test_session_manager_with_message_count(self):
        """Test with_message_count annotation"""
        session = ConversationSessionFactory()
        # Create messages
        MessageFactory.create_batch(3, session=session)

        annotated_session = ConversationSession.objects.with_message_count().get(
            id=session.id
        )
        assert annotated_session.message_count == 3

    def test_session_manager_for_user(self):
        """Test for_user filtering"""
        user1 = UserFactory()
        user2 = UserFactory()

        session1 = ConversationSessionFactory(user=user1)
        session2 = ConversationSessionFactory(user=user2)

        user1_sessions = ConversationSession.objects.for_user(user1)
        assert session1 in user1_sessions
        assert session2 not in user1_sessions


class TestMessageModel:
    """Test Message model functionality"""

    def test_message_creation(self):
        """Test basic message creation"""
        message = MessageFactory()
        assert message.session
        assert message.role in ["user", "assistant"]
        assert message.content
        assert message.timestamp

    def test_message_session_relationship(self):
        """Test relationship with ConversationSession"""
        session = ConversationSessionFactory()
        message = MessageFactory(session=session)

        assert message.session == session
        assert message in session.messages.all()

    def test_message_ordering(self):
        """Test default ordering by timestamp"""
        session = ConversationSessionFactory()
        older_msg = MessageFactory(session=session)
        newer_msg = MessageFactory(session=session)

        messages = list(session.messages.all())
        # Messages should be ordered by timestamp (ascending)
        assert messages[0].id == older_msg.id
        assert messages[1].id == newer_msg.id

    def test_message_cascade_delete(self):
        """Test that messages are deleted when session is deleted"""
        session = ConversationSessionFactory()
        message = MessageFactory(session=session)

        session.delete()
        assert Message.objects.filter(id=message.id).count() == 0
