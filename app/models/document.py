from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_filename: Mapped[str]
    filename: Mapped[str]
    status: Mapped[Literal["processing", "ready", "failed"]] = mapped_column(
        default="processing"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("TIMEZONE('utc', now())")
    )
