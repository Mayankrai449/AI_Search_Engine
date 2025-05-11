from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.db_manager import delete_document as db_delete_document, delete_chatwindow as db_delete_chatwindow
from models.db_manager import *
from models.faiss_manager import load_chatwindow_data
from models.database import get_db
from schemas.query_schema import TitleUpdateRequest
from fastapi import Request

router = APIRouter()

@router.get("/chatwindows")
async def get_all_chat(db: AsyncSession = Depends(get_db)):
    chatwindows = await get_all_chatwindows(db)
    return [{"id": cw.id, "title": cw.title} for cw in chatwindows]


@router.post("/select-chatwindow")
async def select_chatwindow(request: Request, chatwindow_uuid: str, db: AsyncSession = Depends(get_db)):
    index, chunk_ids = await load_chatwindow_data(db, chatwindow_uuid)
    request.app.state.current_chatwindow = chatwindow_uuid
    request.app.state.index = index
    request.app.state.chunk_ids = chunk_ids
    print("Index size:", request.app.state.index.ntotal)

    documents = await get_documents_by_chatwindow(db, chatwindow_uuid)
    return {"chatwindow_uuid": chatwindow_uuid, "documents": [{"uuid": doc.id, "name": doc.name} for doc in documents]}


@router.post("/create-chatwindow")
async def create_chat(db: AsyncSession = Depends(get_db)):
    new_chatwindow = await create_chatwindow(db, title="New ChatWindow")
    return {"chatwindow_uuid": new_chatwindow.id}


@router.patch("/chatwindows/{chatwindow_uuid}/update-title")
async def update_title(chatwindow_uuid: str, request: TitleUpdateRequest, db: AsyncSession = Depends(get_db)):
    updated_chatwindow = await update_chatwindow_title(db, chatwindow_uuid, request.title)
    if not updated_chatwindow:
        raise HTTPException(status_code=404, detail="ChatWindow not found")
    return {"message": "Title updated successfully", "chatwindow_uuid": chatwindow_uuid, "title": request.title}


@router.delete("/delete-doc")
async def delete_pdf(request: Request, chatwindow_uuid: str, doc_uuid: str, db: AsyncSession = Depends(get_db)):
    success = await db_delete_document(db, chatwindow_uuid, doc_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document(chatwindow_uuid, doc_uuid)

    if getattr(request.app.state, "current_chatwindow", None) == chatwindow_uuid:
        request.app.state.index, request.app.state.chunk_ids = await load_chatwindow_data(db, chatwindow_uuid)

    return {"status": "deleted", "doc_uuid": doc_uuid}

@router.delete("/delete-chatwindow")
async def delete_chatwindow_route(request: Request, chatwindow_uuid: str, db: AsyncSession = Depends(get_db)):
    success = await db_delete_chatwindow(db, chatwindow_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="ChatWindow not found")

    delete_chatwindow(chatwindow_uuid)

    if getattr(request.app.state, "current_chatwindow", None) == chatwindow_uuid:
        request.app.state.index = None
        request.app.state.current_chatwindow = None

    return {"status": "chatwindow deleted", "chatwindow_uuid": chatwindow_uuid}