from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class TitleUpdateRequest(BaseModel):
    title: str