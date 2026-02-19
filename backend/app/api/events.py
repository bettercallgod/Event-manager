from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from app.core.database import get_db
from app.models import Event
from app.services.event_service import EventService
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/", response_model=Dict[str, Any])
async def create_event(
    event_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Create a new event from natural language or structured data"""
    event_service = EventService(db)
    
    # If conversation_text is provided, extract event details
    if "conversation_text" in event_data:
        extracted = await ai_service.extract_event_from_conversation(
            event_data["conversation_text"]
        )
        # Merge extracted data with any provided overrides
        event_data = {**extracted, **{k: v for k, v in event_data.items() if k != "conversation_text"}}
    
    # Parse datetime strings
    if event_data.get("start_time"):
        try:
            event_data["start_time"] = datetime.fromisoformat(event_data["start_time"].replace("Z", "+00:00"))
        except:
            pass
    
    if event_data.get("end_time"):
        try:
            event_data["end_time"] = datetime.fromisoformat(event_data["end_time"].replace("Z", "+00:00"))
        except:
            pass
    
    event = await event_service.create_event(event_data)
    
    return {
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "ai_summary": event.ai_summary,
        "category": event.category,
        "location": event.location_name,
        "city": event.city,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "price": event.price,
        "is_free": event.is_free,
        "created_at": event.created_at.isoformat(),
    }


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_events(
    q: str = Query(..., description="Search query"),
    use_semantic: bool = Query(True, description="Use semantic search"),
    category: Optional[str] = None,
    city: Optional[str] = None,
    max_price: Optional[float] = None,
    event_size: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search for events"""
    event_service = EventService(db)
    
    filters = {}
    if category:
        filters["category"] = category
    if city:
        filters["city"] = city
    if max_price is not None:
        filters["max_price"] = max_price
    if event_size:
        filters["event_size"] = event_size
    
    if use_semantic and ai_service.openai_client:
        events = await event_service.search_events_semantic(q, limit=limit, filters=filters)
    else:
        events = await event_service.search_events_keyword(q, limit=limit, filters=filters)
    
    return [
        {
            "id": str(event.id),
            "title": event.title,
            "description": event.description,
            "ai_summary": event.ai_summary,
            "category": event.category,
            "event_size": event.event_size,
            "location": event.location_name,
            "address": event.address,
            "city": event.city,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "price": event.price,
            "is_free": event.is_free,
            "ai_tags": event.ai_tags,
        }
        for event in events
    ]


@router.get("/recommendations", response_model=List[Dict[str, Any]])
async def get_recommendations(
    user_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized event recommendations"""
    event_service = EventService(db)
    
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            events = await event_service.get_personalized_recommendations(user_uuid, limit)
        except ValueError:
            events = await event_service.get_popular_events(limit)
    else:
        events = await event_service.get_popular_events(limit)
    
    return [
        {
            "id": str(event.id),
            "title": event.title,
            "ai_summary": event.ai_summary,
            "category": event.category,
            "location": event.location_name,
            "city": event.city,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "price": event.price,
            "is_free": event.is_free,
        }
        for event in events
    ]


@router.get("/{event_id}", response_model=Dict[str, Any])
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific event by ID"""
    event_service = EventService(db)
    
    try:
        event_uuid = uuid.UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    event = await event_service.get_event_by_id(event_uuid)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "ai_summary": event.ai_summary,
        "category": event.category,
        "event_size": event.event_size,
        "location": event.location_name,
        "address": event.address,
        "city": event.city,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "price": event.price,
        "currency": event.currency,
        "is_free": event.is_free,
        "ai_tags": event.ai_tags,
        "host_id": str(event.host_id) if event.host_id else None,
        "created_at": event.created_at.isoformat(),
    }
