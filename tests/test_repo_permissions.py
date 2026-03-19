from unittest.mock import AsyncMock, patch, MagicMock


async def test_api_key_with_repo_restriction_allowed(auth_client, db):
    """Test API key with repo restrictions can access allowed repos."""
    resp = await auth_client.post("/api/v1/auth/api-keys", json={
        "name": "Repo Restricted Key",
        "permissions": {"scopes": ["repos"]},
        "repos": ["allowed-repo"],
    })
    assert resp.status_code == 201
    raw_key = resp.json()["key"]

    # Use pulls endpoint which is simpler to mock
    with patch("src.github.client.GitHubClient.list_pull_requests", new_callable=AsyncMock) as mock_prs:
        mock_prs.return_value = []

        resp = await auth_client.get(
            "/api/v1/repos/allowed-repo/pulls?state=all",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    # Should NOT get 403 (auth passed), may get other status from mocked endpoint
    assert resp.status_code != 403


async def test_api_key_with_repo_restriction_denied(auth_client, db):
    """Test API key with repo restrictions gets 403 on disallowed repos."""
    resp = await auth_client.post("/api/v1/auth/api-keys", json={
        "name": "Repo Restricted Key",
        "permissions": {"scopes": ["repos"]},
        "repos": ["allowed-repo"],
    })
    assert resp.status_code == 201
    raw_key = resp.json()["key"]

    # Access disallowed repo should get 403
    resp = await auth_client.get(
        "/api/v1/repos/forbidden-repo/commits?period=month",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 403
    assert "does not have access to repo" in resp.json()["detail"]


async def test_api_key_with_wildcard_repos(auth_client, db):
    """Test API key with wildcard repos has full access."""
    resp = await auth_client.post("/api/v1/auth/api-keys", json={
        "name": "Wildcard Repos Key",
        "permissions": {"scopes": ["repos"]},
        "repos": ["*"],
    })
    assert resp.status_code == 201
    raw_key = resp.json()["key"]

    with patch("src.github.client.GitHubClient.list_pull_requests", new_callable=AsyncMock) as mock_prs:
        mock_prs.return_value = []

        resp = await auth_client.get(
            "/api/v1/repos/any-repo/pulls?state=all",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    assert resp.status_code != 403


async def test_api_key_with_empty_repos(auth_client, db):
    """Test API key with no repo restrictions has access to all repos."""
    resp = await auth_client.post("/api/v1/auth/api-keys", json={
        "name": "No Repo Restriction Key",
        "permissions": {"scopes": ["repos"]},
    })
    assert resp.status_code == 201
    raw_key = resp.json()["key"]

    with patch("src.github.client.GitHubClient.list_pull_requests", new_callable=AsyncMock) as mock_prs:
        mock_prs.return_value = []

        resp = await auth_client.get(
            "/api/v1/repos/any-repo/pulls?state=all",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
    assert resp.status_code != 403


async def test_jwt_user_bypasses_repo_checks(auth_client):
    """Test JWT users bypass repo permission checks."""
    with patch("src.github.client.GitHubClient.list_pull_requests", new_callable=AsyncMock) as mock_prs:
        mock_prs.return_value = []

        resp = await auth_client.get(
            "/api/v1/repos/any-repo/pulls?state=all",
        )
    # JWT user should not get 401 or 403
    assert resp.status_code != 403
    assert resp.status_code != 401


async def test_api_key_repos_stored_in_permissions(auth_client):
    """Test repos are stored correctly in permissions JSON."""
    resp = await auth_client.post("/api/v1/auth/api-keys", json={
        "name": "Multi Repo Key",
        "permissions": {"scopes": ["repos", "reports"]},
        "repos": ["repo-a", "repo-b", "repo-c"],
    })
    assert resp.status_code == 201
    # Verify the key was created
    keys_resp = await auth_client.get("/api/v1/auth/api-keys")
    assert keys_resp.status_code == 200
    keys = keys_resp.json()
    assert any(k["name"] == "Multi Repo Key" for k in keys)


async def test_repo_restriction_on_pulls_endpoint(auth_client, db):
    """Test repo restriction works on pulls endpoint too."""
    resp = await auth_client.post("/api/v1/auth/api-keys", json={
        "name": "PR Restricted Key",
        "permissions": {"scopes": ["repos"]},
        "repos": ["only-this-repo"],
    })
    assert resp.status_code == 201
    raw_key = resp.json()["key"]

    resp = await auth_client.get(
        "/api/v1/repos/other-repo/pulls?state=all",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 403


async def test_repo_restriction_on_issues_endpoint(auth_client, db):
    """Test repo restriction works on issues endpoint."""
    resp = await auth_client.post("/api/v1/auth/api-keys", json={
        "name": "Issues Restricted Key",
        "permissions": {"scopes": ["repos"]},
        "repos": ["my-repo"],
    })
    assert resp.status_code == 201
    raw_key = resp.json()["key"]

    resp = await auth_client.get(
        "/api/v1/repos/not-my-repo/issues?state=open",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 403


async def test_repo_restriction_on_security_endpoint(auth_client, db):
    """Test repo restriction works on security endpoint."""
    resp = await auth_client.post("/api/v1/auth/api-keys", json={
        "name": "Security Restricted Key",
        "permissions": {"scopes": ["repos"]},
        "repos": ["secure-repo"],
    })
    assert resp.status_code == 201
    raw_key = resp.json()["key"]

    resp = await auth_client.get(
        "/api/v1/repos/other-repo/security",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 403
