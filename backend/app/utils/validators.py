import re
from typing import List, Optional, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)


class Validators:
    def __init__(self):
        pass

    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        try:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
        except Exception as e:
            logger.error(f"Error validating email {email}: {str(e)}")
            return False

    def validate_phone(self, phone: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if phone is valid, False otherwise
        """
        try:
            # Remove all non-digit characters
            digits_only = re.sub(r'\D', '', phone)
            # Check if it has 10-15 digits (international format)
            return 10 <= len(digits_only) <= 15
        except Exception as e:
            logger.error(f"Error validating phone {phone}: {str(e)}")
            return False

    def validate_name(self, name: str) -> bool:
        """
        Validate person name.
        
        Args:
            name: Name to validate
            
        Returns:
            True if name is valid, False otherwise
        """
        try:
            # Name should be non-empty and contain only letters, spaces, hyphens, and apostrophes
            if not name or not name.strip():
                return False
            pattern = r"^[a-zA-Z\s\-']+$"
            return bool(re.match(pattern, name.strip()))
        except Exception as e:
            logger.error(f"Error validating name {name}: {str(e)}")
            return False

    def validate_currency_amount(self, amount: str) -> Tuple[bool, Optional[float]]:
        """
        Validate and parse currency amount.
        
        Args:
            amount: Currency amount string to validate
            
        Returns:
            Tuple of (is_valid, parsed_amount)
        """
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[^\d.,]', '', amount.strip())
            
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # Both comma and dot present - assume comma is thousands separator
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Only comma - could be decimal separator
                if cleaned.count(',') == 1 and len(cleaned.split(',')[1]) <= 2:
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            
            parsed_amount = float(cleaned)
            return parsed_amount >= 0, parsed_amount if parsed_amount >= 0 else None
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Error validating currency amount {amount}: {str(e)}")
            return False, None

    def validate_quantity(self, quantity: str) -> Tuple[bool, Optional[int]]:
        """
        Validate and parse quantity.
        
        Args:
            quantity: Quantity string to validate
            
        Returns:
            Tuple of (is_valid, parsed_quantity)
        """
        try:
            parsed_quantity = int(quantity)
            return parsed_quantity > 0, parsed_quantity if parsed_quantity > 0 else None
        except (ValueError, TypeError) as e:
            logger.error(f"Error validating quantity {quantity}: {str(e)}")
            return False, None

    def validate_receipt_data(self, receipt_data: dict) -> Tuple[bool, List[str]]:
        """
        Validate receipt data structure and content.
        
        Args:
            receipt_data: Receipt data dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            errors = []
            
            # Check required fields
            required_fields = ["receipt_number", "date", "time", "store", "items", "grand_total"]
            for field in required_fields:
                if field not in receipt_data:
                    errors.append(f"Missing required field: {field}")
            
            # Validate store information
            if "store" in receipt_data:
                store = receipt_data["store"]
                if not isinstance(store, dict):
                    errors.append("Store information must be an object")
                else:
                    if "name" not in store or not store["name"]:
                        errors.append("Store name is required")
            
            # Validate items
            if "items" in receipt_data:
                items = receipt_data["items"]
                if not isinstance(items, list) or len(items) == 0:
                    errors.append("At least one item is required")
                else:
                    for i, item in enumerate(items):
                        if not isinstance(item, dict):
                            errors.append(f"Item {i+1} must be an object")
                            continue
                        
                        required_item_fields = ["name", "quantity", "unit_price", "total"]
                        for field in required_item_fields:
                            if field not in item:
                                errors.append(f"Item {i+1} missing required field: {field}")
                        
                        # Validate item values
                        if "quantity" in item and (not isinstance(item["quantity"], int) or item["quantity"] <= 0):
                            errors.append(f"Item {i+1} quantity must be a positive integer")
                        
                        if "unit_price" in item and (not isinstance(item["unit_price"], (int, float)) or item["unit_price"] < 0):
                            errors.append(f"Item {i+1} unit price must be a non-negative number")
                        
                        if "total" in item and (not isinstance(item["total"], (int, float)) or item["total"] < 0):
                            errors.append(f"Item {i+1} total must be a non-negative number")
            
            # Validate total amount
            if "grand_total" in receipt_data:
                total = receipt_data["grand_total"]
                if not isinstance(total, (int, float)) or total < 0:
                    errors.append("Total amount must be a non-negative number")
            
            is_valid = len(errors) == 0
            logger.info(f"Receipt data validation completed: {len(errors)} errors found")
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating receipt data: {str(e)}")
            return False, [f"Validation error: {str(e)}"]


# Global validators instance
validators = Validators()
