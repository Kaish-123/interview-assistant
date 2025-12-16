"""
Pydantic schemas for API request/response validation
"""
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# ============================================================================
# Chat Schemas
# ============================================================================

class MessageBase(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    images: Optional[List[str]] = Field(None, description="Base64 encoded images")


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    session_id: int
    content_type: str
    created_at: datetime
    is_bookmarked: bool
    
    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"
    system_prompt: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    summary: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChatSessionDetail(ChatSessionResponse):
    messages: List[MessageResponse]


# ============================================================================
# Prompt Template Schemas
# ============================================================================

class PromptTemplateBase(BaseModel):
    tab_name: str
    subtab_name: str
    prompt_text: str
    order_index: Optional[int] = 0


class PromptTemplateCreate(PromptTemplateBase):
    pass


class PromptTemplateUpdate(BaseModel):
    tab_name: Optional[str] = None
    subtab_name: Optional[str] = None
    prompt_text: Optional[str] = None
    order_index: Optional[int] = None


class PromptTemplateResponse(PromptTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TabWithSubtabs(BaseModel):
    tab_name: str
    subtabs: List[PromptTemplateResponse]


# ============================================================================
# Document Schemas
# ============================================================================

class DocumentCreate(BaseModel):
    filename: str
    doc_type: str = "other"
    content: str
    session_id: Optional[int] = None


class DocumentResponse(BaseModel):
    id: int
    filename: str
    doc_type: str
    content: str
    session_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Setup Profile Schemas
# ============================================================================

class SetupProfileCreate(BaseModel):
    name: str
    prompt_ids: List[int]


class SetupProfileResponse(BaseModel):
    id: int
    name: str
    prompt_ids: List[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Audio Schemas
# ============================================================================

class TranscriptionRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio data")
    format: str = Field(default="webm", description="Audio format: webm, wav, mp3")
    prompt: Optional[str] = Field(None, description="Optional context for better transcription")


class TranscriptionResponse(BaseModel):
    text: str
    duration: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


# ============================================================================
# Chat Completion Schemas
# ============================================================================

class ChatCompletionRequest(BaseModel):
    session_id: int
    message: str
    images: Optional[List[str]] = None
    model: str = Field(default="gpt-4o", description="Model to use: gpt-4o, gpt-4o-mini, gpt-4-turbo")
    answer_mode: str = Field(default="default", description="Answer mode: default, quick, detailed, code")
    optimization_mode: bool = Field(default=True, description="Enable context optimization")
    stream: bool = Field(default=True, description="Enable streaming response")


class ChatCompletionResponse(BaseModel):
    message: MessageResponse
    tokens_used: Optional[int] = None
    model: str


# ============================================================================
# Preference Schemas
# ============================================================================

class PreferenceUpdate(BaseModel):
    key: str
    value: Any


class PreferenceResponse(BaseModel):
    key: str
    value: Any
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Performance Diagnostic Schemas
# ============================================================================

class PerformanceDiagnostic(BaseModel):
    total_messages: int
    system_messages: int
    user_messages: int
    assistant_messages: int
    images_count: int
    estimated_total_tokens: int
    estimated_system_tokens: int
    estimated_conversation_tokens: int
    estimated_image_tokens: int
    optimization_mode: bool
    will_send_messages: int
    will_send_tokens: int
    has_summary: bool
    issues: List[str]
    recommendations: List[str]


# ============================================================================
# Quick Setup Schemas
# ============================================================================

class QuickSetupRequest(BaseModel):
    session_id: int
    prompt_ids: List[int]
    additional_text: Optional[str] = None
    images: Optional[List[str]] = None


# ============================================================================
# Bookmark Schemas
# ============================================================================

class BookmarkToggle(BaseModel):
    message_id: int
    is_bookmarked: bool


class BookmarkResponse(BaseModel):
    id: int
    message_preview: str
    session_id: int
    created_at: datetime





