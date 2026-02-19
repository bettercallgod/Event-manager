from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from app.models import Event, UserPreference, User
from app.services.ai_service import ai_service


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_event(self, event_data: Dict[str, Any], host_id: Optional[uuid.UUID] = None) -> Event:
        """Create a new event"""
        # Generate embedding for description
        description = event_data.get("description", "")
        embedding = None
        if description and ai_service.openai_client:
            try:
                embedding = await ai_service.generate_embedding(description)
            except Exception as e:
                print(f"Failed to generate embedding: {e}")
        
        event = Event(
            host_id=host_id,
            title=event_data.get("title", "Untitled Event"),
            description=description,
            description_embedding=embedding,
            category=event_data.get("category", "other"),
            event_size=event_data.get("event_size", "medium"),
            location_name=event_data.get("location_name"),
            address=event_data.get("address"),
            city=event_data.get("city"),
            latitude=event_data.get("latitude"),
            longitude=event_data.get("longitude"),
            start_time=event_data.get("start_time"),
            end_time=event_data.get("end_time"),
            price=event_data.get("price", 0.0),
            currency=event_data.get("currency", "USD"),
            is_free=event_data.get("is_free", event_data.get("price", 0) == 0),
            ai_tags=event_data.get("ai_tags", []),
        )
        
        # Generate AI summary
        if event.title and event.description:
            try:
                event.ai_summary = await ai_service.generate_event_summary({
                    "title": event.title,
                    "description": event.description,
                    "category": event.category,
                })
            except:
                event.ai_summary = event.description[:200]
        
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event
    
    async def search_events_semantic(
        self,
        query: str,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        filters: Optional[Dict] = None
    ) -> List[Event]:
        """Search events using semantic similarity"""
        # Generate query embedding
        query_embedding = await ai_service.generate_embedding(query)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Build base query with semantic similarity
        sql = text("""
            SELECT e.*, 
                   1 - (e.description_embedding <=> :embedding) as similarity
            FROM events e
            WHERE e.is_public = true 
              AND e.is_approved = true
              AND e.status = 'active'
              AND e.start_time > NOW()
        """)
        
        # Apply filters
        params = {"embedding": embedding_str, "limit": limit}
        
        if filters:
            if filters.get("category"):
                sql = text(str(sql) + " AND e.category = :category")
                params["category"] = filters["category"]
            
            if filters.get("city"):
                sql = text(str(sql) + " AND e.city = :city")
                params["city"] = filters["city"]
            
            if filters.get("max_price") is not None:
                sql = text(str(sql) + " AND e.price <= :max_price")
                params["max_price"] = filters["max_price"]
            
            if filters.get("event_size"):
                sql = text(str(sql) + " AND e.event_size = :event_size")
                params["event_size"] = filters["event_size"]
        
        sql = text(str(sql) + " ORDER BY similarity DESC LIMIT :limit")
        
        result = await self.db.execute(sql, params)
        events = result.scalars().all()
        return list(events)
    
    async def search_events_keyword(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[Dict] = None
    ) -> List[Event]:
        """Search events using keyword matching"""
        stmt = select(Event).where(
            and_(
                Event.is_public == True,
                Event.is_approved == True,
                Event.status == "active",
                Event.start_time > datetime.now()
            )
        )
        
        # Keyword search in title and description
        search_term = f"%{query}%"
        stmt = stmt.where(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.location_name.ilike(search_term),
                Event.city.ilike(search_term)
            )
        )
        
        # Apply filters
        if filters:
            if filters.get("category"):
                stmt = stmt.where(Event.category == filters["category"])
            if filters.get("city"):
                stmt = stmt.where(Event.city == filters["city"])
            if filters.get("max_price") is not None:
                stmt = stmt.where(Event.price <= filters["max_price"])
        
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_personalized_recommendations(
        self,
        user_id: uuid.UUID,
        limit: int = 20
    ) -> List[Event]:
        """Get personalized event recommendations for a user"""
        # Get user preferences
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.db.execute(stmt)
        preference = result.scalar_one_or_none()
        
        if not preference or not preference.preference_embedding:
            # Fall back to popular events
            return await self.get_popular_events(limit)
        
        # Semantic search with user preference embedding
        embedding_str = "[" + ",".join(map(str, preference.preference_embedding)) + "]"
        
        sql = text("""
            SELECT e.*, 
                   1 - (e.description_embedding <=> :embedding) as similarity
            FROM events e
            WHERE e.is_public = true 
              AND e.is_approved = true
              AND e.status = 'active'
              AND e.start_time > NOW()
            ORDER BY similarity DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(sql, {"embedding": embedding_str, "limit": limit})
        events = result.scalars().all()
        return list(events)
    
    async def get_popular_events(self, limit: int = 20) -> List[Event]:
        """Get popular/trending events"""
        stmt = select(Event).where(
            and_(
                Event.is_public == True,
                Event.is_approved == True,
                Event.status == "active",
                Event.start_time > datetime.now()
            )
        ).order_by(Event.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_event_by_id(self, event_id: uuid.UUID) -> Optional[Event]:
        """Get a single event by ID"""
        stmt = select(Event).where(Event.id == event_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_user_preferences(
        self,
        user_id: uuid.UUID,
        preferences: Dict[str, Any]
    ) -> UserPreference:
        """Update or create user preferences"""
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.db.execute(stmt)
        user_pref = result.scalar_one_or_none()
        
        if not user_pref:
            user_pref = UserPreference(user_id=user_id)
            self.db.add(user_pref)
        
        # Update fields
        if "preferred_categories" in preferences:
            user_pref.preferred_categories = preferences["preferred_categories"]
        if "preferred_price_range" in preferences:
            user_pref.preferred_price_range = preferences["preferred_price_range"]
        if "preferred_distance_km" in preferences:
            user_pref.preferred_distance_km = preferences["preferred_distance_km"]
        if "preferred_event_sizes" in preferences:
            user_pref.preferred_event_sizes = preferences["preferred_event_sizes"]
        if "liked_event_types" in preferences:
            user_pref.liked_event_types = preferences["liked_event_types"]
        if "disliked_event_types" in preferences:
            user_pref.disliked_event_types = preferences["disliked_event_types"]
        
        # Generate preference embedding if we have categories
        if preferences.get("preferred_categories"):
            try:
                pref_text = ", ".join(preferences["preferred_categories"])
                user_pref.preference_embedding = await ai_service.generate_embedding(pref_text)
            except:
                pass
        
        await self.db.flush()
        await self.db.refresh(user_pref)
        return user_pref
