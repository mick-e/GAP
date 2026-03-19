from unittest.mock import AsyncMock, patch

from src.oauth.schemas import OAuthUserInfo


async def test_github_authorize(client):
    """Test authorize URL generation."""
    with patch("src.oauth.router.get_settings") as mock_settings:
        mock_settings.return_value.github_client_id = "test-client-id"
        mock_settings.return_value.github_client_secret = "test-secret"
        resp = await client.get("/api/v1/oauth/github/authorize")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "test-client-id" in data["url"]
    assert "github.com/login/oauth/authorize" in data["url"]


async def test_github_authorize_not_configured(client):
    """Test authorize returns 501 when not configured."""
    resp = await client.get("/api/v1/oauth/github/authorize")
    assert resp.status_code == 501


async def test_github_callback_success(client, db):
    """Test callback with mocked GitHub API."""
    mock_user = OAuthUserInfo(
        login="testghuser",
        email="ghuser@example.com",
        name="GH User",
        avatar_url="https://avatars.githubusercontent.com/u/12345",
    )

    with (
        patch("src.oauth.router.get_settings") as mock_settings,
        patch("src.oauth.router.exchange_code_for_token", new_callable=AsyncMock) as mock_exchange,
        patch("src.oauth.router.get_github_user", new_callable=AsyncMock) as mock_gh_user,
    ):
        mock_settings.return_value.github_client_id = "test-client-id"
        mock_settings.return_value.github_client_secret = "test-secret"
        mock_exchange.return_value = "gho_test_token"
        mock_gh_user.return_value = mock_user

        resp = await client.post(
            "/api/v1/oauth/github/callback",
            json={"code": "test-auth-code"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "ghuser@example.com"
    assert data["user"]["name"] == "GH User"


async def test_github_callback_creates_new_user(client, db):
    """Test callback creates a new user when none exists."""
    mock_user = OAuthUserInfo(
        login="newghuser",
        email="newuser@example.com",
        name="New GH User",
        avatar_url="https://avatars.githubusercontent.com/u/99999",
    )

    with (
        patch("src.oauth.router.get_settings") as mock_settings,
        patch("src.oauth.router.exchange_code_for_token", new_callable=AsyncMock) as mock_exchange,
        patch("src.oauth.router.get_github_user", new_callable=AsyncMock) as mock_gh_user,
    ):
        mock_settings.return_value.github_client_id = "test-client-id"
        mock_settings.return_value.github_client_secret = "test-secret"
        mock_exchange.return_value = "gho_test_token"
        mock_gh_user.return_value = mock_user

        resp = await client.post(
            "/api/v1/oauth/github/callback",
            json={"code": "test-auth-code"},
        )

    assert resp.status_code == 200
    token = resp.json()["access_token"]

    # Verify user was created by using the token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "newuser@example.com"


async def test_github_callback_links_existing_user(client, db):
    """Test callback links to existing user by email."""
    # First, register a user with the same email
    await client.post("/api/v1/auth/register", json={
        "email": "existing@example.com",
        "password": "testpassword123",
        "name": "Existing User",
    })

    mock_user = OAuthUserInfo(
        login="existingghuser",
        email="existing@example.com",
        name="Existing GH User",
        avatar_url="https://avatars.githubusercontent.com/u/11111",
    )

    with (
        patch("src.oauth.router.get_settings") as mock_settings,
        patch("src.oauth.router.exchange_code_for_token", new_callable=AsyncMock) as mock_exchange,
        patch("src.oauth.router.get_github_user", new_callable=AsyncMock) as mock_gh_user,
    ):
        mock_settings.return_value.github_client_id = "test-client-id"
        mock_settings.return_value.github_client_secret = "test-secret"
        mock_exchange.return_value = "gho_test_token"
        mock_gh_user.return_value = mock_user

        resp = await client.post(
            "/api/v1/oauth/github/callback",
            json={"code": "test-auth-code"},
        )

    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    # Should be the same user with the existing email
    assert me_resp.json()["email"] == "existing@example.com"


async def test_github_callback_not_configured(client):
    """Test callback returns 501 when not configured."""
    resp = await client.post(
        "/api/v1/oauth/github/callback",
        json={"code": "test-code"},
    )
    assert resp.status_code == 501


async def test_github_status_enabled(client):
    """Test status endpoint when OAuth is configured."""
    with patch("src.oauth.router.get_settings") as mock_settings:
        mock_settings.return_value.github_client_id = "test-client-id"
        resp = await client.get("/api/v1/oauth/github/status")
    assert resp.status_code == 200
    assert resp.json()["github_enabled"] is True


async def test_github_status_disabled(client):
    """Test status endpoint when OAuth is not configured."""
    resp = await client.get("/api/v1/oauth/github/status")
    assert resp.status_code == 200
    assert resp.json()["github_enabled"] is False


async def test_github_callback_invalid_code(client):
    """Test callback with invalid code returns error."""
    with (
        patch("src.oauth.router.get_settings") as mock_settings,
        patch(
            "src.oauth.router.exchange_code_for_token",
            new_callable=AsyncMock,
            side_effect=ValueError("GitHub OAuth error: bad_verification_code"),
        ),
    ):
        mock_settings.return_value.github_client_id = "test-client-id"
        mock_settings.return_value.github_client_secret = "test-secret"

        resp = await client.post(
            "/api/v1/oauth/github/callback",
            json={"code": "invalid-code"},
        )

    assert resp.status_code == 400
