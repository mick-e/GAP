from pydantic import BaseModel


class TrendData(BaseModel):
    date: str
    value: float
    label: str | None = None


class TrendComparison(BaseModel):
    metric: str
    current_value: float
    previous_value: float
    change: float
    change_percent: float
    direction: str  # "up", "down", "flat"


class TrendOverview(BaseModel):
    period: str
    velocity: TrendComparison
    quality: TrendComparison
    engagement: TrendComparison


class Sparkline(BaseModel):
    metric: str
    data: list[float]
    labels: list[str]
    current: float
    change_percent: float
