# app/routes/file.py
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.auth import get_current_user
from ..services.file import file_service
from ..schemas.file import File as FileSchema
from ..models.file import File as FileModel
from ..models.chat_files import ChatFile
from ..models.user import User
import logging
from ..services.s3 import s3_service
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])

@router.post("/", response_model=FileSchema)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new file"""
    return await file_service.create_file(db, current_user.id, file)

@router.get("/", response_model=List[FileSchema])
async def get_user_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all files for current user"""
    return await file_service.get_user_files(db, current_user.id, skip, limit)

@router.post("/{file_id}/chat/{chat_id}")
async def add_file_to_chat(
    file_id: int,
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a file to a chat"""
    try:
        # First check if file is already in chat
        existing = db.query(ChatFile).filter(
            ChatFile.chat_id == chat_id,
            ChatFile.file_id == file_id
        ).first()

        if existing:
            # If exists but inactive, reactivate it
            if not existing.active:
                existing.active = True
                db.commit()
            return existing
        
        # If not exists, create new association
        chat_file = ChatFile(
            chat_id=chat_id,
            file_id=file_id,
            active=True
        )
        db.add(chat_file)
        db.commit()
        return chat_file
    except Exception as e:
        logger.error(f"Error adding file to chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add file to chat")

@router.delete("/{file_id}/chat/{chat_id}")
async def remove_file_from_chat(
    file_id: int,
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a file from a chat"""
    try:
        # Mark file as inactive instead of deleting
        result = db.query(ChatFile).filter(
            ChatFile.chat_id == chat_id,
            ChatFile.file_id == file_id
        ).update({"active": False})
        db.commit()
        
        if result == 0:
            raise HTTPException(status_code=404, detail="File not found in chat")
        return {"message": "File removed from chat"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error removing file from chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove file from chat")

@router.get("/{file_id}/url")
async def get_file_url(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a presigned URL for a file"""
    return {"url": await file_service.get_file_url(file_id, db)}

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a file"""
    await file_service.delete_file(db, file_id, current_user.id)
    return {"message": "File deleted successfully"}

@router.post("/upload", response_model=FileSchema)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new file and create file record"""
    try:
        logger.info(f"Starting file upload for user {current_user.id}: {file.filename}")
        
        # Validate file type
        allowed_types = ['application/pdf', 'text/plain', 'text/csv']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="File type not supported. Only PDF, TXT, and CSV files are allowed."
            )
        
        # Upload to S3
        s3_key = await s3_service.upload_file(file, current_user.id)
        logger.info(f"S3 upload successful, key: {s3_key}")
        
        # Create file record
        db_file = FileModel(
            user_id=current_user.id,
            s3_key=s3_key,
            original_name=file.filename
        )
        
        # Save to database
        try:
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            # Try to clean up the S3 file if database save fails
            try:
                await s3_service.delete_file(s3_key)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup S3 file after database error: {str(cleanup_error)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save file information to database"
            )
        
        return db_file
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/chat/{chat_id}/files", response_model=List[FileSchema])
async def get_chat_files(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active files associated with a chat"""
    try:
        files = db.query(FileModel).join(ChatFile).filter(
            ChatFile.chat_id == chat_id,
            ChatFile.active == True,
            FileModel.deleted == False
        ).all()
        return files
    except Exception as e:
        logger.error(f"Error getting chat files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat files")