import hashlib
import hmac

from src.webhooks.verification import verify_github_signature


def test_verify_valid_signature():
    secret = "test-secret"
    payload = b'{"action": "opened"}'
    sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    from unittest.mock import patch
    with patch("src.webhooks.verification.get_settings") as mock:
        mock.return_value.github_webhook_secret = secret
        assert verify_github_signature(payload, sig) is True


def test_verify_invalid_signature():
    from unittest.mock import patch
    with patch("src.webhooks.verification.get_settings") as mock:
        mock.return_value.github_webhook_secret = "secret"
        assert verify_github_signature(b"payload", "sha256=invalid") is False


def test_verify_no_secret_configured():
    from unittest.mock import patch
    with patch("src.webhooks.verification.get_settings") as mock:
        mock.return_value.github_webhook_secret = ""
        assert verify_github_signature(b"payload", None) is True


def test_verify_missing_signature():
    from unittest.mock import patch
    with patch("src.webhooks.verification.get_settings") as mock:
        mock.return_value.github_webhook_secret = "secret"
        assert verify_github_signature(b"payload", None) is False


def test_verify_wrong_prefix():
    from unittest.mock import patch
    with patch("src.webhooks.verification.get_settings") as mock:
        mock.return_value.github_webhook_secret = "secret"
        assert verify_github_signature(b"payload", "sha1=abc") is False


async def test_webhook_endpoint_push(client, db):
    payload = {
        "ref": "refs/heads/main",
        "repository": {"name": "test-repo"},
        "sender": {"login": "testuser"},
    }
    resp = await client.post(
        "/api/v1/webhooks/github",
        json=payload,
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "test-delivery-123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processed"
    assert data["event_type"] == "push"


async def test_webhook_endpoint_missing_event(client):
    resp = await client.post("/api/v1/webhooks/github", json={})
    assert resp.status_code == 400


async def test_webhook_endpoint_pr_event(client, db):
    payload = {
        "action": "opened",
        "pull_request": {"number": 1, "title": "Test PR"},
        "repository": {"name": "test-repo"},
        "sender": {"login": "testuser"},
    }
    resp = await client.post(
        "/api/v1/webhooks/github",
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert resp.status_code == 200
    assert resp.json()["event_type"] == "pull_request"
