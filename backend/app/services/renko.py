"""
Renko Brick Calculator
Converts price ticks into Renko bricks for trend identification
"""
from typing import Dict, Optional
from dataclasses import dataclass
import threading


@dataclass
class RenkoBrick:
    """Renko Brick State"""
    brick_size: float
    upper_limit: Optional[float] = None
    lower_limit: Optional[float] = None
    brick_count: int = 0  # Positive = uptrend, Negative = downtrend
    last_price: float = 0.0


class RenkoCalculator:
    """
    Renko Chart Calculator
    
    Renko charts filter out minor price movements and show only significant moves.
    - Each brick represents a fixed price movement (brick size)
    - Green bricks (positive count) = uptrend
    - Red bricks (negative count) = downtrend
    """
    
    def __init__(self):
        # Store renko state for each instrument
        # {symbol: RenkoBrick}
        self.renko_state: Dict[str, RenkoBrick] = {}
        self.lock = threading.Lock()
    
    def initialize_brick(self, symbol: str, brick_size: float, initial_price: float = None):
        """
        Initialize renko brick for a symbol
        
        Args:
            symbol: Trading symbol
            brick_size: Size of each brick
            initial_price: Initial price (optional)
        """
        with self.lock:
            brick = RenkoBrick(brick_size=brick_size)
            
            if initial_price:
                brick.upper_limit = initial_price + brick_size
                brick.lower_limit = initial_price - brick_size
                brick.last_price = initial_price
            
            self.renko_state[symbol] = brick
            print(f"✓ Renko initialized for {symbol}: brick_size={brick_size}")
    
    def update_brick(self, symbol: str, price: float) -> Dict:
        """
        Update renko brick with new price
        
        Args:
            symbol: Trading symbol
            price: Current price
            
        Returns:
            Dictionary with brick state and change info
        """
        with self.lock:
            if symbol not in self.renko_state:
                # Auto-initialize with default brick size
                self.initialize_brick(symbol, brick_size=1.0, initial_price=price)
                return {'symbol': symbol, 'brick_formed': False, 'brick_count': 0}
            
            brick = self.renko_state[symbol]
            brick.last_price = price
            
            # Initialize limits if not set
            if brick.upper_limit is None:
                brick.upper_limit = price + brick.brick_size
                brick.lower_limit = price - brick.brick_size
                return {'symbol': symbol, 'brick_formed': False, 'brick_count': 0}
            
            brick_formed = False
            old_count = brick.brick_count
            
            # Check if price broke upper limit (uptrend)
            if price > brick.upper_limit:
                # Calculate how many bricks formed
                gap = (price - brick.upper_limit) // brick.brick_size
                bricks_formed = 1 + gap
                
                # Update limits
                brick.lower_limit = brick.upper_limit + (gap * brick.brick_size) - brick.brick_size
                brick.upper_limit = brick.upper_limit + (bricks_formed * brick.brick_size)
                
                # Update brick count (positive = uptrend)
                brick.brick_count = max(1, brick.brick_count + bricks_formed)
                brick_formed = True
            
            # Check if price broke lower limit (downtrend)
            elif price < brick.lower_limit:
                # Calculate how many bricks formed
                gap = (brick.lower_limit - price) // brick.brick_size
                bricks_formed = 1 + gap
                
                # Update limits
                brick.upper_limit = brick.lower_limit - (gap * brick.brick_size) + brick.brick_size
                brick.lower_limit = brick.lower_limit - (bricks_formed * brick.brick_size)
                
                # Update brick count (negative = downtrend)
                brick.brick_count = min(-1, brick.brick_count - bricks_formed)
                brick_formed = True
            
            return {
                'symbol': symbol,
                'brick_formed': brick_formed,
                'brick_count': brick.brick_count,
                'brick_change': brick.brick_count - old_count,
                'upper_limit': brick.upper_limit,
                'lower_limit': brick.lower_limit,
                'price': price
            }
    
    def get_brick_state(self, symbol: str) -> Optional[RenkoBrick]:
        """Get current brick state for symbol"""
        return self.renko_state.get(symbol)
    
    def get_brick_count(self, symbol: str) -> int:
        """Get brick count (positive = uptrend, negative = downtrend)"""
        brick = self.renko_state.get(symbol)
        return brick.brick_count if brick else 0
    
    def is_strong_uptrend(self, symbol: str, threshold: int = 2) -> bool:
        """Check if in strong uptrend (brick count >= threshold)"""
        return self.get_brick_count(symbol) >= threshold
    
    def is_strong_downtrend(self, symbol: str, threshold: int = 2) -> bool:
        """Check if in strong downtrend (brick count <= -threshold)"""
        return self.get_brick_count(symbol) <= -threshold
    
    def reset_brick(self, symbol: str):
        """Reset brick state for symbol"""
        if symbol in self.renko_state:
            del self.renko_state[symbol]
    
    def get_all_states(self) -> Dict[str, Dict]:
        """Get all renko states"""
        return {
            symbol: {
                'brick_size': brick.brick_size,
                'brick_count': brick.brick_count,
                'upper_limit': brick.upper_limit,
                'lower_limit': brick.lower_limit,
                'last_price': brick.last_price
            }
            for symbol, brick in self.renko_state.items()
        }


# Global singleton instance
renko_calculator = RenkoCalculator()
