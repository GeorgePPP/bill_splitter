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
            logger.warning(f"Receipt not found in storage: {receipt_id}")
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        receipt = receipts_storage[receipt_id]
        logger.info(f"Found receipt: {receipt.filename}, text length: {len(receipt.raw_text) if receipt.raw_text else 0}")
        
        # Validate raw text before processing
        if not receipt.raw_text or receipt.raw_text.strip() == "":
            logger.error("Receipt has no raw text to process")
            raise HTTPException(status_code=400, detail="Receipt has no text data to process")
        
        # Single extraction call - this includes validation
        try:
            logger.info("Starting OpenAI data extraction")
            
            # Primary extraction for model (with validation)
            processed_data_model = openai_service.extract_receipt_data(receipt.raw_text)
            
            if not processed_data_model:
                logger.error("OpenAI extraction returned no structured data")
                raise HTTPException(status_code=500, detail="Failed to extract structured data from receipt")
            
            # Store the model data
            receipt.processed_data = processed_data_model
            receipt.updated_at = datetime.now()
            receipts_storage[receipt_id] = receipt
            
            # Convert to schema format for API response
            processed_data_schema = ReceiptDataSchema(
                receipt_number=processed_data_model.receipt_number,
                date=processed_data_model.date,
                time=processed_data_model.time,
                store=StoreInfoSchema(
                    name=processed_data_model.store.name,
                    address=processed_data_model.store.address,
                    phone=processed_data_model.store.phone
                ),
                items=[
                    BillItemSchema(
                        name=item.name,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price
                    )
                    for item in processed_data_model.items
                ],
                subtotal=processed_data_model.subtotal,
                taxes_or_charges=[
                    TaxOrChargeSchema(
                        name=tax_charge.name,
                        amount=tax_charge.amount,
                        percent=tax_charge.percent
                    )
                    for tax_charge in processed_data_model.taxes_or_charges
                ],
                grand_total=processed_data_model.grand_total,
                payment_method=processed_data_model.payment_method,
                transaction_id=processed_data_model.transaction_id,
                notes=processed_data_model.notes
            )
            
            logger.info("OpenAI extraction and schema conversion successful")
            
            return ReceiptProcessResponse(
                success=True,
                message="Receipt processed successfully",
                processed_data=processed_data_schema
            )
            
        except ValueError as e:
            # Handle calculation validation errors specifically
            error_msg = str(e)
            logger.error(f"Receipt calculation validation failed: {error_msg}")
            
            # Get the extracted (but unvalidated) data from the exception
            extracted_data_dict = None
            if hasattr(e, 'unvalidated_data') and e.unvalidated_data:
                unvalidated = e.unvalidated_data
                extracted_data_dict = {
                    "receipt_number": unvalidated.receipt_number,
                    "date": unvalidated.date,
                    "time": unvalidated.time,
                    "store": {
                        "name": unvalidated.store.name,
                        "address": unvalidated.store.address,
                        "phone": unvalidated.store.phone
                    },
                    "items": [
                        {
                            "name": item.name,
                            "quantity": item.quantity,
                            "unit_price": item.unit_price,
                            "total_price": item.total_price
                        }
                        for item in unvalidated.items
                    ],
                    "subtotal": unvalidated.subtotal,
                    "taxes_or_charges": [
                        {
                            "name": tc.name,
                            "amount": tc.amount,
                            "percent": getattr(tc, 'percent', None)
                        }
                        for tc in unvalidated.taxes_or_charges
                    ],
                    "grand_total": unvalidated.grand_total,
                    "payment_method": unvalidated.payment_method,
                    "transaction_id": unvalidated.transaction_id,
                    "notes": unvalidated.notes
                }
            
            # User-friendly error message
            user_friendly_msg = error_msg
            if "Items total" in error_msg and "does not match" in error_msg:
                user_friendly_msg = (
                    "The individual item prices don't add up to the subtotal shown on the receipt. "
                    "Please review and correct the amounts in the validation screen."
                )
            
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Receipt Calculation Validation Failed",
                    "message": user_friendly_msg,
                    "technical_details": error_msg,
                    "extracted_data": extracted_data_dict,
                    "suggestions": [
                        "Review the extracted amounts",
                        "Check for OCR errors in item prices",
                        "Verify tax calculations"
                    ]
                }
            )
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing receipt {receipt_id}: {str(e)}", exc_info=True)
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
    
