#!/usr/bin/env python3
"""
Setup script to create environment files and directories.
"""

import os
import shutil

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_file = ".env"
    env_example = ".env.example"
    
    if not os.path.exists(env_file) and os.path.exists(env_example):
        shutil.copy(env_example, env_file)
        print(f"Created {env_file} from {env_example}")
        print("Please edit .env file with your actual API keys")
    elif not os.path.exists(env_file):
        # Create a basic .env file
        env_content = """# Azure Document Intelligence
OCR_KEY=your_azure_ocr_key_here
OCR_ENDPOINT=your_azure_ocr_endpoint_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# FastAPI
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"Created {env_file} with default values")
        print("Please edit .env file with your actual API keys")

def create_upload_dir():
    """Create uploads directory if it doesn't exist."""
    upload_dir = "backend/uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"Created uploads directory: {upload_dir}")

def main():
    """Main setup function."""
    print("Setting up Bill Splitter environment...")
    
    # Change to backend directory
    os.chdir("backend")
    
    create_env_file()
    create_upload_dir()
    
    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Edit backend/.env with your API keys")
    print("2. Install backend dependencies: pip install -r requirements.txt")
    print("3. Install frontend dependencies: cd ../frontend && npm install")
    print("4. Run backend: cd ../backend && python run.py")
    print("5. Run frontend: cd frontend && npm run dev")

if __name__ == "__main__":
    main()
