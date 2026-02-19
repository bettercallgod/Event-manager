from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from typing import AsyncGenerator

# Demo mode uses in-memory storage
DEMO_EVENTS = []
DEMO_CONVERSATIONS = {}

# Try to create database engine, but handle failures gracefully
try:
    engine = create_async_engine(
        settings.DATABASE_ASYNC_URL,
        echo=settings.DEBUG,
        future=True,
    )
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Database not available: {e}")
    engine = None
    async_session_maker = None
    DB_AVAILABLE = False

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with fallback to demo mode"""
    if not DB_AVAILABLE or settings.DEMO_MODE:
        # Return a demo session
        class DemoSession:
            def __init__(self):
                self.events = DEMO_EVENTS
                self.conversations = DEMO_CONVERSATIONS
            
            async def execute(self, *args, **kwargs):
                class Result:
                    def __init__(self, scalars=None):
                        self._scalars = scalars or []
                    def scalars(self):
                        return self
                    def all(self):
                        return self._scalars
                    def scalar_one_or_none(self):
                        return self._scalars[0] if self._scalars else None
                return Result()
            
            async def flush(self):
                pass
                
            def add(self, obj):
                if hasattr(obj, '__tablename__'):
                    if obj.__tablename__ == 'events':
                        DEMO_EVENTS.append(obj)
                    elif obj.__tablename__ == 'conversations':
                        DEMO_CONVERSATIONS[obj.session_id] = obj
            
            async def commit(self):
                pass
                
            async def refresh(self, obj):
                pass
                
            async def close(self):
                pass
        
        session = DemoSession()
        yield session
        return
    
    if async_session_maker is None:
        raise Exception("Database not configured")
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    if not DB_AVAILABLE or settings.DEMO_MODE:
        print("⚠️ Running in DEMO MODE - no database")
        return
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"⚠️ Failed to initialize database: {e}")
        settings.DEMO_MODE = True
