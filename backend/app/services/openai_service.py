import re
from typing import Optional, Dict, Any, List
from openai import OpenAI
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging import get_logger
from app.models.receipt import ReceiptData
from icecream import ic

logger = get_logger(__name__)


class StoreInfo(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None


class BillItem(BaseModel):
    name: str
    quantity: int = 1
    unit_price: float
    total_price: float


class TaxOrCharge(BaseModel):
    name: str
    amount: float


class ReceiptExtraction(BaseModel):
    receipt_number: str = Field(description="Receipt or order number, generate one like 'RCP-001' if missing")
    date: str = Field(description="Date in YYYY-MM-DD format")
    time: str = Field(description="Time in HH:MM format")
    store: StoreInfo
    items: List[BillItem]
    subtotal: float = Field(description="Subtotal before taxes/charges, use 0.00 if not explicitly shown")
    taxes_or_charges: List[TaxOrCharge] = Field(description="All taxes, charges, discounts (use negative amounts for discounts)")
    grand_total: float = Field(description="Final total payable amount - MANDATORY")
    payment_method: str = "Unknown"
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class OpenAIService:
    def __init__(self):
        if not settings.openai_api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OPENAI_API_KEY environment variable must be set")
        self.client = OpenAI(api_key=settings.openai_api_key)

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
            self._log_input_stats(raw_text, operation_id)
            
            logger.info(f"[{operation_id}] Starting OpenAI receipt data extraction", extra={
                "operation_id": operation_id,
                "operation_type": "openai_extract_receipt"
            })
            
            # Extract using structured output
            extraction = self._extract_with_structured_output(raw_text, operation_id)
            if not extraction:
                return None
            
            # Convert to dictionary for validation
            data_dict = extraction.model_dump()
            ic(data_dict)
            
            # Post-process and validate calculations
            try:
                data_dict = self._post_process_and_validate(data_dict, operation_id)
            except ValueError as e:
                logger.error(f"[{operation_id}] Calculation validation failed: {str(e)}", extra={
                    "operation_id": operation_id,
                    "error_type": "calculation_validation_failed"
                })
                return None
            
            # Normalize items: expand any item with quantity > 1 into multiple items with quantity 1
            data_dict["items"] = self._expand_items_to_unit_quantity(data_dict.get("items", []))
            
            # Create ReceiptData object
            receipt_data = ReceiptData(**data_dict)
            
            logger.info(f"[{operation_id}] Successfully created ReceiptData object", extra={
                "operation_id": operation_id,
                "success": True,
                "receipt_number": receipt_data.receipt_number,
                "store_name": receipt_data.store.name,
                "items_count": len(receipt_data.items),
                "grand_total": receipt_data.grand_total
            })
            
            return receipt_data
            
        except Exception as e:
            self._log_extraction_error(e, operation_id)
            return None

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

    def _extract_with_structured_output(self, raw_text: str, operation_id: str) -> Optional[ReceiptExtraction]:
        """
        Core LLM extraction method using OpenAI's structured output.
        
        Args:
            raw_text: Raw text from OCR
            operation_id: Operation ID for logging
            
        Returns:
            ReceiptExtraction object or None if extraction fails
        """
        try:
            system_prompt = """You are a receipt data extraction expert. Extract information from receipt text with these rules:

CRITICAL EXTRACTION RULES:
1. The grand_total field is MANDATORY - it must be the FINAL amount payable from the receipt
2. Extract ALL taxes, charges, service charges, discounts, and fees into the taxes_or_charges array
3. For discounts, use NEGATIVE amounts in taxes_or_charges (e.g., {"name": "Discount", "amount": -5.00})
4. For subtotal: If explicitly shown on receipt, use that value; otherwise set to 0.00 (DO NOT calculate)
5. Do NOT perform any calculations - only extract amounts exactly as shown on the receipt
6. Ensure items have quantity, unit_price, and total_price fields
7. The grand_total is the authoritative final amount - taxes may already be included in this amount

STRUCTURED TABLE DATA USAGE:
8. If the text contains "=== STRUCTURED TABLE DATA ===" section, check if the table rows contain well-aligned item information
9. Use structured table data ONLY if it clearly shows items with quantities, prices, and totals that align with the raw text
10. If table data is misaligned, incomplete, or doesn't match the receipt items, ignore the table section and use only the raw text
11. Tables should help identify which items belong together and their correct quantities/prices
12. Always cross-reference table data with the raw text to ensure accuracy
Strictly return in this format:
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
}} in JSON format, no other text or markdown formatting or explanations.
"""

            user_prompt = f"""Extract receipt data from this text (which may include both raw OCR text and structured table data):

{raw_text}

Extract all the information according to the schema provided."""
            
            # Log API call
            logger.info(f"[{operation_id}] Sending structured output request to OpenAI", extra={
                "operation_id": operation_id,
                "model": "gpt-4o",
            })

            completion = self.client.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=ReceiptExtraction,
            )

            # Log API response
            self._log_api_response(completion, operation_id)
            
            if not completion.choices[0].message.parsed:
                logger.error(f"[{operation_id}] OpenAI returned no parsed data")
                return None
            
            extraction = completion.choices[0].message.parsed
            
            logger.info(f"[{operation_id}] Successfully extracted structured data", extra={
                "operation_id": operation_id,
                "items_count": len(extraction.items),
                "grand_total": extraction.grand_total,
                "store_name": extraction.store.name
            })
            
            return extraction
            
        except Exception as e:
            logger.error(f"[{operation_id}] OpenAI structured extraction failed: {str(e)}", extra={
                "operation_id": operation_id,
                "error_type": type(e).__name__
            })
            return None

    def _convert_to_receipt_data(self, extraction: ReceiptExtraction) -> ReceiptData:
        """Convert ReceiptExtraction to ReceiptData format."""
        # Convert to dictionary format expected by ReceiptData
        data_dict = {
            "receipt_number": extraction.receipt_number,
            "date": extraction.date,
            "time": extraction.time,
            "store": {
                "name": extraction.store.name,
                "address": extraction.store.address,
                "phone": extraction.store.phone
            },
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in extraction.items
            ],
            "subtotal": extraction.subtotal,
            "taxes_or_charges": [
                {
                    "name": tax_charge.name,
                    "amount": tax_charge.amount
                }
                for tax_charge in extraction.taxes_or_charges
            ],
            "grand_total": extraction.grand_total,
            "payment_method": extraction.payment_method,
            "transaction_id": extraction.transaction_id,
            "notes": extraction.notes
        }
        
        return ReceiptData(**data_dict)

    def _expand_items_to_unit_quantity(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Expand items so that each resulting item has quantity == 1.
        Distribute totals per unit and adjust the last item's total to account for rounding.
        """
        expanded: List[Dict[str, Any]] = []
        for item in items:
            try:
                name = item.get("name")
                quantity = int(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", 0.0))
                total = float(item.get("total_price", item.get("total", 0.0)))

                if quantity <= 1:
                    expanded.append({
                        "name": name,
                        "quantity": 1,
                        "unit_price": unit_price,
                        "total_price": total if quantity == 1 else (total if total > 0 else unit_price)
                    })
                    continue

                # Compute per-unit values
                per_unit_total = round(total / quantity, 2) if total > 0 and quantity > 0 else round(unit_price, 2)
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
                last_total = max(round(total - accumulated, 2) if total > 0 else per_unit_total, 0)

                expanded.append({
                    "name": name,
                    "quantity": 1,
                    "unit_price": per_unit_price,
                    "total_price": last_total
                })
            except Exception:
                # Fallback to single quantity=1 item
                expanded.append({
                    "name": item.get("name"),
                    "quantity": 1,
                    "unit_price": item.get("unit_price", 0.0),
                    "total_price": item.get("total_price", item.get("total", item.get("unit_price", 0.0)))
                })

        return expanded

    def _post_process_and_validate(self, data: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """
        Post-process extracted data using the dedicated validation service.
        
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

    def _log_input_stats(self, raw_text: str, operation_id: str) -> None:
        """Log input statistics for analysis."""
        input_stats = {
            "text_length_chars": len(raw_text),
            "text_length_words": len(raw_text.split()),
            "text_lines": len(raw_text.splitlines()),
            "has_numbers": bool(re.search(r'\d', raw_text)),
            "has_currency_symbols": bool(re.search(r'[\$€£¥]', raw_text)),
            "has_dates": bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', raw_text))
        }
        
        logger.info(f"[{operation_id}] Input analysis", extra={
            "operation_id": operation_id,
            **input_stats,
            "text_preview": raw_text[:300] + "..." if len(raw_text) > 300 else raw_text
        })

    def _log_api_response(self, completion, operation_id: str) -> None:
        """Log API response details for structured output."""
        response_stats = {
            "tokens_used": {
                "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                "total_tokens": completion.usage.total_tokens if completion.usage else 0
            },
            "model_used": completion.model,
            "finish_reason": completion.choices[0].finish_reason,
            "parsed_successfully": completion.choices[0].message.parsed is not None
        }
        
        logger.info(f"[{operation_id}] Received OpenAI structured response", extra={
            "operation_id": operation_id,
            **response_stats
        })

    def _log_extraction_error(self, error: Exception, operation_id: str) -> None:
        """Log extraction errors with categorization."""
        error_details = {
            "operation_id": operation_id,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        # Categorize error
        error_str = str(error).lower()
        if "api" in error_str or "openai" in error_str:
            error_details["error_category"] = "api_error"
        elif "quota" in error_str or "limit" in error_str:
            error_details["error_category"] = "quota_exceeded"
        elif "network" in error_str or "connection" in error_str:
            error_details["error_category"] = "network_error"
        else:
            error_details["error_category"] = "unknown"
        
        logger.error(f"[{operation_id}] OpenAI extraction failed", extra=error_details)


# Global OpenAI service instance
openai_service = OpenAIService()