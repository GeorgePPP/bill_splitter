import json
import os
import re
from typing import Optional, Dict, Any, List
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
        operation_id = f"openai_extract_{hash(raw_text) % 10000}"
        
        try:
            # Log input analysis
            input_stats = {
                "text_length_chars": len(raw_text),
                "text_length_words": len(raw_text.split()),
                "text_lines": len(raw_text.splitlines()),
                "has_numbers": bool(re.search(r'\d', raw_text)),
                "has_currency_symbols": bool(re.search(r'[\$€£¥]', raw_text)),
                "has_dates": bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', raw_text))
            }
            
            logger.info(f"[{operation_id}] Starting OpenAI receipt data extraction", extra={
                "operation_id": operation_id,
                "operation_type": "openai_extract_receipt",
                **input_stats,
                "text_preview": raw_text[:300] + "..." if len(raw_text) > 300 else raw_text
            })
            
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

            # Log API call details
            api_call_info = {
                "model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens": 2000,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt)
            }
            
            logger.info(f"[{operation_id}] Sending request to OpenAI", extra={
                "operation_id": operation_id,
                **api_call_info
            })

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
            
            # Log API response details
            response_stats = {
                "response_length": len(response_text) if response_text else 0,
                "tokens_used": {
                    "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if completion.usage else 0
                },
                "model_used": completion.model,
                "finish_reason": completion.choices[0].finish_reason
            }
            
            logger.info(f"[{operation_id}] Received OpenAI response", extra={
                "operation_id": operation_id,
                **response_stats,
                "response_preview": response_text[:300] + "..." if response_text and len(response_text) > 300 else response_text
            })
            
            if not response_text:
                logger.error(f"[{operation_id}] OpenAI returned empty response", extra={
                    "operation_id": operation_id,
                    "error_type": "empty_response"
                })
                return None
            
            # Clean the response - remove markdown formatting if present
            cleaned_response = self._clean_json_response(response_text)
            
            logger.debug(f"[{operation_id}] Cleaned JSON response", extra={
                "operation_id": operation_id,
                "original_length": len(response_text),
                "cleaned_length": len(cleaned_response),
                "cleaning_applied": response_text != cleaned_response
            })
            
            # Parse the JSON response
            receipt_data_dict = json.loads(cleaned_response)
            
            # Log parsed JSON structure
            json_structure_info = {
                "json_keys": list(receipt_data_dict.keys()),
                "items_count": len(receipt_data_dict.get("items", [])),
                "store_info_present": "store" in receipt_data_dict and isinstance(receipt_data_dict["store"], dict),
                "total_amount": receipt_data_dict.get("total_amount", 0),
                "has_tax": receipt_data_dict.get("tax", 0) > 0,
                "has_service_charge": receipt_data_dict.get("service_charge", 0) > 0,
                "has_discount": receipt_data_dict.get("discount", 0) > 0
            }
            
            logger.info(f"[{operation_id}] Successfully parsed JSON response", extra={
                "operation_id": operation_id,
                **json_structure_info,
                "parsed_data_preview": {k: v for k, v in list(receipt_data_dict.items())[:5]}
            })
            
            # Validate the structure before creating ReceiptData
            if not self._validate_json_structure(receipt_data_dict):
                logger.error(f"[{operation_id}] Invalid JSON structure received", extra={
                    "operation_id": operation_id,
                    "error_type": "invalid_json_structure",
                    "received_keys": list(receipt_data_dict.keys())
                })
                return None
            
            # Normalize items: expand any item with quantity > 1 into multiple items with quantity 1
            try:
                original_items = receipt_data_dict.get("items", [])
                expanded_items = self._expand_items_to_unit_quantity(original_items)
                receipt_data_dict["items"] = expanded_items
                logger.info(
                    f"[{operation_id}] Expanded items to unit quantity",
                    extra={
                        "operation_id": operation_id,
                        "original_items_count": len(original_items),
                        "expanded_items_count": len(expanded_items)
                    }
                )
            except Exception as e:
                logger.warning(
                    f"[{operation_id}] Failed to expand items to unit quantity: {str(e)}",
                    extra={"operation_id": operation_id}
                )
            
            # Create ReceiptData object
            receipt_data = ReceiptData(**receipt_data_dict)
            
            logger.info(f"[{operation_id}] Successfully created ReceiptData object", extra={
                "operation_id": operation_id,
                "success": True,
                "receipt_number": receipt_data.receipt_number,
                "store_name": receipt_data.store.name,
                "items_count": len(receipt_data.items),
                "total_amount": receipt_data.total_amount
            })
            
            return receipt_data
            
        except json.JSONDecodeError as e:
            error_details = {
                "operation_id": operation_id,
                "error_type": "json_decode_error",
                "error_message": str(e),
                "error_line": getattr(e, 'lineno', None),
                "error_column": getattr(e, 'colno', None),
                "response_length": len(response_text) if 'response_text' in locals() else 0
            }
            
            logger.error(f"[{operation_id}] Failed to parse JSON response", extra={
                **error_details,
                "failed_response": response_text[:1000] + "..." if 'response_text' in locals() and len(response_text) > 1000 else response_text if 'response_text' in locals() else None
            })
            return None
            
        except Exception as e:
            error_details = {
                "operation_id": operation_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
            
            # Add specific error context
            if "api" in str(e).lower() or "openai" in str(e).lower():
                error_details["error_category"] = "api_error"
            elif "quota" in str(e).lower() or "limit" in str(e).lower():
                error_details["error_category"] = "quota_exceeded"
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                error_details["error_category"] = "network_error"
            else:
                error_details["error_category"] = "unknown"
            
            logger.error(f"[{operation_id}] OpenAI extraction failed", extra={
                **error_details,
                "response_available": 'response_text' in locals(),
                "response_preview": response_text[:500] if 'response_text' in locals() else None
            })
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


    def _expand_items_to_unit_quantity(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Expand items so that each resulting item has quantity == 1.
        Distribute totals per unit and adjust the last item's total to account for rounding.
        
        Args:
            items: List of item dicts with keys name, quantity, unit_price, total
        
        Returns:
            New list of items where all items have quantity == 1
        """
        expanded: List[Dict[str, Any]] = []
        for item in items:
            try:
                name = item.get("name")
                quantity = int(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", 0.0))
                total = float(item.get("total", 0.0))

                if quantity <= 1:
                    # Ensure quantity is exactly 1
                    expanded.append({
                        "name": name,
                        "quantity": 1,
                        "unit_price": unit_price,
                        "total": total if quantity == 1 else (total if total > 0 else unit_price)
                    })
                    continue

                # Compute per-unit total
                if quantity > 0:
                    per_unit_total = round(total / quantity, 2) if total > 0 else round(unit_price, 2)
                else:
                    per_unit_total = round(unit_price, 2)

                # Set per-unit price equal to per-unit total to ensure total == quantity * unit_price validation
                per_unit_price = per_unit_total

                # Add quantity-1 items with per-unit values
                for _ in range(max(quantity - 1, 0)):
                    expanded.append({
                        "name": name,
                        "quantity": 1,
                        "unit_price": per_unit_price,
                        "total": per_unit_total
                    })

                # Last item gets the remainder to preserve the original total
                accumulated = round(per_unit_total * (quantity - 1), 2)
                last_total = round(total - accumulated, 2) if total > 0 else per_unit_total
                # Guard against negative due to weird inputs
                if last_total < 0:
                    last_total = per_unit_total

                expanded.append({
                    "name": name,
                    "quantity": 1,
                    "unit_price": per_unit_price,
                    "total": last_total
                })
            except Exception:
                # On any parsing error, fallback to a single quantity=1 item best-effort
                expanded.append({
                    "name": item.get("name"),
                    "quantity": 1,
                    "unit_price": item.get("unit_price", 0.0),
                    "total": item.get("total", item.get("unit_price", 0.0))
                })

        return expanded

# Global OpenAI service instance
openai_service = OpenAIService()