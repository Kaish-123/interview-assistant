"""
Chat Routes - Handle chat sessions and messages
"""
import json
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database.db import get_db
from models.schemas import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionDetail,
    MessageCreate, MessageResponse, ChatCompletionRequest,
    BookmarkToggle, PerformanceDiagnostic, QuickSetupRequest
)
from services.chat_service import chat_service
from services.openai_service import openai_service

router = APIRouter(prefix="/chat", tags=["Chat"])


# ============================================================================
# Session Endpoints
# ============================================================================

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    data: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    session = chat_service.create_session(
        db, 
        title=data.title or "New Chat",
        system_prompt=data.system_prompt
    )
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=1,
        summary=session.summary
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_sessions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all chat sessions"""
    sessions = chat_service.get_all_sessions(db, skip=skip, limit=limit)
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages),
            summary=s.summary
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get a specific session with messages"""
    session = chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = chat_service.get_messages(db, session_id)
    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(messages),
        summary=session.summary,
        messages=[
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                content_type=m.content_type,
                images=m.images,
                created_at=m.created_at,
                is_bookmarked=m.is_bookmarked
            )
            for m in messages
        ]
    )


@router.put("/sessions/{session_id}/title")
def update_session_title(
    session_id: int,
    title: str,
    db: Session = Depends(get_db)
):
    """Update session title"""
    session = chat_service.update_session_title(db, session_id, title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "title": session.title}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Delete a chat session"""
    success = chat_service.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}


# ============================================================================
# Message Endpoints
# ============================================================================

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
def add_message(
    session_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Add a message to a session"""
    session = chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    message = chat_service.add_message(
        db,
        session_id=session_id,
        role=data.role,
        content=data.content,
        images=data.images
    )
    
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        content_type=message.content_type,
        images=message.images,
        created_at=message.created_at,
        is_bookmarked=message.is_bookmarked
    )


@router.post("/sessions/{session_id}/complete")
async def complete_chat(
    session_id: int,
    request: ChatCompletionRequest,
    db: Session = Depends(get_db)
):
    """Get a non-streaming chat completion"""
    session = chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add user message
    user_msg = chat_service.add_message(
        db,
        session_id=session_id,
        role="user",
        content=request.message,
        images=request.images
    )
    
    # Get messages for API
    messages = chat_service.get_messages_for_api(
        db, 
        session_id, 
        optimization_mode=request.optimization_mode
    )
    
    # Get completion
    result = await openai_service.get_chat_completion(
        messages,
        model=request.model,
        answer_mode=request.answer_mode
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Add assistant message
    assistant_msg = chat_service.add_message(
        db,
        session_id=session_id,
        role="assistant",
        content=result["content"]
    )
    
    return {
        "message": MessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            content_type=assistant_msg.content_type,
            images=assistant_msg.images,
            created_at=assistant_msg.created_at,
            is_bookmarked=assistant_msg.is_bookmarked
        ),
        "tokens_used": result["tokens_used"],
        "model": request.model
    }


# ============================================================================
# Bookmark Endpoints
# ============================================================================

@router.post("/bookmarks/toggle")
def toggle_bookmark(data: BookmarkToggle, db: Session = Depends(get_db)):
    """Toggle bookmark on a message"""
    message = chat_service.toggle_bookmark(db, data.message_id, data.is_bookmarked)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True, "is_bookmarked": message.is_bookmarked}


@router.get("/sessions/{session_id}/bookmarks", response_model=List[MessageResponse])
def get_session_bookmarks(session_id: int, db: Session = Depends(get_db)):
    """Get all bookmarked messages in a session"""
    messages = chat_service.get_bookmarked_messages(db, session_id)
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            content_type=m.content_type,
            images=m.images,
            created_at=m.created_at,
            is_bookmarked=m.is_bookmarked
        )
        for m in messages
    ]


# ============================================================================
# Performance Endpoints
# ============================================================================

