import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Base
import os
from app.database import get_engine, get_sessionmaker

# Test DB config (matches docker-compose.test.yml)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://testuser:testpassword@localhost:5433/elovote_test"
)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = get_engine()
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(test_engine):
    async_session = get_sessionmaker(test_engine)
    async with async_session() as session:
        yield session 