@router.post("/reprocess/{receipt_id}", response_model=ReceiptProcessResponse)
async def reprocess_receipt_with_corrections(
    receipt_id: str,
    corrected_data: ReceiptDataSchema,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Reprocess receipt with user-corrected data.
    """
    try:
        logger.info(f"Reprocessing receipt {receipt_id} with user corrections")
        
        if receipt_id not in receipts_storage:
            logger.warning(f"Receipt not found in storage: {receipt_id}")
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        receipt = receipts_storage[receipt_id]
        
        # Convert corrected schema data to model format
        from app.models.receipt import ReceiptData, StoreInfo, BillItem, TaxOrCharge
        
        processed_data_model = ReceiptData(
            receipt_number=corrected_data.receipt_number,
            date=corrected_data.date,
            time=corrected_data.time,
            store=StoreInfo(
                name=corrected_data.store.name,
                address=corrected_data.store.address,
                phone=corrected_data.store.phone
            ),
            items=[
                BillItem(
                    name=item.name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price
                )
                for item in corrected_data.items
            ],
            subtotal=corrected_data.subtotal,
            taxes_or_charges=[
                TaxOrCharge(
                    name=tc.name,
                    amount=tc.amount,
                    percent=tc.percent
                )
                for tc in corrected_data.taxes_or_charges
            ],
            grand_total=corrected_data.grand_total,
            payment_method=corrected_data.payment_method,
            transaction_id=corrected_data.transaction_id,
            notes=corrected_data.notes
        )
        
        # Validate the corrected data
        from app.services.receipt_validator import receipt_validator_service
        
        try:
            data_dict = processed_data_model.model_dump()
            operation_id = f"reprocess_{receipt_id}_{hash(str(data_dict)) % 10000}"
            
            validated_data = receipt_validator_service.validate_and_process_receipt(data_dict, operation_id)
            
            # Update receipt with validated data
            receipt.processed_data = ReceiptData(**validated_data)
            receipt.updated_at = datetime.now()
            receipts_storage[receipt_id] = receipt
            
            # Convert back to schema for response
            response_data = ReceiptDataSchema(
                receipt_number=receipt.processed_data.receipt_number,
                date=receipt.processed_data.date,
                time=receipt.processed_data.time,
                store=StoreInfoSchema(
                    name=receipt.processed_data.store.name,
                    address=receipt.processed_data.store.address,
                    phone=receipt.processed_data.store.phone
                ),
                items=[
                    BillItemSchema(
                        name=item.name,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price
                    )
                    for item in receipt.processed_data.items
                ],
                subtotal=receipt.processed_data.subtotal,
                taxes_or_charges=[
                    TaxOrChargeSchema(
                        name=tc.name,
                        amount=tc.amount,
                        percent=tc.percent
                    )
                    for tc in receipt.processed_data.taxes_or_charges
                ],
                grand_total=receipt.processed_data.grand_total,
                payment_method=receipt.processed_data.payment_method,
                transaction_id=receipt.processed_data.transaction_id,
                notes=receipt.processed_data.notes
            )
            
            logger.info(f"Successfully reprocessed receipt {receipt_id}")
            
            return ReceiptProcessResponse(
                success=True,
                message="Receipt reprocessed successfully with corrections",
                processed_data=response_data
            )
            
        except ValueError as e:
            # Validation still failed
            error_msg = str(e)
            logger.error(f"Receipt validation failed after user corrections: {error_msg}")
            
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Receipt Validation Failed",
                    "message": error_msg,
                    "suggestions": [
                        "Please double-check all amounts",
                        "Ensure items add up correctly to subtotal",
                        "Verify taxes are calculated correctly"
                    ]
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing receipt {receipt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")