# app/services/file.py
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from ..models.file import File
from ..models.chat_files import ChatFile
from datetime import datetime
from .s3 import s3_service
import logging

logger = logging.getLogger(__name__)

class FileService:
    @staticmethod
    async def create_file(db: Session, user_id: str, file: UploadFile) -> File:
        """Create a new file record and upload to S3"""
        try:
            # Validate file type
            allowed_types = ['application/pdf', 'text/plain', 'text/csv']
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400, 
                    detail="File type not supported. Only PDF, TXT, and CSV files are allowed."
                )

            # Upload to S3
            s3_key = await s3_service.upload_file(file, user_id)
            
            # Create file record
            db_file = File(
                user_id=user_id,
                s3_key=s3_key,
                original_name=file.filename
            )
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
            
            return db_file
        except Exception as e:
            logger.error(f"Error creating file: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create file")

    @staticmethod
    async def get_user_files(db: Session, user_id: str, skip: int = 0, limit: int = 100):
        """Get all files for a user"""
        return db.query(File).filter(
            File.user_id == user_id,
            File.deleted == False
        ).offset(skip).limit(limit).all()

    @staticmethod
    async def add_file_to_chat(db: Session, chat_id: int, file_id: int) -> ChatFile:
        """Add a file to a chat"""
        try:
            # Check if file is already associated with chat
            existing_chat_file = db.query(ChatFile).filter(
                ChatFile.chat_id == chat_id,
                ChatFile.file_id == file_id
            ).first()

            if existing_chat_file:
                # If file exists but is inactive, reactivate it
                if not existing_chat_file.active:
                    existing_chat_file.active = True
                    db.commit()
                return existing_chat_file
            else:
                # Create new association if it doesn't exist
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

    @staticmethod
    async def remove_file_from_chat(db: Session, chat_id: int, file_id: int):
        """Remove a file from a chat"""
        try:
            db.query(ChatFile).filter(
                ChatFile.chat_id == chat_id,
                ChatFile.file_id == file_id
            ).update({"active": False})
            db.commit()
        except Exception as e:
            logger.error(f"Error removing file from chat: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to remove file from chat")

    @staticmethod
    async def get_file_url(file_id: int, db: Session) -> str:
        """Get a presigned URL for a file"""
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return s3_service.get_file_url(file.s3_key)

    @staticmethod
    async def delete_file(db: Session, file_id: int, user_id: str):
        """Soft delete a file"""
        file = db.query(File).filter(
            File.id == file_id,
            File.user_id == user_id,
            File.deleted == False
        ).first()
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        file.deleted = True
        file.deleted_at = datetime.now()
        db.commit()

file_service = FileService()
