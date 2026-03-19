import logging
from datetime import datetime

from sqlalchemy import select
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

    # Notify admin users about webhook events
    try:
        from src.notifications.service import notify_and_broadcast
        from sqlalchemy import select as sa_select
        from src.models.user import User

        admins = await db.execute(
            sa_select(User).where(User.role == "admin", User.is_active == True)  # noqa: E712
        )
        for admin in admins.scalars().all():
            await notify_and_broadcast(
                db,
                admin.id,
                type="webhook",
                title=f"Webhook: {event_type}",
                message=f"{event_type}/{action} received for {repo_name or 'unknown'}",
                data={"event_id": event.id, "repo": repo_name, "sender": sender},
            )
    except Exception as e:
        logger.warning(f"Failed to send webhook notification: {e}")

    logger.info(f"Processed webhook: {event_type}/{action} for {repo_name}")
    return event


async def list_events(
    db: AsyncSession,
    event_type: str | None = None,
    repo_name: str | None = None,
    processed: bool | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[WebhookEvent]:
    query = select(WebhookEvent).order_by(WebhookEvent.created_at.desc())

    if event_type is not None:
        query = query.where(WebhookEvent.event_type == event_type)
    if repo_name is not None:
        query = query.where(WebhookEvent.repo_name == repo_name)
    if processed is not None:
        query = query.where(WebhookEvent.processed == processed)
    if start_date is not None:
        query = query.where(WebhookEvent.created_at >= start_date)
    if end_date is not None:
        query = query.where(WebhookEvent.created_at <= end_date)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_event(db: AsyncSession, event_id: str) -> WebhookEvent | None:
    result = await db.execute(
        select(WebhookEvent).where(WebhookEvent.id == event_id)
    )
    return result.scalar_one_or_none()


async def replay_event(db: AsyncSession, event_id: str) -> WebhookEvent:
    event = await get_event(db, event_id)
    if event is None:
        raise ValueError(f"Event {event_id} not found")

    # Reset processed state and clear any error
    event.processed = False
    event.error = None
    await db.commit()

    # Re-process: invalidate caches then mark processed
    patterns = EVENT_CACHE_MAP.get(event.event_type, [])
    for pattern in patterns:
        await cache_invalidate_pattern(pattern)

    event.processed = True
    await db.commit()
    await db.refresh(event)

    logger.info(f"Replayed webhook: {event.event_type}/{event.action} for {event.repo_name}")
    return event


async def replay_batch(
    db: AsyncSession, event_ids: list[str]
) -> dict:
    successful = 0
    failed = 0
    results = []

    for event_id in event_ids:
        try:
            await replay_event(db, event_id)
            results.append({"event_id": event_id, "success": True, "error": None})
            successful += 1
        except Exception as e:
            results.append({"event_id": event_id, "success": False, "error": str(e)})
            failed += 1

    return {
        "total": len(event_ids),
        "successful": successful,
        "failed": failed,
        "results": results,
    }
