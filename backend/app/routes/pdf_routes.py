from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from utils.text_utils import extract_and_clean_text, split_text_into_chunks
from models.faiss_manager import *
import numpy as np
import asyncio
import os
import uuid

router = APIRouter()

@router.post("/select-chatwindow")
async def select_chatwindow(request: Request, chatwindow_uuid: str):
    request.app.state.current_chatwindow = chatwindow_uuid
    request.app.state.index = load_chatwindow_embeddings(chatwindow_uuid)
    print("Index size:", request.app.state.index.ntotal)

    request.app.state.text_chunks = load_text_chunks(chatwindow_uuid)
    print("Chunks loaded:", len(request.app.state.text_chunks))

    docs = load_metadata(chatwindow_uuid)
    return {"chatwindow_uuid": chatwindow_uuid, "documents": docs}



@router.post("/upload")
async def upload_pdf(request: Request, chatwindow_uuid: str, pdf_file: UploadFile = File(...)):
    try:
        doc_uuid = str(uuid.uuid4())
        contents = await pdf_file.read()
        pdf_path = f"temp_{pdf_file.filename}"
        with open(pdf_path, 'wb') as f:
            f.write(contents)

        text = await extract_and_clean_text(pdf_path)
        os.remove(pdf_path)

        chunks = split_text_into_chunks(text, chatwindow_uuid, doc_uuid)
        model = request.app.state.model
        loop = asyncio.get_event_loop()

        embeddings = await loop.run_in_executor(
            None, lambda: model.encode(chunks, normalize_embeddings=False)
        )
        embeddings_np = np.array(embeddings, dtype='float32')

        # Check if chatwindow exists, if not create it
        chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
        if not os.path.exists(chat_dir):
            os.makedirs(chat_dir)
            save_metadata(chatwindow_uuid, [])
            save_embeddings(chatwindow_uuid, doc_uuid, np.empty((0, embeddings_np.shape[1]), dtype='float32'))

        save_embeddings(chatwindow_uuid, doc_uuid, embeddings_np)

        docs = load_metadata(chatwindow_uuid)
        docs.append({"uuid": doc_uuid, "name": pdf_file.filename})
        save_metadata(chatwindow_uuid, docs)


        request.app.state.current_chatwindow = chatwindow_uuid
        request.app.state.index = load_chatwindow_embeddings(chatwindow_uuid)
        request.app.state.text_chunks = load_text_chunks(chatwindow_uuid)
        print(f"Selected new chatwindow: {chatwindow_uuid}")
        print("Index size:", request.app.state.index.ntotal)
        print("Chunks loaded:", len(request.app.state.text_chunks))

        return {"status": "success", "doc_uuid": doc_uuid, "chunks_added": len(chunks)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-doc")
async def delete_pdf(request: Request, chatwindow_uuid: str, doc_uuid: str):
    delete_document(chatwindow_uuid, doc_uuid)

    docs = load_metadata(chatwindow_uuid)
    docs = [d for d in docs if d["uuid"] != doc_uuid]
    save_metadata(chatwindow_uuid, docs)

    delete_chunk(chatwindow_uuid, doc_uuid)

    if getattr(request.app.state, "current_chatwindow", None) == chatwindow_uuid:
        request.app.state.current_chatwindow = chatwindow_uuid
        request.app.state.index = load_chatwindow_embeddings(chatwindow_uuid)
        request.app.state.text_chunks = load_text_chunks(chatwindow_uuid)

    return {"status": "deleted", "doc_uuid": doc_uuid}

@router.delete("/delete-chatwindow")
async def delete_chatwindow_route(request: Request, chatwindow_uuid: str):
    delete_chatwindow(chatwindow_uuid)

    if getattr(request.app.state, "current_chatwindow", None) == chatwindow_uuid:
        request.app.state.index = None
        request.app.state.current_chatwindow = None

    return {"status": "chatwindow deleted", "chatwindow_uuid": chatwindow_uuid}
