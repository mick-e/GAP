from datetime import datetime, timedelta, timezone

from src.exports.scheduler import (
    create_export, list_exports, get_export, update_export,
    delete_export, get_due_exports, SCHEDULE_INTERVALS,
)
from src.models.scheduled_export import ScheduledExport


# --- Service tests ---

async def test_create_export(db):
    from src.models.user import User
    user = User(email="exp@example.com", hashed_password="x", name="Exp")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    export = await create_export(
        db, name="Weekly CSV", export_type="csv", data_source="contributors",
        schedule="weekly", recipients=["a@b.com"], config=None, user_id=user.id,
    )
    assert export.name == "Weekly CSV"
    assert export.export_type == "csv"
    assert export.data_source == "contributors"
    assert export.schedule == "weekly"
    assert export.is_active is True
    assert export.next_run_at is not None


async def test_list_exports(db):
    from src.models.user import User
    user = User(email="list@example.com", hashed_password="x", name="List")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await create_export(
        db, "E1", "pdf", "teams", "daily", [], None, user.id,
    )
    await create_export(
        db, "E2", "csv", "trends", "monthly", [], None, user.id,
    )

    exports = await list_exports(db, user.id)
    assert len(exports) == 2


async def test_get_export(db):
    from src.models.user import User
    user = User(email="get@example.com", hashed_password="x", name="Get")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    export = await create_export(
        db, "Get Test", "pdf", "contributors", "daily", [], None, user.id,
    )
    fetched = await get_export(db, export.id, user.id)
    assert fetched is not None
    assert fetched.name == "Get Test"


async def test_update_export(db):
    from src.models.user import User
    user = User(email="upd@example.com", hashed_password="x", name="Upd")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    export = await create_export(
        db, "Update Me", "pdf", "teams", "daily", [], None, user.id,
    )
    updated = await update_export(db, export, name="Updated", schedule="weekly")
    assert updated.name == "Updated"
    assert updated.schedule == "weekly"


async def test_delete_export(db):
    from src.models.user import User
    user = User(email="del@example.com", hashed_password="x", name="Del")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    export = await create_export(
        db, "Delete Me", "csv", "trends", "daily", [], None, user.id,
    )
    await delete_export(db, export)
    result = await get_export(db, export.id, user.id)
    assert result is None


async def test_due_exports(db):
    from src.models.user import User
    user = User(email="due@example.com", hashed_password="x", name="Due")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Export due in the past
    export = ScheduledExport(
        name="Overdue",
        export_type="pdf",
        data_source="contributors",
        schedule="daily",
        recipients=[],
        config={},
        is_active=True,
        next_run_at=datetime.now(timezone.utc) - timedelta(hours=1),
        created_by=user.id,
    )
    db.add(export)

    # Export due in the future
    future = ScheduledExport(
        name="Future",
        export_type="csv",
        data_source="teams",
        schedule="weekly",
        recipients=[],
        config={},
        is_active=True,
        next_run_at=datetime.now(timezone.utc) + timedelta(days=5),
        created_by=user.id,
    )
    db.add(future)

    # Inactive export due in the past
    inactive = ScheduledExport(
        name="Inactive",
        export_type="pdf",
        data_source="trends",
        schedule="daily",
        recipients=[],
        config={},
        is_active=False,
        next_run_at=datetime.now(timezone.utc) - timedelta(hours=2),
        created_by=user.id,
    )
    db.add(inactive)
    await db.commit()

    due = await get_due_exports(db)
    names = [e.name for e in due]
    assert "Overdue" in names
    assert "Future" not in names
    assert "Inactive" not in names


# --- API endpoint tests ---

async def test_export_schedule_crud_api(auth_client):
    # Create
    resp = await auth_client.post("/api/v1/exports/schedule", json={
        "name": "Weekly PDF",
        "export_type": "pdf",
        "data_source": "contributors",
        "schedule": "weekly",
        "recipients": ["test@example.com"],
    })
    assert resp.status_code == 201
    data = resp.json()
    export_id = data["id"]
    assert data["name"] == "Weekly PDF"
    assert data["export_type"] == "pdf"
    assert data["is_active"] is True

    # List
    resp = await auth_client.get("/api/v1/exports/schedules")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Get
    resp = await auth_client.get(f"/api/v1/exports/schedules/{export_id}")
    assert resp.status_code == 200

    # Update
    resp = await auth_client.put(f"/api/v1/exports/schedules/{export_id}", json={
        "name": "Updated Export",
        "schedule": "monthly",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Export"
    assert resp.json()["schedule"] == "monthly"

    # Delete
    resp = await auth_client.delete(f"/api/v1/exports/schedules/{export_id}")
    assert resp.status_code == 204


async def test_export_schedule_validation(auth_client):
    # Invalid schedule
    resp = await auth_client.post("/api/v1/exports/schedule", json={
        "name": "Bad", "export_type": "pdf", "data_source": "contributors",
        "schedule": "hourly",
    })
    assert resp.status_code == 400

    # Invalid export type
    resp = await auth_client.post("/api/v1/exports/schedule", json={
        "name": "Bad", "export_type": "xlsx", "data_source": "contributors",
        "schedule": "daily",
    })
    assert resp.status_code == 400

    # Invalid data source
    resp = await auth_client.post("/api/v1/exports/schedule", json={
        "name": "Bad", "export_type": "pdf", "data_source": "invalid",
        "schedule": "daily",
    })
    assert resp.status_code == 400


async def test_export_schedule_not_found(auth_client):
    resp = await auth_client.get("/api/v1/exports/schedules/nonexistent")
    assert resp.status_code == 404

    resp = await auth_client.delete("/api/v1/exports/schedules/nonexistent")
    assert resp.status_code == 404

    resp = await auth_client.post("/api/v1/exports/schedules/nonexistent/run")
    assert resp.status_code == 404
