# app/services/auth.py
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Firebase Admin
try:
    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
    raise

security = HTTPBearer()

class AuthService:
    @staticmethod
    async def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ):
        try:
            # Verify the Firebase token
            token = credentials.credentials
            decoded_token = auth.verify_id_token(token)
            
            # Get user from database or create if doesn't exist
            user = db.query(User).filter(User.id == decoded_token['uid']).first()
            if not user:
                user = User(
                    id=decoded_token['uid'],
                    email=decoded_token.get('email', 'no-email')
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Created new user with id: {user.id}")
            
            return user
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )

    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ):
        return await AuthService.verify_token(credentials, db)

# Create a dependency that can be used in route handlers
get_current_user = AuthService.get_current_user