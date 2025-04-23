from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.embedding_model import load_model
from models.faiss_manager import init_faiss
from routes import pdf_routes, query_routes, window_routes
import uvicorn
import nltk

nltk.download('punkt_tab', quiet=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = await load_model()
    app.state.index = init_faiss()

    yield


app = FastAPI(title="PDF Embedding + FAISS Search API", lifespan=lifespan)

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
