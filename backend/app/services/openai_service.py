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

    def extract_receipt_data_raw(self, raw_text: str) -> Optional[ReceiptData]:
        """
        Extract structured receipt data from raw OCR text using OpenAI WITHOUT any validation.
        This method only does LLM extraction and parsing - no calculations or validation.
        
        Args:
            raw_text: Raw text extracted from OCR
            
        Returns:
            Raw structured receipt data or None if extraction fails
        """
        operation_id = f"openai_extract_raw_{hash(raw_text) % 10000}"
        
        try:
            logger.info(f"[{operation_id}] Starting RAW OpenAI extraction (no validation)", extra={
                "operation_id": operation_id,
                "text_length": len(raw_text)
            })
            
            # Get raw JSON data from OpenAI
            json_data = self._extract_json_from_openai(raw_text, operation_id)
            if not json_data:
                logger.error(f"[{operation_id}] Failed to extract JSON data from OpenAI")
                return None
            
            # Convert directly to ReceiptData object WITHOUT validation
            receipt_data = ReceiptData(**json_data)
            
            logger.info(f"[{operation_id}] RAW extraction successful", extra={
                "operation_id": operation_id,
                "store_name": receipt_data.store.name,
                "items_count": len(receipt_data.items),
                "grand_total": receipt_data.grand_total
            })
            
            return receipt_data
            
        except Exception as e:
            logger.error(f"[{operation_id}] Error in raw extraction: {str(e)}")
            return None

    def extract_receipt_data(self, raw_text: str) -> Optional[ReceiptData]:
        """
        Extract structured receipt data from raw OCR text using OpenAI WITH validation.
        
        Args:
            raw_text: Raw text extracted from OCR
            
        Returns:
            Validated structured receipt data or None if extraction fails
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
            
            # Improved prompt for better JSON generation according to new requirements
            system_prompt = """You are a receipt data extraction expert. Extract information from receipt text and return ONLY a valid JSON object with no additional text, markdown formatting, or explanations. The JSON must be properly formatted and parseable. The grand_total field is MANDATORY and must be extracted from the receipt."""
            
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
      "total_price": 0.00
    }}
  ],
  "subtotal": 0.00,
  "taxes_or_charges": [
    {{
      "name": "Tax/charge name (e.g., GST, Service Charge, VAT)",
      "amount": 0.00
    }}
  ],
  "grand_total": 0.00,
  "payment_method": "Payment method (or 'Unknown')",
  "transaction_id": "Transaction ID (or null)",
  "notes": "Any additional notes (or null)"
}}

CRITICAL EXTRACTION RULES:
1. The grand_total field is MANDATORY - it must be the FINAL amount payable/total amount/amount payable from the receipt
2. Extract ALL taxes, charges, service charges, and fees into the taxes_or_charges array
3. For subtotal extraction:
   - If "Subtotal", "Amount before tax", "Net amount", or similar is explicitly shown, use that value
   - If NOT explicitly shown, set subtotal to 0.00 (DO NOT calculate it yourself)
   - Look for terms like: "Subtotal", "Sub Total", "Amount Before Tax", "Net Amount", "Before Tax", "Taxable Amount"
4. Do NOT perform any calculations - only extract amounts exactly as shown on the receipt
5. Ensure items have quantity, unit_price, and total_price fields
6. The grand_total is the authoritative final amount - taxes may already be included in this amount

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
                "grand_total": receipt_data_dict.get("grand_total", 0),
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
            
            # Post-process and validate calculations
            try:
                receipt_data_dict = self._post_process_and_validate(receipt_data_dict, operation_id)
            except ValueError as e:
                logger.error(f"[{operation_id}] Calculation validation failed: {str(e)}", extra={
                    "operation_id": operation_id,
                    "error_type": "calculation_validation_failed"
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
                "grand_total": receipt_data.grand_total
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
        Validate that the JSON has required fields according to new structure.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if structure is valid, False otherwise
        """
        try:
            required_fields = ['receipt_number', 'date', 'time', 'store', 'items', 'grand_total', 'subtotal']
            
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
                item_required = ['name', 'quantity', 'unit_price', 'total_price']
                for field in item_required:
                    if field not in item:
                        logger.warning(f"Item missing required field: {field}")
                        return False
            
            # Validate taxes_or_charges structure if present
            if 'taxes_or_charges' in data:
                if not isinstance(data['taxes_or_charges'], list):
                    logger.warning("taxes_or_charges is not a list")
                    return False
                for tax_charge in data['taxes_or_charges']:
                    if not isinstance(tax_charge, dict):
                        logger.warning("Tax/charge item is not a dictionary")
                        return False
                    if 'name' not in tax_charge or 'amount' not in tax_charge:
                        logger.warning("Tax/charge missing required fields (name, amount)")
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
                
            if receipt_data.grand_total <= 0:
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


    def extract_receipt_data_as_schema(self, raw_text: str) -> Optional[Dict[str, Any]]:
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
            from app.schemas.receipt_schema import ReceiptDataSchema, StoreInfoSchema, BillItemSchema, TaxOrChargeSchema
            
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
                        total_price=item.total_price
                    )
                    for item in receipt_data.items
                ],
                subtotal=receipt_data.subtotal,
                taxes_or_charges=[
                    TaxOrChargeSchema(
                        name=tax_charge.name,
                        amount=tax_charge.amount,
                        percent=tax_charge.percent
                    )
                    for tax_charge in receipt_data.taxes_or_charges
                ],
                grand_total=receipt_data.grand_total,
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
                total = float(item.get("total_price", item.get("total", 0.0)))

                if quantity <= 1:
                    # Ensure quantity is exactly 1
                    expanded.append({
                        "name": name,
                        "quantity": 1,
                        "unit_price": unit_price,
                        "total_price": total if quantity == 1 else (total if total > 0 else unit_price)
                    })
                    continue

                # Compute per-unit total
                if quantity > 0:
                    per_unit_total = round(total / quantity, 2) if total > 0 else round(unit_price, 2)
                else:
                    per_unit_total = round(unit_price, 2)

                # Set per-unit price equal to per-unit total to ensure total_price == quantity * unit_price validation
                per_unit_price = per_unit_total

                # Add quantity-1 items with per-unit values
                for _ in range(max(quantity - 1, 0)):
                    expanded.append({
                        "name": name,
                        "quantity": 1,
                        "unit_price": per_unit_price,
                        "total_price": per_unit_total
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
                    "total_price": last_total
                })
            except Exception:
                # On any parsing error, fallback to a single quantity=1 item best-effort
                expanded.append({
                    "name": item.get("name"),
                    "quantity": 1,
                    "unit_price": item.get("unit_price", 0.0),
                    "total_price": item.get("total_price", item.get("total", item.get("unit_price", 0.0)))
                })

        return expanded

    def _extract_json_from_openai(self, raw_text: str, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON data from OpenAI without any validation or post-processing.
        ONLY does LLM extraction and JSON parsing.
        """
        try:
            # Improved prompt for better JSON generation according to new requirements
            system_prompt = """You are a receipt data extraction expert. Extract information from receipt text and return ONLY a valid JSON object with no additional text, markdown formatting, or explanations. At any time, do not calculate anything, just extract"""
            
            user_prompt = f"""Extract receipt data from this text and return as JSON with this exact structure:

{{
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
      "unit_price": "Price per unit" (this or total must be provided),
      "total": "Total price for this item" (this or total must be provided),
    }
  ],
  "subtotal": "Sum of all item totals before tax or discounts" (this is optional and do not need your calculation),
  "taxes_or_charges": [
    {{
      "name": "Tax/charge name (e.g., GST, Service Charge, VAT)",
      "amount": 0.00
    }}
  ],
  "discount": "Any discount applied (if any)",
  "grand_total": "Final total payable", (this must be the final amount payable from the receipt) 
  "payment_method": "Mode of payment (e.g., Cash, Credit Card, Mobile Payment)",
  "transaction_id": "Transaction or reference number from the payment system",
  "notes": "Optional additional notes (e.g., 'Thank you for shopping!')",
}}

