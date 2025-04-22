import faiss
import numpy as np

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
