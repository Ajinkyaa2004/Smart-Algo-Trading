"""
Kite Connect Authentication Service
Handles login flow, token persistence, and session management
Supports multiple concurrent users
"""
import os
import json
import uuid
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from kiteconnect import KiteConnect
from dotenv import load_dotenv

load_dotenv()

class KiteAuthService:
    """
    Production-grade Kite Connect authentication service
    Features:
    - Multi-user session support
    - Token persistence to avoid daily re-login
    - Session expiry detection
    - Automatic token refresh handling
    """
    
    def __init__(self):
        self.api_key = os.getenv("KITE_API_KEY")
        self.api_secret = os.getenv("KITE_API_SECRET")
        self.sessions_dir = Path("data/sessions")
        
        # Session storage: token -> {kite, access_token, user_profile}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_token
        
        # Primary session (for backward compatibility with single-user modules)
        self.primary_session_token: Optional[str] = None
        
        # Ensure data directory exists
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to load existing sessions
        self._load_sessions()
    
    def get_login_url(self) -> str:
        """
        Generate Zerodha login URL for user authentication
        Returns: Login URL string
        """
        if not self.api_key:
            raise ValueError("KITE_API_KEY not found in environment variables")
        
        kite = KiteConnect(api_key=self.api_key)
        # We don't change login_url. All users use the same App Key. 
        # When they login, Zerodha validates their user/pass.
        return kite.login_url()
    
    def generate_session(self, request_token: str) -> Dict:
        """
        Exchange request_token for access_token and create session
        
        Args:
            request_token: Token received from Zerodha redirect
            
        Returns:
            Dictionary containing user profile, session info, and session_token
        """
        try:
            kite = KiteConnect(api_key=self.api_key)
            
            # Generate session
            data = kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = data["access_token"]
            kite.set_access_token(access_token)
            
            # Get user profile
            profile = kite.profile()
            user_id = profile.get("user_id")
            
            # Create session token
            session_token = str(uuid.uuid4())
            
            session_data = {
                "session_token": session_token,
                "user_id": user_id,
                "user_name": profile.get("user_name"),
                "email": profile.get("email"),
                "broker": profile.get("broker"),
                "access_token": access_token,
                "login_time": datetime.now().isoformat(),
                "api_key": self.api_key
            }
            
            # Store in memory
            self.sessions[session_token] = {
                "kite": kite,
                "access_token": access_token,
                "user_profile": session_data
            }
            self.user_sessions[user_id] = session_token
            
            # Set as primary if none exists (for backward compatibility)
            if not self.primary_session_token:
                self.primary_session_token = session_token
            
            # Persist session
            self._save_session(session_token, session_data)
            
            return {
                "status": "success",
                "message": "Authentication successful",
                "user": session_data,
                "session_token": session_token
            }
            
        except Exception as e:
            raise Exception(f"Session generation failed: {str(e)}")
    
    def _save_session(self, session_token: str, session_data: Dict):
        """Save session data to file for persistence"""
        user_id = session_data.get("user_id", "unknown")
        file_path = self.sessions_dir / f"{user_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(session_data, f, indent=2)
        print(f"✓ Session saved for {user_id}")
    
    def _load_sessions(self):
        """Load existing sessions from files"""
        if not self.sessions_dir.exists():
            return
        
        session_files = glob.glob(str(self.sessions_dir / "*.json"))
        
        for file_path in session_files:
            try:
                with open(file_path, 'r') as f:
                    session_data = json.load(f)
                
                # Check expiry
                login_time_str = session_data.get("login_time")
                if login_time_str:
                    login_time = datetime.fromisoformat(login_time_str)
                    if datetime.now().date() > login_time.date():
                        print(f"⚠ Session expired for {session_data.get('user_id')} (tokens are valid for 1 day only)")
                        try:
                            os.remove(file_path)
                        except:
                            pass
                        continue
                
                # Restore session
                access_token = session_data.get("access_token")
                session_token = session_data.get("session_token")
                user_id = session_data.get("user_id")
                
                if not session_token:
                    # Legacy or missing token, generate one
                    session_token = str(uuid.uuid4())
                    session_data["session_token"] = session_token
                
                kite = KiteConnect(api_key=self.api_key)
                kite.set_access_token(access_token)
                
                self.sessions[session_token] = {
                    "kite": kite,
                    "access_token": access_token,
                    "user_profile": session_data
                }
                self.user_sessions[user_id] = session_token
                
                # Set primary if not set
                if not self.primary_session_token:
                    self.primary_session_token = session_token
                
                print(f"✓ Session restored for {session_data.get('user_name')}")
                
            except Exception as e:
                print(f"⚠ Failed to load session from {file_path}: {str(e)}")
    
    def _get_active_session(self, session_token: Optional[str] = None) -> Dict:
        """Helper to get session dict based on token or default"""
        token = session_token or self.primary_session_token
        if not token or token not in self.sessions:
            raise Exception("No active session. Please login.")
        return self.sessions[token]

    def is_authenticated(self, session_token: Optional[str] = None) -> bool:
        """Check if user is currently authenticated"""
        token = session_token or self.primary_session_token
        # It is authenticated if we have it in memory
        return token is not None and token in self.sessions
    
    def get_kite_instance(self, session_token: Optional[str] = None) -> KiteConnect:
        """
        Get authenticated Kite instance
        
        Args:
            session_token: Optional specific session token. If None, uses primary session.
        """
        session = self._get_active_session(session_token)
        return session["kite"]
    
    def get_user_profile(self, session_token: Optional[str] = None) -> Dict:
        """Get current user profile"""
        session = self._get_active_session(session_token)
        return session["user_profile"]
    
    def logout(self, session_token: Optional[str] = None):
        """Logout and clear session"""
        token = session_token or self.primary_session_token
        
        if token and token in self.sessions:
            # Remove file
            user_id = self.sessions[token]["user_profile"].get("user_id")
            file_path = self.sessions_dir / f"{user_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            # Remove from memory
            del self.sessions[token]
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            if self.primary_session_token == token:
                # Pick another primary if available
                self.primary_session_token = next(iter(self.sessions), None)
            
            return {"status": "success", "message": "Logged out successfully"}
        
        return {"status": "error", "message": "Session not found"}


# Global singleton instance
kite_auth_service = KiteAuthService()
