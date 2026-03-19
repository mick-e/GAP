from datetime import date, datetime, timedelta

from src.models.snapshot import Snapshot
from src.trends.predictions import linear_regression, moving_average
from src.trends.service import TrendService


# --- Unit tests for prediction functions ---

async def test_linear_regression_insufficient_data():
    result = linear_regression([])
    assert result["trend"] == "insufficient_data"
    assert result["predictions"] == []

    result = linear_regression([(datetime(2026, 1, 1), 5.0)])
    assert result["trend"] == "insufficient_data"


async def test_linear_regression_increasing():
    base = datetime(2026, 1, 1)
    data = [(base + timedelta(days=i), float(i * 10)) for i in range(30)]
    result = linear_regression(data)
    assert result["trend"] == "increasing"
    assert result["slope"] > 0
    assert len(result["predictions"]) == 3
    assert result["confidence"] == 1.0
    # Predictions should be for 7, 14, 30 days ahead
    assert result["predictions"][0]["days_ahead"] == 7
    assert result["predictions"][1]["days_ahead"] == 14
    assert result["predictions"][2]["days_ahead"] == 30
    # Values should be increasing
    assert result["predictions"][2]["value"] > result["predictions"][0]["value"]


async def test_linear_regression_decreasing():
    base = datetime(2026, 1, 1)
    data = [(base + timedelta(days=i), float(100 - i * 3)) for i in range(20)]
    result = linear_regression(data)
    assert result["trend"] == "decreasing"
    assert result["slope"] < 0


async def test_linear_regression_stable():
    base = datetime(2026, 1, 1)
    data = [(base + timedelta(days=i), 50.0) for i in range(10)]
    result = linear_regression(data)
    assert result["trend"] in ("stable", "flat")


async def test_linear_regression_no_negative_predictions():
    base = datetime(2026, 1, 1)
    # Steeply decreasing data that would predict negatives
    data = [(base + timedelta(days=i), max(0, float(10 - i * 5))) for i in range(5)]
    result = linear_regression(data)
    for pred in result["predictions"]:
        assert pred["value"] >= 0


async def test_linear_regression_confidence_scales():
    base = datetime(2026, 1, 1)
    # 10 points = 10/30 confidence
    data = [(base + timedelta(days=i), float(i)) for i in range(10)]
    result = linear_regression(data)
    assert abs(result["confidence"] - 10 / 30) < 0.01

    # 30 points = 1.0 confidence
    data = [(base + timedelta(days=i), float(i)) for i in range(30)]
    result = linear_regression(data)
    assert result["confidence"] == 1.0


async def test_moving_average_basic():
    base = datetime(2026, 1, 1)
    data = [(base + timedelta(days=i), float(i + 1)) for i in range(10)]
    result = moving_average(data, window=3)
    assert len(result) == 8  # 10 - 3 + 1
    # First MA point: average of 1, 2, 3 = 2.0
    assert result[0]["value"] == 2.0
    assert result[0]["raw_value"] == 3.0


async def test_moving_average_insufficient_data():
    base = datetime(2026, 1, 1)
    data = [(base + timedelta(days=i), float(i)) for i in range(3)]
    result = moving_average(data, window=5)
    assert result == []


async def test_moving_average_smoothing():
    base = datetime(2026, 1, 1)
    # Noisy data
    raw = [10, 20, 10, 20, 10, 20, 10, 20, 10, 20]
    data = [(base + timedelta(days=i), float(v)) for i, v in enumerate(raw)]
    result = moving_average(data, window=4)
    # MA should be more stable than raw
    ma_values = [r["value"] for r in result]
    raw_range = max(raw) - min(raw)
    ma_range = max(ma_values) - min(ma_values)
    assert ma_range < raw_range


# --- Integration tests with service ---

async def test_prediction_endpoint_with_data(db):
    today = date.today()
    for i in range(30):
        db.add(Snapshot(
            snapshot_date=today - timedelta(days=29 - i),
            snapshot_type="daily",
            commit_count=10 + i,
        ))
    await db.commit()

    service = TrendService(db)
    prediction = await service.get_metric_predictions("commit_count", days=90)
    assert prediction.metric == "commit_count"
    assert prediction.trend == "increasing"
    assert len(prediction.predictions) == 3
    assert len(prediction.historical) == 30


async def test_prediction_endpoint_empty(db):
    service = TrendService(db)
    prediction = await service.get_metric_predictions("commit_count", days=90)
    assert prediction.trend == "insufficient_data"
    assert prediction.predictions == []


async def test_moving_average_endpoint(db):
    today = date.today()
    for i in range(14):
        db.add(Snapshot(
            snapshot_date=today - timedelta(days=13 - i),
            snapshot_type="daily",
            commit_count=5 + (i % 3),
        ))
    await db.commit()

    service = TrendService(db)
    ma = await service.get_metric_moving_average("commit_count", days=30, window=3)
    assert len(ma) == 12  # 14 - 3 + 1
    for point in ma:
        assert point.value >= 0
        assert point.raw_value >= 0


async def test_prediction_api(auth_client):
    # Create some data first
    from src.database import get_db
    from src.main import app

    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()
    today = date.today()
    for i in range(10):
        db.add(Snapshot(
            snapshot_date=today - timedelta(days=9 - i),
            snapshot_type="daily",
            commit_count=10 + i * 2,
        ))
    await db.commit()

    resp = await auth_client.get("/api/v1/trends/predictions/commit_count?days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metric"] == "commit_count"
    assert "trend" in data
    assert "predictions" in data


async def test_moving_average_api(auth_client):
    from src.database import get_db
    from src.main import app

    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()
    today = date.today()
    for i in range(10):
        db.add(Snapshot(
            snapshot_date=today - timedelta(days=9 - i),
            snapshot_type="daily",
            commit_count=5,
        ))
    await db.commit()

    resp = await auth_client.get(
        "/api/v1/trends/moving-average/commit_count?days=30&window=3"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
