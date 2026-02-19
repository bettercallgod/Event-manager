from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from app.core.database import get_db
from app.models import Conversation, User
from app.services.ai_service import ai_service
from app.services.event_service import EventService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message", response_model=Dict[str, Any])
async def send_message(
    message_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Send a message to the AI assistant for event discovery"""
    user_message = message_data.get("message", "").strip()
    session_id = message_data.get("session_id", str(uuid.uuid4()))
    user_id = message_data.get("user_id")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Get or create conversation
    conversation = None
    if session_id:
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
    
    if not conversation:
        conversation = Conversation(
            session_id=session_id,
            user_id=uuid.UUID(user_id) if user_id else None,
            message_history=[]
        )
        db.add(conversation)
        await db.flush()
    
    # Get conversation context
    recent_messages = conversation.message_history[-10:] if conversation.message_history else []
    context = {
        "extracted_preferences": conversation.extracted_preferences,
        "search_context": conversation.search_context,
    }
    
    # Build messages for AI
    messages = []
    for msg in recent_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    
    # Get AI response
    ai_response = await ai_service.chat(messages, context)
    
    # Update conversation history
    conversation.message_history.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })
    conversation.message_history.append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    conversation.last_user_message = user_message
    conversation.last_ai_response = ai_response
    conversation.updated_at = datetime.now()
    
    # Try to extract preferences from the conversation
    try:
        full_conversation = "\n".join([m["content"] for m in conversation.message_history[-20:]])
        extracted_prefs = await ai_service.extract_user_preferences(full_conversation)
        if extracted_prefs:
            conversation.extracted_preferences = extracted_prefs
            
            # Update user preferences if we have a user
            if conversation.user_id:
                event_service = EventService(db)
                await event_service.update_user_preferences(
                    conversation.user_id,
                    extracted_prefs
                )
    except Exception as e:
        print(f"Failed to extract preferences: {e}")
    
    await db.commit()
    await db.refresh(conversation)
    
    # Check if user is looking for events and search if appropriate
    events = []
    event_keywords = ["find", "search", "looking for", "recommend", "suggest", "events", "show me"]
    if any(keyword in user_message.lower() for keyword in event_keywords):
        try:
            event_service = EventService(db)
            search_query = user_message
            search_events = await event_service.search_events_semantic(search_query, limit=5)
            events = [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "ai_summary": e.ai_summary,
                    "category": e.category,
                    "city": e.city,
                    "start_time": e.start_time.isoformat() if e.start_time else None,
                    "price": e.price,
                    "is_free": e.is_free,
                }
                for e in search_events[:3]
            ]
        except Exception as e:
            print(f"Failed to search events: {e}")
    
    return {
        "session_id": session_id,
        "user_message": user_message,
        "ai_response": ai_response,
        "events": events,
        "preferences": conversation.extracted_preferences,
    }


@router.get("/session/{session_id}", response_model=Dict[str, Any])
async def get_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history for a session"""
    stmt = select(Conversation).where(Conversation.session_id == session_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "session_id": conversation.session_id,
        "message_history": conversation.message_history,
        "extracted_preferences": conversation.extracted_preferences,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.delete("/session/{session_id}")
async def delete_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation session"""
    stmt = select(Conversation).where(Conversation.session_id == session_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    
    return {"status": "deleted", "session_id": session_id}
