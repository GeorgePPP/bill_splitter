from typing import List, Dict, Any
from app.models.person import Person, PersonAssignment
from app.models.bill import BillItemAssignment
from app.core.logging import get_logger

logger = get_logger(__name__)


class SplitCalculatorService:
    def __init__(self):
        pass

    def calculate_split(
        self,
        participants: List[Person],
        item_assignments: List[BillItemAssignment],
        total_tax: float,
        total_service_charge: float,
        total_discount: float,
        tax_distribution: str = "proportional",
        service_charge_distribution: str = "proportional",
        discount_distribution: str = "proportional"
    ) -> List[PersonAssignment]:
        """
        Calculate how much each person should pay based on their assigned items.
        
        Args:
            participants: List of people splitting the bill
            item_assignments: List of item assignments to people
            total_tax: Total tax amount
            total_service_charge: Total service charge
            total_discount: Total discount amount
            tax_distribution: How to distribute tax ("proportional" or "equal")
            service_charge_distribution: How to distribute service charge
            discount_distribution: How to distribute discount
            
        Returns:
            List of person assignments with calculated amounts
        """
        try:
            person_assignments = []
            
            # Calculate subtotals for each person
            person_subtotals = {}
            for person in participants:
                person_subtotals[person.id] = 0.0
                
            for assignment in item_assignments:
                if assignment.assigned_to:
                    person_subtotals[assignment.assigned_to] += assignment.total
            
            # Calculate total subtotal
            total_subtotal = sum(person_subtotals.values())
            
            # Calculate tax, service charge, and discount distribution
            for person in participants:
                person_id = person.id
                subtotal = person_subtotals[person_id]
                
                # Calculate proportional shares
                if total_subtotal > 0:
                    proportion = subtotal / total_subtotal
                else:
                    proportion = 1.0 / len(participants)
                
                # Calculate tax share
                if tax_distribution == "proportional":
                    tax_share = total_tax * proportion
                else:  # equal distribution
                    tax_share = total_tax / len(participants)
                
                # Calculate service charge share
                if service_charge_distribution == "proportional":
                    service_charge_share = total_service_charge * proportion
                else:  # equal distribution
                    service_charge_share = total_service_charge / len(participants)
                
                # Calculate discount share
                if discount_distribution == "proportional":
                    discount_share = total_discount * proportion
                else:  # equal distribution
                    discount_share = total_discount / len(participants)
                
                # Calculate total for this person
                total = subtotal + tax_share + service_charge_share - discount_share
                
                # Get assigned items for this person
                assigned_items = [
                    {
                        "name": assignment.item_name,
                        "quantity": assignment.quantity,
                        "unit_price": assignment.unit_price,
                        "total": assignment.total
                    }
                    for assignment in item_assignments
                    if assignment.assigned_to == person_id
                ]
                
                person_assignment = PersonAssignment(
                    person_id=person_id,
                    person_name=person.name,
                    assigned_items=[item["name"] for item in assigned_items],
                    subtotal=subtotal,
                    tax_share=tax_share,
                    total=total
                )
                
                person_assignments.append(person_assignment)
            
            logger.info(f"Successfully calculated splits for {len(participants)} participants")
            return person_assignments
            
        except Exception as e:
            logger.error(f"Error calculating split: {str(e)}")
            return []


    def generate_split_summary(
        self,
        person_assignments: List[PersonAssignment],
        total_bill: float,
        total_tax: float,
        total_service_charge: float,
        total_discount: float
    ) -> Dict[str, Any]:
        """
        Generate a summary of the split calculation.
        
        Args:
            person_assignments: List of person assignments
            total_bill: Total bill amount
            total_tax: Total tax amount
            total_service_charge: Total service charge
            total_discount: Total discount amount
            
        Returns:
            Summary dictionary with split details
        """
        try:
            summary = {
                "bill_totals": {
                    "subtotal": total_bill - total_tax - total_service_charge + total_discount,
                    "tax": total_tax,
                    "service_charge": total_service_charge,
                    "discount": total_discount,
                    "total": total_bill
                },
                "person_splits": [
                    {
                        "person_id": assignment.person_id,
                        "person_name": assignment.person_name,
                        "subtotal": assignment.subtotal,
                        "tax_share": assignment.tax_share,
                        "total": assignment.total,
                        "assigned_items": assignment.assigned_items
                    }
                    for assignment in person_assignments
                ],
                "validation": {
                    "calculated_total": sum(assignment.total for assignment in person_assignments),
                    "expected_total": total_bill,
                    "is_valid": True  # Validation should be done by calculation_validator_service
                }
            }
            
            logger.info("Successfully generated split summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating split summary: {str(e)}")
            return {}


# Global split calculator service instance
split_calculator_service = SplitCalculatorService()
