from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
from datetime import datetime

from app.models.bill import BillSplit, BillItemAssignment
from app.models.person import Person
from app.models.receipt import ReceiptData
from app.schemas.bill_schema import BillSplitCreateSchema, BillSplitResponseSchema
from app.services.split_calculator import split_calculator_service
from app.utils.exceptions import BillNotFoundError, PersonNotFoundError
from app.api.dependencies import get_current_user, get_logger_dependency

router = APIRouter(prefix="/bill", tags=["bill"])

# In-memory storage for demo purposes
bills_storage = {}
people_storage = {}


@router.post("/split", response_model=BillSplitResponseSchema)
async def create_bill_split(
    bill_data: BillSplitCreateSchema,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Create a new bill split with participants and item assignments.
    """
    try:
        # Validate participants exist
        for person_id in bill_data.participants:
            if person_id not in people_storage:
                raise HTTPException(status_code=400, detail=f"Person {person_id} not found")
        
        # Create bill split
        bill_split_id = str(uuid.uuid4())
        bill_split = BillSplit(
            id=bill_split_id,
            receipt_data=bill_data.receipt_data,
            participants=[people_storage[pid] for pid in bill_data.participants],
            item_assignments=bill_data.item_assignments,
            tax_distribution=bill_data.tax_distribution,
            service_charge_distribution=bill_data.service_charge_distribution,
            discount_distribution=bill_data.discount_distribution,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Store bill split
        bills_storage[bill_split_id] = bill_split
        
        logger.info(f"Successfully created bill split {bill_split_id}")
        
        return BillSplitResponseSchema(
            id=bill_split.id,
            receipt_data=bill_split.receipt_data,
            participants=[people_storage[pid] for pid in bill_data.participants],
            item_assignments=bill_split.item_assignments,
            tax_distribution=bill_split.tax_distribution,
            service_charge_distribution=bill_split.service_charge_distribution,
            discount_distribution=bill_split.discount_distribution,
            created_at=bill_split.created_at,
            updated_at=bill_split.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bill split: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{bill_id}", response_model=BillSplitResponseSchema)
async def get_bill_split(
    bill_id: str,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Get bill split by ID.
    """
    try:
        if bill_id not in bills_storage:
            raise HTTPException(status_code=404, detail="Bill split not found")
        
        bill_split = bills_storage[bill_id]
        
        return BillSplitResponseSchema(
            id=bill_split.id,
            receipt_data=bill_split.receipt_data,
            participants=bill_split.participants,
            item_assignments=bill_split.item_assignments,
            tax_distribution=bill_split.tax_distribution,
            service_charge_distribution=bill_split.service_charge_distribution,
            discount_distribution=bill_split.discount_distribution,
            created_at=bill_split.created_at,
            updated_at=bill_split.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bill split {bill_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{bill_id}/assignments")
async def update_item_assignments(
    bill_id: str,
    assignments: List[BillItemAssignment],
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Update item assignments for a bill split.
    """
    try:
        if bill_id not in bills_storage:
            raise HTTPException(status_code=404, detail="Bill split not found")
        
        bill_split = bills_storage[bill_id]
        bill_split.item_assignments = assignments
        bill_split.updated_at = datetime.now().isoformat()
        
        bills_storage[bill_id] = bill_split
        
        logger.info(f"Successfully updated item assignments for bill split {bill_id}")
        
        return {
            "success": True,
            "message": "Item assignments updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item assignments for bill {bill_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{bill_id}")
async def delete_bill_split(
    bill_id: str,
    current_user = Depends(get_current_user),
    logger = Depends(get_logger_dependency)
):
    """
    Delete bill split by ID.
    """
    try:
        if bill_id not in bills_storage:
            raise HTTPException(status_code=404, detail="Bill split not found")
        
        del bills_storage[bill_id]
        
        logger.info(f"Successfully deleted bill split {bill_id}")
        
        return {
            "success": True,
            "message": "Bill split deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bill split {bill_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
