import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models.document import Document
from app.schemas.document import DocumentResponse
from worker.tasks import index_document_task

router_documents = APIRouter()
settings = get_settings()


@router_documents.post("/documents", status_code=201)
async def upload_documents(
    upload_files: list[UploadFile], session: AsyncSession = Depends(get_session)
):
    documents = []
    for upload_file in upload_files:
        filename = upload_file.filename
        extension = filename.split(".")[-1].lower()

        if extension not in ["pdf", "txt", "docx"]:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: {extension}"
            )

        try:
            filename_uuid = f"{uuid.uuid4()}.{extension}"
            content = await upload_file.read()
            file_path = f"{settings.upload_dir}/{filename_uuid}"

            with open(file_path, "wb") as f:
                f.write(content)

            document = Document(
                original_filename=filename, filename=filename_uuid, status="processing"
            )

            documents.append(document)
            session.add(document)
            await session.flush()

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    await session.commit()

    for d in documents:
        await index_document_task.kiq(document_id=d.id)

    return [DocumentResponse.model_validate(d) for d in documents]


@router_documents.get("/documents")
async def get_all_documents(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Document))
    documents = result.scalars().all()

    return [DocumentResponse.model_validate(d) for d in documents]


@router_documents.get("/documents/{document_id}")
async def get_document(document_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.model_validate(document)


@router_documents.delete("/documents/{document_id}")
async def delete_document(
    document_id: int, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    await session.delete(document)
    await session.commit()

    file_path = f"{settings.upload_dir}/{document.filename}"
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"detail": f"Document {document_id} deleted"}
