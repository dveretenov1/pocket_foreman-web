# app/schemas/message.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    content: str
    role: str

class MessageCreate(MessageBase):
    chat_id: int

class Message(MessageBase):
    id: int
    chat_id: int
    created_at: datetime
    deleted: bool = False
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True