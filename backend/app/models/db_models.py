from sqlalchemy import Column, String, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from models.database import Base
import uuid

class ChatWindow(Base):
    __tablename__ = "chatwindows"
    __table_args__ = {"schema": "public"}
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    documents = relationship("Document", back_populates="chatwindow", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "public"}
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    embedding_path = Column(String)
    chatwindow_id = Column(String, ForeignKey("public.chatwindows.id"))
    chatwindow = relationship("ChatWindow", back_populates="documents")
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")

class TextChunk(Base):
    __tablename__ = "textchunks"
    __table_args__ = {"schema": "public"}
    id = Column(String, primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    document_id = Column(String, ForeignKey("public.documents.id"))
    chunk = Column(Text)
    chunk_index = Column(Integer)
    document = relationship("Document", back_populates="chunks")