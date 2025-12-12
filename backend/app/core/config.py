# backend/app/core/config.py
import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Azure Document Intelligence (OCR)
    ocr_key: str = os.getenv("OCR_KEY", "")
    ocr_endpoint: str = os.getenv("OCR_ENDPOINT", "")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # CORS
    allowed_origins: List[str] = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:3000,http://localhost:5173"
    ).split(",")
    
    # File Upload (temporary storage only - cleaned up after processing)
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()