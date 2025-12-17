"""
Database configuration and session management
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # For simpler connection management
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Create sync engine for Alembic
from sqlalchemy import create_engine as create_sync_engine
sync_engine = create_sync_engine(settings.DATABASE_SYNC_URL)

# Create base class for models
Base = declarative_base()

async def get_db():
    """
    Dependency function to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Sync session for Alembic
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_db_sync():
    """
    Sync database session for Alembic
    """
    db = SessionLocalSync()
    try:
        yield db
    finally:
        db.close()