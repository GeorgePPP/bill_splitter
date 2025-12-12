# backend/app/services/ocr_service.py
"""
Azure Document Intelligence OCR service for receipt text extraction.
"""
import base64
import os
from typing import Optional
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRService:
    def __init__(self):
        endpoint = settings.ocr_endpoint
        if not endpoint:
            logger.warning("OCR endpoint not configured - OCR will not work")
            self.client = None
            return
            
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
            self.client = None

    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract text from an image using Azure Document Intelligence.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text content in markdown format or None if extraction fails
        """
        if not self.client:
            logger.error("OCR service not initialized")
            return None
            
        operation_id = f"ocr_{hash(image_path) % 10000}"
        
        try:
            logger.info(f"[{operation_id}] Starting OCR extraction: {image_path}")
            
            if not os.path.exists(image_path):
                logger.error(f"[{operation_id}] File not found: {image_path}")
                return None

            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            
            logger.info(f"[{operation_id}] File read: {len(image_data)} bytes")
            
            return self._extract_markdown_content(image_data, operation_id)
                
        except Exception as e:
            logger.error(f"[{operation_id}] OCR extraction failed: {str(e)}")
            return None

    def extract_text_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """Extract text from image bytes."""
        if not self.client:
            logger.error("OCR service not initialized")
            return None
            
        operation_id = f"ocr_bytes_{hash(str(image_bytes)[:100]) % 10000}"
        
        try:
            logger.info(f"[{operation_id}] Starting extraction from {len(image_bytes)} bytes")
            return self._extract_markdown_content(image_bytes, operation_id)
        except Exception as e:
            logger.error(f"[{operation_id}] Error: {str(e)}")
            return None

    def _extract_markdown_content(self, image_data: bytes, operation_id: str) -> Optional[str]:
        """Extract content using Azure Document Intelligence with markdown output."""
        try:
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            analyze_request = AnalyzeDocumentRequest(bytes_source=encoded_image)
            
            logger.info(f"[{operation_id}] Sending to Azure Document Intelligence")
            
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout",
                analyze_request=analyze_request,
                output_content_format="markdown"
            )
            
            logger.info(f"[{operation_id}] Waiting for analysis...")
            result = poller.result()
            
            if hasattr(result, 'content') and result.content:
                content = result.content
                logger.info(f"[{operation_id}] Extraction successful: {len(content)} chars")
                return content
            else:
                logger.warning(f"[{operation_id}] No content in result")
                return None
            
        except Exception as e:
            logger.error(f"[{operation_id}] Extraction failed: {str(e)}")
            return None


# Global OCR service instance
ocr_service = OCRService()