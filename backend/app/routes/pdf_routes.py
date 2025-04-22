from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from utils.text_utils import extract_and_clean_text, split_text_into_chunks
from models.faiss_manager import add_embeddings
import numpy as np
import asyncio
from datetime import datetime, timezone
import os

router = APIRouter()

@router.post("/upload")
async def upload_pdf(request: Request, pdf_file: UploadFile = File(...)):
    try:
        upload_time = datetime.now(timezone.utc).isoformat()

        contents = await pdf_file.read()
        pdf_path = f"temp_{pdf_file.filename}"

        with open(pdf_path, 'wb') as f:
            f.write(contents)

        text = await extract_and_clean_text(pdf_path)
        chunks = split_text_into_chunks(text)
        os.remove(pdf_path)

        model = request.app.state.model
        loop = asyncio.get_event_loop()

        embeddings = await loop.run_in_executor(
            None, lambda: model.encode(chunks, normalize_embeddings=False)
        )

        embeddings_np = np.array(embeddings, dtype='float32')

        add_embeddings(request.app.state.index, embeddings_np)

        if not hasattr(request.app.state, "text_chunks"):
            request.app.state.text_chunks = []

        request.app.state.text_chunks.extend(chunks)

        return {
            "status": "success",
            "chunks_added": len(chunks),
            "upload_time": upload_time
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
