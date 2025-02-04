from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class ChatFile(Base):
    __tablename__ = "chat_files"
    
    chat_id = Column(Integer, ForeignKey("chats.id"), primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), primary_key=True)
    added_at = Column(DateTime, server_default=func.now())
    active = Column(Boolean, default=True)