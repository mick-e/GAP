from pydantic import BaseModel


class WebhookEventResponse(BaseModel):
    id: str
    event_type: str
    action: str | None
    repo_name: str | None
    sender: str | None
    processed: bool
    error: str | None
    created_at: str


class WebhookEventDetail(WebhookEventResponse):
    payload: dict


class WebhookReplayResult(BaseModel):
    event_id: str
    success: bool
    error: str | None = None


class WebhookBatchReplayRequest(BaseModel):
    event_ids: list[str]


class WebhookBatchReplayResult(BaseModel):
    total: int
    successful: int
    failed: int
    results: list[WebhookReplayResult]
