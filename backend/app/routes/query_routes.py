from fastapi import APIRouter, Request, HTTPException
from schemas.query_schema import QueryRequest
from models.faiss_manager import search_embeddings
import numpy as np
import asyncio
from datetime import datetime, timezone

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

        scores, indices = search_embeddings(request.app.state.index, query_np, top_k=query.top_k)

        text_chunks = request.app.state.text_chunks
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(text_chunks):
                continue
            results.append({
                "text": text_chunks[idx],
                "score": float(score)
            })

        return {
            "query": query.query,
            "started_at": start_time,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
