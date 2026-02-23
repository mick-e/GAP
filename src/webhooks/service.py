import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.webhook_event import WebhookEvent
from src.cache import cache_invalidate_pattern

logger = logging.getLogger(__name__)

EVENT_CACHE_MAP = {
    "push": ["commits", "activity"],
    "pull_request": ["pulls", "prs", "contributors"],
    "issues": ["issues"],
    "release": ["releases", "activity"],
    "workflow_run": ["workflows"],
}


async def process_webhook_event(
    db: AsyncSession,
    event_type: str,
    payload: dict,
    delivery_id: str | None = None,
) -> WebhookEvent:
    repo_name = None
    if "repository" in payload:
        repo_name = payload["repository"].get("name")

    action = payload.get("action")
    sender = None
    if "sender" in payload:
        sender = payload["sender"].get("login")

    event = WebhookEvent(
        event_type=event_type,
        action=action,
        repo_name=repo_name,
        sender=sender,
        payload=payload,
        delivery_id=delivery_id,
        processed=False,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Invalidate caches
    patterns = EVENT_CACHE_MAP.get(event_type, [])
    for pattern in patterns:
        await cache_invalidate_pattern(pattern)

    event.processed = True
    await db.commit()

    logger.info(f"Processed webhook: {event_type}/{action} for {repo_name}")
    return event
