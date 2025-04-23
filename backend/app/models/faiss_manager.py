import faiss
import numpy as np
import os
import json

DATA_DIR = "data"
DATA_INDEX_FILE = os.path.join(DATA_DIR, "data.json")

def load_data_index():
    if os.path.exists(DATA_INDEX_FILE):
        with open(DATA_INDEX_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data_index(data):
    with open(DATA_INDEX_FILE, "w") as f:
        json.dump(data, f, indent=2)

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

def save_embeddings(chatwindow_uuid, doc_uuid, doc_name, embeddings_np):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    os.makedirs(chat_dir, exist_ok=True)
    np.save(os.path.join(chat_dir, f"{doc_uuid}.npy"), embeddings_np)

    data_index = load_data_index()
    if chatwindow_uuid not in data_index:
        data_index[chatwindow_uuid] = {
            "title": f"ChatWindow {chatwindow_uuid[:6]}",
            "documents": []
        }
    if not any(doc["uuid"] == doc_uuid for doc in data_index[chatwindow_uuid]["documents"]):
        data_index[chatwindow_uuid]["documents"].append({"uuid": doc_uuid, "name": doc_name})
    save_data_index(data_index)

def delete_document(chatwindow_uuid, doc_uuid):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    npy_path = os.path.join(chat_dir, f"{doc_uuid}.npy")
    if os.path.exists(npy_path):
        os.remove(npy_path)

    data_index = load_data_index()
    if chatwindow_uuid in data_index:
        data_index[chatwindow_uuid]["documents"] = [
            d for d in data_index[chatwindow_uuid]["documents"] if d["uuid"] != doc_uuid
        ]
        save_data_index(data_index)

def delete_chatwindow(chatwindow_uuid):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    if os.path.exists(chat_dir):
        for file in os.listdir(chat_dir):
            os.remove(os.path.join(chat_dir, file))
        os.rmdir(chat_dir)

    data_index = load_data_index()
    if chatwindow_uuid in data_index:
        del data_index[chatwindow_uuid]
        save_data_index(data_index)

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
