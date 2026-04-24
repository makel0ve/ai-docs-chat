import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.pipeline.rag import rag_answer
from app.schemas.chat import ChatRequest

router_chat = APIRouter()


async def format_sse(generator):
    async for answer in generator:
        if isinstance(answer, str):
            yield f"data: {json.dumps({'token': answer}, ensure_ascii=False)}\n\n"

        if isinstance(answer, dict):
            yield f"data: {json.dumps(answer, ensure_ascii=False)}\n\n"


@router_chat.post("/chat")
async def answer_chat(
    chat_request: ChatRequest, session: AsyncSession = Depends(get_session)
):
    return StreamingResponse(
        format_sse(
            rag_answer(
                question=chat_request.question,
                session_id=chat_request.session_id,
                provider=chat_request.provider,
                session=session,
            )
        ),
        media_type="text/event-stream",
    )
