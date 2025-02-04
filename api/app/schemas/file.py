# app/schemas/file.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileBase(BaseModel):
    original_name: str

class FileCreate(FileBase):
    pass

class File(FileBase):
    id: int
    user_id: str
    s3_key: str
    created_at: datetime
    deleted: bool = False
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True