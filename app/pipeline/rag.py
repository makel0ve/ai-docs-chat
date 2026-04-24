import hashlib
import json
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import redis_client
from app.llm.factory import _make_provider
from app.models.chat_session import ChatSession
from app.models.message import Message
from app.pipeline.prompts import build_rag_prompt
from app.pipeline.retriever import search


async def rag_answer(
    question: str, session_id: int, session: AsyncSession, provider: str
) -> AsyncIterator[str]:
    print(f"Using provider: {provider}")

    chat_session = await session.get(ChatSession, session_id)
    if chat_session and chat_session.title is None:
        chat_session.title = question[:50]

    chunks = await search(query=question, session=session)

    chunks_hash = hashlib.sha256(
        f"{question} {sorted([c.id for c in chunks])}".encode()
    ).hexdigest()

    answer_hash = await redis_client.get(f"answer: {chunks_hash}")
    if answer_hash:
        answer_llm = json.loads(answer_hash)
        yield answer_llm

    else:
        prompt = build_rag_prompt(question=question, chunks=chunks)
        answer_llm = ""

        answer_chat = await _make_provider(provider).chat(messages=prompt, stream=True)
        async for answer in answer_chat:
            answer_llm += answer
            yield answer

        await redis_client.set(
            f"answer: {chunks_hash}",
            json.dumps(answer_llm, ensure_ascii=False),
            ex=3600,
        )

    message_user = Message(session_id=session_id, role="user", content=question)

    message_llm = Message(session_id=session_id, role="assistant", content=answer_llm)

    session.add(message_user)
    session.add(message_llm)

    await session.commit()

    chunks_dict = {"chunks": []}
    for chunk in chunks:
        chunks_dict["chunks"].append(
            {
                "content": chunk.content,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
            }
        )

    yield chunks_dict
