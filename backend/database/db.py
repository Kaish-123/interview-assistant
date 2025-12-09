"""
Database configuration and models for Interview Assistant Web
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./interview_assistant.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ChatSession(Base):
    """Store chat sessions with messages"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    summary = Column(Text, nullable=True)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Store individual messages in a chat session"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String(50))  # user, assistant, system
    content = Column(Text)
    content_type = Column(String(50), default="text")  # text, image, multimodal
    images = Column(JSON, nullable=True)  # Store base64 images
    created_at = Column(DateTime, default=datetime.utcnow)
    is_bookmarked = Column(Boolean, default=False)
    
    session = relationship("ChatSession", back_populates="messages")


class PromptTemplate(Base):
    """Store prompt templates organized by tabs"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    tab_name = Column(String(100))
    subtab_name = Column(String(200))
    prompt_text = Column(Text)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    """Store uploaded documents (resumes, JDs)"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    doc_type = Column(String(50))  # resume, jd, other
    content = Column(Text)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPreference(Base):
    """Store user preferences"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SetupProfile(Base):
    """Store quick setup profiles"""
    __tablename__ = "setup_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    prompt_ids = Column(JSON)  # List of prompt template IDs
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database on import
init_db()
