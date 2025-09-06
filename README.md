# Bill Splitter

A modern web application for splitting bills with friends, family, or colleagues. Upload a receipt, assign items to people, and get instant calculations with tax and tip distribution.

## Features

- 📸 **Receipt OCR**: Upload receipt images and extract item data using Azure Document Intelligence
- 🤖 **AI Processing**: Use OpenAI to intelligently parse and structure receipt data
- 👥 **Multi-person Splitting**: Support for any number of people splitting the bill
- 🛒 **Item Assignment**: Drag and drop interface to assign items to specific people
- 💰 **Smart Calculations**: Automatic tax, tip, and discount distribution
- 📱 **Responsive Design**: Works perfectly on desktop and mobile devices
- 🎨 **Modern UI**: Clean, intuitive interface inspired by Splitwise

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Hook Form** for form management
- **React Dropzone** for file uploads
- **Lucide React** for icons

### Backend
- **FastAPI** with Python 3.11+
- **Azure Document Intelligence** for OCR
- **OpenAI GPT-4** for data extraction
- **Pydantic** for data validation
- **Uvicorn** as ASGI server

## Project Structure

```
bill-splitter/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API service layer
│   │   ├── utils/           # Utility functions
│   │   ├── types/           # TypeScript type definitions
│   │   └── styles/          # CSS styles
│   └── package.json
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── services/       # Business logic
│   │   ├── models/         # Data models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── utils/          # Utility functions
│   └── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Azure Document Intelligence account
- OpenAI API account

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```env
   OCR_KEY=your_azure_ocr_key_here
   OCR_ENDPOINT=your_azure_ocr_endpoint_here
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. Run the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000`

## Usage

1. **Select People**: Choose how many people are splitting the bill
2. **Enter Names**: Add names and contact info for each participant
3. **Upload Receipt**: Take a photo or upload an image of your receipt
4. **Assign Items**: Assign each item to the person who ordered it
5. **View Results**: See the final split with tax and tip calculations

## API Endpoints

### Receipt Processing
- `POST /receipt/upload` - Upload receipt image
- `POST /receipt/process/{receipt_id}` - Process receipt with AI
- `GET /receipt/{receipt_id}` - Get receipt data
- `DELETE /receipt/{receipt_id}` - Delete receipt

### Bill Management
- `POST /bill/split` - Create bill split
- `GET /bill/{bill_id}` - Get bill split details
- `PUT /bill/{bill_id}/assignments` - Update item assignments
- `DELETE /bill/{bill_id}` - Delete bill split

### Split Calculations
- `POST /split/calculate` - Calculate bill split
- `GET /split/{split_id}` - Get split calculation
- `GET /split/` - List all splits
- `DELETE /split/{split_id}` - Delete split

## Development

### Running Tests

Backend tests:
```bash
cd backend
pytest
```

Frontend tests:
```bash
cd frontend
npm test
```

### Building for Production

Frontend:
```bash
cd frontend
npm run build
```

Backend:
```bash
cd backend
# The FastAPI app is ready for production deployment
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by Splitwise's user experience
- Built with modern web technologies
- Uses Azure Document Intelligence for OCR
- Powered by OpenAI for intelligent data extraction
