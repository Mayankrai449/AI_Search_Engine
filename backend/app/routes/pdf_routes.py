from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends
from utils.text_utils import extract_and_clean_text, split_text_into_chunks
from models.faiss_manager import load_chatwindow_data, save_embeddings
from models.db_manager import create_document, create_text_chunks, create_image_metadata
from models.embedding_model import encode_with_siglip
from models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image
import numpy as np
import asyncio
import os
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload")
async def upload_pdf(request: Request, chatwindow_uuid: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        doc_uuid = str(uuid.uuid4())
        pdf_path = f"temp/{doc_uuid}.pdf"
        os.makedirs("temp", exist_ok=True)
        with open(pdf_path, 'wb') as f:
            f.write(await file.read())

        logger.info(f"Extracting text and images for chatwindow: {chatwindow_uuid}")
        page_texts, image_data = await extract_and_clean_text(pdf_path, chatwindow_uuid, doc_uuid)
        os.remove(pdf_path)

        paragraphs_with_pages = []
        for page_num, cleaned_page_text in page_texts:
            paragraphs = cleaned_page_text.split('\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    paragraphs_with_pages.append((page_num, paragraph.strip()))

        chunks_with_pages = split_text_into_chunks(paragraphs_with_pages, max_words=400, overlap_words=100)
        chunks = [chunk for chunk, _ in chunks_with_pages]
        logger.info(f"Extracted {len(chunks)} text chunks")

        siglip_model = request.app.state.siglip_model
        siglip_processor = request.app.state.siglip_processor
        loop = asyncio.get_event_loop()

        logger.info("Encoding text chunks...")
        text_embeddings = await loop.run_in_executor(
            None,
            lambda: encode_with_siglip(siglip_model, siglip_processor, texts=chunks)
        )
        text_embeddings_np = np.array(text_embeddings, dtype='float32')
        logger.info(f"Text embeddings shape: {text_embeddings_np.shape}")
        embedding_path = save_embeddings(chatwindow_uuid, file.filename, text_embeddings_np)
        logger.info(f"Saved text embeddings to: {embedding_path}")

        image_embedding_path = None
        if image_data:
            logger.info(f"Processing {len(image_data)} images...")
            images = []
            for img in image_data:
                try:
                    img_pil = Image.open(img["image_path"]).convert("RGB").resize((384, 384))
                    images.append(img_pil)
                except Exception as e:
                    logger.warning(f"Failed to process image {img['image_path']}: {str(e)}")
            if images:
                logger.info("Encoding images...")
                image_embeddings = await loop.run_in_executor(
                    None,
                    lambda: encode_with_siglip(siglip_model, siglip_processor, images=images)
                )
                image_embeddings_np = np.array(image_embeddings, dtype='float32')
                logger.info(f"Image embeddings shape: {image_embeddings_np.shape}")
                image_embedding_path = save_embeddings(chatwindow_uuid, file.filename, image_embeddings_np, is_image=True)
                logger.info(f"Saved image embeddings to: {image_embedding_path}")

        logger.info(f"Creating document for chatwindow: {chatwindow_uuid}")
        document = await create_document(db, chatwindow_uuid, file.filename, embedding_path, image_embedding_path)
        logger.info(f"Created document ID: {document.id}")

        logger.info("Creating text chunks...")
        await create_text_chunks(db, document.id, chunks_with_pages)

        if image_data and images:
            logger.info("Creating image metadata...")
            await create_image_metadata(db, document.id, image_data, offset=0)

        logger.info(f"Loading data for chatwindow: {chatwindow_uuid}")
        index, all_ids = await load_chatwindow_data(db, chatwindow_uuid)
        request.app.state.index = index
        request.app.state.all_ids = all_ids
        request.app.state.current_chatwindow = chatwindow_uuid
        logger.info(f"Updated state: chatwindow={chatwindow_uuid}, index_size={index.ntotal}, all_ids_count={len(all_ids)}")

        return {"status": "success", "doc_uuid": document.id, "chunks_added": len(chunks)}

    except Exception as e:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        logger.error(f"Failed to process PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")