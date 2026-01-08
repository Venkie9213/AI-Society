# app/database.py
"""Database initialization and management"""

import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
import structlog

logger = structlog.get_logger()

# Global database engine and session factory
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker] = None


async def init_db(database_url: str, pool_size: int = 5, max_overflow: int = 10) -> None:
    """Initialize database engine and session factory"""
    global _engine, _async_session_factory
    
    logger.info("initializing_database", url=database_url, pool_size=pool_size)
    
    # Create async engine
    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=pool_size,
        max_overflow=max_overflow,
        poolclass=NullPool,  # Use NullPool for development to avoid connection issues
        connect_args={
            "timeout": 30,
            "command_timeout": 60,
        },
    )
    
    # Create session factory
    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    
    # Test database connection
    async with _engine.begin() as conn:
        result = await conn.execute(conn.text("SELECT 1"))
        version = await conn.execute(conn.text("SELECT version()"))
        version_info = version.scalar()
        logger.info("database_connected", version=version_info)


async def get_db_session() -> AsyncSession:
    """Get database session (dependency injection)"""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with _async_session_factory() as session:
        yield session


async def get_db_pool() -> Optional[AsyncEngine]:
    """Get database engine/connection pool"""
    return _engine


async def close_db_pool() -> None:
    """Close database connection pool"""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("database_pool_disposed")


async def get_session() -> AsyncSession:
    """Dependency to get database session for FastAPI routes"""
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized")
    
    async with _async_session_factory() as session:
        yield session
