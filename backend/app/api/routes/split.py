# backend/app/api/routes/split.py
"""
Stateless bill split calculation endpoint.
All data passed in request, no server-side storage.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas.receipt_schema import ReceiptDataSchema
from app.api.dependencies import get_logger_dependency

router = APIRouter(prefix="/split", tags=["split"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class Participant(BaseModel):
    """A person participating in the bill split."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class ItemAssignment(BaseModel):
    """Assignment of an item to participants."""
    item_index: int = Field(..., description="Index of the item in receipt_data.items")
    person_ids: List[str] = Field(..., description="IDs of people sharing this item")
    shares: Optional[Dict[str, float]] = Field(
        None, 
        description="Custom share ratios per person (defaults to equal split)"
    )


class SplitCalculationRequest(BaseModel):
    """Request for calculating bill split."""
    receipt_data: ReceiptDataSchema
    participants: List[Participant]
    item_assignments: List[ItemAssignment]
    tax_distribution: str = Field(
        "proportional", 
        description="How to distribute tax: 'proportional' or 'equal'"
    )
    service_charge_distribution: str = Field(
        "proportional",
        description="How to distribute service charges: 'proportional' or 'equal'"
    )
    discount_distribution: str = Field(
        "proportional",
        description="How to distribute discounts: 'proportional' or 'equal'"
    )


class PersonSplitResult(BaseModel):
    """Split result for a single person."""
    person_id: str
    person_name: str
    items: List[Dict[str, Any]]
    subtotal: float
    tax_share: float
    service_charge_share: float
    discount_share: float
    total: float


class SplitTotals(BaseModel):
    """Bill totals summary."""
    items_total: float
    subtotal: float
    total_tax: float
    total_service_charge: float
    total_discount: float
    grand_total: float


