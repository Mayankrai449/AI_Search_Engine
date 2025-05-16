from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from models.db_manager import (
    delete_document as db_delete_document,
    delete_chatwindow as db_delete_chatwindow,
    get_all_chatwindows,
    create_chatwindow,
    update_chatwindow_title,
    get_documents_by_chatwindow,
)
from models.faiss_manager import load_chatwindow_data, init_faiss
from models.database import get_db
from schemas.query_schema import TitleUpdateRequest
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/chatwindows")
async def get_all_chat(db: AsyncSession = Depends(get_db)):
    logger.info("Fetching all chatwindows")
    chatwindows = await get_all_chatwindows(db)
    return [{"id": cw.id, "title": cw.title} for cw in chatwindows]

@router.post("/select-chatwindow")
async def select_chatwindow(request: Request, chatwindow_uuid: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"Selecting chatwindow: {chatwindow_uuid}")
    index, all_ids = await load_chatwindow_data(db, chatwindow_uuid)
    request.app.state.current_chatwindow = chatwindow_uuid
    request.app.state.index = index
    request.app.state.all_ids = all_ids
    logger.info(f"Updated state: chatwindow={chatwindow_uuid}, index_size={index.ntotal}, all_ids_count={len(all_ids)}")

    documents = await get_documents_by_chatwindow(db, chatwindow_uuid)
    logger.info(f"Found {len(documents)} documents for chatwindow: {chatwindow_uuid}")
    return {
        "chatwindow_uuid": chatwindow_uuid,
        "documents": [{"uuid": doc.id, "name": doc.name} for doc in documents]
    }

@router.post("/create-chatwindow")
async def create_chat(db: AsyncSession = Depends(get_db)):
    logger.info("Creating new chatwindow")
    new_chatwindow = await create_chatwindow(db, title="New ChatWindow")
    logger.info(f"Created chatwindow: {new_chatwindow.id}")
    return {"chatwindow_uuid": new_chatwindow.id}

@router.patch("/chatwindows/{chatwindow_uuid}/update-title")
async def update_title(chatwindow_uuid: str, request: TitleUpdateRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"Updating title for chatwindow: {chatwindow_uuid}")
    updated_chatwindow = await update_chatwindow_title(db, chatwindow_uuid, request.title)
    if not updated_chatwindow:
        logger.error(f"Chatwindow not found: {chatwindow_uuid}")
        raise HTTPException(status_code=404, detail="ChatWindow not found")
    logger.info(f"Updated title for chatwindow: {chatwindow_uuid}, new title: {request.title}")
    return {"message": "Title updated successfully", "chatwindow_uuid": chatwindow_uuid, "title": request.title}

@router.delete("/delete-doc")
async def delete_pdf(request: Request, chatwindow_uuid: str, doc_uuid: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting document {doc_uuid} from chatwindow: {chatwindow_uuid}")
    success = await db_delete_document(db, chatwindow_uuid, doc_uuid)
    if not success:
        logger.error(f"Document not found: {doc_uuid}")
        raise HTTPException(status_code=404, detail="Document not found")

    from models.faiss_manager import delete_document
    delete_document(chatwindow_uuid, doc_uuid)
    logger.info(f"Deleted embedding files for document: {doc_uuid}")

    if getattr(request.app.state, "current_chatwindow", None) == chatwindow_uuid:
        logger.info(f"Reloading data for current chatwindow: {chatwindow_uuid}")
        index, all_ids = await load_chatwindow_data(db, chatwindow_uuid)
        request.app.state.index = index
        request.app.state.all_ids = all_ids
        logger.info(f"Updated state after deletion: index_size={index.ntotal}, all_ids_count={len(all_ids)}")

    return {"status": "deleted", "doc_uuid": doc_uuid}

@router.delete("/delete-chatwindow")
async def delete_chatwindow_route(request: Request, chatwindow_uuid: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"Deleting chatwindow: {chatwindow_uuid}")
    success = await db_delete_chatwindow(db, chatwindow_uuid)
    if not success:
        logger.error(f"Chatwindow not found: {chatwindow_uuid}")
        raise HTTPException(status_code=404, detail="ChatWindow not found")

    from models.faiss_manager import delete_chatwindow
    delete_chatwindow(chatwindow_uuid)
    logger.info(f"Deleted embedding files for chatwindow: {chatwindow_uuid}")

    if getattr(request.app.state, "current_chatwindow", None) == chatwindow_uuid:
        logger.info(f"Clearing state for deleted chatwindow: {chatwindow_uuid}")
        request.app.state.index = init_faiss(dimension=1152)
        request.app.state.all_ids = []
        request.app.state.current_chatwindow = None

    return {"status": "chatwindow deleted", "chatwindow_uuid": chatwindow_uuid}