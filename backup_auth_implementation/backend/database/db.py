"""
Database configuration and models for Interview Assistant Web
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./interview_assistant.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# User Authentication Models
# ============================================================================

class AuthProvider(enum.Enum):
    """Authentication provider types"""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


class SubscriptionTier(enum.Enum):
    """Subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # Null for OAuth users
    
    # OAuth fields
    auth_provider = Column(String(50), default=AuthProvider.LOCAL.value)
    oauth_id = Column(String(255), nullable=True)  # ID from OAuth provider
    picture_url = Column(String(500), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # Subscription
    subscription_tier = Column(String(50), default=SubscriptionTier.FREE.value)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    api_calls_today = Column(Integer, default=0)
    api_calls_month = Column(Integer, default=0)
    last_api_call = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")


class UserSubscription(Base):
    """Subscription history and management"""
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    tier = Column(String(50), nullable=False)
    status = Column(String(50), default="active")  # active, cancelled, expired, paused
    
    # Payment info
    payment_provider = Column(String(50), nullable=True)  # stripe, razorpay, etc.
    payment_id = Column(String(255), nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    
    # Period
    starts_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="subscriptions")


class RefreshToken(Base):
    """Store refresh tokens for JWT authentication"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")


# ============================================================================
# Chat Models (Updated with User relationship)
# ============================================================================

class ChatSession(Base):
    """Store chat sessions with messages"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous/legacy
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    summary = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="sessions")
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


# ============================================================================
# Prompt Templates
# ============================================================================

class PromptTemplate(Base):
    """Store prompt templates organized by tabs"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null = global template
    tab_name = Column(String(100))
    subtab_name = Column(String(200))
    prompt_text = Column(Text)
    order_index = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    """Store uploaded documents (resumes, JDs)"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String(255))
    doc_type = Column(String(50))  # resume, jd, other
    content = Column(Text)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="documents")


class UserPreference(Base):
    """Store user preferences"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    key = Column(String(100), index=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SetupProfile(Base):
    """Store quick setup profiles"""
    __tablename__ = "setup_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100))
    prompt_ids = Column(JSON)  # List of prompt template IDs
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# Subscription Plans (Static reference)
# ============================================================================

SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "features": {
            "messages_per_day": 20,
            "sessions": 5,
            "document_uploads": 2,
            "models": ["gpt-4o-mini"],
        }
    },
    "starter": {
        "name": "Starter",
        "price": 9.99,
        "features": {
            "messages_per_day": 100,
            "sessions": 50,
            "document_uploads": 20,
            "models": ["gpt-4o-mini", "gpt-4o"],
        }
    },
    "pro": {
        "name": "Pro",
        "price": 29.99,
        "features": {
            "messages_per_day": -1,  # Unlimited
            "sessions": -1,
            "document_uploads": -1,
            "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            "priority_support": True,
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 99.99,
        "features": {
            "messages_per_day": -1,
            "sessions": -1,
            "document_uploads": -1,
            "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4"],
            "priority_support": True,
            "custom_prompts": True,
            "api_access": True,
        }
    }
}


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
