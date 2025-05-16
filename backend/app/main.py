from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from models.embedding_model import *
from models.faiss_manager import init_faiss
from routes import pdf_routes, query_routes, window_routes
import asyncio
import torch
import uvicorn
import nltk

nltk.download('punkt_tab', quiet=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.siglip_model, app.state.siglip_processor = await load_siglip_model()
    app.state.llm_model, app.state.llm_tokenizer = await load_llm_model()
    app.state.index = init_faiss(dimension=1152)
    app.state.all_ids = []

    loop = asyncio.get_event_loop()
    batch_size = 64 if torch.cuda.is_available() else 8
    await loop.run_in_executor(
        None,
        lambda: encode_with_siglip(
            app.state.siglip_model,
            app.state.siglip_processor,
            texts=["Warm-up sentence"],
            batch_size=batch_size
        )
    )

    yield

    del app.state.siglip_model
    del app.state.siglip_processor
    del app.state.llm_model
    del app.state.llm_tokenizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

app = FastAPI(title="NeoSearch: Hybrid AI Search Engine", lifespan=lifespan)

app.mount("/saved_images", StaticFiles(directory="saved_images"), name="saved_images")

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