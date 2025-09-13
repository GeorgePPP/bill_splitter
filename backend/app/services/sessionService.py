# backend/app/services/sessionService.py
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import create_client, Client
from ..core.config import settings

class SessionService:
    def __init__(self):
        if settings.supabase_url and settings.supabase_anon_key:
            self.supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
        else:
            raise ValueError("Supabase URL and key must be provided")
    
    def generate_session_token(self) -> str:
        """Generate a secure random session token"""
        return secrets.token_urlsafe(32)
    
    async def create_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session"""
        session_token = self.generate_session_token()
        expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5 minute expiry
        
        try:
            # Insert into sessions table
            session_result = self.supabase.table("sessions").insert({
                "session_token": session_token,
                "user_id": user_id,
                "expires_at": expires_at.isoformat()
            }).execute()
            
            # Insert into bill_sessions table
            bill_session_result = self.supabase.table("bill_sessions").insert({
                "session_token": session_token,
                "current_step": 1,
                "participants": [],
                "receipt_data": None,
                "receipt_id": None,
                "item_assignments": [],
                "split_results": None,
                "known_participants": []  # Store all participants ever added to this session
            }).execute()
            
            return {
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "created": True
            }
        except Exception as e:
            raise Exception(f"Failed to create session: {str(e)}")
    
    async def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session data by token"""
        try:
            # Check if session exists and is not expired
            session_result = self.supabase.table("sessions").select("*").eq("session_token", session_token).execute()
            
            if not session_result.data:
                return None
            
            session = session_result.data[0]
            expires_at = datetime.fromisoformat(session["expires_at"].replace('Z', '+00:00'))
            
            if expires_at < datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
                # Session expired, clean up
                await self.delete_session(session_token)
                return None
            
            # Get bill session data
            bill_result = self.supabase.table("bill_sessions").select("*").eq("session_token", session_token).execute()
            
            if not bill_result.data:
                return None
            
            bill_session = bill_result.data[0]
            
            return {
                "session_token": session_token,
                "expires_at": session["expires_at"],
                "current_step": bill_session["current_step"],
                "participants": bill_session["participants"],
                "receipt_data": bill_session["receipt_data"],
                "receipt_id": bill_session["receipt_id"],
                "item_assignments": bill_session["item_assignments"],
                "split_results": bill_session["split_results"],
                "known_participants": bill_session.get("known_participants", []),
                "created_at": bill_session["created_at"],
                "updated_at": bill_session["updated_at"]
            }
        except Exception as e:
            raise Exception(f"Failed to get session: {str(e)}")
    
    async def update_session(self, session_token: str, data: Dict[str, Any]) -> bool:
        """Update session data and extend expiry time"""
        try:
            # Check if session exists and is not expired
            session_data = await self.get_session(session_token)
            if not session_data:
                return False
            
            # Extend session expiry by 5 minutes on each update (activity-based extension)
            new_expires_at = datetime.utcnow() + timedelta(minutes=5)
            self.supabase.table("sessions").update({
                "expires_at": new_expires_at.isoformat()
            }).eq("session_token", session_token).execute()
            
            # Prepare update data
            update_data = {}
            allowed_fields = ["current_step", "participants", "receipt_data", "receipt_id", "item_assignments", "split_results", "known_participants"]
            
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            if update_data:
                result = self.supabase.table("bill_sessions").update(update_data).eq("session_token", session_token).execute()
                return len(result.data) > 0
            
            return True
        except Exception as e:
            raise Exception(f"Failed to update session: {str(e)}")
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete a session"""
        try:
            # Delete from sessions table (bill_sessions will cascade delete)
            result = self.supabase.table("sessions").delete().eq("session_token", session_token).execute()
            return len(result.data) > 0
        except Exception as e:
            raise Exception(f"Failed to delete session: {str(e)}")
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            current_time = datetime.utcnow().isoformat()
            result = self.supabase.table("sessions").delete().lt("expires_at", current_time).execute()
            return len(result.data)
        except Exception as e:
            raise Exception(f"Failed to cleanup expired sessions: {str(e)}")
    

# Global instance
session_service = SessionService()
