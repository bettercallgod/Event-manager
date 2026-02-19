from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, VECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    events = relationship("Event", back_populates="host", foreign_keys="Event.host_id")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    
    # Preference embedding for semantic matching
    preference_embedding = Column(VECTOR(1536))  # OpenAI embedding dimension
    
    # Explicit preferences
    preferred_categories = Column(JSON, default=list)
    preferred_price_range = Column(String(20))  # "free", "low", "medium", "high", "any"
    preferred_distance_km = Column(Float, default=50.0)
    preferred_event_sizes = Column(JSON, default=["small", "medium", "large"])
    
    # Learning data
    liked_event_types = Column(JSON, default=list)
    disliked_event_types = Column(JSON, default=list)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    description_embedding = Column(VECTOR(1536))  # For semantic search
    
    # Event metadata
    category = Column(String(100))  # music, food, sports, arts, networking, etc.
    event_size = Column(String(20))  # small (<50), medium (50-200), large (200+)
    
    # Location
    location_name = Column(String(255))
    address = Column(String(500))
    city = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Timing
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    # Pricing
    price = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    is_free = Column(Boolean, default=False)
    
    # Status
    is_public = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=True)  # For moderation
    status = Column(String(20), default="active")  # active, cancelled, completed
    
    # AI-generated metadata
    ai_tags = Column(JSON, default=list)
    ai_summary = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    host = relationship("User", back_populates="events", foreign_keys=[host_id])


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Conversation context
    session_id = Column(String(100), index=True)
    message_history = Column(JSON, default=list)
    
    # Last interaction
    last_user_message = Column(Text)
    last_ai_response = Column(Text)
    
    # Extracted intent from conversation
    extracted_preferences = Column(JSON, default=dict)
    search_context = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
