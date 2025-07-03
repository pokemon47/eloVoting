import pytest_asyncio
from app.database import get_engine
from app.models import Base

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 