@router.get("/sessions/{session_id}/diagnostics", response_model=PerformanceDiagnostic)
def get_diagnostics(session_id: int, db: Session = Depends(get_db)):
    """Get performance diagnostics for a session"""
    session = chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return chat_service.get_performance_diagnostic(db, session_id)


@router.post("/sessions/{session_id}/summarize")
async def summarize_session(session_id: int, db: Session = Depends(get_db)):
    """Generate conversation summary"""
    session = chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    summary = await chat_service.update_session_summary(db, session_id)
    return {"success": True, "summary": summary}


# ============================================================================
# Quick Setup Endpoint
# ============================================================================

@router.post("/sessions/{session_id}/quick-setup")
async def quick_setup(
    session_id: int,
    request: QuickSetupRequest,
    db: Session = Depends(get_db)
):
    """Apply multiple prompts in one message"""
    from database.db import PromptTemplate
    
    session = chat_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get prompts
    prompts = db.query(PromptTemplate)\
        .filter(PromptTemplate.id.in_(request.prompt_ids))\
        .all()
    
    if not prompts:
        raise HTTPException(status_code=400, detail="No valid prompts found")
    
    # Combine prompts
    prompt_texts = [p.prompt_text for p in prompts]
    if request.additional_text:
        prompt_texts.insert(0, request.additional_text)
    
    combined_prompt = "\n\n---\n\n".join(prompt_texts)
    
    # Add user message
    user_msg = chat_service.add_message(
        db,
        session_id=session_id,
        role="user",
        content=combined_prompt,
        images=request.images
    )
    
    # Get completion
    messages = chat_service.get_messages_for_api(db, session_id, optimization_mode=True)
    result = await openai_service.get_chat_completion(messages, model="gpt-4o")
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Add assistant message
    assistant_msg = chat_service.add_message(
        db,
        session_id=session_id,
        role="assistant",
        content=result["content"]
    )
    
    return {
        "success": True,
        "prompts_applied": len(prompts),
        "message": MessageResponse(
            id=assistant_msg.id,
            session_id=assistant_msg.session_id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            content_type=assistant_msg.content_type,
            images=assistant_msg.images,
            created_at=assistant_msg.created_at,
            is_bookmarked=assistant_msg.is_bookmarked
        )
    }


# ============================================================================
# WebSocket for Streaming
# ============================================================================

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: int):
    """WebSocket endpoint for streaming chat"""
    await websocket.accept()
    print(f"🔌 WebSocket connected for session {session_id}")
    
    # Get database session
    db = next(get_db())
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            print(f"📩 Received WebSocket data: {data[:200]}...")
            request = json.loads(data)
            
            action = request.get("action", "message")
            print(f"📋 Action: {action}")
            
            if action == "message":
                # Add user message
                content = request.get("content", "")
                images = request.get("images", None)
                model = request.get("model", "gpt-4o")
                answer_mode = request.get("answer_mode", "default")
                optimization_mode = request.get("optimization_mode", True)
                
                user_msg = chat_service.add_message(
                    db,
                    session_id=session_id,
                    role="user",
                    content=content,
                    images=images
                )
                
                # Send user message confirmation
                await websocket.send_json({
                    "type": "user_message",
                    "message_id": user_msg.id
                })
                
                # Get messages for API
                messages = chat_service.get_messages_for_api(
                    db, 
                    session_id, 
                    optimization_mode=optimization_mode
                )
                
                # Stream response
                full_response = ""
                await websocket.send_json({"type": "stream_start"})
                
                async for chunk in openai_service.stream_chat_completion(
                    messages,
                    model=model,
                    answer_mode=answer_mode
                ):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "content": chunk
                    })
                
                # Save assistant message
                assistant_msg = chat_service.add_message(
                    db,
                    session_id=session_id,
                    role="assistant",
                    content=full_response
                )
                
                await websocket.send_json({
                    "type": "stream_end",
                    "message_id": assistant_msg.id,
                    "full_content": full_response
                })
            
            elif action == "stop":
                # Client requested to stop streaming
                await websocket.send_json({"type": "stopped"})
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        db.close()

