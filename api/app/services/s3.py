# app/services/s3.py
import boto3
from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError
from ..config import get_settings
import logging
from datetime import datetime, timedelta
import io

logger = logging.getLogger(__name__)
settings = get_settings()

class S3Service:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_BUCKET_NAME

    async def upload_file(self, file: UploadFile, user_id: str) -> str:
        """
        Upload a file to S3 and return the S3 key
        """
        try:
            # Generate unique file key
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_key = f"{user_id}/{timestamp}_{file.filename}"
            
            # Read file content
            contents = await file.read()
            
            # Upload to S3 with proper content type
            content_type = file.content_type or 'application/octet-stream'
            self.s3.upload_fileobj(
                io.BytesIO(contents),
                self.bucket_name,
                file_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'private'  # Ensure files are private
                }
            )
            
            logger.info(f"File uploaded successfully: {file_key}")
            return file_key
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to upload file")

    def delete_file(self, file_key: str) -> None:
        """
        Delete a file from S3
        """
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"File deleted successfully: {file_key}")
        except Exception as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete file")

    def get_file_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for file download
        """
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate file URL")

    async def get_file_content(self, file_key: str) -> str:
        """
        Get file content from S3
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=file_key)
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading file from S3: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to read file content")

# Create a single instance of S3Service
s3_service = S3Service()