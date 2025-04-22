import faiss
import numpy as np
import os
import json

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

def load_chatwindow_embeddings(chatwindow_uuid, dimension=384):
    index = init_faiss(dimension)
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    if not os.path.exists(chat_dir):
        os.makedirs(chat_dir)
        save_metadata(chatwindow_uuid, [])

    for file in os.listdir(chat_dir):
        if file.endswith(".npy"):
            embedding = np.load(os.path.join(chat_dir, file))
            faiss.normalize_L2(embedding)
            index.add(embedding)

    return index

def save_embeddings(chatwindow_uuid, doc_uuid, embeddings_np):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    os.makedirs(chat_dir, exist_ok=True)
    np.save(os.path.join(chat_dir, f"{doc_uuid}.npy"), embeddings_np)

def delete_document(chatwindow_uuid, doc_uuid):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    npy_path = os.path.join(chat_dir, f"{doc_uuid}.npy")
    if os.path.exists(npy_path):
        os.remove(npy_path)

def delete_chatwindow(chatwindow_uuid):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    if os.path.exists(chat_dir):
        for file in os.listdir(chat_dir):
            os.remove(os.path.join(chat_dir, file))
        os.rmdir(chat_dir)

def save_metadata(chatwindow_uuid, docs):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    os.makedirs(chat_dir, exist_ok=True)
    with open(os.path.join(chat_dir, "metadata.json"), "w") as f:
        json.dump({"docs": docs}, f)

def load_metadata(chatwindow_uuid):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    meta_path = os.path.join(chat_dir, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            return json.load(f)["docs"]
    return []


def save_text_chunks(chatwindow_uuid, doc_uuid, text_chunks):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    os.makedirs(chat_dir, exist_ok=True)

    chunks_path = os.path.join(chat_dir, "chunks.json")

    if os.path.exists(chunks_path):
        with open(chunks_path, "r") as f:
            all_chunks = json.load(f)
    else:
        all_chunks = {}

    all_chunks[doc_uuid] = text_chunks

    with open(chunks_path, "w") as f:
        json.dump(all_chunks, f)

def delete_chunk(chatwindow_uuid, doc_uuid):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    chunks_path = os.path.join(chat_dir, "chunks.json")
    
    if os.path.exists(chunks_path):
        with open(chunks_path, "r") as f:
            all_chunks = json.load(f)

        if doc_uuid in all_chunks:
            del all_chunks[doc_uuid]

        with open(chunks_path, "w") as f:
            json.dump(all_chunks, f)

def load_text_chunks(chatwindow_uuid):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    chunks_path = os.path.join(chat_dir, "chunks.json")

    if os.path.exists(chunks_path):
        with open(chunks_path, "r") as f:
            all_chunks = json.load(f)
            flattened_chunks = [chunk for chunks in all_chunks.values() for chunk in chunks]
            return flattened_chunks

    return []