CRITICAL EXTRACTION RULES:
1. The grand_total field is MANDATORY - it must be the FINAL amount payable/total amount/amount payable from the receipt
2. Extract ALL taxes, charges, service charges, and fees into the taxes_or_charges array
3. For subtotal extraction:
   - If "Subtotal", "Amount before tax", "Net amount", or similar is explicitly shown, use that value
   - If NOT explicitly shown, set subtotal to 0.00 (DO NOT calculate it yourself)
   - Look for terms like: "Subtotal", "Sub Total", "Amount Before Tax", "Net Amount", "Before Tax", "Taxable Amount"
4. Do NOT perform any calculations - only extract amounts exactly as shown on the receipt
5. Ensure items have quantity, unit_price, and total_price fields
6. The grand_total is the authoritative final amount - taxes may already be included in this amount

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
                model="gpt-4o-mini",
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
                logger.error(f"[{operation_id}] OpenAI returned empty response")
                return None
            
            # Clean the response - remove markdown formatting if present
            cleaned_response = self._clean_json_response(response_text)
            
            # Parse JSON
            try:
                json_data = json.loads(cleaned_response)
                logger.info(f"[{operation_id}] Successfully parsed JSON response")
                return json_data
            except json.JSONDecodeError as e:
                logger.error(f"[{operation_id}] JSON parsing failed: {str(e)}")
                logger.error(f"[{operation_id}] Raw response: {cleaned_response}")
                return None
                
        except Exception as e:
            logger.error(f"[{operation_id}] OpenAI API call failed: {str(e)}")
            return None

    def _post_process_and_validate(self, data: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """
        Post-process extracted data using the dedicated validation service.
        OpenAI service now only handles LLM extraction and parsing.
        
        Args:
            data: Extracted receipt data dictionary
            operation_id: Operation ID for logging
            
        Returns:
            Validated and corrected data dictionary
            
        Raises:
            ValueError: If calculations cannot be reconciled
        """
        from app.services.receipt_validator import receipt_validator_service
        
        logger.info(f"[{operation_id}] Delegating validation to receipt validator service", extra={
            "operation_id": operation_id,
            "step": "delegate_validation"
        })
        
        return receipt_validator_service.validate_and_process_receipt(data, operation_id)

# Global OpenAI service instance
openai_service = OpenAIService()