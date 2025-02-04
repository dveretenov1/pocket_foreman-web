from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    s3_key = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="files")
    chats = relationship("Chat", secondary="chat_files", back_populates="files")
