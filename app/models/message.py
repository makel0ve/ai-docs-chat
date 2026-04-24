from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE")
    )
    role: Mapped[Literal["user", "assistant"]]
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("TIMEZONE('utc', now())")
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")  # type: ignore
