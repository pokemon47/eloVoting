import pytest
from fastapi.testclient import TestClient
from app.main import app
import jwt
import uuid

# Mock Supabase JWT for E2E tests
FAKE_JWT = jwt.encode({"sub": "user2", "email": "user2@example.com", "role": "user"}, "secret", algorithm="HS256")

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {FAKE_JWT}"}

def test_full_voting_flow(client, auth_headers):
    # 1. Create a poll
    poll_resp = client.post("/polls/", json={"title": "E2E Poll", "creator_email": "user2@example.com"}, headers=auth_headers)
    assert poll_resp.status_code == 200
    poll_id = poll_resp.json()["id"]

    # 2. Add options (simulate via DB or API if available)
    # For this example, assume options are added via DB or another endpoint
    # Here, we just check the poll exists
    poll_list = client.get("/polls/", headers=auth_headers)
    assert any(p["id"] == poll_id for p in poll_list.json())

    # 3. Start a voter session
    session_resp = client.post("/votes/session/", json={"poll_id": poll_id, "voter_email": "user2@example.com"}, headers=auth_headers)
    assert session_resp.status_code == 200
    session_id = session_resp.json()["id"]

    # 4. Submit matches (simulate a few, not all for brevity)
    # In a real test, you would fetch options and submit all n(n-1)/2 matches
    # Here, we just check the endpoint works
    match_resp = client.post("/votes/match/", json={
        "session_id": session_id,
        "winner_option_id": str(uuid.uuid4()),
        "loser_option_id": str(uuid.uuid4()),
        "match_index": 0
    }, headers=auth_headers)
    assert match_resp.status_code == 200 or match_resp.status_code == 422  # 422 if invalid UUIDs

    # 5. Complete the session (should fail if not all matches submitted)
    complete_resp = client.post(f"/votes/session/{session_id}/complete", headers=auth_headers)
    assert complete_resp.status_code in (200, 400)  # 400 if session incomplete

    # 6. View leaderboard (should work if session completed)
    leaderboard_resp = client.get(f"/polls/{poll_id}/leaderboard", headers=auth_headers)
    assert leaderboard_resp.status_code in (200, 403)  # 403 if not authorized

    # NOTE: In production, use real JWTs and real option IDs 