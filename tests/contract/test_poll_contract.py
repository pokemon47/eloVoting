import pytest
from fastapi.testclient import TestClient
from app.main import app
import jwt
import os

# Mock Supabase JWT (for contract tests)
FAKE_JWT = jwt.encode({"sub": "user1", "email": "user1@example.com", "role": "user"}, "secret", algorithm="HS256")

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {FAKE_JWT}"}

def test_create_poll_contract(client, auth_headers):
    resp = client.post("/polls/", json={"title": "Test Poll", "creator_email": "user1@example.com"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data and "title" in data
    assert data["title"] == "Test Poll"

def test_list_polls_contract(client, auth_headers):
    resp = client.get("/polls/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_get_poll_not_found(client, auth_headers):
    resp = client.get("/polls/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404
    assert "not found" in resp.text.lower() 