import json
import os
from typing import Optional, Dict, Any
from openai import OpenAI
from ..core.config import settings
from ..core.logging import get_logger
from ..models.receipt import ReceiptData

logger = get_logger(__name__)


class OpenAIService:
    def __init__(self):
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
            template = """
{
  "receipt_number": "Unique identifier for the receipt (e.g., RCP-2023-001)",
  "date": "Date of purchase (YYYY-MM-DD)",
  "time": "Time of purchase (HH:MM)",
  "store": {
    "name": "Name of the store or restaurant",
    "address": "Address of the store",
    "phone": "Contact phone number of the store"
  },
  "items": [
    {
      "name": "Name of the purchased item (e.g., 'Burger', 'Milk')",
      "quantity": "Number of units purchased",
      "unit_price": "Price per unit" (in whichever currency),
      "total": "Calculated total for this line (quantity × unit_price)"
    }
  ],
  "subtotal": "Sum of all item totals before tax or discounts",
  "tax": "Applicable tax amount (e.g., VAT, sales tax)",
  "service_charge": "Applicable service charge",
  "discount": "Any discount applied (if any)",
  "total_amount": "Final total after tax and discounts",
  "payment_method": "Mode of payment (e.g., Cash, Credit Card, Mobile Payment)",
  "transaction_id": "Transaction or reference number from the payment system",
  "notes": "Optional additional notes (e.g., 'Thank you for shopping!')"
}
"""

            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Your task is to create a JSON that follows a template based on my raw text invoice. Strictly return the JSON only, no explanation or trailing word."
                    },
                    {
                        "role": "user",
                        "content": f"Here's the template that you should follow: {template}"
                    },
                    {
                        "role": "user",
                        "content": f"Here's the raw extracted text: {raw_text}"
                    }
                ]
            )

            response_text = completion.choices[0].message.content
            logger.info("Successfully extracted receipt data using OpenAI")
            
            # Parse the JSON response
            receipt_data = json.loads(response_text)
            return ReceiptData(**receipt_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from OpenAI: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error extracting receipt data: {str(e)}")
            return None

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
                if not item.name or item.quantity <= 0 or item.unit_price <= 0:
                    logger.warning(f"Invalid item data: {item}")
                    return False
                    
            logger.info("Receipt data validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error validating receipt data: {str(e)}")
            return False


# Global OpenAI service instance
openai_service = OpenAIService()
