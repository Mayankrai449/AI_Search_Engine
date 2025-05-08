from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.db_models import ChatWindow, Document, TextChunk
import uuid

async def create_chatwindow(db: AsyncSession, title: str):
    chatwindow_id = str(uuid.uuid4())
    chatwindow = ChatWindow(id=chatwindow_id, title=title)
    db.add(chatwindow)
    await db.commit()
    await db.refresh(chatwindow)
    return chatwindow

async def get_chatwindow(db: AsyncSession, chatwindow_id: str):
    result = await db.execute(select(ChatWindow).filter(ChatWindow.id == chatwindow_id))
    return result.scalars().first()

async def get_all_chatwindows(db: AsyncSession):
    result = await db.execute(select(ChatWindow))
    return result.scalars().all()

async def update_chatwindow_title(db: AsyncSession, chatwindow_id: str, title: str):
    chatwindow = await get_chatwindow(db, chatwindow_id)
    if chatwindow:
        chatwindow.title = title
        await db.commit()
        return chatwindow
    return None

async def delete_chatwindow(db: AsyncSession, chatwindow_id: str):
    chatwindow = await get_chatwindow(db, chatwindow_id)
    if chatwindow:
        await db.delete(chatwindow)
        await db.commit()
        return True
    return False

async def create_document(db: AsyncSession, chatwindow_id: str, name: str, embedding_path: str):
    document_id = str(uuid.uuid4())
    document = Document(id=document_id, name=name, embedding_path=embedding_path, chatwindow_id=chatwindow_id)
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document

async def get_documents_by_chatwindow(db: AsyncSession, chatwindow_id: str):
    result = await db.execute(select(Document).filter(Document.chatwindow_id == chatwindow_id))
    return result.scalars().all()

async def delete_document(db: AsyncSession, chatwindow_id: str, doc_id: str):
    document = await db.execute(select(Document).filter(Document.id == doc_id, Document.chatwindow_id == chatwindow_id))
    document = document.scalars().first()
    if document:
        await db.execute(delete(TextChunk).where(TextChunk.document_id == doc_id))
        await db.delete(document)
        await db.commit()
        return True
    return False

async def create_text_chunks(db: AsyncSession, document_id: str, chunks_with_pages: list[tuple[str, int]]):
    for i, (chunk_text, page_number) in enumerate(chunks_with_pages):
        chunk = TextChunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            chunk=chunk_text,
            chunk_index=i,
            page_number=page_number
        )
        db.add(chunk)
    await db.commit()