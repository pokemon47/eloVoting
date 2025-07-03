import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import jwt
import os

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# Mock Supabase JWT (for contract tests)
FAKE_JWT = jwt.encode({"sub": "user1", "email": "user1@example.com", "role": "user"}, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {FAKE_JWT}"}

@pytest.mark.asyncio
async def test_create_poll_contract(async_client, auth_headers):
    resp = await async_client.post("/polls/", json={"title": "Test Poll", "creator_email": "user1@example.com"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Poll"
    assert data["creator_email"] == "user1@example.com"

@pytest.mark.asyncio
async def test_list_polls_contract(async_client, auth_headers):
    # Ensure at least one poll exists
    await async_client.post("/polls/", json={"title": "Test Poll", "creator_email": "user1@example.com"}, headers=auth_headers)
    resp = await async_client.get("/polls/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) > 0

@pytest.mark.asyncio
async def test_get_poll_not_found(async_client, auth_headers):
    resp = await async_client.get("/polls/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404 