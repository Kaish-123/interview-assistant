"""
Database Models - SQLAlchemy ORM
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, 
    ForeignKey, Enum, Float, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()


class PlanType(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INACTIVE = "inactive"


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    PENDING = "pending"


# ==================== USER MODEL ====================
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    
    # Subscription
    plan = Column(Enum(PlanType), default=PlanType.FREE)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.INACTIVE)
    stripe_customer_id = Column(String(255), unique=True, nullable=True)
    
    # Usage tracking
    messages_sent_today = Column(Integer, default=0)
    last_usage_reset = Column(DateTime, server_default=func.now())
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    telegram_accounts = relationship("TelegramAccount", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    message_logs = relationship("MessageLog", back_populates="user", cascade="all, delete-orphan")


# ==================== SUBSCRIPTION MODEL ====================
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Stripe
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    stripe_price_id = Column(String(255), nullable=True)
    
    # Plan details
    plan = Column(Enum(PlanType), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    
    # Billing period
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")


# ==================== TELEGRAM ACCOUNT MODEL ====================
class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Telegram credentials (encrypted in production)
    phone_number = Column(String(20), nullable=False)
    api_id = Column(String(50), nullable=False)
    api_hash = Column(String(100), nullable=False)
    session_data = Column(Text, nullable=True)  # Encrypted session string
    
    # Status
    is_active = Column(Boolean, default=True)
    is_authorized = Column(Boolean, default=False)
    last_used = Column(DateTime, nullable=True)
    
    # Settings
    nickname = Column(String(100), nullable=True)  # User-friendly name
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="telegram_accounts")
    target_groups = relationship("TargetGroup", back_populates="telegram_account", cascade="all, delete-orphan")


# ==================== TARGET GROUP MODEL ====================
class TargetGroup(Base):
    __tablename__ = "target_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    telegram_account_id = Column(UUID(as_uuid=True), ForeignKey("telegram_accounts.id", ondelete="CASCADE"), nullable=False)
    
    # Group info
    username = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    telegram_id = Column(String(50), nullable=True)
    member_count = Column(Integer, nullable=True)
    group_type = Column(String(50), nullable=True)  # group, supergroup, channel
    
    # Status
    enabled = Column(Boolean, default=True)
    can_post = Column(Boolean, default=True)
    source = Column(String(100), nullable=True)  # manual, growth:keyword
    
    # Stats
    messages_sent = Column(Integer, default=0)
    last_message_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    telegram_account = relationship("TelegramAccount", back_populates="target_groups")
    message_logs = relationship("MessageLog", back_populates="target_group", cascade="all, delete-orphan")


# ==================== MARKETING MESSAGE MODEL ====================
class MarketingMessage(Base):
    __tablename__ = "marketing_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    name = Column(String(255), nullable=True)  # Internal name
    text = Column(Text, nullable=False)
    
    # Status
    enabled = Column(Boolean, default=True)
    
    # Stats
    times_used = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ==================== MESSAGE LOG MODEL ====================
class MessageLog(Base):
    __tablename__ = "message_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_group_id = Column(UUID(as_uuid=True), ForeignKey("target_groups.id", ondelete="SET NULL"), nullable=True)
    
    # Message details
    group_username = Column(String(255), nullable=False)
    group_name = Column(String(255), nullable=True)
    message_preview = Column(String(200), nullable=True)  # First 200 chars
    
    # Status
    status = Column(Enum(MessageStatus), nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="message_logs")
    target_group = relationship("TargetGroup", back_populates="message_logs")


# ==================== GROWTH KEYWORD MODEL ====================
class GrowthKeyword(Base):
    __tablename__ = "growth_keywords"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    keyword = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    groups_found = Column(Integer, default=0)
    last_searched = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())


# ==================== USER SETTINGS MODEL ====================
class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Auto-send settings
    auto_send_enabled = Column(Boolean, default=False)
    send_interval_minutes = Column(Integer, default=30)
    delay_between_groups_seconds = Column(Integer, default=3)
    
    # Auto-growth settings
    auto_growth_enabled = Column(Boolean, default=False)
    growth_interval_hours = Column(Integer, default=6)
    max_groups_per_growth = Column(Integer, default=5)
    
    # Timestamps
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

