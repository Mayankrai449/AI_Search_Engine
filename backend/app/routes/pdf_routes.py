from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends
from utils.text_utils import extract_and_clean_text, split_text_into_chunks
from models.faiss_manager import load_chatwindow_data, save_embeddings
from models.db_manager import create_document, create_text_chunks
from models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
import asyncio
import os
import uuid

router = APIRouter()


@router.post("/upload")
async def upload_pdf(request: Request, chatwindow_uuid: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        doc_uuid = str(uuid.uuid4())
        pdf_path = f"temp/{doc_uuid}.pdf"
        os.makedirs("temp", exist_ok=True)
        with open(pdf_path, 'wb') as f:
            f.write(await file.read())

        page_texts = await extract_and_clean_text(pdf_path)
        print(page_texts)
        os.remove(pdf_path)

        paragraphs_with_pages = []
        for page_num, cleaned_page_text in page_texts:
            paragraphs = cleaned_page_text.split('\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    paragraphs_with_pages.append((page_num, paragraph.strip()))

        chunks_with_pages = split_text_into_chunks(paragraphs_with_pages, max_words=400, overlap_words=100)

        chunks = [chunk for chunk, _ in chunks_with_pages]

        model = request.app.state.sentence_model
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: model.encode(chunks, normalize_embeddings=False)
        )
        embeddings_np = np.array(embeddings, dtype='float32')

        embedding_path = save_embeddings(chatwindow_uuid, file.filename, embeddings_np)
        
        document = await create_document(db, chatwindow_uuid, file.filename, embedding_path)

        await create_text_chunks(db, document.id, chunks_with_pages)

        request.app.state.current_chatwindow = chatwindow_uuid
        request.app.state.index, request.app.state.chunk_ids = await load_chatwindow_data(db, chatwindow_uuid)
        print(f"Selected new chatwindow: {chatwindow_uuid}")
        print("Index size:", request.app.state.index.ntotal)

        return {"status": "success", "doc_uuid": document.id, "chunks_added": len(chunks)}

    except Exception as e:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

