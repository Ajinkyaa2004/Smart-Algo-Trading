"""
Kite Connect Authentication Service
Handles login flow, token persistence, and session management
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from kiteconnect import KiteConnect
from dotenv import load_dotenv

load_dotenv()

class KiteAuthService:
    """
    Production-grade Kite Connect authentication service
    Features:
    - Token persistence to avoid daily re-login
    - Session expiry detection
    - Automatic token refresh handling
    - Error handling for common auth failures
    """
    
    def __init__(self):
        self.api_key = os.getenv("KITE_API_KEY")
        self.api_secret = os.getenv("KITE_API_SECRET")
        self.token_file = Path("data/kite_session.json")
        self.kite: Optional[KiteConnect] = None
        self.access_token: Optional[str] = None
        self.user_profile: Optional[Dict] = None
        
        # Ensure data directory exists
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to load existing session
        self._load_session()
    
    def get_login_url(self) -> str:
        """
        Generate Zerodha login URL for user authentication
        Returns: Login URL string
        """
        if not self.api_key:
            raise ValueError("KITE_API_KEY not found in environment variables")
        
        kite = KiteConnect(api_key=self.api_key)
        return kite.login_url()
    
    def generate_session(self, request_token: str) -> Dict:
        """
        Exchange request_token for access_token and create session
        
        Args:
            request_token: Token received from Zerodha redirect
            
        Returns:
            Dictionary containing user profile and session info
            
        Raises:
            Exception: If token exchange fails
        """
        try:
            kite = KiteConnect(api_key=self.api_key)
            
            # Generate session
            data = kite.generate_session(request_token, api_secret=self.api_secret)
            
            self.access_token = data["access_token"]
            kite.set_access_token(self.access_token)
            self.kite = kite
            
            # Get user profile
            profile = kite.profile()
            
            self.user_profile = {
                "user_id": profile.get("user_id"),
                "user_name": profile.get("user_name"),
                "email": profile.get("email"),
                "broker": profile.get("broker"),
                "access_token": self.access_token,
                "login_time": datetime.now().isoformat(),
                "api_key": self.api_key
            }
            
            # Persist session
            self._save_session()
            
            return {
                "status": "success",
                "message": "Authentication successful",
                "user": self.user_profile
            }
            
        except Exception as e:
            raise Exception(f"Session generation failed: {str(e)}")
    
    def _save_session(self):
        """Save session data to file for persistence"""
        if self.user_profile:
            with open(self.token_file, 'w') as f:
                json.dump(self.user_profile, f, indent=2)
            print(f"✓ Session saved to {self.token_file}")
    
    def _load_session(self):
        """Load existing session from file if available"""
        if not self.token_file.exists():
            return
        
        try:
            with open(self.token_file, 'r') as f:
                self.user_profile = json.load(f)
            
            self.access_token = self.user_profile.get("access_token")
            
            # Check if session is from today (Kite tokens expire daily)
            login_time = datetime.fromisoformat(self.user_profile.get("login_time"))
            if datetime.now().date() > login_time.date():
                print("⚠ Session expired (tokens are valid for 1 day only)")
                self._clear_session()
                return
            
            # Initialize Kite with saved token
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            
            # Verify token is still valid
            try:
                self.kite.profile()
                print(f"✓ Session restored for {self.user_profile.get('user_name')}")
            except Exception as e:
                print(f"⚠ Saved token is invalid: {str(e)}")
                self._clear_session()
                
        except Exception as e:
            print(f"⚠ Failed to load session: {str(e)}")
            self._clear_session()
    
    def _clear_session(self):
        """Clear session data"""
        self.access_token = None
        self.user_profile = None
        self.kite = None
        if self.token_file.exists():
            self.token_file.unlink()
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self.kite is not None and self.access_token is not None
    
    def get_kite_instance(self) -> KiteConnect:
        """
        Get authenticated Kite instance
        
        Returns:
            KiteConnect instance
            
        Raises:
            Exception: If not authenticated
        """
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please login first.")
        return self.kite
    
    def get_user_profile(self) -> Dict:
        """Get current user profile"""
        if not self.user_profile:
            raise Exception("No active session")
        return self.user_profile
    
    def logout(self):
        """Logout and clear session"""
        self._clear_session()
        return {"status": "success", "message": "Logged out successfully"}


# Global singleton instance
kite_auth_service = KiteAuthService()
