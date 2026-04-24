from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatSessionResponse(BaseModel):
    id: int
    created_at: datetime
    title: str | None

    model_config = ConfigDict(from_attributes=True)
