from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.models import Event
from app.services.event_service import EventService, DEMO_EVENTS
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
        conversation_text = event_data.pop("conversation_text")
        
        # Try to use AI to extract, fall back to simple parsing
        try:
            if ai_service.openai_client:
                extracted = await ai_service.extract_event_from_conversation(conversation_text)
                event_data = {**extracted, **event_data}
            else:
                # Simple extraction for demo mode
                event_data["title"] = event_data.get("title", "New Event")
                event_data["description"] = conversation_text
                event_data["ai_summary"] = conversation_text[:200]
        except Exception as e:
            print(f"AI extraction failed: {e}")
            event_data["title"] = event_data.get("title", "New Event")
            event_data["description"] = conversation_text
            event_data["ai_summary"] = conversation_text[:200]
    
    # Parse datetime strings
    if event_data.get("start_time"):
        try:
            event_data["start_time"] = datetime.fromisoformat(str(event_data["start_time"]).replace("Z", "+00:00"))
        except:
            pass
    
    if event_data.get("end_time"):
        try:
            event_data["end_time"] = datetime.fromisoformat(str(event_data["end_time"]).replace("Z", "+00:00"))
        except:
            pass
    
    event = await event_service.create_event(event_data)
    
    return {
        "id": str(event.id),
        "title": event.title,
        "description": event.description,
        "ai_summary": event.ai_summary,
        "category": event.category,
        "location": getattr(event, 'location_name', None) or getattr(event, 'location', None),
        "city": event.city,
        "start_time": event.start_time.isoformat() if hasattr(event, 'start_time') and event.start_time else str(event.start_time) if hasattr(event, 'start_time') else None,
        "price": event.price,
        "is_free": event.is_free,
        "created_at": event.created_at.isoformat() if hasattr(event, 'created_at') and event.created_at else datetime.now().isoformat(),
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
    
    # Check if AI is available
    use_semantic = use_semantic and ai_service.openai_client is not None
    
    if use_semantic:
        events = await event_service.search_events_semantic(q, limit=limit, filters=filters)
    else:
        events = await event_service.search_events_keyword(q, limit=limit, filters=filters)
    
    return [
        {
            "id": str(event.id) if hasattr(event, 'id') else str(event.get("id", "")),
            "title": event.title if hasattr(event, 'title') else event.get("title", ""),
            "description": event.description if hasattr(event, 'description') else event.get("description", ""),
            "ai_summary": event.ai_summary if hasattr(event, 'ai_summary') else event.get("ai_summary", ""),
            "category": event.category if hasattr(event, 'category') else event.get("category", ""),
            "event_size": event.event_size if hasattr(event, 'event_size') else event.get("event_size", ""),
            "location": event.location_name if hasattr(event, 'location_name') else event.get("location_name", ""),
            "address": event.address if hasattr(event, 'address') else event.get("address", ""),
            "city": event.city if hasattr(event, 'city') else event.get("city", ""),
            "start_time": event.start_time.isoformat() if hasattr(event, 'start_time') and event.start_time else event.get("start_time", ""),
            "end_time": event.end_time.isoformat() if hasattr(event, 'end_time') and event.end_time else event.get("end_time", ""),
            "price": event.price if hasattr(event, 'price') else event.get("price", 0),
            "is_free": event.is_free if hasattr(event, 'is_free') else event.get("is_free", False),
            "ai_tags": event.ai_tags if hasattr(event, 'ai_tags') else event.get("ai_tags", []),
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
            "id": str(event.id) if hasattr(event, 'id') else str(event.get("id", "")),
            "title": event.title if hasattr(event, 'title') else event.get("title", ""),
            "ai_summary": event.ai_summary if hasattr(event, 'ai_summary') else event.get("ai_summary", ""),
            "category": event.category if hasattr(event, 'category') else event.get("category", ""),
            "location": event.location_name if hasattr(event, 'location_name') else event.get("location_name", ""),
            "city": event.city if hasattr(event, 'city') else event.get("city", ""),
            "start_time": event.start_time.isoformat() if hasattr(event, 'start_time') and event.start_time else event.get("start_time", ""),
            "price": event.price if hasattr(event, 'price') else event.get("price", 0),
            "is_free": event.is_free if hasattr(event, 'is_free') else event.get("is_free", False),
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
        # In demo mode, try to find by string ID
        for event in DEMO_EVENTS:
            if str(event["id"]) == event_id:
                return event
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    event = await event_service.get_event_by_id(event_uuid)
    
    if not event:
        # Check demo events
        for ev in DEMO_EVENTS:
            if str(ev["id"]) == event_id:
                return ev
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "id": str(event.id) if hasattr(event, 'id') else str(event.get("id", "")),
        "title": event.title if hasattr(event, 'title') else event.get("title", ""),
        "description": event.description if hasattr(event, 'description') else event.get("description", ""),
        "ai_summary": event.ai_summary if hasattr(event, 'ai_summary') else event.get("ai_summary", ""),
        "category": event.category if hasattr(event, 'category') else event.get("category", ""),
        "event_size": event.event_size if hasattr(event, 'event_size') else event.get("event_size", ""),
        "location": event.location_name if hasattr(event, 'location_name') else event.get("location_name", ""),
        "address": event.address if hasattr(event, 'address') else event.get("address", ""),
        "city": event.city if hasattr(event, 'city') else event.get("city", ""),
        "latitude": event.latitude if hasattr(event, 'latitude') else event.get("latitude"),
        "longitude": event.longitude if hasattr(event, 'longitude') else event.get("longitude"),
        "start_time": event.start_time.isoformat() if hasattr(event, 'start_time') and event.start_time else event.get("start_time", ""),
        "end_time": event.end_time.isoformat() if hasattr(event, 'end_time') and event.end_time else event.get("end_time", ""),
        "price": event.price if hasattr(event, 'price') else event.get("price", 0),
        "currency": event.currency if hasattr(event, 'currency') else event.get("currency", "USD"),
        "is_free": event.is_free if hasattr(event, 'is_free') else event.get("is_free", False),
        "ai_tags": event.ai_tags if hasattr(event, 'ai_tags') else event.get("ai_tags", []),
        "host_id": str(event.host_id) if hasattr(event, 'host_id') and event.host_id else None,
        "created_at": event.created_at.isoformat() if hasattr(event, 'created_at') and event.created_at else datetime.now().isoformat(),
    }
