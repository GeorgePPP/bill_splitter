from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
import uuid
from datetime import datetime

from app.services.ocr_service import ocr_service
from app.services.openai_service import openai_service
from app.services.bill_parser import bill_parser_service
from app.utils.file_handler import file_handler
from app.utils.validators import validators
from app.utils.exceptions import FileProcessingError, OCRProcessingError, DataExtractionError
from app.schemas.receipt_schema import (
    ReceiptUploadResponse, 
    ReceiptProcessResponse, 
    ReceiptDataSchema,
    StoreInfoSchema,
    BillItemSchema,
    TaxOrChargeSchema
)
from app.models.receipt import Receipt
from app.api.dependencies import get_current_user, get_logger_dependency

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
        # Validate file with detailed logging
        logger.info(f"Validating uploaded file: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}, content_type: {file.content_type}")
        
        is_valid, error_message = file_handler.validate_file(file)
        if not is_valid:
            logger.warning(f"File validation failed: {error_message}", extra={
                "filename": file.filename,
                "content_type": file.content_type,
                "validation_error": error_message
            })
            raise HTTPException(status_code=400, detail=error_message)
        
        logger.info("File validation successful")
        
        # Save file with error handling
        try:
            file_path = file_handler.save_file(file)
            if not file_path:
                logger.error("File save operation returned None", extra={
                    "filename": file.filename,
                    "operation": "file_save"
                })
                raise HTTPException(status_code=500, detail="Failed to save file")
            
            logger.info(f"File saved successfully to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error during file save operation: {str(e)}", extra={
                "filename": file.filename,
                "error_type": type(e).__name__,
                "operation": "file_save"
            })
            raise HTTPException(status_code=500, detail="Failed to save file")
        
        # Extract text using OCR with comprehensive error handling
        try:
            logger.info("Starting OCR text extraction")
            raw_text = ocr_service.extract_text_from_image(file_path)
            
            if not raw_text:
                logger.error("OCR extraction returned no text", extra={
                    "file_path": file_path,
                    "operation": "ocr_extraction"
                })
                
                # Clean up saved file
                try:
                    file_handler.delete_file(file_path)
                    logger.info("Cleaned up saved file after OCR failure")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up file after OCR failure: {str(cleanup_error)}")
                
                raise HTTPException(status_code=500, detail="Failed to extract text from image")
            
            logger.info(f"OCR extraction successful, extracted {len(raw_text)} characters")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during OCR extraction: {str(e)}", extra={
                "file_path": file_path,
                "error_type": type(e).__name__,
                "operation": "ocr_extraction"
            })
            
            # Clean up saved file
            try:
                file_handler.delete_file(file_path)
                logger.info("Cleaned up saved file after OCR error")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up file after OCR error: {str(cleanup_error)}")
            
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
        # Get receipt from storage with logging
        logger.info(f"Processing receipt: {receipt_id}")
        
        if receipt_id not in receipts_storage:
            logger.warning(f"Receipt not found in storage: {receipt_id}", extra={
                "receipt_id": receipt_id,
                "operation": "receipt_lookup"
            })
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        receipt = receipts_storage[receipt_id]
        logger.info(f"Found receipt: {receipt.filename}, text length: {len(receipt.raw_text) if receipt.raw_text else 0}")
        
        # Validate raw text before processing
        if not receipt.raw_text or receipt.raw_text.strip() == "":
            logger.error("Receipt has no raw text to process", extra={
                "receipt_id": receipt_id,
                "filename": receipt.filename,
                "operation": "openai_processing"
            })
            raise HTTPException(status_code=400, detail="Receipt has no text data to process")
        
        # Extract structured data using OpenAI with comprehensive error handling
        try:
            logger.info("Starting OpenAI data extraction")
            processed_data_schema = openai_service.extract_receipt_data_as_schema(receipt.raw_text)
            
            if not processed_data_schema:
                logger.error("OpenAI extraction returned no structured data", extra={
                    "receipt_id": receipt_id,
                    "text_length": len(receipt.raw_text),
                    "operation": "openai_extraction"
                })
                raise HTTPException(status_code=500, detail="Failed to extract structured data from receipt")
            
            logger.info("OpenAI schema extraction successful", extra={
                "receipt_id": receipt_id,
                "extracted_items_count": len(processed_data_schema.items),
                "grand_total": processed_data_schema.grand_total,
                "store_name": processed_data_schema.store.name
            })
            
        except HTTPException:
            raise
        except ValueError as e:
            # Handle calculation validation errors specifically
            error_msg = str(e)
            logger.error(f"Receipt calculation validation failed: {error_msg}", extra={
                "receipt_id": receipt_id,
                "error_type": "calculation_validation_error",
                "operation": "openai_extraction",
                "text_preview": receipt.raw_text[:200] + "..." if len(receipt.raw_text) > 200 else receipt.raw_text
            })
            raise HTTPException(
                status_code=422, 
                detail=f"Receipt calculation validation failed: {error_msg}. Please check that the receipt totals are correct."
            )
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI extraction: {str(e)}", extra={
                "receipt_id": receipt_id,
                "error_type": type(e).__name__,
                "operation": "openai_extraction",
                "text_preview": receipt.raw_text[:200] + "..." if len(receipt.raw_text) > 200 else receipt.raw_text
            })
            raise HTTPException(status_code=500, detail="Failed to extract structured data from receipt")
        
        # Also get the model for storage with error handling
        try:
            processed_data_model = openai_service.extract_receipt_data(receipt.raw_text)
            if processed_data_model:
                receipt.processed_data = processed_data_model
                receipt.updated_at = datetime.now()
                receipts_storage[receipt_id] = receipt
                logger.info("Receipt data model stored successfully")
            else:
                logger.warning("OpenAI model extraction returned None, schema will be used for response")
                
        except Exception as e:
            logger.warning(f"Failed to extract/store receipt data model: {str(e)}", extra={
                "receipt_id": receipt_id,
                "error_type": type(e).__name__,
                "operation": "model_storage"
            })
            # Continue anyway since we have the schema for response
        
        logger.info(f"Successfully processed receipt {receipt_id}")
        
        return ReceiptProcessResponse(
            success=True,
            message="Receipt processed successfully",
            processed_data=processed_data_schema
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
