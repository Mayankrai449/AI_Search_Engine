from fastapi import APIRouter, Request, HTTPException, Depends
from schemas.query_schema import QueryRequest
from models.faiss_manager import search_embeddings
from models.embedding_model import generate_tailored_response, encode_with_amp
from models.database import get_db
from models.db_models import TextChunk
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import numpy as np
import asyncio
from datetime import datetime, timezone
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize

router = APIRouter()

@router.post("/search")
async def search_query(request: Request, query: QueryRequest, db: AsyncSession = Depends(get_db)):
    try:
        sentence_model = request.app.state.sentence_model
        llm_model = request.app.state.llm_model
        llm_tokenizer = request.app.state.llm_tokenizer
        device = sentence_model.device
        loop = asyncio.get_event_loop()

        start_time = datetime.now(timezone.utc).isoformat()

        query_embedding = await loop.run_in_executor(
            None,
            lambda: encode_with_amp(sentence_model, [query.query], batch_size=64)
        )
        query_np = np.array(query_embedding, dtype='float32')

        index = request.app.state.index
        if index is None or index.ntotal == 0:
            raise HTTPException(status_code=400, detail="No chatwindow selected or no embeddings available.")

        scores, indices = search_embeddings(index, query_np, top_k=query.top_k)

        chunk_ids = request.app.state.chunk_ids
        if not chunk_ids:
            raise HTTPException(status_code=400, detail="No chunk IDs available for the current chatwindow.")

        text_chunks = []
        valid_indices = [idx for idx in indices[0] if idx != -1 and idx < len(chunk_ids)]
        if not valid_indices:
            return {
                "query": query.query,
                "started_at": start_time,
                "results": [],
                "tailored_response": "No relevant chunks found."
            }

        chunk_id_list = [chunk_ids[idx] for idx in valid_indices]
        result = await db.execute(
            select(TextChunk).filter(TextChunk.id.in_(chunk_id_list))
        )
        chunks = result.scalars().all()

        chunk_dict = {chunk.id: chunk.chunk for chunk in chunks}
        text_chunks = [chunk_dict.get(chunk_ids[idx], "") for idx in valid_indices]
        valid_chunk_ids = [chunk_ids[idx] for idx in valid_indices]
        valid_scores = [scores[0][i] for i, idx in enumerate(indices[0]) if idx in valid_indices]

        tokenized_chunks = [word_tokenize(chunk.lower()) for chunk in text_chunks]
        bm25 = BM25Okapi(tokenized_chunks)
        tokenized_query = word_tokenize(query.query.lower())
        bm25_scores = bm25.get_scores(tokenized_query)

        bm25_results = []
        for i, (score, chunk_id) in enumerate(zip(valid_scores, valid_chunk_ids)):
            bm25_score = bm25_scores[i]
            total_score = float(score) + bm25_score
            bm25_results.append({
                "text": text_chunks[i],
                "score": total_score,
                "bm25_score": bm25_score,
                "vector_score": float(score),
                "chunk_id": chunk_id
            })

        ranked_results = sorted(bm25_results, key=lambda x: x["score"], reverse=True)

        tailored_response = await generate_tailored_response(
            llm_model, llm_tokenizer, query.query, text_chunks, max_length=200
        )

        return {
            "query": query.query,
            "started_at": start_time,
            "results": ranked_results,
            "tailored_response": tailored_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")