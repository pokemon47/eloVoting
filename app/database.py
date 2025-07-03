import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine.url import URL
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_engine():
    print("[DEBUG] get_engine called. connect_args=", {"statement_cache_size": 0}, "DATABASE_URL=", DATABASE_URL)
    return create_async_engine(
        DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
        echo=False,
        future=True,
        connect_args={"statement_cache_size": 0}  # Prevent asyncpg prepared statement errors with PgBouncer
    )

def get_sessionmaker(engine=None):
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

# Dependency for FastAPI
async def get_async_session():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session

Base = declarative_base() 