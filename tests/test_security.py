

async def test_cors_headers(client):
    """CORS should return configured origins, not wildcard."""
    resp = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


async def test_cors_rejects_unknown_origin(client):
    """CORS should not include unknown origins."""
    resp = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.headers.get("access-control-allow-origin") != "http://evil.com"


async def test_health_check_database(client):
    """Health check should report database status."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "ok"


async def test_health_check_redis_not_configured(client):
    """Health check should report Redis as not configured when no URL set."""
    resp = await client.get("/health")
    data = resp.json()
    assert "redis" in data


async def test_rate_limit_login(client):
    """Login should be rate-limited to 10/minute."""
    for i in range(11):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": f"test{i}@example.com", "password": "wrong"},
        )
    assert resp.status_code == 429
