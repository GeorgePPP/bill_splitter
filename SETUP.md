# Bill Splitter Setup Guide

This guide will help you set up the Bill Splitter application on your local machine.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Node.js 18+** and npm
- **Python 3.11+** and pip
- **Git** (for cloning the repository)

## API Keys Required

You'll need the following API keys:

1. **Azure Document Intelligence** (for OCR)
   - Sign up at [Azure Portal](https://portal.azure.com)
   - Create a Document Intelligence resource
   - Get your key and endpoint

2. **OpenAI API** (for data extraction)
   - Sign up at [OpenAI](https://platform.openai.com)
   - Create an API key

## Quick Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd bill-splitter

# Run the setup script
python setup_env.py
```

### 2. Configure Environment Variables

Edit `backend/.env` with your actual API keys:

```env
# Azure Document Intelligence
OCR_KEY=your_actual_azure_ocr_key_here
OCR_ENDPOINT=your_actual_azure_ocr_endpoint_here

# OpenAI
OPENAI_API_KEY=your_actual_openai_api_key_here

# FastAPI
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
```

### 3. Install Dependencies

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 4. Run the Application

**Start the Backend:**
```bash
cd backend
python run.py
```
The backend will be available at `http://localhost:8000`

**Start the Frontend:**
```bash
cd frontend
npm run dev
```
The frontend will be available at `http://localhost:3000`

## Manual Setup (Alternative)

If you prefer to set up manually:

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. Create uploads directory:
   ```bash
   mkdir uploads
   ```

6. Run the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## Testing the Application

1. Open your browser and go to `http://localhost:3000`
2. Follow the steps to split a bill:
   - Select number of people
   - Enter participant names
   - Upload a receipt image
   - Assign items to people
   - View the calculated split

## Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure the backend is running on port 8000 and frontend on port 3000
2. **API Key Errors**: Verify your API keys are correct in the `.env` file
3. **File Upload Issues**: Check that the uploads directory exists and has proper permissions
4. **OCR Errors**: Ensure your Azure Document Intelligence service is active and properly configured

### Logs

- Backend logs: Check the terminal where you ran the backend server
- Frontend logs: Check the browser console (F12)
- Network errors: Check the Network tab in browser dev tools

## Development

### Backend Development

- The backend uses FastAPI with auto-reload enabled
- API documentation is available at `http://localhost:8000/docs`
- Changes to Python files will automatically restart the server

### Frontend Development

- The frontend uses Vite with hot module replacement
- Changes to React components will automatically update in the browser
- TypeScript errors will be shown in the terminal and browser

## Production Deployment

For production deployment, you'll need to:

1. Build the frontend: `npm run build`
2. Configure production environment variables
3. Set up a production WSGI server (like Gunicorn)
4. Configure reverse proxy (like Nginx)
5. Set up SSL certificates
6. Configure proper CORS settings

## Support

If you encounter any issues:

1. Check the logs for error messages
2. Verify all API keys are correct
3. Ensure all dependencies are installed
4. Check that all required directories exist
5. Verify network connectivity

For additional help, please open an issue in the repository.
