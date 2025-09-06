from typing import List, Dict, Any
from app.models.receipt import ReceiptData, BillItem
from app.core.logging import get_logger

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
                    "taxes_or_charges": [
                        {
                            "name": tax_charge.name,
                            "amount": tax_charge.amount,
                            "percent": tax_charge.percent
                        }
                        for tax_charge in receipt_data.taxes_or_charges
                    ],
                    "grand_total": receipt_data.grand_total
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
                    "total_price": item.total_price,
                    "assigned_to": None  # Will be set during assignment
                }
                parsed_data["items"].append(parsed_item)
            
            logger.info(f"Successfully parsed receipt data with {len(parsed_data['items'])} items")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing receipt data: {str(e)}")
            return {}


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
