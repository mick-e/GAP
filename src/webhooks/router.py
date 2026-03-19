from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.audit.service import log_action
from src.models.user import User
from src.auth.dependencies import require_admin
from .verification import verify_github_signature
from .service import process_webhook_event, list_events, get_event, replay_event, replay_batch
from .schemas import (
    WebhookEventResponse,
    WebhookEventDetail,
    WebhookReplayResult,
    WebhookBatchReplayRequest,
    WebhookBatchReplayResult,
)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/github")
async def receive_github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_github_event: str | None = Header(None),
    x_hub_signature_256: str | None = Header(None),
    x_github_delivery: str | None = Header(None),
):
    body = await request.body()

    if not verify_github_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if not x_github_event:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")

    payload = await request.json()
    event = await process_webhook_event(db, x_github_event, payload, x_github_delivery)

    await log_action(
        db, None, "webhook.received", "webhook_event", event.id,
        details={
            "event_type": x_github_event,
            "action": event.action,
            "delivery_id": x_github_delivery,
        },
        ip_address=request.client.host if request.client else None,
    )

    return {
        "status": "processed",
        "event_id": event.id,
        "event_type": x_github_event,
        "action": event.action,
    }


@router.get("/events", response_model=list[WebhookEventResponse])
async def list_webhook_events(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    event_type: str | None = Query(None),
    repo_name: str | None = Query(None),
    processed: bool | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    events = await list_events(
        db,
        event_type=event_type,
        repo_name=repo_name,
        processed=processed,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return [_to_response(e) for e in events]


@router.get("/events/{event_id}", response_model=WebhookEventDetail)
async def get_webhook_event(
    event_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _to_detail(event)


@router.post("/events/{event_id}/replay", response_model=WebhookReplayResult)
async def replay_webhook_event(
    event_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await replay_event(db, event_id)
        return WebhookReplayResult(event_id=event_id, success=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/events/replay-batch", response_model=WebhookBatchReplayResult)
async def replay_webhook_events_batch(
    body: WebhookBatchReplayRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await replay_batch(db, body.event_ids)
    return WebhookBatchReplayResult(**result)


def _to_response(event) -> WebhookEventResponse:
    return WebhookEventResponse(
        id=event.id,
        event_type=event.event_type,
        action=event.action,
        repo_name=event.repo_name,
        sender=event.sender,
        processed=event.processed,
        error=event.error,
        created_at=event.created_at.isoformat(),
    )


def _to_detail(event) -> WebhookEventDetail:
    return WebhookEventDetail(
        id=event.id,
        event_type=event.event_type,
        action=event.action,
        repo_name=event.repo_name,
        sender=event.sender,
        processed=event.processed,
        error=event.error,
        created_at=event.created_at.isoformat(),
        payload=event.payload,
    )
