from datetime import date, timedelta

from src.metrics.engine import (
    validate_formula, evaluate_formula, tokenize, FormulaError, ALLOWED_VARIABLES,
)
from src.metrics.service import create_metric, list_metrics, get_metric, delete_metric
from src.models.snapshot import Snapshot


# --- Formula engine unit tests ---

async def test_tokenize_simple():
    tokens = tokenize("commits + prs")
    assert tokens == ["commits", "+", "prs"]


async def test_tokenize_complex():
    tokens = tokenize("deploy_frequency * (1 - cfr)")
    assert tokens == ["deploy_frequency", "*", "(", "1", "-", "cfr", ")"]


async def test_tokenize_numbers():
    tokens = tokenize("commits / 100.5")
    assert tokens == ["commits", "/", "100.5"]


async def test_validate_formula_valid():
    assert validate_formula("commits + prs") is True
    assert validate_formula("deploy_frequency * (1 - cfr)") is True
    assert validate_formula("commits / 100") is True
    assert validate_formula("(commits + prs) * 2.5") is True
    assert validate_formula("stars + forks") is True


async def test_validate_formula_invalid():
    assert validate_formula("__import__('os')") is False
    assert validate_formula("exec('code')") is False
    assert validate_formula("commits; rm -rf /") is False
    assert validate_formula("invalid_var + 1") is False
    assert validate_formula("") is False  # Empty formula


async def test_evaluate_simple():
    result = evaluate_formula("commits + prs", {"commits": 100, "prs": 50})
    assert result == 150.0


async def test_evaluate_complex():
    result = evaluate_formula(
        "deploy_frequency * (1 - cfr)",
        {"deploy_frequency": 5.0, "cfr": 0.1},
    )
    assert abs(result - 4.5) < 0.001


async def test_evaluate_division():
    result = evaluate_formula("commits / prs", {"commits": 100, "prs": 20})
    assert result == 5.0


async def test_evaluate_division_by_zero():
    result = evaluate_formula("commits / prs", {"commits": 100, "prs": 0})
    assert result == 0.0  # Safe division by zero


async def test_evaluate_nested_parens():
    result = evaluate_formula(
        "((commits + prs) * 2) / 10",
        {"commits": 30, "prs": 20},
    )
    assert result == 10.0


async def test_evaluate_order_of_operations():
    result = evaluate_formula(
        "commits + prs * 2",
        {"commits": 10, "prs": 5},
    )
    assert result == 20.0  # Not 30


async def test_evaluate_missing_variable():
    try:
        evaluate_formula("commits + unknown_var", {"commits": 10})
        assert False, "Should have raised FormulaError"
    except FormulaError:
        pass


async def test_no_code_injection():
    """Ensure no code injection is possible."""
    assert validate_formula("__import__('os').system('ls')") is False
    assert validate_formula("eval('1+1')") is False
    assert validate_formula("lambda: 1") is False


# --- Service integration tests ---

async def test_create_metric(db):
    from src.models.user import User
    user = User(email="test@example.com", hashed_password="x", name="Test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    metric = await create_metric(
        db, name="Velocity", formula="commits + prs",
        user_id=user.id, description="Team velocity",
    )
    assert metric.name == "Velocity"
    assert metric.formula == "commits + prs"
    assert metric.created_by == user.id


async def test_create_metric_invalid_formula(db):
    from src.models.user import User
    user = User(email="test2@example.com", hashed_password="x", name="Test")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    try:
        await create_metric(
            db, name="Bad", formula="exec('rm -rf /')", user_id=user.id,
        )
        assert False, "Should have raised FormulaError"
    except FormulaError:
        pass


async def test_list_metrics_own_and_public(db):
    from src.models.user import User
    user1 = User(email="u1@example.com", hashed_password="x", name="U1")
    user2 = User(email="u2@example.com", hashed_password="x", name="U2")
    db.add(user1)
    db.add(user2)
    await db.commit()
    await db.refresh(user1)
    await db.refresh(user2)

    await create_metric(db, "Private1", "commits", user1.id)
    await create_metric(db, "Public1", "prs", user2.id, is_public=True)
    await create_metric(db, "Private2", "issues", user2.id)

    # User1 should see own (Private1) + public (Public1)
    metrics = await list_metrics(db, user1.id)
    names = [m.name for m in metrics]
    assert "Private1" in names
    assert "Public1" in names
    assert "Private2" not in names


async def test_delete_metric(db):
    from src.models.user import User
    user = User(email="del@example.com", hashed_password="x", name="Del")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    metric = await create_metric(db, "ToDelete", "commits", user.id)
    await delete_metric(db, metric)
    result = await get_metric(db, metric.id, user.id)
    assert result is None


# --- API endpoint tests ---

async def test_metrics_crud_api(auth_client):
    # Create
    resp = await auth_client.post("/api/v1/metrics/custom", json={
        "name": "Velocity",
        "formula": "commits + prs",
        "description": "Team velocity score",
    })
    assert resp.status_code == 201
    data = resp.json()
    metric_id = data["id"]
    assert data["name"] == "Velocity"
    assert data["formula"] == "commits + prs"

    # List
    resp = await auth_client.get("/api/v1/metrics/custom")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Get
    resp = await auth_client.get(f"/api/v1/metrics/custom/{metric_id}")
    assert resp.status_code == 200

    # Update
    resp = await auth_client.put(f"/api/v1/metrics/custom/{metric_id}", json={
        "name": "Velocity v2",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Velocity v2"

    # Delete
    resp = await auth_client.delete(f"/api/v1/metrics/custom/{metric_id}")
    assert resp.status_code == 204


async def test_metrics_invalid_formula_api(auth_client):
    resp = await auth_client.post("/api/v1/metrics/custom", json={
        "name": "Bad",
        "formula": "exec('bad')",
    })
    assert resp.status_code == 400


async def test_metrics_variables_api(auth_client):
    resp = await auth_client.get("/api/v1/metrics/variables")
    assert resp.status_code == 200
    data = resp.json()
    names = [v["name"] for v in data]
    assert "commits" in names
    assert "prs" in names
    assert "deploy_frequency" in names


async def test_metrics_evaluate_api(auth_client):
    # Create metric
    resp = await auth_client.post("/api/v1/metrics/custom", json={
        "name": "Simple",
        "formula": "commits + prs",
    })
    metric_id = resp.json()["id"]

    # Add some snapshot data
    from src.database import get_db
    from src.main import app
    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()
    today = date.today()
    db.add(Snapshot(
        snapshot_date=today, snapshot_type="daily",
        commit_count=50, pr_count=20,
    ))
    await db.commit()

    resp = await auth_client.post(f"/api/v1/metrics/custom/{metric_id}/evaluate?days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == 70.0


async def test_metrics_not_found(auth_client):
    resp = await auth_client.get("/api/v1/metrics/custom/nonexistent")
    assert resp.status_code == 404
