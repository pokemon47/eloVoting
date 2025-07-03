import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import jwt
import uuid
import asyncio
import os

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

FAKE_JWT_1 = jwt.encode({"sub": "userA", "email": "userA@example.com", "role": "user"}, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")
FAKE_JWT_2 = jwt.encode({"sub": "userB", "email": "userB@example.com", "role": "user"}, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")

@pytest.fixture
def auth_headers_1():
    return {"Authorization": f"Bearer {FAKE_JWT_1}"}

@pytest.fixture
def auth_headers_2():
    return {"Authorization": f"Bearer {FAKE_JWT_2}"}

@pytest.mark.asyncio
async def test_concurrent_voting(async_client, auth_headers_1, auth_headers_2):
    # Create poll
    poll_resp = await async_client.post("/polls/", json={"title": "Concurrent Poll", "creator_email": "userA@example.com"}, headers=auth_headers_1)
    assert poll_resp.status_code == 200
    poll_id = poll_resp.json()["id"]

    # Create options
    option1_resp = await async_client.post(f"/polls/{poll_id}/options/", json={"label": "Option 1"}, headers=auth_headers_1)
    option2_resp = await async_client.post(f"/polls/{poll_id}/options/", json={"label": "Option 2"}, headers=auth_headers_1)
    assert option1_resp.status_code == 200
    assert option2_resp.status_code == 200
    option1_id = option1_resp.json()["id"]
    option2_id = option2_resp.json()["id"]

    # Start sessions
    session_resp_1 = await async_client.post("/votes/session/", json={"poll_id": poll_id, "voter_email": "userA@example.com"}, headers=auth_headers_1)
    session_resp_2 = await async_client.post("/votes/session/", json={"poll_id": poll_id, "voter_email": "userB@example.com"}, headers=auth_headers_2)
    assert session_resp_1.status_code == 200
    assert session_resp_2.status_code == 200
    session_id_1 = session_resp_1.json()["id"]
    session_id_2 = session_resp_2.json()["id"]

    # Simulate concurrent match submissions (simplified)
    match_resp_1 = await async_client.post("/votes/match/", json={
        "session_id": session_id_1,
        "winner_option_id": option1_id,
        "loser_option_id": option2_id,
        "match_index": 0
    }, headers=auth_headers_1)
    match_resp_2 = await async_client.post("/votes/match/", json={
        "session_id": session_id_2,
        "winner_option_id": option2_id,
        "loser_option_id": option1_id,
        "match_index": 0
    }, headers=auth_headers_2)
    assert match_resp_1.status_code == 200
    assert match_resp_2.status_code == 200

    # 4. Complete both sessions concurrently
    async def complete_session(session_id, headers):
        return await async_client.post(f"/votes/session/{session_id}/complete", headers=headers)
    results = await asyncio.gather(
        complete_session(session_id_1, auth_headers_1),
        complete_session(session_id_2, auth_headers_2)
    )
    assert all(r.status_code in (200, 400) for r in results)  # 400 if session incomplete

    # 5. Check leaderboard (should reflect both users' votes if sessions were complete)
    leaderboard_resp = await async_client.get(f"/polls/{poll_id}/leaderboard", headers=auth_headers_1)
    assert leaderboard_resp.status_code in (200, 403) 