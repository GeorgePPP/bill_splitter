# backend/app/services/ocr_service.py
import base64
import os
import re
from typing import Optional
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRService:
    def __init__(self):
        # Ensure endpoint has proper format
        endpoint = settings.ocr_endpoint
        if not endpoint.startswith('https://'):
            endpoint = f"https://{endpoint}"
        if not endpoint.endswith('/'):
            endpoint = f"{endpoint}/"
            
        logger.info(f"Initializing OCR service with endpoint: {endpoint}")
        
        try:
            self.client = DocumentIntelligenceClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(settings.ocr_key)
            )
            logger.info("OCR service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OCR service: {str(e)}")
            raise

    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract text from an image using Azure Document Intelligence.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text content or None if extraction fails
        """
        operation_id = f"ocr_extract_{hash(image_path) % 10000}"
        
        try:
            logger.info(f"[{operation_id}] Starting OCR text extraction", extra={
                "operation_id": operation_id,
                "image_path": image_path,
                "operation_type": "ocr_extract_image"
            })
            
            # Validate file exists
            if not os.path.exists(image_path):
                logger.error(f"[{operation_id}] File not found", extra={
                    "operation_id": operation_id,
                    "image_path": image_path,
                    "error_type": "file_not_found"
                })
                return None

            # Read file and log stats
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            
            file_stats = {
                "file_size_bytes": len(image_data),
                "file_size_kb": round(len(image_data) / 1024, 2),
                "file_extension": os.path.splitext(image_path)[1].lower()
            }
            
            logger.info(f"[{operation_id}] File read successfully", extra={
                "operation_id": operation_id,
                **file_stats
            })
            
            # Prepare Azure request
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            analyze_request = AnalyzeDocumentRequest(bytes_source=encoded_image)
            
            logger.info(f"[{operation_id}] Sending request to Azure Document Intelligence", extra={
                "operation_id": operation_id,
                "model_id": "prebuilt-read",
                "request_size_bytes": len(encoded_image)
            })
            
            # Make API call
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",
                analyze_request=analyze_request
            )
            
            logger.info(f"[{operation_id}] Waiting for Azure analysis to complete...")
            result = poller.result()
            
            # Process result
            if hasattr(result, 'content') and result.content:
                content = result.content
                
                # Log extraction results with detailed stats
                extraction_stats = {
                    "content_length_chars": len(content),
                    "content_length_words": len(content.split()) if content else 0,
                    "content_lines": len(content.splitlines()) if content else 0,
                    "has_numbers": bool(re.search(r'\d', content)) if content else False,
                    "has_currency": bool(re.search(r'[\$€£¥]', content)) if content else False
                }
                
                logger.info(f"[{operation_id}] OCR extraction successful", extra={
                    "operation_id": operation_id,
                    "success": True,
                    **extraction_stats,
                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                })
                
                return content
            else:
                logger.warning(f"[{operation_id}] No content found in Azure analysis result", extra={
                    "operation_id": operation_id,
                    "result_type": type(result).__name__,
                    "has_content_attr": hasattr(result, 'content'),
                    "content_value": getattr(result, 'content', None)
                })
                return None
                
        except Exception as e:
            error_details = {
                "operation_id": operation_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "image_path": image_path
            }
            
            # Add more specific error context
            if "authentication" in str(e).lower():
                error_details["error_category"] = "authentication"
            elif "quota" in str(e).lower() or "rate" in str(e).lower():
                error_details["error_category"] = "rate_limit"
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                error_details["error_category"] = "network"
            else:
                error_details["error_category"] = "unknown"
            
            logger.error(f"[{operation_id}] OCR extraction failed", extra=error_details)
            return None

    def extract_text_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """
        Extract text from image bytes using Azure Document Intelligence.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            logger.info(f"Starting text extraction from {len(image_bytes)} bytes")
            
            # Encode exactly like your working code
            encoded_bytes = base64.b64encode(image_bytes).decode("utf-8")
            
            # Use the exact same method as your working code
            poller = self.client.begin_analyze_document(
                "prebuilt-read", 
                AnalyzeDocumentRequest(bytes_source=encoded_bytes)
            )
            
            logger.info("Waiting for analysis to complete...")
            result: AnalyzeResult = poller.result()
            
            # Extract content exactly like your working code
            content = result.get("content")
            
            if content:
                logger.info(f"Successfully extracted {len(content)} characters of text")
                return content
            else:
                logger.warning("No content found in analysis result")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text from image bytes: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return None


# Global OCR service instance
ocr_service = OCRService()