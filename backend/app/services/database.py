"""
Database service for managing connections and sessions
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging

from app.core.config import settings
from app.models.job import Base

logger = logging.getLogger(__name__)

# Async engine for FastAPI
async_engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

# Sync engine for migrations
sync_engine = None


async def init_db():
    """Initialize database connection"""
    global async_engine, async_session_maker
    
    try:
        # Create async engine
        database_url = settings.DATABASE_URL
        
        # Handle different database types
        if database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
            # Se já tiver +asyncpg, não precisa substituir
            if not database_url.startswith("postgresql+asyncpg://"):
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


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the configured async session factory"""
    if async_session_maker is None:
        raise RuntimeError("Database session maker is not initialized. Call init_db() first.")
    return async_session_maker


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager that yields a managed session"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a managed session"""
    async with session_scope() as session:
        yield session


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
