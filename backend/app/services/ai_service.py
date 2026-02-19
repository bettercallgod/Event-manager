from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from typing import Optional, List, Dict, Any
import json
from app.core.config import settings


class AIService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.use_anthropic = settings.ANTHROPIC_API_KEY and True
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    async def chat(self, messages: List[Dict[str, str]], context: Optional[Dict] = None) -> str:
        """Chat with AI assistant"""
        system_prompt = """You are an AI assistant for an event discovery platform. Help users find events they'll love through natural conversation.

Your capabilities:
- Ask clarifying questions about what kind of events they're looking for
- Learn their preferences (music taste, budget, location, group size, etc.)
- Recommend events based on their interests
- Help hosts create events through conversation (no forms!)
- Be friendly, helpful, and conversational

When users want to find events, ask about:
- What type of experience they want (music, food, arts, sports, networking, etc.)
- When they're looking to go out
- Their location or how far they're willing to travel
- Budget preferences
- Group size (solo, date, friends, family)

When hosts want to create events, naturally extract:
- Event name and description
- Date and time
- Location
- Price (if any)
- What makes it special

Be concise but warm. Use emojis sparingly. Focus on helping them discover or create amazing experiences!"""

        if context:
            system_prompt += f"\n\nCurrent context: {json.dumps(context, indent=2)}"

        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        if self.use_anthropic and self.anthropic_client:
            return await self._chat_anthropic(full_messages)
        else:
            return await self._chat_openai(full_messages)
    
    async def _chat_openai(self, messages: List[Dict[str, str]]) -> str:
        response = await self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    
    async def _chat_anthropic(self, messages: List[Dict[str, str]]) -> str:
        # Convert OpenAI format to Anthropic format
        system_message = next((m["content"] for m in messages if m["role"] == "system"), "")
        anthropic_messages = [m for m in messages if m["role"] != "system"]
        
        response = await self.anthropic_client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1000,
            system=system_message,
            messages=anthropic_messages
        )
        return response.content[0].text
    
    async def extract_event_from_conversation(self, conversation_text: str) -> Dict[str, Any]:
        """Extract event details from natural language description"""
        prompt = f"""Extract event details from this conversation and return as JSON:

{conversation_text}

Return ONLY valid JSON with this structure (all fields optional except title):
{{
    "title": "Event name",
    "description": "Full description",
    "category": "music|food|sports|arts|networking|education|family|other",
    "event_size": "small|medium|large",
    "location_name": "Venue name",
    "address": "Full address",
    "city": "City name",
    "start_time": "ISO 8601 datetime or null",
    "end_time": "ISO 8601 datetime or null",
    "price": 0.0,
    "is_free": true,
    "ai_tags": ["tag1", "tag2"]
}}

If information is not mentioned, use null or reasonable defaults."""

        response = await self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an event extraction assistant. Extract structured data from natural language."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        try:
            extracted = json.loads(response.choices[0].message.content)
            return extracted
        except:
            return {"title": "Untitled Event", "description": conversation_text}
    
    async def extract_user_preferences(self, conversation_text: str) -> Dict[str, Any]:
        """Extract user preferences from conversation"""
        prompt = f"""Extract user preferences from this conversation:

{conversation_text}

Return ONLY valid JSON:
{{
    "preferred_categories": ["music", "food"],
    "preferred_price_range": "free|low|medium|high|any",
    "preferred_distance_km": 50,
    "preferred_event_sizes": ["small", "medium"],
    "liked_event_types": ["jazz", "indie"],
    "disliked_event_types": ["edm"]
}}

Use empty arrays for unknown preferences."""

        response = await self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Extract user preferences as JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {}
    
    async def generate_event_summary(self, event_data: Dict) -> str:
        """Generate a compelling event summary"""
        prompt = f"""Write a compelling 2-3 sentence summary for this event:

{json.dumps(event_data, indent=2)}

Make it exciting and highlight what makes this event special."""

        response = await self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Write engaging event summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content


ai_service = AIService()
