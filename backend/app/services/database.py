"""
Database service for managing connections and sessions
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging

from app.core.config import settings
from app.models.job import Base

logger = logging.getLogger(__name__)

# Async engine for FastAPI
async_engine = None
async_session_maker = None

# Sync engine for migrations
sync_engine = None


async def init_db():
    """Initialize database connection"""
    global async_engine, async_session_maker
    
    try:
        # Create async engine
        database_url = settings.DATABASE_URL
        
        # Handle different database types
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            async_engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=True
            )
        elif database_url.startswith("sqlite"):
            # SQLite for development/testing
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            async_engine = create_async_engine(
                database_url,
                echo=settings.DEBUG,
                connect_args={"check_same_thread": False}
            )
        else:
            raise ValueError(f"Unsupported database URL: {database_url}")
        
        # Create session maker
        async_session_maker = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """Close database connections"""
    global async_engine
    
    if async_engine:
        await async_engine.dispose()
        logger.info("Database connections closed")


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_engine():
    """Get synchronous engine for migrations"""
    global sync_engine
    
    if not sync_engine:
        sync_engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True
        )
    
    return sync_engine
