# backend/app/utils/file_handler.py
"""
File handling utilities for temporary receipt image storage.
Files are cleaned up after processing.
"""
import os
import uuid
from typing import Optional, Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileHandler:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.max_file_size = settings.max_file_size
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        """Ensure upload directory exists."""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
            logger.info(f"Created upload directory: {self.upload_dir}")

    def validate_file(self, file: UploadFile) -> Tuple[bool, str]:
        """
        Validate uploaded file for size and type.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file size
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            
            if file_size > self.max_file_size:
                return False, f"File too large. Maximum: {self.max_file_size // 1024 // 1024}MB"
            
            # Check file type
            allowed_types = [
                "image/jpeg", "image/jpg", "image/png", 
                "image/tiff", "image/bmp", "image/webp"
            ]
            if file.content_type not in allowed_types:
                return False, f"File type '{file.content_type}' not supported. Use: JPEG, PNG, TIFF, BMP, WebP"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def save_file(self, file: UploadFile) -> Optional[str]:
        """
        Save uploaded file temporarily.
        
        Returns:
            Path to saved file or None if failed
        """
        try:
            ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
            filename = f"{uuid.uuid4()}{ext}"
            file_path = os.path.join(self.upload_dir, filename)
            
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            logger.info(f"Saved file: {file_path} ({len(content)} bytes)")
            return file_path
            
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """Delete file from disk."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"File delete error: {str(e)}")
            return False


# Global instance
file_handler = FileHandler()