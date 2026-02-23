from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from .verification import verify_github_signature
from .service import process_webhook_event

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

    return {
        "status": "processed",
        "event_id": event.id,
        "event_type": x_github_event,
        "action": event.action,
    }
