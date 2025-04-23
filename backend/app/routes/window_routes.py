from fastapi import APIRouter, HTTPException
from models.faiss_manager import *
from schemas.query_schema import TitleUpdateRequest
import uuid

router = APIRouter()

@router.get("/chatwindows")
async def get_all_chatwindows():
    return load_data_index()


@router.post("/create-chatwindow")
async def create_chatwindow():
    data_index = load_data_index()
    while True:
        new_uuid = str(uuid.uuid4())
        if new_uuid not in data_index:
            break

    return {"chatwindow_uuid": new_uuid}



@router.patch("/chatwindows/{chatwindow_uuid}/update-title")
async def update_chatwindow_title(chatwindow_uuid: str, request: TitleUpdateRequest):
    data_index = load_data_index()
    if chatwindow_uuid not in data_index:
        raise HTTPException(status_code=404, detail="ChatWindow not found")

    data_index[chatwindow_uuid]["title"] = request.title
    save_data_index(data_index)
    return {"message": "Title updated successfully", "chatwindow_uuid": chatwindow_uuid, "title": request.title}