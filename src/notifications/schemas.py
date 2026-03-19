from datetime import datetime
from pydantic import BaseModel


class NotificationCreate(BaseModel):
    type: str
    title: str
    message: str
    data: dict | None = None
    user_id: str | None = None  # None = broadcast


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    data: dict | None = None
    read: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int
