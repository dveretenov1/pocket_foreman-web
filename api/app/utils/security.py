# app/utils/security.py
from fastapi import HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

def handle_api_error(e: Exception) -> Dict[str, Any]:
    """Convert exceptions to appropriate API responses"""
    if isinstance(e, APIError):
        return {
            "error": e.detail,
            "status_code": e.status_code
        }
    
    # Log unexpected errors
    logger.error(f"Unexpected error: {str(e)}")
    return {
        "error": "Internal server error",
        "status_code": 500
    }

# app/utils/responses.py
from typing import TypeVar, Generic, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

def success_response(data: Any = None, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "meta": meta
    }

def error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    return {
        "success": False,
        "error": message,
        "status_code": status_code
    }