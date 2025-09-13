# backend/app/api/routes/session.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from ...services.sessionService import session_service

router = APIRouter(prefix="/session", tags=["session"])

class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None

class UpdateSessionRequest(BaseModel):
    current_step: Optional[int] = None
    participants: Optional[List[Dict[str, Any]]] = None
    receipt_data: Optional[Dict[str, Any]] = None
    receipt_id: Optional[str] = None
    item_assignments: Optional[List[Dict[str, Any]]] = None
    split_results: Optional[List[Dict[str, Any]]] = None
    known_participants: Optional[List[Dict[str, Any]]] = None

@router.post("/create")
async def create_session(request: CreateSessionRequest = CreateSessionRequest()):
    """Create a new guest session"""
    try:
        result = await session_service.create_session(request.user_id)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/{session_token}")
async def get_session(session_token: str):
    """Get complete session data"""
    try:
        session_data = await session_service.get_session(session_token)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )
        
        return {
            "success": True,
            "data": session_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )

@router.put("/{session_token}")
async def update_session(session_token: str, request: UpdateSessionRequest):
    """Update session data"""
    try:
        # Convert request to dict, excluding None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        success = await session_service.update_session(session_token, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )
        
        return {
            "success": True,
            "message": "Session updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )

@router.delete("/{session_token}")
async def delete_session(session_token: str):
    """Delete a session"""
    try:
        success = await session_service.delete_session(session_token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {
            "success": True,
            "message": "Session deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )

