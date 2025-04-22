from fastapi import APIRouter, Request, HTTPException
from schemas.query_schema import QueryRequest
from models.faiss_manager import search_embeddings
import numpy as np
import asyncio
from datetime import datetime, timezone
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize

router = APIRouter()

@router.post("/search")
async def search_query(request: Request, query: QueryRequest):
    try:
        model = request.app.state.model
        loop = asyncio.get_event_loop()

        start_time = datetime.now(timezone.utc).isoformat()

        query_embedding = await loop.run_in_executor(
            None, lambda: model.encode([query.query], normalize_embeddings=False)
        )

        query_np = np.array(query_embedding, dtype='float32')

        index = request.app.state.index
        if index is None or index.ntotal == 0:
            raise HTTPException(status_code=400, detail="No chatwindow selected or no embeddings available.")

        scores, indices = search_embeddings(index, query_np, top_k=query.top_k)

        text_chunks = request.app.state.text_chunks

        tokenized_chunks = [word_tokenize(chunk.lower()) for chunk in text_chunks]

        bm25 = BM25Okapi(tokenized_chunks)

        tokenized_query = word_tokenize(query.query.lower())

        bm25_scores = bm25.get_scores(tokenized_query)

        bm25_results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(text_chunks):
                continue
            bm25_score = bm25_scores[idx]
            total_score = float(score) + bm25_score
            
            bm25_results.append({
                "text": text_chunks[idx],
                "score": total_score,
                "bm25_score": bm25_score,
                "vector_score": float(score)
            })

        ranked_results = sorted(bm25_results, key=lambda x: x["score"], reverse=True)


        return {
            "query": query.query,
            "started_at": start_time,
            "results": ranked_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
