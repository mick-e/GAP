from datetime import datetime, timedelta


def linear_regression(data_points: list[tuple[datetime, float]]) -> dict:
    """Simple linear regression on time series data.
    Returns slope, intercept, and predictions for next 7/14/30 days."""
    if len(data_points) < 2:
        return {"trend": "insufficient_data", "predictions": []}

    # Convert datetimes to numeric (days from first point)
    t0 = data_points[0][0]
    xs = [(p[0] - t0).total_seconds() / 86400 for p in data_points]
    ys = [p[1] for p in data_points]

    n = len(xs)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_x2 = sum(x * x for x in xs)

    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return {"trend": "flat", "slope": 0, "predictions": []}

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    # Determine trend
    if abs(slope) < 0.01:
        trend = "stable"
    elif slope > 0:
        trend = "increasing"
    else:
        trend = "decreasing"

    # Generate predictions
    last_x = xs[-1]
    predictions = []
    for days_ahead in [7, 14, 30]:
        pred_x = last_x + days_ahead
        pred_y = max(0, slope * pred_x + intercept)  # Don't predict negative
        pred_date = data_points[-1][0] + timedelta(days=days_ahead)
        predictions.append({
            "date": pred_date.isoformat(),
            "value": round(pred_y, 2),
            "days_ahead": days_ahead,
        })

    return {
        "trend": trend,
        "slope": round(slope, 4),
        "predictions": predictions,
        "confidence": min(1.0, len(data_points) / 30),
    }


def moving_average(
    data_points: list[tuple[datetime, float]], window: int = 7
) -> list[dict]:
    """Calculate moving average for smoothing."""
    if len(data_points) < window:
        return []

    result = []
    for i in range(window - 1, len(data_points)):
        window_values = [p[1] for p in data_points[i - window + 1:i + 1]]
        avg = sum(window_values) / len(window_values)
        result.append({
            "date": data_points[i][0].isoformat(),
            "value": round(avg, 2),
            "raw_value": data_points[i][1],
        })
    return result
