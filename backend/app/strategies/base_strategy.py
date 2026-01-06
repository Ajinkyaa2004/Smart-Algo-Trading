"""
Base Strategy Framework
Defines the interface and common functionality for all trading strategies
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime
import pandas as pd
from enum import Enum


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    EXIT = "EXIT"


class PositionType(Enum):
    """Position types"""
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


@dataclass
class TradingSignal:
    """Trading signal with entry/exit details"""
    timestamp: datetime
    symbol: str
    signal_type: SignalType
    price: float
    quantity: int
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    reason: str = ""
    confidence: float = 1.0
    metadata: Dict = None


@dataclass
class Position:
    """Active trading position"""
    symbol: str
    position_type: PositionType
    entry_price: float
    quantity: int
    entry_time: datetime
    stop_loss: float
    target: float
    current_price: float = 0.0
    pnl: float = 0.0
    order_id: Optional[str] = None


@dataclass
class StrategyConfig:
    """Strategy configuration"""
    name: str
    symbol: str
    exchange: str = "NSE"
    capital: float = 100000.0
    risk_per_trade: float = 0.02  # 2% risk per trade
    max_positions: int = 3
    product: str = "MIS"  # MIS, CNC, NRML
    
    # Risk management
    max_loss_per_day: float = 5000.0
    max_trades_per_day: int = 10
    
    # Strategy-specific parameters
    params: Dict = None


class BaseStrategy(ABC):
    """
    Base class for all trading strategies
    Provides common functionality and enforces interface
    """
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.position: Optional[Position] = None
        self.signals: List[TradingSignal] = []
        self.trades_today = 0
        self.pnl_today = 0.0
        self.is_active = True
        
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        """
        Generate trading signal based on strategy logic
        
        Args:
            df: Historical OHLCV data
            current_price: Current market price
            
        Returns:
            TradingSignal or None
        """
        pass
    
    @abstractmethod
    def calculate_stop_loss(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate stop-loss price
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Stop-loss price
        """
        pass
    
    @abstractmethod
    def calculate_target(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate target price
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Target price
        """
        pass
    
    def calculate_position_size(self, entry_price: float, stop_loss: float) -> int:
        """
        Calculate position size based on risk management
        
        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            
        Returns:
            Quantity to trade
        """
        # Risk amount per trade
        risk_amount = self.config.capital * self.config.risk_per_trade
        
        # Risk per share
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            return 0
        
        # Calculate quantity
        quantity = int(risk_amount / risk_per_share)
        
        # Ensure we don't exceed capital
        max_quantity = int(self.config.capital / entry_price)
        
        return min(quantity, max_quantity)
    
    def check_risk_limits(self) -> bool:
        """
        Check if risk limits are breached
        
        Returns:
            True if within limits, False otherwise
        """
        # Check daily loss limit
        if abs(self.pnl_today) >= self.config.max_loss_per_day:
            print(f"⚠ Daily loss limit reached: ₹{self.pnl_today:.2f}")
            return False
        
        # Check daily trade limit
        if self.trades_today >= self.config.max_trades_per_day:
            print(f"⚠ Daily trade limit reached: {self.trades_today} trades")
            return False
        
        # Check max positions
        if self.position is not None:
            print(f"⚠ Already in position")
            return False
        
        return True
    
    def update_position(self, current_price: float):
        """
        Update position with current price and check exit conditions
        
        Args:
            current_price: Current market price
        """
        if self.position is None:
            return
        
        self.position.current_price = current_price
        
        # Calculate PnL
        if self.position.position_type == PositionType.LONG:
            self.position.pnl = (current_price - self.position.entry_price) * self.position.quantity
        else:  # SHORT
            self.position.pnl = (self.position.entry_price - current_price) * self.position.quantity
    
    def check_exit_conditions(self, current_price: float) -> Optional[TradingSignal]:
        """
        Check if stop-loss or target is hit
        
        Args:
            current_price: Current market price
            
        Returns:
            EXIT signal if conditions met, None otherwise
        """
        if self.position is None:
            return None
        
        exit_signal = None
        
        if self.position.position_type == PositionType.LONG:
            # Check stop-loss
            if current_price <= self.position.stop_loss:
                exit_signal = TradingSignal(
                    timestamp=datetime.now(),
                    symbol=self.config.symbol,
                    signal_type=SignalType.EXIT,
                    price=current_price,
                    quantity=self.position.quantity,
                    reason="Stop-loss hit",
                    metadata={"exit_type": "stop_loss"}
                )
            
            # Check target
            elif current_price >= self.position.target:
                exit_signal = TradingSignal(
                    timestamp=datetime.now(),
                    symbol=self.config.symbol,
                    signal_type=SignalType.EXIT,
                    price=current_price,
                    quantity=self.position.quantity,
                    reason="Target reached",
                    metadata={"exit_type": "target"}
                )
        
        else:  # SHORT position
            # Check stop-loss
            if current_price >= self.position.stop_loss:
                exit_signal = TradingSignal(
                    timestamp=datetime.now(),
                    symbol=self.config.symbol,
                    signal_type=SignalType.EXIT,
                    price=current_price,
                    quantity=self.position.quantity,
                    reason="Stop-loss hit",
                    metadata={"exit_type": "stop_loss"}
                )
            
            # Check target
            elif current_price <= self.position.target:
                exit_signal = TradingSignal(
                    timestamp=datetime.now(),
                    symbol=self.config.symbol,
                    signal_type=SignalType.EXIT,
                    price=current_price,
                    quantity=self.position.quantity,
                    reason="Target reached",
                    metadata={"exit_type": "target"}
                )
        
        return exit_signal
    
    def open_position(self, signal: TradingSignal):
        """
        Open a new position
        
        Args:
            signal: Trading signal with entry details
        """
        position_type = PositionType.LONG if signal.signal_type == SignalType.BUY else PositionType.SHORT
        
        self.position = Position(
            symbol=signal.symbol,
            position_type=position_type,
            entry_price=signal.price,
            quantity=signal.quantity,
            entry_time=signal.timestamp,
            stop_loss=signal.stop_loss,
            target=signal.target,
            current_price=signal.price
        )
        
        self.trades_today += 1
        print(f"✓ Position opened: {position_type.value} {signal.quantity} @ ₹{signal.price:.2f}")
    
    def close_position(self, exit_price: float, reason: str = "Manual exit"):
        """
        Close current position
        
        Args:
            exit_price: Exit price
            reason: Reason for exit
        """
        if self.position is None:
            return
        
        # Calculate final PnL
        if self.position.position_type == PositionType.LONG:
            pnl = (exit_price - self.position.entry_price) * self.position.quantity
        else:
            pnl = (self.position.entry_price - exit_price) * self.position.quantity
        
        self.pnl_today += pnl
        
        print(f"✓ Position closed: PnL = ₹{pnl:.2f} ({reason})")
        
        self.position = None
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.trades_today = 0
        self.pnl_today = 0.0
        self.is_active = True
    
    def get_status(self) -> Dict:
        """
        Get current strategy status
        
        Returns:
            Status dictionary
        """
        return {
            "name": self.config.name,
            "symbol": self.config.symbol,
            "is_active": self.is_active,
            "has_position": self.position is not None,
            "position": {
                "type": self.position.position_type.value if self.position else None,
                "entry_price": self.position.entry_price if self.position else None,
                "current_price": self.position.current_price if self.position else None,
                "quantity": self.position.quantity if self.position else None,
                "pnl": self.position.pnl if self.position else 0.0,
                "stop_loss": self.position.stop_loss if self.position else None,
                "target": self.position.target if self.position else None
            } if self.position else None,
            "trades_today": self.trades_today,
            "pnl_today": self.pnl_today,
            "capital": self.config.capital
        }
