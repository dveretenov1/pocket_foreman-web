# app/routes/user.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth import get_current_user
from ..schemas.user import User as UserSchema
from ..models.user import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/register", response_model=UserSchema)
async def register_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new user in the database"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.id == current_user.id).first()
    if existing_user:
        return existing_user

    # Create new user record
    try:
        db_user = User(
            id=current_user.id,
            email=current_user.email,
            created_at=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user")
