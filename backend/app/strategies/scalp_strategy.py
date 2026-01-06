"""
Scalping Strategy (High Frequency for Testing)
Generates frequent signals based on RSI extremes.
Designed to create multiple trades in 1-2 minutes for testing dashboards.
"""
from typing import Optional, Dict
import pandas as pd
from datetime import datetime
from app.strategies.base_strategy import BaseStrategy, StrategyConfig, TradingSignal, SignalType, PositionType

class ScalpingStrategy(BaseStrategy):
    """
    Rapid Fire Scalping Strategy (Test Strategy)
    - BUY when RSI < 60 (Very aggressive)
    - SELL when RSI > 40 (Very aggressive)
    - Tight Stop Loss (0.2%)
    - Quick Target (0.4%)
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # Strategy Parameters
        self.rsi_period = config.params.get("rsi_period", 7)  # Fast RSI
        self.rsi_buy = config.params.get("rsi_buy", 60)       # High threshold to trigger buys easily
        self.rsi_sell = config.params.get("rsi_sell", 40)     # Low threshold to trigger sells easily
        
        # State
        self.last_signal_time = None
        
    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        """
        Generate rapid signals
        """
        # 1. Update Position PnL if active
        self.update_position(current_price)
        
        # 2. Check Risk Limits
        if not self.check_risk_limits():
            return None
        
        # 3. Check Exit Conditions (Stop Loss / Target)
        exit_signal = self.check_exit_conditions(current_price)
        if exit_signal:
            return exit_signal
        
        # 4. If already in position, don't generate new entry signals
        if self.position is not None:
            return None
            
        # 5. Calculate RSI (Manually or using library)
        # Simple RSI calculation for last few candles
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        if rsi.empty:
            return None
            
        current_rsi = rsi.iloc[-1]
        
        timestamp = datetime.now()
        
        # LOGIC: Extremely sensitive triggers
        # Just alternate basically.
        
        signal = None
        
        # BUY Condition
        if current_rsi < self.rsi_buy:
            signal = TradingSignal(
                timestamp=timestamp,
                symbol=self.config.symbol,
                signal_type=SignalType.BUY,
                price=current_price,
                quantity=0, # Calculated later
                stop_loss=self.calculate_stop_loss(current_price, SignalType.BUY),
                target=self.calculate_target(current_price, SignalType.BUY),
                reason=f"Scalp Buy (RSI: {current_rsi:.2f})",
                confidence=0.8
            )
            
        # SELL Condition (Short)
        elif current_rsi > self.rsi_sell:
            signal = TradingSignal(
                timestamp=timestamp,
                symbol=self.config.symbol,
                signal_type=SignalType.SELL, # FIXED: Was SignalType.SHORT
                price=current_price,
                quantity=0,
                stop_loss=self.calculate_stop_loss(current_price, SignalType.SELL),
                target=self.calculate_target(current_price, SignalType.SELL),
                reason=f"Scalp Short (RSI: {current_rsi:.2f})",
                confidence=0.8
            )
            
        return signal

    def calculate_stop_loss(self, entry_price: float, signal_type: SignalType) -> float:
        """Tight 0.2% SL"""
        sl_pct = 0.002
        if signal_type == SignalType.BUY:
            return entry_price * (1 - sl_pct)
        else:
            return entry_price * (1 + sl_pct)

    def calculate_target(self, entry_price: float, signal_type: SignalType) -> float:
        """Quick 0.4% Target"""
        target_pct = 0.004
        if signal_type == SignalType.BUY:
            return entry_price * (1 + target_pct)
        else:
            return entry_price * (1 - target_pct)
