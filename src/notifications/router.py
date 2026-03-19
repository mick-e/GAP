from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.auth.service import decode_access_token, get_user_by_id
from src.models.user import User
from .manager import manager
from .schemas import NotificationResponse, UnreadCountResponse
from . import service

router = APIRouter(prefix="/api/v1", tags=["notifications"])


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub", "")
    async for session in get_db():
        user = await get_user_by_id(session, user_id)
        if not user or not user.is_active:
            await websocket.close(code=4001, reason="User not found")
            return

    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@router.get("/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False, description="Only show unread"),
    limit: int = Query(50, ge=1, le=200, description="Max notifications"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List notifications for the current user."""
    return await service.get_notifications(db, user.id, unread_only, limit)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    success = await service.mark_read(db, notification_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok"}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    count = await service.mark_all_read(db, user.id)
    return {"status": "ok", "marked_read": count}


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get unread notification count."""
    count = await service.get_unread_count(db, user.id)
    return UnreadCountResponse(count=count)
