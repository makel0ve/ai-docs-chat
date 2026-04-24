from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers.chat import router_chat
from app.routers.documents import router_documents
from app.routers.sessions import router_sessions
from worker.broker import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not broker.is_worker_process:
        await broker.startup()
    yield
    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(router_documents)
app.include_router(router_sessions)
app.include_router(router_chat)
