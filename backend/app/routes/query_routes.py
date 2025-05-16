from fastapi import APIRouter, Request, HTTPException, Depends
from schemas.query_schema import QueryRequest
from models.faiss_manager import search_embeddings
from models.embedding_model import generate_tailored_response, encode_with_siglip
from models.database import get_db
from models.db_models import Document, TextChunk, ImageMetadata
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import numpy as np
import asyncio
from datetime import datetime, timezone
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/search")
async def search_query(request: Request, query: QueryRequest, images: bool = True, db: AsyncSession = Depends(get_db)):
    if not hasattr(request.app.state, 'current_chatwindow') or not request.app.state.current_chatwindow:
        raise HTTPException(status_code=400, detail="No chatwindow selected")
    chatwindow_uuid = request.app.state.current_chatwindow
    logger.info(f"Searching in chatwindow: {chatwindow_uuid}, images_enabled={images}")
    try:
        siglip_model = request.app.state.siglip_model
        siglip_processor = request.app.state.siglip_processor
        llm_model = request.app.state.llm_model
        llm_tokenizer = request.app.state.llm_tokenizer
        loop = asyncio.get_event_loop()

        start_time = datetime.now(timezone.utc).isoformat()

        logger.info(f"Encoding query: {query.query}")
        query_embedding = await loop.run_in_executor(
            None,
            lambda: encode_with_siglip(siglip_model, siglip_processor, texts=[query.query])
        )
        query_np = np.array(query_embedding, dtype='float32')
        logger.info(f"Query embedding shape: {query_np.shape}")

        index = request.app.state.index
        if index is None or index.ntotal == 0:
            raise HTTPException(status_code=400, detail="No chatwindow selected or no embeddings available.")

        search_k = max(query.top_k, 10) if images else query.top_k
        scores, indices = search_embeddings(index, query_np, top_k=search_k)
        logger.info(f"FAISS search returned {len(indices[0])} indices")

        if not hasattr(request.app.state, 'all_ids'):
            raise HTTPException(status_code=500, detail="Application state missing all_ids attribute")
        all_ids = request.app.state.all_ids
        if not all_ids:
            raise HTTPException(status_code=400, detail="No IDs available for the current chatwindow.")
        logger.info(f"Total all_ids count: {len(all_ids)}, types: {[t for t, _ in all_ids]}")

        text_results = []
        image_results = []
        text_chunks = []

        text_ids = []
        image_ids = []
        for i, idx in enumerate(indices[0]):
            if idx == -1 or idx >= len(all_ids):
                logger.warning(f"Invalid index {idx} in FAISS results")
                continue
            type, id = all_ids[idx]
            logger.info(f"FAISS index {idx}: type={type}, id={id}, score={scores[0][i]}")
            if type == 'text':
                text_ids.append((id, i, scores[0][i]))
            elif type == 'image' and images:
                image_ids.append((id, i, scores[0][i]))

        logger.info(f"Text IDs: {len(text_ids)}, Image IDs: {len(image_ids)}")

        text_ids = text_ids[:query.top_k]

        if image_ids and images:
            image_ids = sorted(image_ids, key=lambda x: x[2], reverse=True)[:1]
            logger.info(f"Selected top 1 image ID: {image_ids}")

        if text_ids:
            text_ids_only = [id for id, _, _ in text_ids]
            logger.info(f"Fetching {len(text_ids)} text chunks from database")
            text_query = select(TextChunk).filter(TextChunk.id.in_(text_ids_only)).options(selectinload(TextChunk.document))
            text_result = await db.execute(text_query)
            text_chunks_db = {chunk.id: chunk for chunk in text_result.scalars().all()}
            for id, i, score in text_ids:
                chunk = text_chunks_db.get(id)
                if chunk:
                    text_results.append({
                        "text": chunk.chunk,
                        "page_number": chunk.page_number,
                        "pdf_name": chunk.document.name,
                        "vector_score": float(score),
                        "chunk_id": chunk.id
                    })
                    text_chunks.append(chunk.chunk)

        if image_ids and images:
            image_ids_only = [id for id, _, _ in image_ids]
            logger.info(f"Fetching {len(image_ids)} image metadata from database")
            image_query = select(ImageMetadata).filter(ImageMetadata.id.in_(image_ids_only)).options(selectinload(ImageMetadata.document))
            image_result = await db.execute(image_query)
            image_metadata_db = {image.id: image for image in image_result.scalars().all()}
            for id, i, score in image_ids:
                image = image_metadata_db.get(id)
                if image:
                    image_results.append({
                        "image_path": image.image_path,
                        "metadata": image.meta_data,
                        "pdf_name": image.document.name,
                        "score": float(score)
                    })

        if text_results:
            tokenized_chunks = [word_tokenize(chunk["text"].lower()) for chunk in text_results]
            bm25 = BM25Okapi(tokenized_chunks)
            tokenized_query = word_tokenize(query.query.lower())
            bm25_scores = bm25.get_scores(tokenized_query)

            for i, result in enumerate(text_results):
                bm25_score = bm25_scores[i]
                result["bm25_score"] = bm25_score
                result["score"] = result["vector_score"] + bm25_score

            text_results = sorted(text_results, key=lambda x: x["score"], reverse=True)

        logger.info(f"Generating tailored response for {len(text_chunks)} chunks")
        tailored_response = await generate_tailored_response(
            llm_model, llm_tokenizer, query.query, text_chunks, max_length=200
        )

        response = {
            "query": query.query,
            "started_at": start_time,
            "text_results": text_results,
            "tailored_response": tailored_response
        }
        if images:
            response["image_results"] = image_results

        logger.info(f"Search completed successfully, text_results={len(text_results)}, image_results={len(image_results)}")
        return response

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")