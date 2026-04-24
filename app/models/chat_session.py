from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("TIMEZONE('utc', now())")
    )
    messages: Mapped[list["Message"]] = relationship(
        cascade="all, delete-orphan", back_populates="session"
    )  # type: ignore
    title: Mapped[str | None] = mapped_column(default=None)
