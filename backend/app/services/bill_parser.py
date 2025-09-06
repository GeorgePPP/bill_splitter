from typing import List, Dict, Any
from ..models.receipt import ReceiptData, BillItem
from ..core.logging import get_logger

logger = get_logger(__name__)


class BillParserService:
    def __init__(self):
        pass

    def parse_receipt_data(self, receipt_data: ReceiptData) -> Dict[str, Any]:
        """
        Parse receipt data into a structured format for bill splitting.
        
        Args:
            receipt_data: The structured receipt data
            
        Returns:
            Parsed bill data ready for splitting
        """
        try:
            parsed_data = {
                "receipt_info": {
                    "receipt_number": receipt_data.receipt_number,
                    "date": receipt_data.date,
                    "time": receipt_data.time,
                    "store": {
                        "name": receipt_data.store.name,
                        "address": receipt_data.store.address,
                        "phone": receipt_data.store.phone
                    }
                },
                "items": [],
                "totals": {
                    "subtotal": receipt_data.subtotal,
                    "tax": receipt_data.tax,
                    "service_charge": receipt_data.service_charge,
                    "discount": receipt_data.discount,
                    "total_amount": receipt_data.total_amount
                },
                "payment_info": {
                    "method": receipt_data.payment_method,
                    "transaction_id": receipt_data.transaction_id,
                    "notes": receipt_data.notes
                }
            }
            
            # Parse items
            for item in receipt_data.items:
                parsed_item = {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total": item.total,
                    "assigned_to": None  # Will be set during assignment
                }
                parsed_data["items"].append(parsed_item)
            
            logger.info(f"Successfully parsed receipt data with {len(parsed_data['items'])} items")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing receipt data: {str(e)}")
            return {}

    def validate_bill_items(self, items: List[BillItem]) -> bool:
        """
        Validate bill items for completeness and accuracy.
        
        Args:
            items: List of bill items to validate
            
        Returns:
            True if all items are valid, False otherwise
        """
        try:
            for item in items:
                if not item.name or item.name.strip() == "":
                    logger.warning("Item with empty name found")
                    return False
                    
                if item.quantity <= 0:
                    logger.warning(f"Invalid quantity for item {item.name}: {item.quantity}")
                    return False
                    
                if item.unit_price <= 0:
                    logger.warning(f"Invalid unit price for item {item.name}: {item.unit_price}")
                    return False
                    
                # Check if calculated total matches expected total
                expected_total = item.quantity * item.unit_price
                if abs(item.total - expected_total) > 0.01:  # Allow for small floating point differences
                    logger.warning(f"Total mismatch for item {item.name}: expected {expected_total}, got {item.total}")
                    # Don't return False here as OCR might have slight inaccuracies
                    
            logger.info("Bill items validation completed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating bill items: {str(e)}")
            return False

    def categorize_items(self, items: List[BillItem]) -> Dict[str, List[BillItem]]:
        """
        Categorize items by type (food, drinks, etc.) for better organization.
        
        Args:
            items: List of bill items to categorize
            
        Returns:
            Dictionary with categories as keys and lists of items as values
        """
        try:
            categories = {
                "food": [],
                "drinks": [],
                "other": []
            }
            
            # Simple categorization based on item names
            food_keywords = ["burger", "pizza", "pasta", "salad", "sandwich", "chicken", "beef", "fish", "rice", "noodles"]
            drink_keywords = ["coffee", "tea", "juice", "soda", "water", "beer", "wine", "cocktail", "smoothie"]
            
            for item in items:
                item_name_lower = item.name.lower()
                categorized = False
                
                for keyword in food_keywords:
                    if keyword in item_name_lower:
                        categories["food"].append(item)
                        categorized = True
                        break
                        
                if not categorized:
                    for keyword in drink_keywords:
                        if keyword in item_name_lower:
                            categories["drinks"].append(item)
                            categorized = True
                            break
                            
                if not categorized:
                    categories["other"].append(item)
            
            logger.info(f"Categorized {len(items)} items into {len([cat for cat in categories.values() if cat])} categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error categorizing items: {str(e)}")
            return {"other": items}


# Global bill parser service instance
bill_parser_service = BillParserService()
