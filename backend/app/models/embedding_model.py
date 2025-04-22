from sentence_transformers import SentenceTransformer
import asyncio

model = None

async def load_model():
    global model
    if model is None:
        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(None, lambda: SentenceTransformer('all-MiniLM-L6-v2'))
    return model
