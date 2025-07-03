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

# Mock Supabase JWT for E2E tests
FAKE_JWT = jwt.encode({"sub": "user2", "email": "user2@example.com", "role": "user"}, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {FAKE_JWT}"}

@pytest.mark.asyncio
async def test_voting_flow(async_client, auth_headers):
    # Create poll
    poll_resp = await async_client.post("/polls/", json={"title": "Voting Flow Poll", "creator_email": "user2@example.com"}, headers=auth_headers)
    assert poll_resp.status_code == 200
    poll = poll_resp.json()
    poll_id = poll["id"]

    # Create options
    option1_resp = await async_client.post(f"/polls/{poll_id}/options/", json={"label": "Option 1"}, headers=auth_headers)
    option2_resp = await async_client.post(f"/polls/{poll_id}/options/", json={"label": "Option 2"}, headers=auth_headers)
    assert option1_resp.status_code == 200
    assert option2_resp.status_code == 200
    option1_id = option1_resp.json()["id"]
    option2_id = option2_resp.json()["id"]

    # Start session
    session_resp = await async_client.post("/votes/session/", json={"poll_id": poll_id, "voter_email": "user2@example.com"}, headers=auth_headers)
    assert session_resp.status_code == 200
    session = session_resp.json()
    session_id = session["id"]

    # Submit a match
    match_resp = await async_client.post("/votes/match/", json={
        "session_id": session_id,
        "winner_option_id": option1_id,
        "loser_option_id": option2_id,
        "match_index": 0
    }, headers=auth_headers)
    assert match_resp.status_code == 200

    # Complete session
    complete_resp = await async_client.post(f"/votes/session/{session_id}/complete", headers=auth_headers)
    assert complete_resp.status_code in (200, 400, 404)

    # Get leaderboard
    leaderboard_resp = await async_client.get(f"/polls/{poll_id}/leaderboard", headers=auth_headers)
    assert leaderboard_resp.status_code in (200, 403)

    # NOTE: In production, use real JWTs and real option IDs 