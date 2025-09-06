from typing import List, Dict, Any, Tuple
from app.models.person import Person
from app.models.bill import BillItemAssignment
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaxCalculatorService:
    def __init__(self):
        pass

    def calculate_tax_distribution(
        self,
        participants: List[Person],
        item_assignments: List[BillItemAssignment],
        total_tax: float,
        distribution_method: str = "proportional"
    ) -> Dict[str, float]:
        """
        Calculate how tax should be distributed among participants.
        
        Args:
            participants: List of people splitting the bill
            item_assignments: List of item assignments to people
            total_tax: Total tax amount
            distribution_method: Method for distribution ("proportional" or "equal")
            
        Returns:
            Dictionary mapping person_id to tax amount
        """
        try:
            tax_distribution = {}
            
            if distribution_method == "equal":
                # Equal distribution among all participants
                tax_per_person = total_tax / len(participants)
                for person in participants:
                    tax_distribution[person.id] = tax_per_person
                    
            else:  # proportional distribution
                # Calculate each person's subtotal
                person_subtotals = {}
                for person in participants:
                    person_subtotals[person.id] = 0.0
                    
                for assignment in item_assignments:
                    if assignment.assigned_to:
                        person_subtotals[assignment.assigned_to] += assignment.total
                
                total_subtotal = sum(person_subtotals.values())
                
                # Distribute tax proportionally
                for person in participants:
                    if total_subtotal > 0:
                        proportion = person_subtotals[person.id] / total_subtotal
                        tax_distribution[person.id] = total_tax * proportion
                    else:
                        tax_distribution[person.id] = total_tax / len(participants)
            
            logger.info(f"Successfully calculated tax distribution using {distribution_method} method")
            return tax_distribution
            
        except Exception as e:
            logger.error(f"Error calculating tax distribution: {str(e)}")
            return {}

    def calculate_service_charge_distribution(
        self,
        participants: List[Person],
        item_assignments: List[BillItemAssignment],
        total_service_charge: float,
        distribution_method: str = "proportional"
    ) -> Dict[str, float]:
        """
        Calculate how service charge should be distributed among participants.
        
        Args:
            participants: List of people splitting the bill
            item_assignments: List of item assignments to people
            total_service_charge: Total service charge amount
            distribution_method: Method for distribution ("proportional" or "equal")
            
        Returns:
            Dictionary mapping person_id to service charge amount
        """
        try:
            service_charge_distribution = {}
            
            if distribution_method == "equal":
                # Equal distribution among all participants
                charge_per_person = total_service_charge / len(participants)
                for person in participants:
                    service_charge_distribution[person.id] = charge_per_person
                    
            else:  # proportional distribution
                # Calculate each person's subtotal
                person_subtotals = {}
                for person in participants:
                    person_subtotals[person.id] = 0.0
                    
                for assignment in item_assignments:
                    if assignment.assigned_to:
                        person_subtotals[assignment.assigned_to] += assignment.total
                
                total_subtotal = sum(person_subtotals.values())
                
                # Distribute service charge proportionally
                for person in participants:
                    if total_subtotal > 0:
                        proportion = person_subtotals[person.id] / total_subtotal
                        service_charge_distribution[person.id] = total_service_charge * proportion
                    else:
                        service_charge_distribution[person.id] = total_service_charge / len(participants)
            
            logger.info(f"Successfully calculated service charge distribution using {distribution_method} method")
            return service_charge_distribution
            
        except Exception as e:
            logger.error(f"Error calculating service charge distribution: {str(e)}")
            return {}

    def calculate_discount_distribution(
        self,
        participants: List[Person],
        item_assignments: List[BillItemAssignment],
        total_discount: float,
        distribution_method: str = "proportional"
    ) -> Dict[str, float]:
        """
        Calculate how discount should be distributed among participants.
        
        Args:
            participants: List of people splitting the bill
            item_assignments: List of item assignments to people
            total_discount: Total discount amount
            distribution_method: Method for distribution ("proportional" or "equal")
            
        Returns:
            Dictionary mapping person_id to discount amount
        """
        try:
            discount_distribution = {}
            
            if distribution_method == "equal":
                # Equal distribution among all participants
                discount_per_person = total_discount / len(participants)
                for person in participants:
                    discount_distribution[person.id] = discount_per_person
                    
            else:  # proportional distribution
                # Calculate each person's subtotal
                person_subtotals = {}
                for person in participants:
                    person_subtotals[person.id] = 0.0
                    
                for assignment in item_assignments:
                    if assignment.assigned_to:
                        person_subtotals[assignment.assigned_to] += assignment.total
                
                total_subtotal = sum(person_subtotals.values())
                
                # Distribute discount proportionally
                for person in participants:
                    if total_subtotal > 0:
                        proportion = person_subtotals[person.id] / total_subtotal
                        discount_distribution[person.id] = total_discount * proportion
                    else:
                        discount_distribution[person.id] = total_discount / len(participants)
            
            logger.info(f"Successfully calculated discount distribution using {distribution_method} method")
            return discount_distribution
            
        except Exception as e:
            logger.error(f"Error calculating discount distribution: {str(e)}")
            return {}



# Global tax calculator service instance
tax_calculator_service = TaxCalculatorService()
