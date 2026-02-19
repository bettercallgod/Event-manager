# 🚀 Quick Start Guide

Get EventDiscovery AI running in 5 minutes!

## Option 1: Docker (Recommended) ⭐

### 1. Setup Environment
```bash
cd event-discovery
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```

### 2. Start Everything
```bash
docker-compose up -d
```

### 3. Open the App
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Done! 🎉

---

## Option 2: Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ with pgvector
- OpenAI API key

### 1. Install PostgreSQL with pgvector

**macOS (Homebrew)**:
```bash
brew install postgresql@15
brew install pgvector
```

**Windows**:
Download from: https://www.postgresql.org/download/windows/
Then install pgvector extension.

**Linux (Ubuntu)**:
```bash
sudo apt install postgresql-15 postgresql-15-pgvector
```

### 2. Create Database
```bash
createdb eventdiscovery
psql -d eventdiscovery -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Setup Python
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Initialize Database
```bash
python init_db.py
```

### 6. Run the Server
```bash
python -m uvicorn app.main:app --reload
```

### 7. Open the App
http://localhost:8000

---

## Test It Out!

### 1. Chat with AI
Go to http://localhost:8000 and try:
> "I'm looking for live music this weekend, maybe jazz or indie, budget around $30"

### 2. Create an Event
Click "Create Event" and describe:
> "Hosting a rooftop yoga session Saturday morning at 9am, free with donation option, bringing my own mat recommended"

### 3. Search Events
Use the search bar to find events by description!

---

## Troubleshooting

### Database Connection Error
Make sure PostgreSQL is running:
```bash
# macOS
brew services start postgresql@15

# Windows
net start postgresql-x64-15

# Linux
sudo systemctl start postgresql
```

### Port Already in Use
Change the port in `docker-compose.yml` or run uvicorn on a different port:
```bash
python -m uvicorn app.main:app --reload --port 8001
```

### OpenAI API Error
Check that your API key is correct in `.env` and has credits available.

---

## Next Steps

- Check out the API docs at http://localhost:8000/docs
- Read the full README.md for deployment options
- Start building features! 🛠️
