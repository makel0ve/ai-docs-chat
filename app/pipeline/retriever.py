import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import redis_client
from app.llm.factory import get_embedding_provider
from app.models.chunk import Chunk


async def search(query: str, session: AsyncSession, top_k: int = 5) -> list[Chunk]:
    query_hash = hashlib.sha256(query.encode()).hexdigest()

    query_embedding_hash = await redis_client.get(f"emb: {query_hash}")
    if query_embedding_hash:
        query_embedding = json.loads(query_embedding_hash)

    else:
        query_embedding = (await get_embedding_provider().embed([query]))[0]
        await redis_client.set(
            f"emb: {query_hash}",
            json.dumps(query_embedding, ensure_ascii=False),
            ex=604800,
        )

    stmt = (
        select(Chunk)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )

    result = await session.execute(stmt)
    chunks = result.scalars().all()

    return chunks
