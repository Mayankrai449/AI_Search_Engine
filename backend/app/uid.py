import uuid
import faiss
import numpy as np
import os
import json

DATA_DIR = "data"

print(uuid.uuid4())

def load_metadata(chatwindow_uuid):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    meta_path = os.path.join(chat_dir, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            return json.load(f)["docs"]
    return []

def init_faiss(dimension=384):
    index = faiss.IndexFlatIP(dimension)
    return index

def save_metadata(chatwindow_uuid, docs):
    chat_dir = os.path.join(DATA_DIR, chatwindow_uuid)
    os.makedirs(chat_dir, exist_ok=True)
    with open(os.path.join(chat_dir, "metadata.json"), "w") as f:
        json.dump({"docs": docs}, f)

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

var = '7a1856ce-4c30-4fa4-b028-9875b0123391'
var1 = load_chatwindow_embeddings(var)
docs = load_metadata(var)

print(var1)
print(docs)
