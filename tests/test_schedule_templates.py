

async def test_list_templates(auth_client):
    resp = await auth_client.get("/api/v1/schedules/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    ids = {t["id"] for t in data}
    assert "daily_standup" in ids
    assert "weekly_digest" in ids
    assert "monthly_quality" in ids
    assert "release_tracker" in ids
    assert "security_weekly" in ids


async def test_get_template_by_id(auth_client):
    resp = await auth_client.get("/api/v1/schedules/templates/daily_standup")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "daily_standup"
    assert data["name"] == "Daily Standup Report"
    assert data["report_type"] == "activity"
    assert data["schedule"] == "daily"
    assert "config" in data


async def test_get_template_not_found(auth_client):
    resp = await auth_client.get("/api/v1/schedules/templates/nonexistent")
    assert resp.status_code == 404


async def test_create_schedule_from_template(auth_client):
    resp = await auth_client.post("/api/v1/schedules/from-template", json={
        "template_id": "weekly_digest",
        "recipients": ["team@example.com"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Weekly Team Digest"
    assert data["report_type"] == "activity"
    assert data["schedule"] == "weekly"
    assert data["recipients"] == ["team@example.com"]
    assert data["is_active"] is True


async def test_create_schedule_from_template_with_name_override(auth_client):
    resp = await auth_client.post("/api/v1/schedules/from-template", json={
        "template_id": "monthly_quality",
        "recipients": ["qa@example.com"],
        "name": "Custom Quality Check",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Custom Quality Check"
    assert data["report_type"] == "quality"
    assert data["schedule"] == "monthly"


async def test_create_schedule_from_invalid_template(auth_client):
    resp = await auth_client.post("/api/v1/schedules/from-template", json={
        "template_id": "nonexistent",
        "recipients": [],
    })
    assert resp.status_code == 404


async def test_template_has_correct_config(auth_client):
    resp = await auth_client.get("/api/v1/schedules/templates/security_weekly")
    assert resp.status_code == 200
    data = resp.json()
    assert data["config"]["include_security"] is True
    assert data["config"]["security_only"] is True
    assert data["config"]["period_days"] == 7
