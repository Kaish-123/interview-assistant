"""
Chat Service - Manages chat sessions and messages
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from database.db import ChatSession, ChatMessage, Document
from services.openai_service import openai_service


class ChatService:
    """Service class for chat management"""
    
    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful interview assistant. "
        "Provide detailed technical answers and ask follow-up questions when appropriate."
    )
    
    def create_session(
        self, 
        db: Session, 
        title: str = "New Chat",
        system_prompt: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Add system message
        system_msg = ChatMessage(
            session_id=session.id,
            role="system",
            content=system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            content_type="text"
        )
        db.add(system_msg)
        db.commit()
        
        return session
    
    def get_session(self, db: Session, session_id: int) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        return db.query(ChatSession).filter(ChatSession.id == session_id).first()
    
    def get_all_sessions(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[ChatSession]:
        """Get all chat sessions"""
        return db.query(ChatSession)\
            .filter(ChatSession.is_active == True)\
            .order_by(ChatSession.updated_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def update_session_title(
        self, 
        db: Session, 
        session_id: int, 
        title: str
    ) -> Optional[ChatSession]:
        """Update session title"""
        session = self.get_session(db, session_id)
        if session:
            session.title = title
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
        return session
    
    def delete_session(self, db: Session, session_id: int) -> bool:
        """Soft delete a session"""
        session = self.get_session(db, session_id)
        if session:
            session.is_active = False
            db.commit()
            return True
        return False
    
    def add_message(
        self,
        db: Session,
        session_id: int,
        role: str,
        content: str,
        images: Optional[List[str]] = None
    ) -> ChatMessage:
        """Add a message to a session"""
        content_type = "multimodal" if images else "text"
        
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            content_type=content_type,
            images=images
        )
        db.add(message)
        
        # Update session timestamp
        session = self.get_session(db, session_id)
        if session:
            session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        return message
    
    def get_messages(
        self, 
        db: Session, 
        session_id: int,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get all messages in a session"""
        query = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .order_by(ChatMessage.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_messages_for_api(
        self,
        db: Session,
        session_id: int,
        optimization_mode: bool = True
    ) -> List[Dict[str, Any]]:
        """Get messages formatted for OpenAI API"""
        messages = self.get_messages(db, session_id)
        session = self.get_session(db, session_id)
        
        api_messages = []
        for msg in messages:
            if msg.images:
                # Multimodal message
                content = [{"type": "text", "text": msg.content}]
                for img in msg.images:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": img}
                    })
                api_messages.append({"role": msg.role, "content": content})
            else:
                api_messages.append({"role": msg.role, "content": msg.content})
        
        # Apply optimization
        summary = session.summary if session else None
        return openai_service.build_optimized_messages(
            api_messages, 
            summary=summary,
            optimization_mode=optimization_mode
        )
    
    def toggle_bookmark(
        self, 
        db: Session, 
        message_id: int, 
        is_bookmarked: bool
    ) -> Optional[ChatMessage]:
        """Toggle bookmark on a message"""
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if message:
            message.is_bookmarked = is_bookmarked
            db.commit()
            db.refresh(message)
        return message
    
    def get_bookmarked_messages(
        self, 
        db: Session, 
        session_id: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get all bookmarked messages"""
        query = db.query(ChatMessage).filter(ChatMessage.is_bookmarked == True)
        if session_id:
            query = query.filter(ChatMessage.session_id == session_id)
        return query.order_by(ChatMessage.created_at.desc()).all()
    
    def add_document_context(
        self,
        db: Session,
        session_id: int,
        filename: str,
        content: str,
        doc_type: str = "resume"
    ) -> ChatMessage:
        """Add document content as system context"""
        # Save document
        doc = Document(
            filename=filename,
            doc_type=doc_type,
            content=content,
            session_id=session_id
        )
        db.add(doc)
        
        # Add as system message
        system_content = f"Use this {doc_type} content to contextualize answers (from file: {filename}): {content}"
        message = self.add_message(db, session_id, "system", system_content)
        
        db.commit()
        return message
    
    async def update_session_summary(self, db: Session, session_id: int) -> Optional[str]:
        """Generate and store conversation summary"""
        messages = self.get_messages_for_api(db, session_id, optimization_mode=False)
        summary = await openai_service.summarize_conversation(messages)
        
        if summary:
            session = self.get_session(db, session_id)
            if session:
                session.summary = summary
                db.commit()
        
        return summary
    
    def get_performance_diagnostic(self, db: Session, session_id: int) -> Dict[str, Any]:
        """Generate performance diagnostic for a session"""
        messages = self.get_messages(db, session_id)
        session = self.get_session(db, session_id)
        
        diag = {
            "total_messages": len(messages),
            "system_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "images_count": 0,
            "estimated_total_tokens": 0,
            "estimated_system_tokens": 0,
            "estimated_conversation_tokens": 0,
            "estimated_image_tokens": 0,
            "optimization_mode": openai_service.optimization_mode,
            "will_send_messages": 0,
            "will_send_tokens": 0,
            "has_summary": bool(session and session.summary),
            "issues": [],
            "recommendations": []
        }
        
        for msg in messages:
            if msg.role == "system":
                diag["system_messages"] += 1
                diag["estimated_system_tokens"] += len(msg.content) // 4
            elif msg.role == "user":
                diag["user_messages"] += 1
                diag["estimated_conversation_tokens"] += len(msg.content) // 4
            elif msg.role == "assistant":
                diag["assistant_messages"] += 1
                diag["estimated_conversation_tokens"] += len(msg.content) // 4
            
            if msg.images:
                diag["images_count"] += len(msg.images)
                diag["estimated_image_tokens"] += len(msg.images) * (85 if openai_service.optimization_mode else 765)
        
        diag["estimated_total_tokens"] = (
            diag["estimated_system_tokens"] + 
            diag["estimated_conversation_tokens"] + 
            diag["estimated_image_tokens"]
        )
        
        # Calculate optimized tokens
        optimized_msgs = self.get_messages_for_api(db, session_id, optimization_mode=True)
        diag["will_send_messages"] = len(optimized_msgs)
        diag["will_send_tokens"] = openai_service.estimate_tokens(optimized_msgs)
        
        # Identify issues
        if diag["estimated_system_tokens"] > 8000:
            diag["issues"].append("System messages are very large")
            diag["recommendations"].append("System messages will be auto-truncated")
        
        if diag["images_count"] > 5:
            diag["issues"].append(f"Many images in chat ({diag['images_count']})")
            diag["recommendations"].append("Old images will be stripped automatically")
        
        if diag["total_messages"] > 20 and not diag["has_summary"]:
            diag["issues"].append("Long conversation without summary")
            diag["recommendations"].append("Generate summary to improve performance")
        
        if diag["will_send_tokens"] > 15000:
            diag["issues"].append(f"High token count ({diag['will_send_tokens']:,})")
            diag["recommendations"].append("Consider starting a new chat")
        
        return diag
    
    def generate_session_title(self, db: Session, session_id: int) -> str:
        """Generate a title based on conversation content"""
        messages = self.get_messages(db, session_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Look for resume attachment
        for msg in messages:
            if msg.role == "system" and "Use this resume content" in msg.content:
                import re
                match = re.search(r'from file:\s*(.+?)\)', msg.content)
                if match:
                    filename = match.group(1).strip()
                    name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    return f"{name} - {timestamp}"
        
        return timestamp


# Create singleton instance
chat_service = ChatService()




