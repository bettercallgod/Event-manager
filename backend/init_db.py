"""
Database initialization script
Run this to create tables and enable pgvector extension
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def init_database():
    """Initialize database with pgvector extension and tables"""
    
    database_url = os.getenv("DATABASE_ASYNC_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/eventdiscovery")
    
    # Extract connection info from URL
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    url_parts = database_url.replace("postgresql+asyncpg://", "").split("@")
    credentials = url_parts[0]
    host_db = url_parts[1].split("/")
    host = host_db[0]
    dbname = host_db[1]
    
    user, password = credentials.split(":")
    
    print(f"🔌 Connecting to PostgreSQL...")
    
    # Connect to default database first to create extension
    conn = await asyncpg.connect(
        host=host.split(":")[0],
        port=int(host.split(":")[1]) if ":" in host else 5432,
        user=user,
        password=password,
        database="postgres"
    )
    
    try:
        # Create database if not exists
        try:
            await conn.execute(f'CREATE DATABASE {dbname}')
            print(f"✅ Database '{dbname}' created")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print(f"ℹ️  Database '{dbname}' already exists")
        
        await conn.close()
        
        # Connect to our database
        conn = await asyncpg.connect(
            host=host.split(":")[0],
            port=int(host.split(":")[1]) if ":" in host else 5432,
            user=user,
            password=password,
            database=dbname
        )
        
        # Enable pgvector extension
        await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        print("✅ pgvector extension enabled")
        
        # Create tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE,
                username VARCHAR(100) UNIQUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ
            )
        """)
        print("✅ Table 'users' created")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                preference_embedding vector(1536),
                preferred_categories JSONB DEFAULT '[]',
                preferred_price_range VARCHAR(20),
                preferred_distance_km FLOAT DEFAULT 50.0,
                preferred_event_sizes JSONB DEFAULT '["small", "medium", "large"]',
                liked_event_types JSONB DEFAULT '[]',
                disliked_event_types JSONB DEFAULT '[]',
                updated_at TIMESTAMPTZ
            )
        """)
        print("✅ Table 'user_preferences' created")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                host_id UUID REFERENCES users(id),
                title VARCHAR(255) NOT NULL,
                description TEXT,
                description_embedding vector(1536),
                category VARCHAR(100),
                event_size VARCHAR(20),
                location_name VARCHAR(255),
                address VARCHAR(500),
                city VARCHAR(100),
                latitude FLOAT,
                longitude FLOAT,
                start_time TIMESTAMPTZ,
                end_time TIMESTAMPTZ,
                price FLOAT DEFAULT 0.0,
                currency VARCHAR(3) DEFAULT 'USD',
                is_free BOOLEAN DEFAULT FALSE,
                is_public BOOLEAN DEFAULT TRUE,
                is_approved BOOLEAN DEFAULT TRUE,
                status VARCHAR(20) DEFAULT 'active',
                ai_tags JSONB DEFAULT '[]',
                ai_summary TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ
            )
        """)
        print("✅ Table 'events' created")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                session_id VARCHAR(100),
                message_history JSONB DEFAULT '[]',
                last_user_message TEXT,
                last_ai_response TEXT,
                extracted_preferences JSONB DEFAULT '{}',
                search_context JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ
            )
        """)
        print("✅ Table 'conversations' created")
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events(category)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_city ON events(city)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_embedding ON events USING ivfflat (description_embedding vector_cosine_ops) WITH (lists = 100)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
        print("✅ Indexes created")
        
        print("\n🎉 Database initialization complete!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_database())
