# app/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..services.auth import get_current_user
from ..services.chat import chat_service
from ..services.file import file_service
from ..schemas.chat import Chat as ChatSchema, ChatCreate
from ..schemas.message import Message as MessageSchema, MessageCreate
from ..models.user import User
from ..models.file import File
from ..models.chat import Chat
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("/", response_model=ChatSchema)
async def create_chat(
    chat: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat"""
    return await chat_service.create_chat(db, current_user.id, chat.title)

@router.get("/", response_model=List[ChatSchema])
async def get_user_chats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all chats for current user"""
    return await chat_service.get_user_chats(db, current_user.id, skip, limit)

@router.post("/latest/files", response_model=ChatSchema)
async def add_files_to_latest_chat(
    file_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add files to the latest chat or create a new chat if none exists"""
    try:
        # Get latest chat
        latest_chat = db.query(Chat).filter(
            Chat.user_id == current_user.id,
            Chat.deleted == False
        ).order_by(Chat.updated_at.desc()).first()

        # If no chat exists, create one
        if not latest_chat:
            latest_chat = await chat_service.create_chat(db, current_user.id, "New Chat")

        # Add files to chat
        results = []
        for file_id in file_ids:
            result = await file_service.add_file_to_chat(db, latest_chat.id, file_id)
            results.append(result)

        # Update chat's updated_at timestamp
        latest_chat.updated_at = datetime.now()
        db.commit()
        db.refresh(latest_chat)

        return latest_chat
    except Exception as e:
        logger.error(f"Error adding files to latest chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add files to chat")

@router.get("/{chat_id}/messages", response_model=List[MessageSchema])
async def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages for a chat"""
    return await chat_service.get_chat_messages(db, chat_id, current_user.id)

@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: int,
    content: str = Body(..., embed=True),
    file_ids: List[int] = Body(default=[], embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message in a chat.
    Returns a streaming response with Claude's reply.
    """
    # Get files if file_ids provided
    files = []
    if file_ids:
        files = db.query(File).filter(File.id.in_(file_ids)).all()
        if len(files) != len(file_ids):
            raise HTTPException(status_code=400, detail="Some files not found")

    async def event_generator():
        try:
            # Directly yield from the chat service's generator
            async for chunk in chat_service.send_message(
                db=db,
                chat_id=chat_id,
                content=content,
                user_id=current_user.id,
                files=files
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming error in route: {str(e)}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        finally:
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat"""
    await chat_service.delete_chat(db, chat_id, current_user.id)
    return {"message": "Chat deleted successfully"}

@router.put("/{chat_id}/title")
async def update_chat_title(
    chat_id: int,
    title: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update chat title"""
    updated_chat = await chat_service.update_chat_title(
        db, 
        chat_id, 
        title, 
        current_user.id
    )
    return updated_chat

@router.post("/{chat_id}/files")
async def add_files_to_chat(
    chat_id: int,
    file_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add multiple files to a chat"""
    results = []
    for file_id in file_ids:
        result = await file_service.add_file_to_chat(db, chat_id, file_id)
        results.append(result)
    return {"message": f"Added {len(results)} files to chat"}

@router.delete("/{chat_id}/files/{file_id}")
async def remove_file_from_chat(
    chat_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a file from a chat"""
    await file_service.remove_file_from_chat(db, chat_id, file_id)
    return {"message": "File removed from chat"}

@router.get("/{chat_id}/files")
async def get_chat_files(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all files associated with a chat"""
    files = await chat_service.get_chat_files(db, chat_id, current_user.id)
    return files
