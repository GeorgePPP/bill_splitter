import base64
import os
from typing import Optional
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class OCRService:
    def __init__(self):
        self.client = DocumentIntelligenceClient(
            endpoint=settings.ocr_endpoint,
            credential=AzureKeyCredential(settings.ocr_key)
        )

    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract text from an image using Azure Document Intelligence.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            with open(image_path, "rb") as image:
                b64_data = image.read()
                encoded_bytes = base64.b64encode(b64_data).decode("utf-8")

            poller = self.client.begin_analyze_document(
                "prebuilt-read", 
                AnalyzeDocumentRequest(bytes_source=encoded_bytes)
            )
            result: AnalyzeResult = poller.result()
            
            content = result.get("content")
            logger.info(f"Successfully extracted text from {image_path}")
            return content
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
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
            encoded_bytes = base64.b64encode(image_bytes).decode("utf-8")

            poller = self.client.begin_analyze_document(
                "prebuilt-read", 
                AnalyzeDocumentRequest(bytes_source=encoded_bytes)
            )
            result: AnalyzeResult = poller.result()
            
            content = result.get("content")
            logger.info("Successfully extracted text from image bytes")
            return content
            
        except Exception as e:
            logger.error(f"Error extracting text from image bytes: {str(e)}")
            return None


# Global OCR service instance
ocr_service = OCRService()
