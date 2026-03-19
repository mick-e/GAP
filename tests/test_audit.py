from src.audit.service import log_action, get_audit_logs, get_user_audit_trail, get_audit_stats
from src.audit.schemas import AuditLogFilter
from src.models.audit_log import AuditLog


async def test_log_action_creates_entry(db):
    entry = await log_action(db, None, "test.action", status="success")
    assert entry.id is not None
    assert entry.action == "test.action"
    assert entry.status == "success"


async def test_log_action_with_all_fields(db):
    entry = await log_action(
        db, "user-123", "auth.login", "user", "user-123",
        details={"method": "password"},
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        status="success",
    )
    assert entry.user_id == "user-123"
    assert entry.action == "auth.login"
    assert entry.resource_type == "user"
    assert entry.resource_id == "user-123"
    assert entry.details == {"method": "password"}
    assert entry.ip_address == "127.0.0.1"
    assert entry.user_agent == "TestAgent/1.0"


async def test_get_audit_logs_returns_entries(db):
    await log_action(db, None, "auth.login")
    await log_action(db, None, "auth.register")

    filters = AuditLogFilter()
    logs = await get_audit_logs(db, filters)
    assert len(logs) == 2


async def test_get_audit_logs_filter_by_action(db):
    await log_action(db, None, "auth.login")
    await log_action(db, None, "auth.register")

    filters = AuditLogFilter(action="auth.login")
    logs = await get_audit_logs(db, filters)
    assert len(logs) == 1
    assert logs[0].action == "auth.login"


async def test_get_audit_logs_filter_by_status(db):
    await log_action(db, None, "auth.login", status="success")
    await log_action(db, None, "auth.login", status="failure")

    filters = AuditLogFilter(status="failure")
    logs = await get_audit_logs(db, filters)
    assert len(logs) == 1
    assert logs[0].status == "failure"


async def test_get_audit_logs_pagination(db):
    for i in range(5):
        await log_action(db, None, f"action.{i}")

    filters = AuditLogFilter(limit=2, offset=0)
    logs = await get_audit_logs(db, filters)
    assert len(logs) == 2

    filters = AuditLogFilter(limit=2, offset=3)
    logs = await get_audit_logs(db, filters)
    assert len(logs) == 2


async def test_get_user_audit_trail(db):
    await log_action(db, "user-1", "auth.login")
    await log_action(db, "user-2", "auth.login")
    await log_action(db, "user-1", "api_key.create")

    trail = await get_user_audit_trail(db, "user-1")
    assert len(trail) == 2
    assert all(e.user_id == "user-1" for e in trail)


async def test_get_audit_stats(db):
    await log_action(db, None, "auth.login")
    await log_action(db, None, "auth.login")
    await log_action(db, None, "auth.register")

    stats = await get_audit_stats(db)
    assert stats["total"] == 3
    assert stats["by_action"]["auth.login"] == 2
    assert stats["by_action"]["auth.register"] == 1


async def test_audit_logs_endpoint_requires_admin(auth_client):
    resp = await auth_client.get("/api/v1/audit/logs")
    assert resp.status_code == 403


async def test_audit_stats_endpoint_requires_admin(auth_client):
    resp = await auth_client.get("/api/v1/audit/stats")
    assert resp.status_code == 403


async def test_audit_user_trail_endpoint_requires_admin(auth_client):
    resp = await auth_client.get("/api/v1/audit/logs/some-user-id")
    assert resp.status_code == 403


async def test_audit_logs_endpoint_admin_access(auth_client, db):
    # Promote user to admin
    from sqlalchemy import update
    from src.models.user import User
    await db.execute(update(User).values(role="admin"))
    await db.commit()

    resp = await auth_client.get("/api/v1/audit/logs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_audit_stats_endpoint_admin_access(auth_client, db):
    from sqlalchemy import update
    from src.models.user import User
    await db.execute(update(User).values(role="admin"))
    await db.commit()

    resp = await auth_client.get("/api/v1/audit/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "by_action" in data
    assert "by_day" in data


async def test_login_creates_audit_entry(client, db):
    await client.post("/api/v1/auth/register", json={
        "email": "audit@example.com", "password": "pass123"
    })
    await client.post("/api/v1/auth/login", json={
        "email": "audit@example.com", "password": "pass123"
    })

    filters = AuditLogFilter(action="auth.login")
    logs = await get_audit_logs(db, filters)
    assert len(logs) >= 1
    assert logs[0].action == "auth.login"


async def test_failed_login_creates_audit_entry(client, db):
    await client.post("/api/v1/auth/login", json={
        "email": "noone@example.com", "password": "wrong"
    })

    filters = AuditLogFilter(action="auth.login", status="failure")
    logs = await get_audit_logs(db, filters)
    assert len(logs) >= 1
    assert logs[0].status == "failure"


async def test_register_creates_audit_entry(client, db):
    await client.post("/api/v1/auth/register", json={
        "email": "reg@example.com", "password": "pass123", "name": "Reg"
    })

    filters = AuditLogFilter(action="auth.register")
    logs = await get_audit_logs(db, filters)
    assert len(logs) >= 1


async def test_api_key_create_audit_entry(auth_client, db):
    await auth_client.post("/api/v1/auth/api-keys", json={"name": "Audited Key"})

    filters = AuditLogFilter(action="api_key.create")
    logs = await get_audit_logs(db, filters)
    assert len(logs) >= 1
    assert logs[0].details["name"] == "Audited Key"
