# backend/app/services/ocr_service.py
import base64
import os
import re
from typing import Optional, Dict, List, Any
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
        Extract text from an image using Azure Document Intelligence with enhanced table extraction.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text content with structured table data or None if extraction fails
        """
        operation_id = f"ocr_extract_{hash(image_path) % 10000}"
        
        try:
            logger.info(f"[{operation_id}] Starting enhanced OCR text extraction", extra={
                "operation_id": operation_id,
                "image_path": image_path,
                "operation_type": "ocr_extract_image_enhanced"
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
            
            # Extract enhanced content with tables
            enhanced_content = self._extract_enhanced_content(image_data, operation_id)
            return enhanced_content
                
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
        Extract text from image bytes using Azure Document Intelligence with enhanced table extraction.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Extracted text content with structured table data or None if extraction fails
        """
        operation_id = f"ocr_extract_bytes_{hash(str(image_bytes)) % 10000}"
        
        try:
            logger.info(f"[{operation_id}] Starting enhanced text extraction from {len(image_bytes)} bytes")
            
            # Extract enhanced content with tables
            enhanced_content = self._extract_enhanced_content(image_bytes, operation_id)
            return enhanced_content
                
        except Exception as e:
            logger.error(f"[{operation_id}] Error extracting text from image bytes: {str(e)}")
            logger.error(f"[{operation_id}] Error type: {type(e).__name__}")
            return None

    def _extract_enhanced_content(self, image_data: bytes, operation_id: str) -> Optional[str]:
        """
        Extract enhanced content using prebuilt-layout for better table detection.
        
        Args:
            image_data: Raw image bytes
            operation_id: Operation ID for logging
            
        Returns:
            Enhanced content with raw text and structured table data
        """
        try:
            # Encode image data
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            analyze_request = AnalyzeDocumentRequest(bytes_source=encoded_image)
            
            logger.info(f"[{operation_id}] Sending request to Azure Document Intelligence (prebuilt-read)", extra={
                "operation_id": operation_id,
                "model_id": "prebuilt-read",
                "request_size_bytes": len(encoded_image)
            })
            
            # Use prebuilt-read for enhanced table detection
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-read",
                analyze_request=analyze_request
            )
            
            logger.info(f"[{operation_id}] Waiting for Azure read analysis to complete...")
            result = poller.result()
            
            # Extract raw content
            raw_content = ""
            if hasattr(result, 'content') and result.content:
                raw_content = result.content
            
            # Extract table data
            table_data = self._extract_table_data(result, operation_id)
            
            # Combine raw content with structured table data
            enhanced_content = self._format_enhanced_content(raw_content, table_data, operation_id)
            
            # Log extraction results
            extraction_stats = {
                "raw_content_length": len(raw_content),
                "tables_found": len(table_data),
                "enhanced_content_length": len(enhanced_content),
                "has_numbers": bool(re.search(r'\d', enhanced_content)),
                "has_currency": bool(re.search(r'[\$€£¥]', enhanced_content))
            }
            
            logger.info(f"[{operation_id}] Enhanced OCR extraction successful", extra={
                "operation_id": operation_id,
                "success": True,
                **extraction_stats,
                "content_preview": enhanced_content[:300] + "..." if len(enhanced_content) > 300 else enhanced_content
            })
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"[{operation_id}] Enhanced content extraction failed: {str(e)}")
            return None

    def _extract_table_data(self, result: AnalyzeResult, operation_id: str) -> List[Dict[str, Any]]:
        """
        Extract structured table data from Azure analysis result.
        
        Args:
            result: Azure Document Intelligence analysis result
            operation_id: Operation ID for logging
            
        Returns:
            List of structured table data
        """
        tables_data = []
        
        try:
            if hasattr(result, 'tables') and result.tables:
                for table_idx, table in enumerate(result.tables):
                    logger.info(f"[{operation_id}] Processing table {table_idx}: {table.row_count} rows × {table.column_count} columns")
                    
                    # Create table structure
                    table_structure = {
                        "table_index": table_idx,
                        "row_count": table.row_count,
                        "column_count": table.column_count,
                        "cells": []
                    }
                    
                    # Extract cell data
                    for cell in table.cells:
                        cell_data = {
                            "row": cell.row_index,
                            "column": cell.column_index,
                            "content": cell.content.strip() if cell.content else "",
                            "row_span": getattr(cell, 'row_span', 1),
                            "column_span": getattr(cell, 'column_span', 1)
                        }
                        table_structure["cells"].append(cell_data)
                    
                    tables_data.append(table_structure)
                    
                logger.info(f"[{operation_id}] Extracted {len(tables_data)} tables successfully")
            else:
                logger.info(f"[{operation_id}] No tables found in document")
                
        except Exception as e:
            logger.warning(f"[{operation_id}] Error extracting table data: {str(e)}")
            
        return tables_data

    def _format_enhanced_content(self, raw_content: str, tables_data: List[Dict[str, Any]], operation_id: str) -> str:
        """
        Format enhanced content combining raw text with structured table data.
        
        Args:
            raw_content: Raw OCR text
            tables_data: Structured table data
            operation_id: Operation ID for logging
            
        Returns:
            Enhanced formatted content
        """
        try:
            # Start with raw content
            enhanced_content = raw_content
            
            # Add structured table data if available
            if tables_data:
                enhanced_content += "\n\n=== STRUCTURED TABLE DATA ===\n"
                
                for table in tables_data:
                    enhanced_content += f"\n--- Table {table['table_index'] + 1} ({table['row_count']} rows × {table['column_count']} columns) ---\n"
                    
                    # Group cells by row for better formatting
                    rows = {}
                    for cell in table['cells']:
                        row_idx = cell['row']
                        if row_idx not in rows:
                            rows[row_idx] = []
                        rows[row_idx].append(cell)
                    
                    # Format each row
                    for row_idx in sorted(rows.keys()):
                        row_cells = sorted(rows[row_idx], key=lambda x: x['column'])
                        row_content = " | ".join([cell['content'] for cell in row_cells if cell['content']])
                        if row_content.strip():
                            enhanced_content += f"Row {row_idx}: {row_content}\n"
                
                enhanced_content += "=== END STRUCTURED TABLE DATA ===\n"
                
                logger.info(f"[{operation_id}] Enhanced content formatted with {len(tables_data)} tables")
            else:
                logger.info(f"[{operation_id}] No tables to add - using raw content only")
            
            return enhanced_content
            
        except Exception as e:
            logger.warning(f"[{operation_id}] Error formatting enhanced content: {str(e)}")
            return raw_content


# Global OCR service instance
ocr_service = OCRService()