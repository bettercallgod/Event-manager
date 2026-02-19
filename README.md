# 🎉 EventDiscovery AI

An AI-powered event discovery platform that helps users find local events through natural language conversations. Built as a two-sided marketplace for event discovery and promotion.

## ✨ Features

### For Event Goers
- **Natural Language Discovery**: Chat with AI to find events matching your interests
- **Personalized Recommendations**: AI learns your preferences over time
- **Semantic Search**: Find events by describing what you want, not just keywords
- **Transparent Matching**: See why events are recommended to you

### For Event Hosts
- **No-Form Event Creation**: Describe your event in natural language
- **AI-Powered Optimization**: Automatic tagging, categorization, and summaries
- **Instant Publishing**: Get your event live in seconds

## 🏗️ Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15+ with pgvector extension
- **AI**: OpenAI (gpt-4o-mini), optional Anthropic (Claude Sonnet)
- **Frontend**: HTML/JavaScript with Tailwind CSS
- **Deployment**: Docker containerized, Railway/Fly.io ready

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key (required)
- Anthropic API key (optional)

### 1. Clone & Setup

```bash
cd event-discovery

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=sk-...
```

### 2. Start with Docker

```bash
docker-compose up -d
```

The application will be available at:
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Local Development (without Docker)

```bash
# Install PostgreSQL 15+ with pgvector
# Create database: CREATE DATABASE eventdiscovery;

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run the server
python -m uvicorn app.main:app --reload
```

## 📖 API Endpoints

### Events
- `POST /api/events/` - Create event (natural language or structured)
- `GET /api/events/search?q=query` - Search events
- `GET /api/events/recommendations` - Get personalized recommendations
- `GET /api/events/{id}` - Get event details

### Chat
- `POST /api/chat/message` - Send message to AI assistant
- `GET /api/chat/session/{id}` - Get conversation history
- `DELETE /api/chat/session/{id}` - Delete conversation

## 🤖 How It Works

### Event Discovery Flow
1. User chats with AI about what they're looking for
2. AI extracts preferences and search intent
3. System performs semantic search using pgvector embeddings
4. Personalized results are returned with explanations
5. User preferences are updated based on interactions

### Event Creation Flow
1. Host describes event in natural language
2. AI extracts structured data (title, date, location, price, etc.)
3. Event is created with AI-generated tags and summary
4. Event becomes searchable immediately

## 🗄️ Database Schema

### Tables
- **users**: User accounts
- **events**: Event listings with vector embeddings
- **user_preferences**: Learned preferences with embeddings
- **conversations**: Chat history and context

### Vector Search
Uses pgvector for semantic similarity search on:
- Event descriptions (1536-dim OpenAI embeddings)
- User preferences (1536-dim OpenAI embeddings)

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for embeddings & chat |
| `ANTHROPIC_API_KEY` | No | Anthropic API key (optional fallback) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | Secret key for JWT tokens |
| `DEBUG` | No | Enable debug mode (default: true) |

## 📦 Deployment

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🧪 Testing

```bash
cd backend
pytest
```

## 📝 Example Usage

### Chat with AI
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Looking for live jazz music this weekend, budget around $30"}'
```

### Create Event
```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Content-Type: application/json" \
  -d '{"conversation_text": "Hosting a rooftop yoga session Saturday morning at 9am, free with donation option"}'
```

### Search Events
```bash
curl "http://localhost:8000/api/events/search?q=outdoor+music+concert&category=music&max_price=50"
```

## 🎯 Roadmap

- [ ] User authentication & profiles
- [ ] Event RSVP and ticketing
- [ ] Social features (friends, sharing)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics for hosts
- [ ] Multi-city expansion
- [ ] Integration with ticketing platforms

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a PR

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [pgvector](https://github.com/pgvector/pgvector)
- [OpenAI](https://openai.com/)
- [Tailwind CSS](https://tailwindcss.com/)

---

**Made with ❤️ for event lovers everywhere**
