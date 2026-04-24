from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.chat_session import ChatSession
from app.models.message import Message
from app.schemas.message import MessageResponse
from app.schemas.session import ChatSessionResponse

router_sessions = APIRouter()


@router_sessions.post("/sessions")
async def create_session(session: AsyncSession = Depends(get_session)):
    chat_session = ChatSession()

    session.add(chat_session)
    await session.commit()

    return {"session_id": chat_session.id}


@router_sessions.get("/sessions")
async def get_all_sessions(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ChatSession))
    chat_sessions = result.scalars().all()

    return [ChatSessionResponse.model_validate(cs) for cs in chat_sessions]


@router_sessions.get("/sessions/{session_id}/messages")
async def get_all_messages_session(
    session_id: int, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    return [MessageResponse.model_validate(m) for m in messages]


@router_sessions.delete("/sessions/{session_id}")
async def delete_session(session_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    chat_session = result.scalar_one_or_none()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    await session.delete(chat_session)
    await session.commit()
