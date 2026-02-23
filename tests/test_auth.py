import pytest


async def test_register(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "securepass123",
        "name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["name"] == "New User"
    assert data["role"] == "user"


async def test_register_duplicate_email(client):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com", "password": "pass123"
    })
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com", "password": "pass456"
    })
    assert resp.status_code == 400


async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com", "password": "pass123"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "password": "pass123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com", "password": "pass123"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com", "password": "wrongpass"
    })
    assert resp.status_code == 401


async def test_get_me(auth_client):
    resp = await auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"


async def test_get_me_unauthenticated(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_create_api_key(auth_client):
    resp = await auth_client.post("/api/v1/auth/api-keys", json={"name": "Test Key"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Key"
    assert data["key"].startswith("bhapi_")
    assert "prefix" in data


async def test_list_api_keys(auth_client):
    await auth_client.post("/api/v1/auth/api-keys", json={"name": "Key 1"})
    await auth_client.post("/api/v1/auth/api-keys", json={"name": "Key 2"})

    resp = await auth_client.get("/api/v1/auth/api-keys")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


async def test_delete_api_key(auth_client):
    resp = await auth_client.post("/api/v1/auth/api-keys", json={"name": "Delete Me"})
    key_id = resp.json()["id"]

    resp = await auth_client.delete(f"/api/v1/auth/api-keys/{key_id}")
    assert resp.status_code == 204

    resp = await auth_client.get("/api/v1/auth/api-keys")
    assert len(resp.json()) == 0


async def test_jwt_token_auth(client):
    await client.post("/api/v1/auth/register", json={
        "email": "jwt@example.com", "password": "pass123"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "jwt@example.com", "password": "pass123"
    })
    token = resp.json()["access_token"]

    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "jwt@example.com"
