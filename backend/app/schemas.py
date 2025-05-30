from datetime import datetime
from typing import List, Optional
from ninja import Schema


class ContentRequest(Schema):
    name: str
    content: str


class ContentResponse(Schema):
    id: int
    name: str
    content: str
    created_at: datetime
    updated_at: datetime
    processed: bool
    key_concepts: Optional[List[str]]
    difficulty_level: Optional[str]
    estimated_study_time: Optional[int]
    user_id: int  # Added to show content ownership


class ContentAnalysisResponse(Schema):
    id: int
    name: str
    key_concepts: List[str]
    difficulty_level: str
    estimated_study_time: int
    processed: bool


# Authentication Schemas
class SignUpRequest(Schema):
    username: str
    email: str
    password: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""


class LoginRequest(Schema):
    username: str
    password: str


class TokenResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user_id: int
    username: str
    email: str


class RefreshTokenRequest(Schema):
    refresh_token: str


class UserProfileResponse(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    date_joined: datetime
    is_active: bool


# Conversational Assistant Schemas
class SessionRequest(Schema):
    title: Optional[str] = None


class SessionResponse(Schema):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class MessageRequest(Schema):
    content: str


class MessageResponse(Schema):
    id: int
    role: str
    content: str
    timestamp: datetime
    token_count: Optional[int]


class DebugPassageInfo(Schema):
    name: str
    content: str
    key_concepts: List[str]
    difficulty_level: str
    score: float
    chunk_info: Optional[dict] = None


class DebugQueryAnalysis(Schema):
    original_query: str
    embedding_model: str
    search_time_ms: float
    total_indexed_contents: int


class DebugProcessingInfo(Schema):
    generation_time_ms: float
    model: str
    tokens_used: Optional[int]
    context_length: int


class DebugInfo(Schema):
    relevant_passages: List[DebugPassageInfo]
    query_analysis: DebugQueryAnalysis
    processing_info: DebugProcessingInfo


class MessagesWithDebugResponse(Schema):
    messages: List[MessageResponse]
    debug_info: Optional[DebugInfo] = None


class ChatRequest(Schema):
    message: str


class ChatResponse(Schema):
    response: str
    session_id: str
    relevant_content: List[str]
