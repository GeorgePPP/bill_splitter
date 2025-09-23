# backend/app/services/sessionService.py
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from supabase import create_client, Client
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self.sessions_enabled = settings.enable_sessions
        
        if not self.sessions_enabled:
            logger.info("Session management is DISABLED. Set ENABLE_SESSIONS=true in .env to enable.")
            self.supabase = None
            return
            
        try:
            if not settings.supabase_url or not settings.supabase_anon_key:
                logger.warning("Sessions are enabled but Supabase credentials not configured.")
                logger.warning("Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
                logger.warning("Or set ENABLE_SESSIONS=false to disable session management")
                self.supabase = None
                return
            
            # Validate URL format
            if not self._validate_supabase_url(settings.supabase_url):
                logger.error(f"Invalid Supabase URL format: {settings.supabase_url}")
                logger.error("Expected format: https://your-project-id.supabase.co")
                self.supabase = None
                return
                
            # Check for placeholder values
            if "your-project" in settings.supabase_url.lower() or "your_supabase" in settings.supabase_anon_key.lower():
                logger.error("Supabase credentials contain placeholder values. Please update your .env file with actual credentials.")
                self.supabase = None
                return
            
            logger.info(f"Initializing Supabase client with URL: {settings.supabase_url}")
            self.supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
            logger.info("Session service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize session service: {str(e)}")
            if "getaddrinfo failed" in str(e):
                logger.error("DNS resolution failed. Check your Supabase URL and internet connection.")
            self.supabase = None
    
    def _validate_supabase_url(self, url: str) -> bool:
        """Validate Supabase URL format"""
        import re
        # Should match: https://projectid.supabase.co
        pattern = r'^https://[a-zA-Z0-9]+\.supabase\.co$'
        return bool(re.match(pattern, url))
    
    def generate_session_token(self) -> str:
        """Generate a secure random session token"""
        return secrets.token_urlsafe(32)
    
    async def create_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session"""
        if not self.sessions_enabled:
            raise Exception("Session management is disabled. Set ENABLE_SESSIONS=true in .env to enable.")
            
        if not self.supabase:
            raise Exception("Database connection not available. Please check Supabase configuration.")
            
        session_token = self.generate_session_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)  # 5 minute expiry
        
        try:
            logger.info(f"Creating new session with token: {session_token}")
            
            # Insert into sessions table
            session_result = self.supabase.table("sessions").insert({
                "session_token": session_token,
                "user_id": user_id,
                "expires_at": expires_at.isoformat()
            }).execute()
            
            if not session_result.data:
                raise Exception("Failed to create session record")
            
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
            
            if not bill_session_result.data:
                # Clean up the session record if bill_session creation failed
                self.supabase.table("sessions").delete().eq("session_token", session_token).execute()
                raise Exception("Failed to create bill session record")
            
            logger.info(f"Session created successfully: {session_token}")
            return {
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "created": True
            }
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise Exception(f"Failed to create session: {str(e)}")
    
    async def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session data by token"""
        if not self.sessions_enabled:
            raise Exception("Session management is disabled. Set ENABLE_SESSIONS=true in .env to enable.")
            
        if not self.supabase:
            raise Exception("Database connection not available. Please check Supabase configuration.")
            
        try:
            logger.info(f"Retrieving session: {session_token}")
            
            # Check if session exists and is not expired
            session_result = self.supabase.table("sessions").select("*").eq("session_token", session_token).execute()
            
            if not session_result.data:
                logger.info(f"Session not found: {session_token}")
                return None
            
            session = session_result.data[0]
            
            # Parse the expiry time with proper timezone handling
            expires_at_str = session["expires_at"]
            if expires_at_str.endswith('Z'):
                expires_at_str = expires_at_str[:-1] + '+00:00'
            elif '+' not in expires_at_str and 'T' in expires_at_str:
                expires_at_str += '+00:00'
                
            expires_at = datetime.fromisoformat(expires_at_str)
            current_time = datetime.now(timezone.utc)
            
            if expires_at < current_time:
                # Session expired, clean up
                logger.info(f"Session expired, cleaning up: {session_token}")
                await self.delete_session(session_token)
                return None
            
            # Get bill session data
            bill_result = self.supabase.table("bill_sessions").select("*").eq("session_token", session_token).execute()
            
            if not bill_result.data:
                logger.warning(f"Session found but no bill session data: {session_token}")
                return None
            
            bill_session = bill_result.data[0]
            
            result = {
                "session_token": session_token,
                "expires_at": session["expires_at"],
                "current_step": bill_session["current_step"],
                "participants": bill_session["participants"] or [],
                "receipt_data": bill_session["receipt_data"],
                "receipt_id": bill_session["receipt_id"],
                "item_assignments": bill_session["item_assignments"] or [],
                "split_results": bill_session["split_results"],
                "known_participants": bill_session.get("known_participants", []),
                "created_at": bill_session["created_at"],
                "updated_at": bill_session["updated_at"]
            }
            
            logger.info(f"Session retrieved successfully: {session_token}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_token}: {str(e)}")
            raise Exception(f"Failed to get session: {str(e)}")
    
    async def update_session(self, session_token: str, data: Dict[str, Any]) -> bool:
        """Update session data and extend expiry time"""
        if not self.sessions_enabled:
            raise Exception("Session management is disabled. Set ENABLE_SESSIONS=true in .env to enable.")
            
        if not self.supabase:
            raise Exception("Database connection not available. Please check Supabase configuration.")
            
        try:
            logger.info(f"Updating session: {session_token}")
            
            # Check if session exists and is not expired
            session_data = await self.get_session(session_token)
            if not session_data:
                logger.warning(f"Session not found for update: {session_token}")
                return False
            
            # Extend session expiry by 5 minutes on each update (activity-based extension)
            new_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            session_update_result = self.supabase.table("sessions").update({
                "expires_at": new_expires_at.isoformat()
            }).eq("session_token", session_token).execute()
            
            if not session_update_result.data:
                logger.error(f"Failed to extend session expiry: {session_token}")
                return False
            
            # Prepare update data
            update_data = {}
            allowed_fields = ["current_step", "participants", "receipt_data", "receipt_id", "item_assignments", "split_results", "known_participants"]
            
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            if update_data:
                logger.info(f"Updating bill session data: {list(update_data.keys())}")
                result = self.supabase.table("bill_sessions").update(update_data).eq("session_token", session_token).execute()
                
                if not result.data:
                    logger.error(f"Failed to update bill session data: {session_token}")
                    return False
                    
                logger.info(f"Session updated successfully: {session_token}")
                return True
            else:
                logger.info(f"No valid fields to update for session: {session_token}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating session {session_token}: {str(e)}")
            raise Exception(f"Failed to update session: {str(e)}")
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete a session"""
        if not self.sessions_enabled:
            raise Exception("Session management is disabled. Set ENABLE_SESSIONS=true in .env to enable.")
            
        if not self.supabase:
            raise Exception("Database connection not available. Please check Supabase configuration.")
            
        try:
            logger.info(f"Deleting session: {session_token}")
            
            # Delete from sessions table (bill_sessions will cascade delete if foreign key constraints are set up)
            result = self.supabase.table("sessions").delete().eq("session_token", session_token).execute()
            
            success = len(result.data) > 0 if result.data else False
            if success:
                logger.info(f"Session deleted successfully: {session_token}")
            else:
                logger.warning(f"Session not found for deletion: {session_token}")
                
            return success
        except Exception as e:
            logger.error(f"Error deleting session {session_token}: {str(e)}")
            raise Exception(f"Failed to delete session: {str(e)}")
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        if not self.supabase:
            raise Exception("Database connection not available. Please check Supabase configuration.")
            
        try:
            logger.info("Cleaning up expired sessions")
            current_time = datetime.now(timezone.utc).isoformat()
            result = self.supabase.table("sessions").delete().lt("expires_at", current_time).execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            raise Exception(f"Failed to cleanup expired sessions: {str(e)}")
    

# Global instance
session_service = SessionService()
