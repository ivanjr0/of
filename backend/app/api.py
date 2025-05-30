import re
import uuid
from datetime import datetime
from typing import List, Optional

# import django_rq
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from ninja import NinjaAPI
from django.conf import settings
from django.db.models import Count

from app.models import Content, ConversationSession, Message
from app.schemas import (
    ContentRequest,
    ContentResponse,
    SignUpRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfileResponse,
    SessionRequest,
    SessionResponse,
    MessageRequest,
    MessageResponse,
    ChatResponse,
    MessagesWithDebugResponse,
)
from app.tasks import analyze_content_async
from app.services import ContentService, SessionService, MessageService, DebugService
from app.auth import jwt_auth, generate_tokens, verify_refresh_token
from app.llms import (
    analyze_content,
    search_relevant_content,
    generate_assistant_response,
)
from app.queue_manager import queue_manager

# Create Ninja API instance
api = NinjaAPI(
    title="Content Management API", description="Educational Content Analysis System"
)


# LLM function imports (dynamic to avoid circular dependency)
def get_llm_functions():
    """Dynamically import LLM functions to avoid circular imports"""

    return analyze_content, search_relevant_content, generate_assistant_response


# Authentication Endpoints (No auth required)
@api.post("/auth/signup", response=TokenResponse)
def signup(request, data: SignUpRequest):
    """Create a new user account"""
    try:
        # Input validation
        if not data.username or not data.username.strip():
            return JsonResponse({"error": "Username is required"}, status=400)
        
        if not data.email or not data.email.strip():
            return JsonResponse({"error": "Email is required"}, status=400)
            
        if not data.password or len(data.password) < 8:
            return JsonResponse({"error": "Password must be at least 8 characters long"}, status=400)
        
        # Additional validation
        if len(data.username) < 3:
            return JsonResponse({"error": "Username must be at least 3 characters long"}, status=400)
            
        if "@" not in data.email:
            return JsonResponse({"error": "Please provide a valid email address"}, status=400)
        
        # Check if user already exists
        if User.objects.filter(username=data.username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)
        
        if User.objects.filter(email=data.email).exists():
            return JsonResponse({"error": "Email already exists"}, status=400)
        
        # Create new user
        user = User.objects.create_user(
            username=data.username.strip(),
            email=data.email.strip().lower(),
            password=data.password,
            first_name=data.first_name.strip() if data.first_name else "",
            last_name=data.last_name.strip() if data.last_name else ""
        )
        
        # Generate tokens
        tokens = generate_tokens(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user_id=user.id,
            username=user.username,
            email=user.email
        )
        
    except IntegrityError:
        return JsonResponse({"error": "Failed to create user"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        print(f"Signup error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@api.post("/auth/login", response=TokenResponse)
def login(request, data: LoginRequest):
    """Login with username and password"""
    try:
        # Input validation
        if not data.username or not data.username.strip():
            return JsonResponse({"error": "Username is required"}, status=400)
            
        if not data.password:
            return JsonResponse({"error": "Password is required"}, status=400)
        
        user = authenticate(username=data.username.strip(), password=data.password)
        
        if not user:
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        
        if not user.is_active:
            return JsonResponse({"error": "Account is disabled"}, status=401)
        
        # Generate tokens
        tokens = generate_tokens(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user_id=user.id,
            username=user.username,
            email=user.email
        )
        
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        print(f"Login error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@api.post("/auth/refresh", response=TokenResponse)
def refresh_token(request, data: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        if not data.refresh_token or not data.refresh_token.strip():
            return JsonResponse({"error": "Refresh token is required"}, status=400)
            
        user = verify_refresh_token(data.refresh_token)
        
        if not user:
            return JsonResponse({"error": "Invalid refresh token"}, status=401)
        
        # Generate new tokens
        tokens = generate_tokens(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user_id=user.id,
            username=user.username,
            email=user.email
        )
        
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        print(f"Token refresh error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


@api.get("/auth/profile", response=UserProfileResponse, auth=jwt_auth)
def get_profile(request):
    """Get current user profile"""
    user = request.user
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        date_joined=user.date_joined,
        is_active=user.is_active
    )


# Protected API Endpoints (Require authentication)
@api.post("/content", auth=jwt_auth)
def post_content(request, data: ContentRequest):
    try:
        # Use service for sanitization
        sanitized_content = ContentService.sanitize_content(data.content)
        sanitized_name = ContentService.sanitize_name(data.name)

        content = Content.objects.create(
            name=sanitized_name, 
            content=sanitized_content, 
            user=request.user,  # Associate with authenticated user
            analysis_status="pending"
        )

        # Enqueue async content analysis using queue manager
        queue_manager.enqueue(analyze_content_async, content.id)

        return ContentResponse(
            id=content.id,
            name=content.name,
            content=content.content,
            created_at=content.created_at,
            updated_at=content.updated_at,
            processed=content.processed,
            key_concepts=content.key_concepts,
            difficulty_level=content.difficulty_level,
            estimated_study_time=content.estimated_study_time,
            user_id=content.user_id
        )
    except Exception as e:
        print(f"Error creating content: {str(e)}")
        return JsonResponse({"error": f"Invalid request data: {str(e)}"}, status=400)


@api.get("/content/{content_id}", response=ContentResponse, auth=jwt_auth)
def get_content(request, content_id: int):
    try:
        # Only allow users to access their own content
        content = Content.objects.get(id=content_id, user=request.user, is_deleted=False)
        return ContentResponse(
            id=content.id,
            name=content.name,
            content=content.content,
            created_at=content.created_at,
            updated_at=content.updated_at,
            processed=content.processed,
            key_concepts=content.key_concepts,
            difficulty_level=content.difficulty_level,
            estimated_study_time=content.estimated_study_time,
            user_id=content.user_id
        )
    except Content.DoesNotExist:
        return JsonResponse({"error": "Content not found"}, status=404)


@api.get("/content", response=List[ContentResponse], auth=jwt_auth)
def list_contents(request, limit: Optional[int] = 20, offset: Optional[int] = 0):
    safe_limit, safe_offset = ContentService.validate_pagination_params(limit, offset)
    # Only show user's own content
    contents = Content.objects.filter(
        user=request.user, 
        is_deleted=False
    ).order_by("-created_at")[safe_offset : safe_offset + safe_limit]
    
    return [
        ContentResponse(
            id=content.id,
            name=content.name,
            content=content.content,
            created_at=content.created_at,
            updated_at=content.updated_at,
            processed=content.processed,
            key_concepts=content.key_concepts,
            difficulty_level=content.difficulty_level,
            estimated_study_time=content.estimated_study_time,
            user_id=content.user_id
        ) for content in contents
    ]


@api.get("/health")
def health_check(request):
    # Health check endpoint for service monitoring
    return {"status": "ok", "service": "content-management-backend"}


@api.delete("/content/{content_id}", auth=jwt_auth)
def delete_content(request, content_id: int):
    # Only allow users to delete their own content
    updated = Content.all_objects.filter(
        id=content_id, 
        user=request.user
    ).update(is_deleted=True)
    if updated == 0:
        return JsonResponse({"error": "Content not found"}, status=404)
    return {"status": "success"}


# Conversational Assistant Endpoints


@api.post("/sessions", response=SessionResponse, auth=jwt_auth)
def create_session(request, data: SessionRequest):
    try:
        title = data.title or SessionService.generate_default_title()
        session = ConversationSession.objects.create(user=request.user, title=title)

        return SessionResponse(
            id=str(session.id),
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0,
        )
    except Exception as e:
        return JsonResponse({"error": f"Session creation failed: {str(e)}"}, status=400)


@api.get("/sessions", response=List[SessionResponse], auth=jwt_auth)
def list_user_sessions(
    request, limit: Optional[int] = 20, offset: Optional[int] = 0
):
    """List sessions for the authenticated user"""
    safe_limit, safe_offset = ContentService.validate_pagination_params(
        limit, offset
    )

    # Use annotate to get message count in a single query (eliminates N+1)
    sessions = ConversationSession.objects.filter(
        user=request.user, is_deleted=False
    ).annotate(
        message_count=Count("messages")
    ).select_related("user")[safe_offset : safe_offset + safe_limit]

    return [
        SessionResponse(
            id=str(session.id),
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=session.message_count,  # Now using annotated field
        )
        for session in sessions
    ]


@api.get("/sessions/{session_id}/messages", response=MessagesWithDebugResponse, auth=jwt_auth)
def get_session_messages(
    request, session_id: str, limit: Optional[int] = 50, offset: Optional[int] = 0
):
    if not SessionService.validate_session_id(session_id):
        return JsonResponse({"error": "Invalid session ID format"}, status=400)

    try:
        # Ensure user owns the session
        session = ConversationSession.objects.get(
            id=session_id, 
            user=request.user, 
            is_deleted=False
        )
        safe_limit, safe_offset = ContentService.validate_pagination_params(
            limit, offset
        )
        messages = session.messages.order_by("timestamp")[
            safe_offset : safe_offset + safe_limit
        ]
        
        message_responses = [
            MessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                timestamp=message.timestamp,
                token_count=message.token_count
            ) for message in messages
        ]
        
        # Get debug info for this session
        debug_info = DebugService.get_debug_info(session_id)
        
        # Convert debug_info to schema format if it exists
        debug_response = None
        if debug_info:
            from app.schemas import DebugInfo, DebugPassageInfo, DebugQueryAnalysis, DebugProcessingInfo
            
            try:
                debug_response = DebugInfo(
                    relevant_passages=[
                        DebugPassageInfo(**passage) for passage in debug_info.get("relevant_passages", [])
                    ],
                    query_analysis=DebugQueryAnalysis(**debug_info.get("query_analysis", {})),
                    processing_info=DebugProcessingInfo(**debug_info.get("processing_info", {}))
                )
            except Exception as e:
                print(f"Error creating debug response: {e}")
                debug_response = None
        
        return MessagesWithDebugResponse(
            messages=message_responses,
            debug_info=debug_response
        )
        
    except ConversationSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)


@api.post("/sessions/{session_id}/messages", response=ChatResponse, auth=jwt_auth)
def send_message(request, session_id: str, data: MessageRequest):
    if not SessionService.validate_session_id(session_id):
        return JsonResponse({"error": "Invalid session ID format"}, status=400)

    if not MessageService.validate_message_content(data.content):
        return JsonResponse({"error": "Invalid message content"}, status=400)

    try:
        # Ensure user owns the session
        session = ConversationSession.objects.get(
            id=session_id, 
            user=request.user, 
            is_deleted=False
        )

        # Save user message
        user_message = Message.objects.create(
            session=session, role="user", content=data.content
        )

        # Get LLM functions dynamically
        _, _, generate_assistant_response = get_llm_functions()
        queue_manager.enqueue(generate_assistant_response, session.id, user_message.id)

        return ChatResponse(
            response=MessageService.get_processing_response(),
            session_id=str(session.id),
            relevant_content=[],
        )
    except ConversationSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)


@api.delete("/sessions/{session_id}", auth=jwt_auth)
def delete_session(request, session_id: str):
    try:
        # Only allow users to delete their own sessions
        session = ConversationSession.objects.get(
            id=session_id,
            user=request.user
        )
        session.is_deleted = True
        session.save()
        return {"status": "success"}
    except ConversationSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)


# Background Job Management Endpoints


@api.get("/content/{content_id}/status", auth=jwt_auth)
def get_content_analysis_status(request, content_id: int):
    """Get the analysis status of a content item"""
    try:
        # Ensure user owns the content
        content = Content.objects.get(id=content_id, user=request.user)
        response = {
            "content_id": content_id,
            "analysis_status": content.analysis_status,
            "processed": content.processed,
        }

        # Include analysis results if completed
        if content.analysis_status == "completed" and hasattr(content, "analysis"):
            analysis = content.analysis
            response.update(
                {
                    "key_concepts": analysis.key_concepts,
                    "difficulty_level": analysis.difficulty_level,
                    "estimated_study_time": analysis.estimated_study_time,
                }
            )

        return response
    except Content.DoesNotExist:
        return JsonResponse({"error": "Content not found"}, status=404)


@api.post("/content/{content_id}/reanalyze", auth=jwt_auth)
def reanalyze_content(request, content_id: int):
    """Trigger re-analysis of a specific content item"""
    try:
        # Ensure user owns the content
        content = Content.objects.get(id=content_id, user=request.user)

        # Reset status and enqueue for analysis
        content.analysis_status = "pending"
        content.save()

        queue_manager.enqueue(analyze_content_async, content.id)

        return {
            "status": "success",
            "message": f"Content {content_id} queued for re-analysis",
        }
    except Content.DoesNotExist:
        return JsonResponse({"error": "Content not found"}, status=404)


@api.get("/jobs/stats")
def get_job_stats(request):
    """Get statistics about background jobs"""
    return {"queues": {"default": queue_manager.get_queue_stats()}}
