"""
Receipt validation service for handling tax-inclusive/exclusive scenarios.
Separated from OpenAI service to maintain single responsibility principle.
"""

from typing import Dict, Any, List, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReceiptValidatorService:
    """Service for validating receipt calculations and determining tax scenarios."""
    
    def __init__(self):
        pass
    
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
        logger.info(f"[{operation_id}] Starting receipt validation", extra={
            "operation_id": operation_id,
            "step": "validation_start"
        })
        
        # Extract and validate basic data
        items = data.get("items", [])
        provided_subtotal = float(data.get("subtotal", 0.0))
        taxes_or_charges = data.get("taxes_or_charges", [])
        grand_total = float(data.get("grand_total", 0.0))
        
        # Validate grand total exists (critical requirement)
        if grand_total <= 0:
            error_msg = "Grand total is missing or invalid - this is the final amount payable and is mandatory"
            logger.error(f"[{operation_id}] {error_msg}", extra={
                "operation_id": operation_id,
                "step": "grand_total_validation",
                "grand_total": grand_total
            })
            raise ValueError(error_msg)
        
        # Calculate items total and validate individual item calculations
        calculated_items_total, item_validation_errors = self._validate_items(items, operation_id)
        
        # Calculate total taxes and charges
        total_taxes_charges = sum(float(tc.get("amount", 0.0)) for tc in taxes_or_charges)
        
        logger.info(f"[{operation_id}] Basic calculations", extra={
            "operation_id": operation_id,
            "calculated_items_total": calculated_items_total,
            "provided_subtotal": provided_subtotal,
            "total_taxes_charges": total_taxes_charges,
            "grand_total": grand_total,
            "item_errors_count": len(item_validation_errors)
        })
        
        # Determine tax scenario and validate
        final_subtotal, tax_scenario = self._determine_tax_scenario(
            calculated_items_total=calculated_items_total,
            provided_subtotal=provided_subtotal,
            total_taxes_charges=total_taxes_charges,
            grand_total=grand_total,
            item_validation_errors=item_validation_errors,
            operation_id=operation_id
        )
        
        # Calculate tax percentages
        self._calculate_tax_percentages(taxes_or_charges, final_subtotal, total_taxes_charges, tax_scenario, operation_id)
        
        # Update data with validation results
        data["subtotal"] = final_subtotal
        data["_validation_info"] = {
            "tax_scenario": tax_scenario,
            "items_total": calculated_items_total,
            "final_subtotal": final_subtotal,
            "total_taxes_charges": total_taxes_charges,
            "validation_passed": True
        }
        
        logger.info(f"[{operation_id}] Validation completed successfully", extra={
            "operation_id": operation_id,
            "tax_scenario": tax_scenario,
            "final_subtotal": final_subtotal,
            "grand_total": grand_total
        })
        
        return data
    
    def _validate_items(self, items: List[Dict[str, Any]], operation_id: str) -> Tuple[float, List[Dict]]:
        """Validate individual item calculations and return total."""
        calculated_items_total = 0.0
        item_validation_errors = []
        
        for i, item in enumerate(items):
            name = item.get("name", f"Item {i+1}")
            quantity = float(item.get("quantity", 0))
            unit_price = float(item.get("unit_price", 0))
            total_price = float(item.get("total_price", 0))
            
            expected_item_total = quantity * unit_price
            item_diff = abs(total_price - expected_item_total)
            
            if item_diff > 0.01:  # Allow 1 cent tolerance
                item_validation_errors.append({
                    "item": name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "provided_total": total_price,
                    "calculated_total": expected_item_total,
                    "difference": item_diff
                })
            
            calculated_items_total += total_price
        
        logger.info(f"[{operation_id}] Items validation", extra={
            "operation_id": operation_id,
            "items_count": len(items),
            "calculated_items_total": calculated_items_total,
            "item_errors_count": len(item_validation_errors),
            "item_errors": item_validation_errors
        })
        
        return calculated_items_total, item_validation_errors
    
    def _determine_tax_scenario(self, calculated_items_total: float, provided_subtotal: float, 
                               total_taxes_charges: float, grand_total: float, 
                               item_validation_errors: List[Dict], operation_id: str) -> Tuple[float, str]:
        """Determine if receipt uses tax-inclusive or tax-exclusive pricing."""
        
        subtotal_explicitly_provided = provided_subtotal > 0.01
        
        if subtotal_explicitly_provided:
            # Scenario 1: Subtotal explicitly provided - this is tax-exclusive
            logger.info(f"[{operation_id}] Scenario 1: Subtotal explicitly provided (tax-exclusive)", extra={
                "operation_id": operation_id,
                "provided_subtotal": provided_subtotal,
                "scenario": "tax_exclusive_with_subtotal"
            })
            
            # Validate that items add up to subtotal
            subtotal_diff = abs(calculated_items_total - provided_subtotal)
            if subtotal_diff > 0.01:
                error_msg = (
                    f"Items total ({calculated_items_total:.2f}) does not match provided subtotal ({provided_subtotal:.2f}). "
                    f"Difference: {subtotal_diff:.2f}. "
                    f"Individual item errors: {len(item_validation_errors)} items have calculation mismatches."
                )
                logger.error(f"[{operation_id}] {error_msg}", extra={
                    "operation_id": operation_id,
                    "step": "subtotal_items_validation_failed"
                })
                raise ValueError(error_msg)
            
            # Validate grand total = subtotal + taxes (for tax-exclusive)
            expected_grand_total = provided_subtotal + total_taxes_charges
            grand_total_diff = abs(expected_grand_total - grand_total)
            
            if grand_total_diff > 0.01:
                error_msg = (
                    f"Grand total validation failed. Expected: {expected_grand_total:.2f} "
                    f"(subtotal {provided_subtotal:.2f} + taxes {total_taxes_charges:.2f}), "
                    f"but receipt shows: {grand_total:.2f}. Difference: {grand_total_diff:.2f}."
                )
                logger.error(f"[{operation_id}] {error_msg}", extra={
                    "operation_id": operation_id,
                    "step": "grand_total_validation_failed"
                })
                raise ValueError(error_msg)
            
            return provided_subtotal, "tax_exclusive"
        
        else:
            # Scenario 2: No subtotal provided - determine from items vs grand total
            logger.info(f"[{operation_id}] Scenario 2: No subtotal provided, determining scenario", extra={
                "operation_id": operation_id,
                "scenario": "subtotal_not_provided"
            })
            
            if total_taxes_charges == 0:
                # No taxes - items should equal grand total
                items_grand_diff = abs(calculated_items_total - grand_total)
                if items_grand_diff <= 0.01:
                    return grand_total, "no_taxes"
                else:
                    error_msg = (
                        f"Items total ({calculated_items_total:.2f}) does not match grand total ({grand_total:.2f}) "
                        f"and no taxes/charges are present. Difference: {items_grand_diff:.2f}."
                    )
                    logger.error(f"[{operation_id}] {error_msg}")
                    raise ValueError(error_msg)
            
            # Check both scenarios
            items_grand_diff = abs(calculated_items_total - grand_total)
            calculated_subtotal = grand_total - total_taxes_charges
            items_subtotal_diff = abs(calculated_items_total - calculated_subtotal)
            
            logger.info(f"[{operation_id}] Checking tax scenarios", extra={
                "operation_id": operation_id,
                "items_vs_grand_total_diff": items_grand_diff,
                "items_vs_calculated_subtotal_diff": items_subtotal_diff,
                "calculated_subtotal": calculated_subtotal
            })
            
            # Rule: Items must equal either Grand Total (tax-inclusive) OR Grand Total - Taxes (tax-exclusive)
            if items_grand_diff <= 0.01:
                # Tax-inclusive: items already include tax
                logger.info(f"[{operation_id}] Tax-inclusive scenario detected")
                return grand_total, "tax_inclusive"
            elif items_subtotal_diff <= 0.01 and calculated_subtotal >= 0:
                # Tax-exclusive: items + taxes = grand total
                logger.info(f"[{operation_id}] Tax-exclusive scenario detected")
                return calculated_subtotal, "tax_exclusive"
            else:
                # Neither scenario matches
                error_msg = (
                    f"Items total ({calculated_items_total:.2f}) matches neither scenario:\n"
                    f"• Tax-inclusive: Items should equal Grand Total ({grand_total:.2f}) - Difference: {items_grand_diff:.2f}\n"
                    f"• Tax-exclusive: Items should equal Subtotal ({calculated_subtotal:.2f}) - Difference: {items_subtotal_diff:.2f}"
                )
                logger.error(f"[{operation_id}] {error_msg}")
                raise ValueError(error_msg)
    
    def _calculate_tax_percentages(self, taxes_or_charges: List[Dict], final_subtotal: float, 
                                  total_taxes_charges: float, tax_scenario: str, operation_id: str):
        """Calculate tax percentages based on the determined scenario."""
        if total_taxes_charges == 0 or final_subtotal <= 0:
            return
        
        for tax_charge in taxes_or_charges:
            amount = float(tax_charge.get("amount", 0.0))
            
            if tax_scenario == "tax_inclusive":
                # For tax-inclusive, calculate percentage based on tax-exclusive amount
                tax_exclusive_base = final_subtotal - total_taxes_charges
                if tax_exclusive_base > 0:
                    calculated_percent = round((amount / tax_exclusive_base) * 100, 2)
                else:
                    calculated_percent = 0.0
            else:
                # For tax-exclusive, calculate percentage based on subtotal
                calculated_percent = round((amount / final_subtotal) * 100, 2)
            
            tax_charge["percent"] = calculated_percent
            
            logger.info(f"[{operation_id}] Tax percentage calculated", extra={
                "operation_id": operation_id,
                "tax_name": tax_charge.get("name"),
                "amount": amount,
                "calculated_percent": calculated_percent,
                "scenario": tax_scenario
            })


# Global receipt validator service instance
receipt_validator_service = ReceiptValidatorService()
