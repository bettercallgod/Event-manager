from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.config import settings
    from app.core.database import init_db
    from app.api import events, chat
except ImportError as e:
    print(f"Import error: {e}")
    settings = None
    init_db = None
    events = None
    chat = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting EventDiscovery AI...")
    if init_db:
        try:
            await init_db()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️ Database init failed (demo mode): {e}")
    yield
    # Shutdown
    print("👋 Shutting down EventDiscovery AI...")


app = FastAPI(
    title="EventDiscovery AI" if not settings else settings.APP_NAME,
    version="1.0.0" if not settings else settings.APP_VERSION,
    description="AI-powered event discovery platform",
    lifespan=lifespan,
)

# CORS - allow all origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates - handle Vercel structure
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(base_dir, "frontend")
templates_dir = os.path.join(frontend_dir, "templates")
static_dir = os.path.join(frontend_dir, "static")

# Try to mount templates
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
    
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
else:
    # Fallback - return simple HTML
    @app.get("/")
    async def root():
        return HTMLResponse(content="""
        <html>
        <head><title>EventDiscovery AI</title></head>
        <body>
            <h1>🎉 EventDiscovery AI</h1>
            <p>Backend is running! API available at /api/events</p>
        </body>
        </html>
        """)

# Try to mount static files
if os.path.exists(static_dir):
    try:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    except Exception as e:
        print(f"Static files mount warning: {e}")

# Include routers if available
if events and chat:
    app.include_router(events.router)
    app.include_router(chat.router)

# Health check
@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "app": "EventDiscovery AI",
        "version": "1.0.0",
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
