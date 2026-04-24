from app.pipeline.indexer import index_document
from worker.broker import broker


@broker.task
async def index_document_task(document_id: int) -> None:
    await index_document(document_id)
