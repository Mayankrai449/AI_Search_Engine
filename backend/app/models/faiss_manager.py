import faiss
import numpy as np
import os
from sqlalchemy.future import select
from models.db_models import Document, TextChunk

DATA_DIR = "data"

def init_faiss(dimension=384):
    index = faiss.IndexFlatIP(dimension)
    return index

def add_embeddings(index, embeddings):
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

def search_embeddings(index, query_vector, top_k=3):
    faiss.normalize_L2(query_vector)
    scores, indices = index.search(query_vector, top_k)
    return scores, indices

async def load_chatwindow_data(db, chatwindow_id: str, dimension=384):
    index = init_faiss(dimension)
    chunk_ids = []
    documents = await db.execute(select(Document).filter(Document.chatwindow_id == chatwindow_id))
    documents = documents.scalars().all()

    for doc in documents:
        embeddings = np.load(doc.embedding_path)
        chunks = await db.execute(
            select(TextChunk).filter(TextChunk.document_id == doc.id).order_by(TextChunk.chunk_index)
        )
        chunks = chunks.scalars().all()
        for i, embedding in enumerate(embeddings):
            add_embeddings(index, embedding[np.newaxis, :])
            chunk_ids.append(chunks[i].id)
    return index, chunk_ids

def save_embeddings(chatwindow_id: str, doc_id: str, doc_name: str, embeddings_np):
    chat_dir = os.path.join(DATA_DIR, chatwindow_id)
    os.makedirs(chat_dir, exist_ok=True)
    embedding_path = os.path.join(chat_dir, f"{doc_id}.npy")
    np.save(embedding_path, embeddings_np)
    return embedding_path

def delete_document(chatwindow_id: str, doc_id: str):
    chat_dir = os.path.join(DATA_DIR, chatwindow_id)
    npy_path = os.path.join(chat_dir, f"{doc_id}.npy")
    if os.path.exists(npy_path):
        os.remove(npy_path)

def delete_chatwindow(chatwindow_id: str):
    chat_dir = os.path.join(DATA_DIR, chatwindow_id)
    if os.path.exists(chat_dir):
        for file in os.listdir(chat_dir):
            if file.endswith(".npy"):
                os.remove(os.path.join(chat_dir, file))
        os.rmdir(chat_dir)