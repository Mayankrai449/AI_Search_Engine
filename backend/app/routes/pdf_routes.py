from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends
from utils.text_utils import extract_and_clean_text, split_text_into_chunks
from models.faiss_manager import load_chatwindow_data, save_embeddings, delete_document, delete_chatwindow
from models.db_manager import create_document, create_text_chunks, get_documents_by_chatwindow, delete_document as db_delete_document, delete_chatwindow as db_delete_chatwindow
from models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
import asyncio
import os
import uuid

router = APIRouter()

@router.post("/select-chatwindow")
async def select_chatwindow(request: Request, chatwindow_uuid: str, db: AsyncSession = Depends(get_db)):
    index, chunk_ids = await load_chatwindow_data(db, chatwindow_uuid)
    request.app.state.current_chatwindow = chatwindow_uuid
    request.app.state.index = index
    request.app.state.chunk_ids = chunk_ids
    print("Index size:", request.app.state.index.ntotal)

    documents = await get_documents_by_chatwindow(db, chatwindow_uuid)
    return {"chatwindow_uuid": chatwindow_uuid, "documents": [{"uuid": doc.id, "name": doc.name} for doc in documents]}

@router.post("/upload")
async def upload_pdf(request: Request, chatwindow_uuid: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        doc_uuid = str(uuid.uuid4())
        pdf_path = f"temp/{doc_uuid}.pdf"
        os.makedirs("temp", exist_ok=True)
        with open(pdf_path, 'wb') as f:
            f.write(await file.read())

        text = await extract_and_clean_text(pdf_path)
        os.remove(pdf_path)

        chunks = split_text_into_chunks(text, max_words=400, overlap_words=100)

        model = request.app.state.model
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: model.encode(chunks, normalize_embeddings=False)
        )
        embeddings_np = np.array(embeddings, dtype='float32')

        embedding_path = save_embeddings(chatwindow_uuid, doc_uuid, file.filename, embeddings_np)

        document = await create_document(db, chatwindow_uuid, file.filename, embedding_path)
        await create_text_chunks(db, document.id, chunks)

        request.app.state.current_chatwindow = chatwindow_uuid
        request.app.state.index, request.app.state.chunk_ids = await load_chatwindow_data(db, chatwindow_uuid)
        print(f"Selected new chatwindow: {chatwindow_uuid}")
        print("Index size:", request.app.state.index.ntotal)

        return {"status": "success", "doc_uuid": doc_uuid, "chunks_added": len(chunks)}

    except Exception as e:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

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