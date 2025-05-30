"""
Optimized Django models with custom managers and database indexes.
"""

import uuid
from django.db import models
from django.db.models import Count, Prefetch
from django.contrib.auth.models import User


class ActiveManager(models.Manager):
    """Manager that filters out soft-deleted items by default"""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def with_deleted(self):
        """Include soft-deleted items"""
        return super().get_queryset()


class ContentManager(ActiveManager):
    """Custom manager for Content model with optimized queries"""

    def get_processed(self):
        """Get only processed content"""
        return self.filter(processed=True)

    def get_unprocessed(self):
        """Get only unprocessed content"""
        return self.filter(processed=False)


class Content(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contents")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    processed = models.BooleanField(default=False, db_index=True)

    # Analysis fields
    key_concepts = models.JSONField(null=True, blank=True)
    difficulty_level = models.CharField(
        max_length=50, null=True, blank=True, db_index=True
    )
    estimated_study_time = models.IntegerField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    # Analysis status tracking
    ANALYSIS_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    analysis_status = models.CharField(
        max_length=20, choices=ANALYSIS_STATUS_CHOICES, default="pending", db_index=True
    )

    # Managers
    objects = ContentManager()
    all_objects = models.Manager()  # Includes deleted

    class Meta:
        app_label = "app"
        indexes = [
            models.Index(fields=["-created_at", "is_deleted"]),
            models.Index(fields=["processed", "is_deleted"]),
            models.Index(fields=["user", "-created_at", "is_deleted"]),
        ]
        ordering = ["-created_at"]


class AnalysisResult(models.Model):
    """Stores detailed analysis results for content"""

    content = models.OneToOneField(
        Content, on_delete=models.CASCADE, related_name="analysis"
    )
    key_concepts = models.JSONField()
    difficulty_level = models.CharField(max_length=50, db_index=True)
    estimated_study_time = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app"
        indexes = [
            models.Index(fields=["created_at"]),
        ]


class ContentChunk(models.Model):
    """Stores chunked content for better vector search and retrieval"""

    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, related_name="chunks"
    )
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()  # Position of chunk in original content
    total_chunks = models.IntegerField()  # Total number of chunks for this content
    start_char = (
        models.IntegerField()
    )  # Starting character position in original content
    end_char = models.IntegerField()  # Ending character position in original content
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "app"
        indexes = [
            models.Index(fields=["content", "chunk_index"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["content", "chunk_index"]
        unique_together = [["content", "chunk_index"]]


class SessionManager(ActiveManager):
    """Custom manager for ConversationSession with optimized queries"""

    def with_message_count(self):
        """Annotate sessions with message count to avoid N+1 queries"""
        return self.annotate(message_count=Count("messages"))

    def for_user(self, user):
        """Get sessions for a specific user with optimizations"""
        return self.filter(user=user).select_related("user")


class ConversationSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=255, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    # Managers
    objects = SessionManager()
    all_objects = models.Manager()

    class Meta:
        app_label = "app"
        indexes = [
            models.Index(fields=["user", "-updated_at", "is_deleted"]),
            models.Index(fields=["-updated_at", "is_deleted"]),
        ]
        ordering = ["-updated_at"]


class Message(models.Model):
    session = models.ForeignKey(
        ConversationSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(
        max_length=20,
        choices=[("user", "User"), ("assistant", "Assistant")],
        db_index=True,
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    token_count = models.IntegerField(null=True, blank=True)

    objects = models.Manager()

    class Meta:
        app_label = "app"
        indexes = [
            models.Index(fields=["session", "timestamp"]),
            models.Index(fields=["session", "role", "timestamp"]),
        ]
        ordering = ["timestamp"]
