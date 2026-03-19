import pytest
from unittest.mock import AsyncMock, MagicMock

from src.notifications.manager import ConnectionManager
from src.notifications.service import (
    create_notification,
    get_notifications,
    mark_read,
    mark_all_read,
    get_unread_count,
)
from src.models.notification import Notification


# --- ConnectionManager tests ---


async def test_manager_connect():
    mgr = ConnectionManager()
    ws = AsyncMock()
    await mgr.connect(ws, "user-1")
    assert "user-1" in mgr.active_connections
    assert ws in mgr.active_connections["user-1"]
    ws.accept.assert_awaited_once()


async def test_manager_disconnect():
    mgr = ConnectionManager()
    ws = AsyncMock()
    await mgr.connect(ws, "user-1")
    mgr.disconnect(ws, "user-1")
    assert "user-1" not in mgr.active_connections


async def test_manager_disconnect_one_of_many():
    mgr = ConnectionManager()
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    await mgr.connect(ws1, "user-1")
    await mgr.connect(ws2, "user-1")
    mgr.disconnect(ws1, "user-1")
    assert ws2 in mgr.active_connections["user-1"]
    assert ws1 not in mgr.active_connections["user-1"]


async def test_manager_send_to_user():
    mgr = ConnectionManager()
    ws = AsyncMock()
    await mgr.connect(ws, "user-1")
    await mgr.send_to_user("user-1", {"msg": "hello"})
    ws.send_json.assert_awaited_once_with({"msg": "hello"})


async def test_manager_send_to_nonexistent_user():
    mgr = ConnectionManager()
    # Should not raise
    await mgr.send_to_user("nobody", {"msg": "hello"})


async def test_manager_broadcast():
    mgr = ConnectionManager()
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    await mgr.connect(ws1, "user-1")
    await mgr.connect(ws2, "user-2")
    await mgr.broadcast({"msg": "broadcast"})
    ws1.send_json.assert_awaited_once_with({"msg": "broadcast"})
    ws2.send_json.assert_awaited_once_with({"msg": "broadcast"})


async def test_manager_send_handles_error():
    mgr = ConnectionManager()
    ws = AsyncMock()
    ws.send_json.side_effect = RuntimeError("connection lost")
    await mgr.connect(ws, "user-1")
    # Should not raise
    await mgr.send_to_user("user-1", {"msg": "hello"})


# --- Service tests (with real DB) ---


async def test_create_notification(db):
    from src.models.user import User
    user = User(email="notif@test.com", hashed_password="x", name="Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    n = await create_notification(
        db, user.id, "alert", "Test Alert", "Something happened"
    )
    assert n.id is not None
    assert n.type == "alert"
    assert n.title == "Test Alert"
    assert n.read is False


async def test_get_notifications(db):
    from src.models.user import User
    user = User(email="notif2@test.com", hashed_password="x")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await create_notification(db, user.id, "alert", "A1", "msg1")
    await create_notification(db, user.id, "system", "A2", "msg2")

    results = await get_notifications(db, user.id)
    assert len(results) == 2


async def test_get_notifications_unread_only(db):
    from src.models.user import User
    user = User(email="notif3@test.com", hashed_password="x")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    n1 = await create_notification(db, user.id, "alert", "A1", "msg1")
    await create_notification(db, user.id, "alert", "A2", "msg2")
    await mark_read(db, n1.id, user.id)

    results = await get_notifications(db, user.id, unread_only=True)
    assert len(results) == 1
    assert results[0].title == "A2"


async def test_mark_read(db):
    from src.models.user import User
    user = User(email="notif4@test.com", hashed_password="x")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    n = await create_notification(db, user.id, "alert", "A1", "msg1")
    assert n.read is False

    success = await mark_read(db, n.id, user.id)
    assert success is True


async def test_mark_read_wrong_user(db):
    from src.models.user import User
    user = User(email="notif5@test.com", hashed_password="x")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    n = await create_notification(db, user.id, "alert", "A1", "msg1")
    success = await mark_read(db, n.id, "wrong-user-id")
    assert success is False


async def test_mark_all_read(db):
    from src.models.user import User
    user = User(email="notif6@test.com", hashed_password="x")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await create_notification(db, user.id, "alert", "A1", "msg1")
    await create_notification(db, user.id, "alert", "A2", "msg2")
    await create_notification(db, user.id, "alert", "A3", "msg3")

    count = await mark_all_read(db, user.id)
    assert count == 3

    unread = await get_unread_count(db, user.id)
    assert unread == 0


async def test_unread_count(db):
    from src.models.user import User
    user = User(email="notif7@test.com", hashed_password="x")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await create_notification(db, user.id, "alert", "A1", "msg1")
    await create_notification(db, user.id, "alert", "A2", "msg2")

    count = await get_unread_count(db, user.id)
    assert count == 2


# --- HTTP endpoint tests ---


async def test_list_notifications_requires_auth(client):
    resp = await client.get("/api/v1/notifications")
    assert resp.status_code == 401


async def test_unread_count_requires_auth(client):
    resp = await client.get("/api/v1/notifications/unread-count")
    assert resp.status_code == 401


async def test_notifications_crud_flow(auth_client, db):
    # Create some notifications for the user
    me = await auth_client.get("/api/v1/auth/me")
    user_id = me.json()["id"]

    await create_notification(db, user_id, "alert", "Test1", "msg1")
    await create_notification(db, user_id, "system", "Test2", "msg2")

    # List
    resp = await auth_client.get("/api/v1/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

    # Unread count
    resp = await auth_client.get("/api/v1/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json()["count"] == 2

    # Mark one as read
    nid = data[0]["id"]
    resp = await auth_client.post(f"/api/v1/notifications/{nid}/read")
    assert resp.status_code == 200

    # Unread count should be 1
    resp = await auth_client.get("/api/v1/notifications/unread-count")
    assert resp.json()["count"] == 1

    # Mark all as read
    resp = await auth_client.post("/api/v1/notifications/read-all")
    assert resp.status_code == 200
    assert resp.json()["marked_read"] == 1

    # Unread count should be 0
    resp = await auth_client.get("/api/v1/notifications/unread-count")
    assert resp.json()["count"] == 0


async def test_mark_read_not_found(auth_client):
    resp = await auth_client.post("/api/v1/notifications/nonexistent-id/read")
    assert resp.status_code == 404
