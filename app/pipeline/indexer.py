from sqlalchemy import select

from app.config import get_settings
from app.database import async_session
from app.llm.factory import get_embedding_provider
from app.models.chunk import Chunk
from app.models.document import Document
from app.pipeline.chunker import split_into_chunks
from app.pipeline.parser import extract_text

settings = get_settings()


def _batched(items: list, batch_size: int) -> list[list]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


async def index_document(document_id: int) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one()

        try:
            text = extract_text(f"{settings.upload_dir}/{document.filename}")
            chunks = split_into_chunks(text)

            all_embeddings = []
            for batch in _batched(chunks, settings.batch_size):
                batch_embeddings = await get_embedding_provider().embed(batch)
                all_embeddings.extend(batch_embeddings)

            for index, (chunk_text, embedding) in enumerate(
                zip(chunks, all_embeddings)
            ):
                chunk = Chunk(
                    document_id=document_id,
                    content=chunk_text,
                    chunk_index=index,
                    embedding=embedding,
                )
                session.add(chunk)

            document.status = "ready"
            await session.commit()

        except Exception as e:
            document.status = "failed"
            await session.commit()
            raise ValueError(f"Failed to index document {document_id}: {e}")
