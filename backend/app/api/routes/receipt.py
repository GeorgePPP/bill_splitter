from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
import uuid
from datetime import datetime

from ...services.ocr_service import ocr_service
from ...services.openai_service import openai_service
from ...services.bill_parser import bill_parser_service
from ...utils.file_handler import file_handler
from ...utils.validators import validators
from ...utils.exceptions import FileProcessingError, OCRProcessingError, DataExtractionError
from ...schemas.receipt_schema import ReceiptUploadResponse, ReceiptProcessResponse
from ...models.receipt import Receipt
from ..dependencies import get_current_user, get_logger_dependency

router = APIRouter(prefix="/receipt", tags=["receipt"])

# In-memory storage for demo purposes
receipts_storage = {}


@router.post("/upload", response_model=ReceiptUploadResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Upload a receipt image for OCR processing.
    """
    try:
        # Validate file
        is_valid, error_message = file_handler.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Save file
        file_path = file_handler.save_file(file)
        if not file_path:
            raise HTTPException(status_code=500, detail="Failed to save file")
        
        # Extract text using OCR
        raw_text = ocr_service.extract_text_from_image(file_path)
        if not raw_text:
            # Clean up saved file
            file_handler.delete_file(file_path)
            raise HTTPException(status_code=500, detail="Failed to extract text from image")
        
        # Create receipt record
        receipt_id = str(uuid.uuid4())
        receipt = Receipt(
            id=receipt_id,
            filename=file.filename,
            raw_text=raw_text,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store receipt
        receipts_storage[receipt_id] = receipt
        
        logger.info(f"Successfully uploaded and processed receipt {receipt_id}")
        
        return ReceiptUploadResponse(
            success=True,
            message="Receipt uploaded and processed successfully",
            receipt_id=receipt_id,
            raw_text=raw_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading receipt: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process/{receipt_id}", response_model=ReceiptProcessResponse)
async def process_receipt(
    receipt_id: str,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Process uploaded receipt using OpenAI to extract structured data.
    """
    try:
        # Get receipt from storage
        if receipt_id not in receipts_storage:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        receipt = receipts_storage[receipt_id]
        
        # Extract structured data using OpenAI
        processed_data = openai_service.extract_receipt_data(receipt.raw_text)
        if not processed_data:
            raise HTTPException(status_code=500, detail="Failed to extract structured data from receipt")
        
        # Validate extracted data
        if not openai_service.validate_receipt_data(processed_data):
            raise HTTPException(status_code=400, detail="Extracted data validation failed")
        
        # Update receipt with processed data
        receipt.processed_data = processed_data
        receipt.updated_at = datetime.now()
        receipts_storage[receipt_id] = receipt
        
        logger.info(f"Successfully processed receipt {receipt_id}")
        
        return ReceiptProcessResponse(
            success=True,
            message="Receipt processed successfully",
            processed_data=processed_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing receipt {receipt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{receipt_id}")
async def get_receipt(
    receipt_id: str,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Get receipt information by ID.
    """
    try:
        if receipt_id not in receipts_storage:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        receipt = receipts_storage[receipt_id]
        
        return {
            "id": receipt.id,
            "filename": receipt.filename,
            "raw_text": receipt.raw_text,
            "processed_data": receipt.processed_data,
            "created_at": receipt.created_at.isoformat(),
            "updated_at": receipt.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting receipt {receipt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{receipt_id}")
async def delete_receipt(
    receipt_id: str,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Delete receipt by ID.
    """
    try:
        if receipt_id not in receipts_storage:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Remove from storage
        del receipts_storage[receipt_id]
        
        logger.info(f"Successfully deleted receipt {receipt_id}")
        
        return {
            "success": True,
            "message": "Receipt deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting receipt {receipt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
