# backend/app/services/receipt_validator.py
"""
Receipt validation service for handling tax-inclusive/exclusive scenarios.

CRITICAL: This service contains the core validation logic that ensures
receipt calculations are correct. It handles two main scenarios:

1. Tax-exclusive: items_total = subtotal, grand_total = subtotal + taxes
2. Tax-inclusive: items_total = grand_total (taxes already in prices)

The validator auto-detects which scenario applies and validates accordingly.
"""

from typing import Dict, Any, List, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)

# Tolerance for floating point comparisons (5 cents)
ERROR_TOLERANCE_IN_DOLLARS = 0.05


class ReceiptValidatorService:
    """Service for validating receipt calculations and determining tax scenarios."""
    
    def validate_and_process_receipt(self, data: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """
        Validate receipt data and determine tax scenario.
        
        Args:
            data: Extracted receipt data dictionary
            operation_id: Operation ID for logging
            
        Returns:
            Validated and processed data dictionary with tax scenario info
            
        Raises:
            ValueError: If calculations cannot be reconciled
        """
        logger.info(f"[{operation_id}] Starting validation")
        
        # Validate JSON structure
        if not self._validate_json_structure(data, operation_id):
            raise ValueError("Invalid JSON structure received")
        
        # Extract values
        items = data.get("items", [])
        provided_subtotal = float(data.get("subtotal", 0.0))
        taxes_or_charges = data.get("taxes_or_charges", [])
        grand_total = float(data.get("grand_total", 0.0))
        
        # Validate grand total (critical requirement)
        if grand_total <= 0:
            raise ValueError("Grand total is missing or invalid - this is mandatory")
        
        # Calculate items total and validate individual items
        calculated_items_total, item_errors = self._validate_items(items, operation_id)
        
        # Calculate total taxes/charges
        total_taxes_charges = sum(float(tc.get("amount", 0.0)) for tc in taxes_or_charges)
        
        logger.info(f"[{operation_id}] Calculations: items={calculated_items_total:.2f}, "
                   f"subtotal={provided_subtotal:.2f}, taxes={total_taxes_charges:.2f}, "
                   f"grand_total={grand_total:.2f}")
        
        # Determine tax scenario and validate
        final_subtotal, tax_scenario = self._determine_tax_scenario(
            calculated_items_total=calculated_items_total,
            provided_subtotal=provided_subtotal,
            total_taxes_charges=total_taxes_charges,
            grand_total=grand_total,
            item_validation_errors=item_errors,
            operation_id=operation_id
        )
        
        # Calculate tax percentages
        self._calculate_tax_percentages(
            taxes_or_charges, final_subtotal, total_taxes_charges, tax_scenario, operation_id
        )
        
        # Update data with results
        data["subtotal"] = final_subtotal
        data["_validation_info"] = {
            "tax_scenario": tax_scenario,
            "items_total": calculated_items_total,
            "final_subtotal": final_subtotal,
            "total_taxes_charges": total_taxes_charges,
            "validation_passed": True
        }
        
        logger.info(f"[{operation_id}] Validation passed: {tax_scenario}")
        return data
    
    def _validate_items(self, items: List[Dict[str, Any]], operation_id: str) -> Tuple[float, List[Dict]]:
        """Validate individual item calculations and return total."""
        calculated_total = 0.0
        errors = []
        
        for i, item in enumerate(items):
            name = item.get("name", f"Item {i+1}")
            quantity = float(item.get("quantity", 0))
            unit_price = float(item.get("unit_price", 0))
            total_price = float(item.get("total_price", 0))
            
            expected_total = quantity * unit_price
            diff = abs(total_price - expected_total)
            
            if diff > ERROR_TOLERANCE_IN_DOLLARS:
                errors.append({
                    "item": name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "provided_total": total_price,
                    "calculated_total": expected_total,
                    "difference": diff
                })
            
            calculated_total += total_price
        
        logger.info(f"[{operation_id}] Items: {len(items)} items, total={calculated_total:.2f}, errors={len(errors)}")
        return calculated_total, errors
    
    def _determine_tax_scenario(
        self,
        calculated_items_total: float,
        provided_subtotal: float,
        total_taxes_charges: float,
        grand_total: float,
        item_validation_errors: List[Dict],
        operation_id: str
    ) -> Tuple[float, str]:
        """
        Determine if receipt uses tax-inclusive or tax-exclusive pricing.
        
        Tax-exclusive: Items + Taxes = Grand Total
        Tax-inclusive: Items = Grand Total (taxes already included)
        """
        subtotal_provided = provided_subtotal > 0
        
        if subtotal_provided:
            # SCENARIO 1: Subtotal explicitly provided (tax-exclusive)
            logger.info(f"[{operation_id}] Scenario: Tax-exclusive (subtotal provided)")
            
            # Items should match subtotal
            subtotal_diff = abs(calculated_items_total - provided_subtotal)
            if subtotal_diff > ERROR_TOLERANCE_IN_DOLLARS:
                raise ValueError(
                    f"Items total ({calculated_items_total:.2f}) does not match "
                    f"provided subtotal ({provided_subtotal:.2f}). Difference: {subtotal_diff:.2f}."
                )
            
            # Grand total should = subtotal + taxes
            expected_grand = provided_subtotal + total_taxes_charges
            grand_diff = abs(expected_grand - grand_total)
            
            if grand_diff > ERROR_TOLERANCE_IN_DOLLARS:
                raise ValueError(
                    f"Grand total validation failed. Expected: {expected_grand:.2f} "
                    f"(subtotal {provided_subtotal:.2f} + taxes {total_taxes_charges:.2f}), "
                    f"but got: {grand_total:.2f}. Difference: {grand_diff:.2f}."
                )
            
            return provided_subtotal, "tax_exclusive"
        
        else:
            # SCENARIO 2: No subtotal - determine from calculations
            logger.info(f"[{operation_id}] Scenario: Determining tax treatment")
            
            if total_taxes_charges == 0:
                # No taxes - items should equal grand total
                diff = abs(calculated_items_total - grand_total)
                if diff <= ERROR_TOLERANCE_IN_DOLLARS:
                    return grand_total, "no_taxes"
                else:
                    raise ValueError(
                        f"Items total ({calculated_items_total:.2f}) does not match "
                        f"grand total ({grand_total:.2f}) and no taxes present. "
                        f"Difference: {diff:.2f}."
                    )
            
            # Check both scenarios
            items_vs_grand = abs(calculated_items_total - grand_total)
            calculated_subtotal = grand_total - total_taxes_charges
            items_vs_subtotal = abs(calculated_items_total - calculated_subtotal)
            
            logger.info(f"[{operation_id}] Checking: items_vs_grand={items_vs_grand:.2f}, "
                       f"items_vs_subtotal={items_vs_subtotal:.2f}")
            
            # Items = Grand Total → Tax-inclusive
            if items_vs_grand <= ERROR_TOLERANCE_IN_DOLLARS:
                logger.info(f"[{operation_id}] Tax-inclusive detected")
                return grand_total, "tax_inclusive"
            
            # Items = Grand Total - Taxes → Tax-exclusive
            elif items_vs_subtotal <= ERROR_TOLERANCE_IN_DOLLARS and calculated_subtotal >= 0:
                logger.info(f"[{operation_id}] Tax-exclusive detected")
                return calculated_subtotal, "tax_exclusive"
            
            else:
                # Neither matches
                raise ValueError(
                    f"Items total ({calculated_items_total:.2f}) matches neither scenario:\n"
                    f"• Tax-inclusive: Items should equal Grand Total ({grand_total:.2f}) - Diff: {items_vs_grand:.2f}\n"
                    f"• Tax-exclusive: Items should equal Subtotal ({calculated_subtotal:.2f}) - Diff: {items_vs_subtotal:.2f}"
                )
    
    def _calculate_tax_percentages(
        self,
        taxes_or_charges: List[Dict],
        final_subtotal: float,
        total_taxes_charges: float,
        tax_scenario: str,
        operation_id: str
    ):
        """Calculate and attach tax percentages."""
        if total_taxes_charges == 0 or final_subtotal <= 0:
            return
        
        for tc in taxes_or_charges:
            amount = float(tc.get("amount", 0.0))
            
            if tax_scenario == "tax_inclusive":
                # Base is subtotal minus taxes
                tax_exclusive_base = final_subtotal - total_taxes_charges
                if tax_exclusive_base > 0:
                    percent = round((amount / tax_exclusive_base) * 100, 2)
                else:
                    percent = 0.0
            else:
                # Base is subtotal
                percent = round((amount / final_subtotal) * 100, 2)
            
            tc["percent"] = percent
            logger.info(f"[{operation_id}] Tax '{tc.get('name')}': {amount:.2f} = {percent}%")

    def _validate_json_structure(self, data: Dict[str, Any], operation_id: str) -> bool:
        """Validate JSON structure has required fields."""
        try:
            required = ['receipt_number', 'date', 'time', 'store', 'items', 'grand_total', 'subtotal']
            
            for field in required:
                if field not in data:
                    logger.warning(f"[{operation_id}] Missing field: {field}")
                    return False
            
            # Validate store
            if not isinstance(data['store'], dict) or 'name' not in data['store']:
                logger.warning(f"[{operation_id}] Invalid store structure")
                return False
            
            # Validate items
            if not isinstance(data['items'], list) or len(data['items']) == 0:
                logger.warning(f"[{operation_id}] Invalid/empty items list")
                return False
            
            # Validate each item
            for item in data['items']:
                if not isinstance(item, dict):
                    return False
                for field in ['name', 'quantity', 'unit_price', 'total_price']:
                    if field not in item:
                        logger.warning(f"[{operation_id}] Item missing: {field}")
                        return False
            
            # Validate taxes_or_charges
            if 'taxes_or_charges' in data:
                if not isinstance(data['taxes_or_charges'], list):
                    return False
                for tc in data['taxes_or_charges']:
                    if not isinstance(tc, dict) or 'name' not in tc or 'amount' not in tc:
                        return False
            
            logger.info(f"[{operation_id}] Structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"[{operation_id}] Structure validation error: {str(e)}")
            return False


# Global instance
receipt_validator_service = ReceiptValidatorService()