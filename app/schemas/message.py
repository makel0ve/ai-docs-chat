from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
