import logging

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.notification import Notification
from .manager import manager

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: str,
    type: str,
    title: str,
    message: str,
    data: dict | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        data=data,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def get_notifications(
    db: AsyncSession,
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> list[Notification]:
    stmt = select(Notification).where(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).limit(limit)
    if unread_only:
        stmt = stmt.where(Notification.read == False)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_read(
    db: AsyncSession, notification_id: str, user_id: str
) -> bool:
    result = await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(read=True)
    )
    await db.commit()
    return result.rowcount > 0


async def mark_all_read(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read == False)  # noqa: E712
        .values(read=True)
    )
    await db.commit()
    return result.rowcount


async def get_unread_count(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.read == False,  # noqa: E712
        )
    )
    return result.scalar_one()


async def notify_and_broadcast(
    db: AsyncSession,
    user_id: str,
    type: str,
    title: str,
    message: str,
    data: dict | None = None,
) -> Notification:
    notification = await create_notification(db, user_id, type, title, message, data)
    await manager.send_to_user(user_id, {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "data": notification.data,
        "read": notification.read,
        "created_at": notification.created_at.isoformat(),
    })
    logger.info(f"Notification sent to user {user_id}: {title}")
    return notification
