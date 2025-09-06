from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import uuid
from datetime import datetime

from app.models.split import SplitCalculation, PersonSplit
from app.models.person import Person
from app.schemas.split_schema import SplitCalculationRequestSchema, SplitCalculationResponseSchema
from app.services.split_calculator import split_calculator_service
from app.services.tax_calculator import tax_calculator_service
from app.utils.exceptions import BillNotFoundError, CalculationError
from app.api.dependencies import get_current_user, get_logger_dependency

router = APIRouter(prefix="/split", tags=["split"])

# In-memory storage for demo purposes
splits_storage = {}


@router.post("/calculate", response_model=SplitCalculationResponseSchema)
async def calculate_split(
    split_request: SplitCalculationRequestSchema,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Calculate bill split for participants.
    """
    try:
        # Get bill data (this would come from a database in a real app)
        # For now, we'll create a mock calculation
        
        # Create person splits
        person_splits = []
        total_bill = 0.0
        total_tax = 0.0
        total_service_charge = 0.0
        total_discount = 0.0
        
        # Mock calculation - in real app, this would use actual bill data
        for i, person_id in enumerate(split_request.participants):
            # Mock person data
            person_name = f"Person {i+1}"
            
            # Mock item assignments
            mock_items = [
                {
                    "name": f"Item {i+1}A",
                    "quantity": 1,
                    "unit_price": 10.0,
                    "total": 10.0
                },
                {
                    "name": f"Item {i+1}B", 
                    "quantity": 2,
                    "unit_price": 5.0,
                    "total": 10.0
                }
            ]
            
            subtotal = sum(item["total"] for item in mock_items)
            tax_share = subtotal * 0.1  # 10% tax
            service_charge_share = subtotal * 0.05  # 5% service charge
            discount_share = 0.0  # No discount for demo
            total = subtotal + tax_share + service_charge_share - discount_share
            
            person_split = PersonSplit(
                person_id=person_id,
                person_name=person_name,
                items=mock_items,
                subtotal=subtotal,
                tax_share=tax_share,
                service_charge_share=service_charge_share,
                discount_share=discount_share,
                total=total
            )
            
            person_splits.append(person_split)
            total_bill += total
            total_tax += tax_share
            total_service_charge += service_charge_share
            total_discount += discount_share
        
        # Create split calculation
        split_id = str(uuid.uuid4())
        split_calculation = SplitCalculation(
            bill_id=split_request.bill_id,
            participants=split_request.participants,
            person_splits=person_splits,
            total_bill=total_bill,
            total_tax=total_tax,
            total_service_charge=total_service_charge,
            total_discount=total_discount,
            calculation_method=split_request.calculation_method
        )
        
        # Store split calculation
        splits_storage[split_id] = split_calculation
        
        logger.info(f"Successfully calculated split {split_id}")
        
        return SplitCalculationResponseSchema(
            success=True,
            message="Split calculation completed successfully",
            calculation={
                "split_id": split_id,
                "bill_id": split_request.bill_id,
                "participants": split_request.participants,
                "person_splits": [
                    {
                        "person_id": split.person_id,
                        "person_name": split.person_name,
                        "items": split.items,
                        "subtotal": split.subtotal,
                        "tax_share": split.tax_share,
                        "service_charge_share": split.service_charge_share,
                        "discount_share": split.discount_share,
                        "total": split.total
                    }
                    for split in person_splits
                ],
                "totals": {
                    "total_bill": total_bill,
                    "total_tax": total_tax,
                    "total_service_charge": total_service_charge,
                    "total_discount": total_discount
                },
                "calculation_method": split_request.calculation_method
            }
        )
        
    except Exception as e:
        logger.error(f"Error calculating split: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{split_id}")
async def get_split_calculation(
    split_id: str,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Get split calculation by ID.
    """
    try:
        if split_id not in splits_storage:
            raise HTTPException(status_code=404, detail="Split calculation not found")
        
        split_calculation = splits_storage[split_id]
        
        return {
            "split_id": split_id,
            "bill_id": split_calculation.bill_id,
            "participants": split_calculation.participants,
            "person_splits": [
                {
                    "person_id": split.person_id,
                    "person_name": split.person_name,
                    "items": split.items,
                    "subtotal": split.subtotal,
                    "tax_share": split.tax_share,
                    "service_charge_share": split.service_charge_share,
                    "discount_share": split.discount_share,
                    "total": split.total
                }
                for split in split_calculation.person_splits
            ],
            "totals": {
                "total_bill": split_calculation.total_bill,
                "total_tax": split_calculation.total_tax,
                "total_service_charge": split_calculation.total_service_charge,
                "total_discount": split_calculation.total_discount
            },
            "calculation_method": split_calculation.calculation_method
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting split calculation {split_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/")
async def list_split_calculations(
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    List all split calculations for the current user.
    """
    try:
        calculations = []
        for split_id, split_calculation in splits_storage.items():
            calculations.append({
                "split_id": split_id,
                "bill_id": split_calculation.bill_id,
                "participants": split_calculation.participants,
                "total_bill": split_calculation.total_bill,
                "calculation_method": split_calculation.calculation_method
            })
        
        return {
            "calculations": calculations,
            "total": len(calculations)
        }
        
    except Exception as e:
        logger.error(f"Error listing split calculations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{split_id}")
async def delete_split_calculation(
    split_id: str,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Delete split calculation by ID.
    """
    try:
        if split_id not in splits_storage:
            raise HTTPException(status_code=404, detail="Split calculation not found")
        
        del splits_storage[split_id]
        
        logger.info(f"Successfully deleted split calculation {split_id}")
        
        return {
            "success": True,
            "message": "Split calculation deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting split calculation {split_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
