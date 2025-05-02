from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.embedding_model import load_model
from models.faiss_manager import init_faiss
from routes import pdf_routes, query_routes, window_routes
import asyncio
import torch
from torch.amp import autocast
import uvicorn
import nltk

nltk.download('punkt_tab', quiet=True)

def encode_with_amp(model, texts, batch_size=64):
    device = model.device
    if device.type == 'cuda':
        with autocast(device_type='cuda'):
            return model.encode(texts, convert_to_numpy=True, batch_size=batch_size)
    return model.encode(texts, convert_to_numpy=True, batch_size=batch_size)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = await load_model()
    app.state.index = init_faiss(dimension=768)
    print(torch.cuda.is_available())
    loop = asyncio.get_event_loop()
    batch_size = 64 if torch.cuda.is_available() else 8
    await loop.run_in_executor(
        None,
        lambda: encode_with_amp(app.state.model, ["Warm-up sentence"], batch_size=batch_size)
    )
    yield


app = FastAPI(title="NeoSearch: Hybrid AI Search Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdf_routes.router, tags=["PDF"])
app.include_router(query_routes.router, tags=["Query"])
app.include_router(window_routes.router, tags=["Window"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