class SplitCalculationResponse(BaseModel):
    """Response for split calculation."""
    success: bool
    message: str
    person_splits: List[PersonSplitResult]
    totals: SplitTotals
    unassigned_items: List[Dict[str, Any]] = []
    validation_warnings: List[str] = []


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/calculate", response_model=SplitCalculationResponse)
async def calculate_split(
    request: SplitCalculationRequest,
    logger=Depends(get_logger_dependency)
):
    """
    Calculate bill split based on item assignments.
    
    This is a stateless calculation - all data is passed in the request
    and the result is returned without any server-side storage.
    
    Item assignments specify which participants are responsible for each item.
    Items can be split among multiple people with optional custom share ratios.
    
    Tax, service charges, and discounts can be distributed either:
    - proportionally (based on each person's subtotal)
    - equally (same amount per person)
    """
    try:
        logger.info(f"Calculating split for {len(request.participants)} participants")
        
        receipt = request.receipt_data
        participants = {p.id: p for p in request.participants}
        
        # Validate participants exist
        if not participants:
            raise HTTPException(status_code=400, detail="At least one participant is required")
        
        # Initialize person splits
        person_data: Dict[str, Dict[str, Any]] = {
            pid: {
                "person_id": pid,
                "person_name": p.name,
                "items": [],
                "subtotal": 0.0
            }
            for pid, p in participants.items()
        }
        
        # Track which items are assigned
        assigned_indices = set()
        unassigned_items = []
        validation_warnings = []
        
        # Process item assignments
        for assignment in request.item_assignments:
            idx = assignment.item_index
            
            # Validate index
            if idx < 0 or idx >= len(receipt.items):
                validation_warnings.append(f"Invalid item index: {idx}")
                continue
            
            item = receipt.items[idx]
            assigned_indices.add(idx)
            
            # Validate person IDs
            valid_person_ids = [pid for pid in assignment.person_ids if pid in participants]
            if not valid_person_ids:
                validation_warnings.append(f"No valid participants for item '{item.name}'")
                continue
            
            # Calculate shares
            if assignment.shares:
                # Custom shares provided
                total_share = sum(
                    assignment.shares.get(pid, 0) 
                    for pid in valid_person_ids
                )
                if total_share <= 0:
                    # Fall back to equal split
                    shares = {pid: 1.0 / len(valid_person_ids) for pid in valid_person_ids}
                else:
                    shares = {
                        pid: assignment.shares.get(pid, 0) / total_share 
                        for pid in valid_person_ids
                    }
            else:
                # Equal split
                shares = {pid: 1.0 / len(valid_person_ids) for pid in valid_person_ids}
            
            # Distribute item cost
            item_total = item.total_price
            
            for pid in valid_person_ids:
                share_ratio = shares[pid]
                share_amount = round(item_total * share_ratio, 2)
                
                person_data[pid]["items"].append({
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "share_ratio": share_ratio,
                    "share_amount": share_amount,
                    "shared_with": [
                        participants[p].name for p in valid_person_ids if p != pid
                    ] if len(valid_person_ids) > 1 else []
                })
                
                person_data[pid]["subtotal"] += share_amount
        
        # Find unassigned items
        for idx, item in enumerate(receipt.items):
            if idx not in assigned_indices:
                unassigned_items.append({
                    "index": idx,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                })
        
        if unassigned_items:
            validation_warnings.append(
                f"{len(unassigned_items)} item(s) not assigned to anyone"
            )
        
        # Calculate totals
        items_total = sum(item.total_price for item in receipt.items)
        total_subtotal = sum(pd["subtotal"] for pd in person_data.values())
        
        # Extract taxes and charges
        total_tax = 0.0
        total_service_charge = 0.0
        total_discount = 0.0
        
        for tc in receipt.taxes_or_charges:
            amount = tc.amount
            name_lower = tc.name.lower()
            
            if amount < 0:
                # Negative amount = discount
                total_discount += abs(amount)
            elif "service" in name_lower or "svc" in name_lower:
                total_service_charge += amount
            else:
                # Default to tax
                total_tax += amount
        
        # Distribute tax, service charge, and discount
        person_splits = []
        
        for pid, data in person_data.items():
            subtotal = data["subtotal"]
            
            # Calculate proportion for this person
            if total_subtotal > 0:
                proportion = subtotal / total_subtotal
            else:
                proportion = 1.0 / len(participants) if participants else 0
            
            # Tax share
            if request.tax_distribution == "equal":
                tax_share = total_tax / len(participants) if participants else 0
            else:
                tax_share = total_tax * proportion
            
            # Service charge share
            if request.service_charge_distribution == "equal":
                service_share = total_service_charge / len(participants) if participants else 0
            else:
                service_share = total_service_charge * proportion
            
            # Discount share
            if request.discount_distribution == "equal":
                discount_share = total_discount / len(participants) if participants else 0
            else:
                discount_share = total_discount * proportion
            
            # Calculate total
            total = subtotal + tax_share + service_share - discount_share
            
            person_splits.append(PersonSplitResult(
                person_id=pid,
                person_name=data["person_name"],
                items=data["items"],
                subtotal=round(subtotal, 2),
                tax_share=round(tax_share, 2),
                service_charge_share=round(service_share, 2),
                discount_share=round(discount_share, 2),
                total=round(total, 2)
            ))
        
        # Verify totals add up
        calculated_grand_total = sum(ps.total for ps in person_splits)
        if abs(calculated_grand_total - receipt.grand_total) > 0.05:
            validation_warnings.append(
                f"Split total ({calculated_grand_total:.2f}) differs from receipt total ({receipt.grand_total:.2f})"
            )
        
        logger.info(f"Split calculated: {len(person_splits)} participants, total: {calculated_grand_total:.2f}")
        
        return SplitCalculationResponse(
            success=True,
            message="Split calculated successfully",
            person_splits=person_splits,
            totals=SplitTotals(
                items_total=round(items_total, 2),
                subtotal=round(receipt.subtotal, 2),
                total_tax=round(total_tax, 2),
                total_service_charge=round(total_service_charge, 2),
                total_discount=round(total_discount, 2),
                grand_total=round(receipt.grand_total, 2)
            ),
            unassigned_items=unassigned_items,
            validation_warnings=validation_warnings
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating split: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/preview")
async def preview_equal_split(
    receipt_data: ReceiptDataSchema,
    participant_count: int,
    logger=Depends(get_logger_dependency)
):
    """
    Quick preview of an equal split without item assignments.
    
    Useful for showing users what they would owe if splitting equally.
    """
    try:
        if participant_count < 1:
            raise HTTPException(status_code=400, detail="At least 1 participant required")
        
        # Calculate totals
        items_total = sum(item.total_price for item in receipt_data.items)
        
        total_tax = 0.0
        total_service_charge = 0.0
        total_discount = 0.0
        
        for tc in receipt_data.taxes_or_charges:
            if tc.amount < 0:
                total_discount += abs(tc.amount)
            elif "service" in tc.name.lower():
                total_service_charge += tc.amount
            else:
                total_tax += tc.amount
        
        per_person = receipt_data.grand_total / participant_count
        
        return {
            "success": True,
            "participant_count": participant_count,
            "per_person_total": round(per_person, 2),
            "totals": {
                "items_total": round(items_total, 2),
                "subtotal": round(receipt_data.subtotal, 2),
                "total_tax": round(total_tax, 2),
                "total_service_charge": round(total_service_charge, 2),
                "total_discount": round(total_discount, 2),
                "grand_total": round(receipt_data.grand_total, 2)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating preview: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")