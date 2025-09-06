import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure Document Intelligence
    ocr_key: str = os.getenv("OCR_KEY", "")
    ocr_endpoint: str = os.getenv("OCR_ENDPOINT", "")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # FastAPI
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS
    allowed_origins: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    
    # File Upload
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    
    class Config:
        env_file = ".env"


settings = Settings()
