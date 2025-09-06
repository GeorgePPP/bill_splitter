import json
import os
import re
from typing import Optional, Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.core.logging import get_logger
from app.models.receipt import ReceiptData

logger = get_logger(__name__)


class OpenAIService:
    def __init__(self):
        if not settings.openai_api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def extract_receipt_data(self, raw_text: str) -> Optional[ReceiptData]:
        """
        Extract structured receipt data from raw OCR text using OpenAI.
        
        Args:
            raw_text: Raw text extracted from OCR
            
        Returns:
            Structured receipt data or None if extraction fails
        """
        try:
            logger.info(f"Starting OpenAI extraction for text of length: {len(raw_text)}")
            
            # Improved prompt for better JSON generation
            system_prompt = """You are a receipt data extraction expert. Extract information from receipt text and return ONLY a valid JSON object with no additional text, markdown formatting, or explanations. The JSON must be properly formatted and parseable."""
            
            user_prompt = f"""Extract receipt data from this text and return as JSON with this exact structure:

{{
  "receipt_number": "Receipt or order number (or generate one like 'RCP-001' if missing)",
  "date": "Date in YYYY-MM-DD format",
  "time": "Time in HH:MM format",
  "store": {{
    "name": "Store/restaurant name",
    "address": "Store address (or null if not found)",
    "phone": "Store phone (or null if not found)"
  }},
  "items": [
    {{
      "name": "Item name",
      "quantity": 1,
      "unit_price": 0.00,
      "total": 0.00
    }}
  ],
  "subtotal": 0.00,
  "tax": 0.00,
  "service_charge": 0.00,
  "discount": 0.00,
  "total_amount": 0.00,
  "payment_method": "Payment method (or 'Unknown')",
  "transaction_id": "Transaction ID (or null)",
  "notes": "Any additional notes (or null)"
}}

Receipt text:
{raw_text}

Return only the JSON object:"""

            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Lower temperature for more consistent output
                max_tokens=2000
            )

            response_text = completion.choices[0].message.content
            logger.info(f"Received OpenAI response of length: {len(response_text) if response_text else 0}")
            
            if not response_text:
                logger.error("OpenAI returned empty response")
                return None
            
            # Log the raw response for debugging
            logger.debug(f"Raw OpenAI response: {response_text[:500]}...")
            
            # Clean the response - remove markdown formatting if present
            cleaned_response = self._clean_json_response(response_text)
            
            # Parse the JSON response
            receipt_data_dict = json.loads(cleaned_response)
            logger.info("Successfully parsed JSON response from OpenAI")
            
            # Validate the structure before creating ReceiptData
            if not self._validate_json_structure(receipt_data_dict):
                logger.error("Invalid JSON structure received from OpenAI")
                return None
            
            # Create ReceiptData object
            receipt_data = ReceiptData(**receipt_data_dict)
            logger.info("Successfully created ReceiptData object")
            
            return receipt_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from OpenAI: {str(e)}")
            logger.error(f"Response that failed to parse: {response_text[:1000] if response_text else 'None'}")
            return None
        except Exception as e:
            logger.error(f"Error extracting receipt data: {str(e)}")
            logger.error(f"Response: {response_text[:500] if 'response_text' in locals() else 'No response'}")
            return None

    def _clean_json_response(self, response: str) -> str:
        """
        Clean the OpenAI response to extract valid JSON.
        
        Args:
            response: Raw response from OpenAI
            
        Returns:
            Cleaned JSON string
        """
        try:
            # Remove markdown code blocks if present
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*$', '', response)
            
            # Remove any leading/trailing whitespace
            response = response.strip()
            
            # Try to find JSON object boundaries
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                response = response[start_idx:end_idx + 1]
            
            return response
            
        except Exception as e:
            logger.error(f"Error cleaning JSON response: {str(e)}")
            return response

    def _validate_json_structure(self, data: Dict[str, Any]) -> bool:
        """
        Validate that the JSON has required fields.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if structure is valid, False otherwise
        """
        try:
            required_fields = ['receipt_number', 'date', 'time', 'store', 'items', 'total_amount']
            
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate store structure
            if not isinstance(data['store'], dict) or 'name' not in data['store']:
                logger.warning("Invalid store structure")
                return False
            
            # Validate items structure
            if not isinstance(data['items'], list) or len(data['items']) == 0:
                logger.warning("Invalid or empty items list")
                return False
            
            # Validate each item
            for item in data['items']:
                if not isinstance(item, dict):
                    logger.warning("Item is not a dictionary")
                    return False
                item_required = ['name', 'quantity', 'unit_price', 'total']
                for field in item_required:
                    if field not in item:
                        logger.warning(f"Item missing required field: {field}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating JSON structure: {str(e)}")
            return False

    def validate_receipt_data(self, receipt_data: ReceiptData) -> bool:
        """
        Validate the extracted receipt data for completeness and accuracy.
        
        Args:
            receipt_data: The extracted receipt data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check if essential fields are present
            if not receipt_data.items or len(receipt_data.items) == 0:
                logger.warning("No items found in receipt data")
                return False
                
            if receipt_data.total_amount <= 0:
                logger.warning("Invalid total amount in receipt data")
                return False
                
            # Validate item data
            for item in receipt_data.items:
                if not item.name or item.quantity <= 0 or item.unit_price < 0:
                    logger.warning(f"Invalid item data: {item}")
                    return False
                    
            logger.info("Receipt data validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error validating receipt data: {str(e)}")
            return False


    def extract_receipt_data_as_schema(self, raw_text: str) -> Optional['ReceiptDataSchema']:
        """
        Extract structured receipt data and return as schema object.
        
        Args:
            raw_text: Raw text extracted from OCR
            
        Returns:
            ReceiptDataSchema object or None if extraction fails
        """
        try:
            # First get the ReceiptData model
            receipt_data = self.extract_receipt_data(raw_text)
            if not receipt_data:
                return None
            
            # Import here to avoid circular imports
            from app.schemas.receipt_schema import ReceiptDataSchema, StoreInfoSchema, BillItemSchema
            
            # Convert to schema
            return ReceiptDataSchema(
                receipt_number=receipt_data.receipt_number,
                date=receipt_data.date,
                time=receipt_data.time,
                store=StoreInfoSchema(
                    name=receipt_data.store.name,
                    address=receipt_data.store.address,
                    phone=receipt_data.store.phone
                ),
                items=[
                    BillItemSchema(
                        name=item.name,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total=item.total
                    )
                    for item in receipt_data.items
                ],
                subtotal=receipt_data.subtotal,
                tax=receipt_data.tax,
                service_charge=receipt_data.service_charge,
                discount=receipt_data.discount,
                total_amount=receipt_data.total_amount,
                payment_method=receipt_data.payment_method,
                transaction_id=receipt_data.transaction_id,
                notes=receipt_data.notes
            )
            
        except Exception as e:
            logger.error(f"Error converting receipt data to schema: {str(e)}")
            return None


# Global OpenAI service instance
openai_service = OpenAIService()