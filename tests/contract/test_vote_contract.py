import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import jwt
import uuid
import os

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

FAKE_JWT = jwt.encode({"sub": "user3", "email": "user3@example.com", "role": "user"}, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {FAKE_JWT}"}

@pytest.mark.asyncio
async def test_start_session_contract(async_client, auth_headers):
    # Create poll first
    poll_resp = await async_client.post("/polls/", json={"title": "Test Poll", "creator_email": "user3@example.com"}, headers=auth_headers)
    assert poll_resp.status_code == 200
    poll_id = poll_resp.json()["id"]
    # Now create session
    resp = await async_client.post("/votes/session/", json={"poll_id": poll_id, "voter_email": "user3@example.com"}, headers=auth_headers)
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_submit_match_contract(async_client, auth_headers):
    # Create poll
    poll_resp = await async_client.post("/polls/", json={"title": "Test Poll", "creator_email": "user3@example.com"}, headers=auth_headers)
    assert poll_resp.status_code == 200
    poll_id = poll_resp.json()["id"]
    # Create two options
    option1_resp = await async_client.post(f"/polls/{poll_id}/options/", json={"label": "Option 1"}, headers=auth_headers)
    option2_resp = await async_client.post(f"/polls/{poll_id}/options/", json={"label": "Option 2"}, headers=auth_headers)
    assert option1_resp.status_code == 200
    assert option2_resp.status_code == 200
    option1_id = option1_resp.json()["id"]
    option2_id = option2_resp.json()["id"]
    # Create session
    session_resp = await async_client.post("/votes/session/", json={"poll_id": poll_id, "voter_email": "user3@example.com"}, headers=auth_headers)
    assert session_resp.status_code == 200
    session_id = session_resp.json()["id"]
    # Now submit match
    resp = await async_client.post("/votes/match/", json={
        "session_id": session_id,
        "winner_option_id": option1_id,
        "loser_option_id": option2_id,
        "match_index": 0
    }, headers=auth_headers)
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_complete_session_unauthorized(async_client):
    session_id = str(uuid.uuid4())
    resp = await async_client.post(f"/votes/session/{session_id}/complete")
    assert resp.status_code == 403 or resp.status_code == 401

@pytest.mark.asyncio
async def test_complete_session_double(async_client, auth_headers):
    # Create poll
    poll_resp = await async_client.post("/polls/", json={"title": "Test Poll", "creator_email": "user3@example.com"}, headers=auth_headers)
    assert poll_resp.status_code == 200
    poll_id = poll_resp.json()["id"]
    # Create session
    session_resp = await async_client.post("/votes/session/", json={"poll_id": poll_id, "voter_email": "user3@example.com"}, headers=auth_headers)
    assert session_resp.status_code == 200
    session_id = session_resp.json()["id"]
    # Complete session (will fail if not all matches submitted, but should not 404)
    resp1 = await async_client.post(f"/votes/session/{session_id}/complete", headers=auth_headers)
    assert resp1.status_code in (200, 400)
    resp2 = await async_client.post(f"/votes/session/{session_id}/complete", headers=auth_headers)
    assert resp2.status_code in (400, 404)

@pytest.mark.asyncio
async def test_submit_match_bad_input(async_client, auth_headers):
    # Missing required fields
    resp = await async_client.post("/votes/match/", json={"session_id": str(uuid.uuid4())}, headers=auth_headers)
    assert resp.status_code == 422 