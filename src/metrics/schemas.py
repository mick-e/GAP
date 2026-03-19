from pydantic import BaseModel


class CustomMetricCreate(BaseModel):
    name: str
    description: str | None = None
    formula: str
    is_public: bool = False


class CustomMetricUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    formula: str | None = None
    is_public: bool | None = None


class CustomMetricResponse(BaseModel):
    id: str
    name: str
    description: str | None
    formula: str
    is_public: bool
    created_by: str
    created_at: str


class CustomMetricEvaluation(BaseModel):
    metric_id: str
    metric_name: str
    formula: str
    result: float
    variables: dict[str, float]


class VariableInfo(BaseModel):
    name: str
    description: str
