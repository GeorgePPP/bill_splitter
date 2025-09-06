from typing import Any, Dict, List
from decimal import Decimal, ROUND_HALF_UP
from app.core.logging import get_logger

logger = get_logger(__name__)


class Formatters:
    def __init__(self):
        self.currency_symbol = "$"
        self.decimal_places = 2

    def format_currency(self, amount: float, symbol: str = None) -> str:
        """
        Format amount as currency.
        
        Args:
            amount: Amount to format
            symbol: Currency symbol to use
            
        Returns:
            Formatted currency string
        """
        try:
            symbol = symbol or self.currency_symbol
            rounded_amount = round(amount, self.decimal_places)
            return f"{symbol}{rounded_amount:.2f}"
        except Exception as e:
            logger.error(f"Error formatting currency {amount}: {str(e)}")
            return f"{symbol}0.00"

    def format_percentage(self, value: float, decimal_places: int = 1) -> str:
        """
        Format value as percentage.
        
        Args:
            value: Value to format (0.1 = 10%)
            decimal_places: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        try:
            percentage = value * 100
            return f"{percentage:.{decimal_places}f}%"
        except Exception as e:
            logger.error(f"Error formatting percentage {value}: {str(e)}")
            return "0.0%"

    def round_to_cents(self, amount: float) -> float:
        """
        Round amount to the nearest cent.
        
        Args:
            amount: Amount to round
            
        Returns:
            Rounded amount
        """
        try:
            decimal_amount = Decimal(str(amount))
            rounded = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            return float(rounded)
        except Exception as e:
            logger.error(f"Error rounding amount {amount}: {str(e)}")
            return round(amount, 2)

    def format_receipt_summary(self, receipt_data: Dict[str, Any]) -> str:
        """
        Format receipt data into a readable summary.
        
        Args:
            receipt_data: Receipt data dictionary
            
        Returns:
            Formatted summary string
        """
        try:
            summary_parts = []
            
            # Store information
            if "store" in receipt_data and "name" in receipt_data["store"]:
                summary_parts.append(f"Store: {receipt_data['store']['name']}")
            
            # Date and time
            if "date" in receipt_data:
                summary_parts.append(f"Date: {receipt_data['date']}")
            if "time" in receipt_data:
                summary_parts.append(f"Time: {receipt_data['time']}")
            
            # Items
            if "items" in receipt_data:
                summary_parts.append(f"Items: {len(receipt_data['items'])}")
                for item in receipt_data["items"][:3]:  # Show first 3 items
                    if "name" in item and "total" in item:
                        summary_parts.append(f"  - {item['name']}: {self.format_currency(item['total'])}")
                if len(receipt_data["items"]) > 3:
                    summary_parts.append(f"  ... and {len(receipt_data['items']) - 3} more items")
            
            # Totals
            if "grand_total" in receipt_data:
                summary_parts.append(f"Total: {self.format_currency(receipt_data['grand_total'])}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error formatting receipt summary: {str(e)}")
            return "Error formatting receipt summary"

    def format_split_summary(self, person_assignments: List[Dict[str, Any]]) -> str:
        """
        Format split calculation into a readable summary.
        
        Args:
            person_assignments: List of person assignment dictionaries
            
        Returns:
            Formatted summary string
        """
        try:
            summary_parts = []
            total_amount = 0
            
            for assignment in person_assignments:
                person_name = assignment.get("person_name", "Unknown")
                subtotal = assignment.get("subtotal", 0)
                tax_share = assignment.get("tax_share", 0)
                total = assignment.get("total", 0)
                total_amount += total
                
                summary_parts.append(f"{person_name}:")
                summary_parts.append(f"  Subtotal: {self.format_currency(subtotal)}")
                summary_parts.append(f"  Tax: {self.format_currency(tax_share)}")
                summary_parts.append(f"  Total: {self.format_currency(total)}")
                summary_parts.append("")
            
            summary_parts.append(f"Grand Total: {self.format_currency(total_amount)}")
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error formatting split summary: {str(e)}")
            return "Error formatting split summary"

    def format_item_list(self, items: List[Dict[str, Any]]) -> str:
        """
        Format list of items into a readable string.
        
        Args:
            items: List of item dictionaries
            
        Returns:
            Formatted item list string
        """
        try:
            if not items:
                return "No items"
            
            item_lines = []
            for item in items:
                name = item.get("name", "Unknown Item")
                quantity = item.get("quantity", 1)
                unit_price = item.get("unit_price", 0)
                total = item.get("total", 0)
                
                item_line = f"{quantity}x {name} @ {self.format_currency(unit_price)} = {self.format_currency(total)}"
                item_lines.append(item_line)
            
            return "\n".join(item_lines)
            
        except Exception as e:
            logger.error(f"Error formatting item list: {str(e)}")
            return "Error formatting item list"

    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number for display.
        
        Args:
            phone: Raw phone number string
            
        Returns:
            Formatted phone number
        """
        try:
            # Remove all non-digit characters
            digits = ''.join(filter(str.isdigit, phone))
            
            if len(digits) == 10:
                # US format: (XXX) XXX-XXXX
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                # US format with country code: +1 (XXX) XXX-XXXX
                return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            else:
                # International format: +XX XXX XXX XXXX
                return f"+{digits}"
                
        except Exception as e:
            logger.error(f"Error formatting phone number {phone}: {str(e)}")
            return phone


# Global formatters instance
formatters = Formatters()
