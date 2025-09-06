# backend/app/services/ocr_service.py
import base64
import os
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
        try:
            logger.info(f"Starting text extraction from: {image_path}")
            
            # Validate file exists
            if not os.path.exists(image_path):
                logger.error(f"File not found: {image_path}")
                return None

            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                
            logger.info(f"Read {len(image_data)} bytes from image file")
            
            # Use the newer analyze_document method with base64 encoding
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            analyze_request = AnalyzeDocumentRequest(
                bytes_source=encoded_image
            )
            
            logger.info("Sending request to Azure Document Intelligence...")
            
            # Use the synchronous method instead of begin_analyze_document
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",
                analyze_request=analyze_request
            )
            
            logger.info("Waiting for analysis to complete...")
            result = poller.result()
            
            # Extract content from the result
            if hasattr(result, 'content') and result.content:
                content = result.content
                logger.info(f"Successfully extracted {len(content)} characters of text")
                return content
            else:
                logger.warning("No content found in analysis result")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
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