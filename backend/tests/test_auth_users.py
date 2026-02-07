import uuid
import os


def test_token_success(client):
    admin_id = os.environ.get("DEFAULT_ADMIN_ID", "admin")
    admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin")
    res = client.post(
        "/token",
        data={"username": admin_id, "password": admin_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["tokenType"] == "bearer"
    assert isinstance(body["accessToken"], str) and body["accessToken"]


def test_token_invalid_credentials(client):
    admin_id = os.environ.get("DEFAULT_ADMIN_ID", "admin")
    res = client.post(
        "/token",
        data={"username": admin_id, "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401


def test_users_me_requires_auth(client):
    res = client.get("/users/me")
    assert res.status_code == 401


def test_users_me_returns_current_user(client, auth_headers):
    admin_id = os.environ.get("DEFAULT_ADMIN_ID", "admin")
    res = client.get("/users/me", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == admin_id
    assert body["name"]


def test_users_crud(client, auth_headers):
    user_id = f"u-{uuid.uuid4().hex[:8]}"
    payload = {
        "id": user_id,
        "name": f"Test User {user_id}",
        "role": "Security Analyst",
        "clearanceLevel": "L1",
        "status": "ACTIVE",
        "permissions": ["READ_LOGS"],
        "avatarSeed": "seed",
        "password": "pass1234",
    }

    res = client.post("/users", json=payload, headers=auth_headers)
    assert res.status_code == 200
    created = res.json()
    assert created["id"] == user_id
    assert created["name"] == payload["name"]

    res = client.get("/users", headers=auth_headers)
    assert res.status_code == 200
    users = res.json()
    assert any(u["id"] == user_id for u in users)

    payload_update = {**payload, "status": "LOCKED", "password": "newpass"}
    res = client.put(f"/users/{user_id}", json=payload_update, headers=auth_headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["status"] == "LOCKED"

    res = client.delete(f"/users/{user_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == {"ok": True}

    res = client.delete(f"/users/{user_id}", headers=auth_headers)
    assert res.status_code == 404


def test_create_user_duplicate_name_rejected(client, auth_headers):
    payload = {
        "id": "dup1",
        "name": "Duplicate Name",
        "role": "Security Analyst",
        "clearanceLevel": "L1",
        "status": "ACTIVE",
        "permissions": ["READ_LOGS"],
        "password": "pass1234",
    }

    res = client.post("/users", json=payload, headers=auth_headers)
    assert res.status_code == 200
    res = client.post("/users", json={**payload, "id": "dup2"}, headers=auth_headers)
    assert res.status_code == 400
