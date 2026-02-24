

async def test_create_schedule(auth_client):
    resp = await auth_client.post("/api/v1/schedules", json={
        "name": "Weekly Activity",
        "report_type": "activity",
        "schedule": "weekly",
        "recipients": ["test@example.com"],
        "config": {"period": "week"},
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Weekly Activity"
    assert data["schedule"] == "weekly"
    assert data["is_active"] is True


async def test_create_schedule_invalid_type(auth_client):
    resp = await auth_client.post("/api/v1/schedules", json={
        "name": "Bad", "report_type": "invalid", "schedule": "daily"
    })
    assert resp.status_code == 400


async def test_create_schedule_invalid_schedule(auth_client):
    resp = await auth_client.post("/api/v1/schedules", json={
        "name": "Bad", "report_type": "activity", "schedule": "hourly"
    })
    assert resp.status_code == 400


async def test_list_schedules(auth_client):
    await auth_client.post("/api/v1/schedules", json={
        "name": "Job 1", "report_type": "activity", "schedule": "daily"
    })
    await auth_client.post("/api/v1/schedules", json={
        "name": "Job 2", "report_type": "quality", "schedule": "weekly"
    })

    resp = await auth_client.get("/api/v1/schedules")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_get_schedule(auth_client):
    resp = await auth_client.post("/api/v1/schedules", json={
        "name": "Get Me", "report_type": "activity", "schedule": "daily"
    })
    job_id = resp.json()["id"]

    resp = await auth_client.get(f"/api/v1/schedules/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me"


async def test_update_schedule(auth_client):
    resp = await auth_client.post("/api/v1/schedules", json={
        "name": "Update Me", "report_type": "activity", "schedule": "daily"
    })
    job_id = resp.json()["id"]

    resp = await auth_client.put(f"/api/v1/schedules/{job_id}", json={
        "name": "Updated", "schedule": "weekly"
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["schedule"] == "weekly"


async def test_delete_schedule(auth_client):
    resp = await auth_client.post("/api/v1/schedules", json={
        "name": "Delete Me", "report_type": "releases", "schedule": "monthly"
    })
    job_id = resp.json()["id"]

    resp = await auth_client.delete(f"/api/v1/schedules/{job_id}")
    assert resp.status_code == 204

    resp = await auth_client.get(f"/api/v1/schedules/{job_id}")
    assert resp.status_code == 404
