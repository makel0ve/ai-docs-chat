from pgvector.sqlalchemy import VECTOR
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )
    content: Mapped[str]
    chunk_index: Mapped[int]
    embedding: Mapped[list[float]] = mapped_column(VECTOR(1024))
