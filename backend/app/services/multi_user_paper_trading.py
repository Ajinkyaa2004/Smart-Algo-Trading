"""
Multi-User Paper Trading Manager
Manages separate paper trading engines for each user
"""
from typing import Dict, Optional
from app.services.paper_trading import PaperTradingEngine
import threading


class MultiUserPaperTradingManager:
    """
    Manages separate paper trading engines for each user
    Each user gets their own isolated trading environment
    """
    
    def __init__(self):
        # user_id -> PaperTradingEngine
        self.user_engines: Dict[str, PaperTradingEngine] = {}
        self.lock = threading.Lock()
        print("✓ Multi-User Paper Trading Manager initialized")
    
    def get_engine(self, user_id: str) -> PaperTradingEngine:
        """
        Get or create paper trading engine for a specific user
        
        Args:
            user_id: User ID (from Zerodha profile)
            
        Returns:
            PaperTradingEngine instance for this user
        """
        with self.lock:
            if user_id not in self.user_engines:
                print(f"📊 Creating new paper trading engine for user: {user_id}")
                # Create new engine with user-specific database collections
                engine = PaperTradingEngine(user_id=user_id)
                self.user_engines[user_id] = engine
            
            return self.user_engines[user_id]
    
    def remove_engine(self, user_id: str):
        """Remove engine for a user (called on logout)"""
        with self.lock:
            if user_id in self.user_engines:
                del self.user_engines[user_id]
                print(f"🗑️  Removed paper trading engine for user: {user_id}")


# Global multi-user manager
multi_user_paper_manager = MultiUserPaperTradingManager()
