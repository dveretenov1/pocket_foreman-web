# app/schemas/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from .message import Message
from .file import File
from ..services.billing.usage import usage_service
from ..services.billing.token_conversion import token_conversion
import logging

logger = logging.getLogger(__name__)

class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []
    files: List[File] = []
    deleted: bool = False
    deleted_at: Optional[datetime] = None

    async def record_message_usage(self, db, user_message, claude_response, chat_id):
        try:
            # Record usage for the user's message
            await usage_service.record_usage(
                db=db,
                user_id=self.user_id,
                chat_id=chat_id,
                message_id=user_message.id,
                input_tokens=len(user_message.content.split()),  # Simple approximation
                output_tokens=0,
                storage_bytes=0
            )

            # Record usage for Claude's response
            await usage_service.record_usage(
                db=db,
                user_id=self.user_id,
                chat_id=chat_id,
                message_id=claude_response.id,
                input_tokens=0,
                output_tokens=len(claude_response.content.split()),  # Simple approximation
                storage_bytes=0
            )
        except Exception as e:
            logger.error(f"Failed to record usage: {str(e)}")
            # Don't raise the error - we don't want to break the chat flow

    class Config:
        from_attributes = True