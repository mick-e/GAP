import hashlib
import hmac

from src.config import get_settings


def verify_github_signature(payload: bytes, signature: str | None) -> bool:
    settings = get_settings()
    if not settings.github_webhook_secret:
        return True  # No secret configured, skip verification
    if not signature:
        return False
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
