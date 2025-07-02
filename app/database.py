import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine.url import URL
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(
    DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=False,
    future=True
)

async_session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session 