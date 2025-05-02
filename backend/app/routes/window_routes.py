from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from models.db_manager import *
from models.database import get_db
from schemas.query_schema import TitleUpdateRequest

router = APIRouter()

@router.get("/chatwindows")
async def get_all_chat(db: AsyncSession = Depends(get_db)):
    chatwindows = await get_all_chatwindows(db)
    return [{"id": cw.id, "title": cw.title} for cw in chatwindows]

@router.post("/create-chatwindow")
async def create_chat(db: AsyncSession = Depends(get_db)):
    new_chatwindow = await create_chatwindow(db, title="New ChatWindow")
    return {"chatwindow_uuid": new_chatwindow.id}

@router.patch("/chatwindows/{chatwindow_uuid}/update-title")
async def update_title(chatwindow_uuid: str, request: TitleUpdateRequest, db: AsyncSession = Depends(get_db)):
    updated_chatwindow = await update_chatwindow_title(db, chatwindow_uuid, request.title)
    if not updated_chatwindow:
        raise HTTPException(status_code=404, detail="ChatWindow not found")
    return {"message": "Title updated successfully", "chatwindow_uuid": chatwindow_uuid, "title": request.title}