#!/usr/bin/env python3
"""
Environment setup helper for Bill Splitter Backend
Creates a sample .env file if one doesn't exist.
"""

import os

def create_sample_env():
    """Create a sample .env file with required environment variables."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        print(f"✓ .env file already exists at {env_path}")
        return
    
    env_content = """# Environment Variables for Bill Splitter Backend

# Supabase Configuration (Required for session management)
# Get these from your Supabase project dashboard
# Your project appears to be: xysgdyeeqjdffzygmske
SUPABASE_URL=https://xysgdyeeqjdffzygmske.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Azure Document Intelligence (OCR) - Optional
OCR_KEY=your_azure_ocr_key_here
OCR_ENDPOINT=https://your-region.cognitiveservices.azure.com/

# OpenAI Configuration - Optional
OPENAI_API_KEY=your_openai_api_key_here

# FastAPI Security
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# File Upload Settings
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✓ Created sample .env file at {env_path}")
        print("\n📋 Next steps:")
        print("1. Edit the .env file and add your actual Supabase credentials")
        print("2. Get Supabase URL and anon key from: https://supabase.com/dashboard/project/your-project/settings/api")
        print("3. Optionally add Azure OCR and OpenAI keys for full functionality")
        print("4. Run the server: python run.py")
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")

def check_database_schema():
    """Check if database migration is needed."""
    print("\n🗄️  Database Schema Check:")
    print("Make sure your Supabase database has the following tables:")
    print("1. sessions (session_token, user_id, expires_at, created_at)")
    print("2. bill_sessions (session_token, current_step, participants, receipt_data, etc.)")
    print("\nRun the SQL in DATABASE_MIGRATION.sql if you haven't already.")

if __name__ == "__main__":
    print("🔧 Bill Splitter Backend Environment Setup")
    print("=" * 50)
    
    create_sample_env()
    check_database_schema()
    
    print("\n✅ Setup complete! Edit the .env file with your actual credentials.")
