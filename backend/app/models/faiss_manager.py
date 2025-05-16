import faiss
import numpy as np
import os
from sqlalchemy.future import select
from models.db_models import Document, TextChunk, ImageMetadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "data"

def init_faiss(dimension=1152):
    logger.info(f"Initializing FAISS index with dimension: {dimension}")
    index = faiss.IndexFlatIP(dimension)
    return index

def add_embeddings(index, embeddings):
    logger.info(f"Adding embeddings with shape: {embeddings.shape}")
    if embeddings.shape[1] != index.d:
        logger.error(f"Dimension mismatch: embedding dimension {embeddings.shape[1]} != index dimension {index.d}")
        raise ValueError(f"Embedding dimension {embeddings.shape[1]} does not match index dimension {index.d}")
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

def search_embeddings(index, query_vector, top_k=3):
    logger.info(f"Searching FAISS index with query shape: {query_vector.shape}")
    if query_vector.shape[1] != index.d:
        logger.error(f"Query dimension mismatch: query dimension {query_vector.shape[1]} != index dimension {index.d}")
        raise ValueError(f"Query dimension {query_vector.shape[1]} does not match index dimension {index.d}")
    faiss.normalize_L2(query_vector)
    scores, indices = index.search(query_vector, top_k)
    logger.info(f"FAISS search returned scores: {scores[0].tolist()}, indices: {indices[0].tolist()}")
    return scores, indices

async def load_chatwindow_data(db, chatwindow_id: str, dimension=1152):
    index = init_faiss(dimension)
    all_ids = []
    current_id = 0

    documents = await db.execute(select(Document).filter(Document.chatwindow_id == chatwindow_id))
    documents = documents.scalars().all()
    logger.info(f"Found {len(documents)} documents for chatwindow: {chatwindow_id}")

    text_count = 0
    image_count = 0
    for doc in documents:
        logger.info(f"Loading text embeddings from: {doc.embedding_path}")
        try:
            text_embeddings = np.load(doc.embedding_path)
            logger.info(f"Text embeddings shape: {text_embeddings.shape}")
            chunks = await db.execute(
                select(TextChunk).filter(TextChunk.document_id == doc.id).order_by(TextChunk.chunk_index)
            )
            chunks = chunks.scalars().all()
            logger.info(f"Found {len(chunks)} text chunks for document: {doc.id}")
            for i, embedding in enumerate(text_embeddings):
                if embedding.shape[0] != dimension:
                    logger.error(f"Text embedding dimension mismatch for chunk {i}: {embedding.shape[0]} != {dimension}")
                    continue
                add_embeddings(index, embedding[np.newaxis, :])
                all_ids.append(('text', chunks[i].id))
                text_count += 1
                current_id += 1
        except Exception as e:
            logger.error(f"Failed to load text embeddings for document {doc.id}: {str(e)}")

        if doc.image_embedding_path and os.path.exists(doc.image_embedding_path):
            logger.info(f"Loading image embeddings from: {doc.image_embedding_path}")
            try:
                image_embeddings = np.load(doc.image_embedding_path)
                logger.info(f"Image embeddings shape: {image_embeddings.shape}")
                images = await db.execute(
                    select(ImageMetadata).filter(ImageMetadata.document_id == doc.id)
                )
                images = images.scalars().all()
                logger.info(f"Found {len(images)} image metadata for document: {doc.id}")
                for i, embedding in enumerate(image_embeddings):
                    if embedding.shape[0] != dimension:
                        logger.error(f"Image embedding dimension mismatch for image {i}: {embedding.shape[0]} != {dimension}")
                        continue
                    add_embeddings(index, embedding[np.newaxis, :])
                    all_ids.append(('image', images[i].id))
                    image_count += 1
                    current_id += 1
            except Exception as e:
                logger.error(f"Failed to load image embeddings for document {doc.id}: {str(e)}")

    logger.info(f"Loaded {index.ntotal} embeddings for chatwindow {chatwindow_id}: {text_count} text, {image_count} images")
    return index, all_ids

def save_embeddings(chatwindow_id: str, doc_name: str, embeddings_np, is_image=False):
    chat_dir = os.path.join(DATA_DIR, chatwindow_id)
    os.makedirs(chat_dir, exist_ok=True)
    prefix = "image" if is_image else "text"
    embedding_path = os.path.join(chat_dir, f"{prefix}_{doc_name}.npy")
    logger.info(f"Saving embeddings to: {embedding_path}, shape: {embeddings_np.shape}")
    np.save(embedding_path, embeddings_np)
    return embedding_path

def delete_document(chatwindow_id: str, doc_id: str):
    chat_dir = os.path.join(DATA_DIR, chatwindow_id)
    for prefix in ["text", "image"]:
        npy_path = os.path.join(chat_dir, f"{prefix}_{doc_id}.npy")
        if os.path.exists(npy_path):
            logger.info(f"Deleting embedding file: {npy_path}")
            os.remove(npy_path)

def delete_chatwindow(chatwindow_id: str):
    chat_dir = os.path.join(DATA_DIR, chatwindow_id)
    if os.path.exists(chat_dir):
        for file in os.listdir(chat_dir):
            if file.endswith(".npy"):
                logger.info(f"Deleting embedding file: {os.path.join(chat_dir, file)}")
                os.remove(os.path.join(chat_dir, file))
        logger.info(f"Removing directory: {chat_dir}")
        os.rmdir(chat_dir)