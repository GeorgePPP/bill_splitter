import os
import uuid
from typing import Optional
from fastapi import UploadFile
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class FileHandler:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.max_file_size = settings.max_file_size
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        """Ensure the upload directory exists."""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
            logger.info(f"Created upload directory: {self.upload_dir}")

    def validate_file(self, file: UploadFile) -> tuple[bool, str]:
        """
        Validate uploaded file for size and type.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file size
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                return False, f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
            
            # Check file type
            allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/tiff", "image/bmp"]
            if file.content_type not in allowed_types:
                return False, f"File type {file.content_type} not supported. Allowed types: {', '.join(allowed_types)}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return False, f"Error validating file: {str(e)}"

    def save_file(self, file: UploadFile) -> Optional[str]:
        """
        Save uploaded file to disk.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Path to saved file or None if save failed
        """
        try:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            logger.info(f"Successfully saved file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Successfully deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False

    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                return None
                
            stat = os.stat(file_path)
            return {
                "path": file_path,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return None


# Global file handler instance
file_handler = FileHandler()
