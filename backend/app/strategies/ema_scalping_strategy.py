"""
EMA Scalping Strategy (9 EMA / 21 EMA)
Classic crossover strategy for high-frequency scalping
"""
import pandas as pd
from typing import Optional
from datetime import datetime
from app.strategies.base_strategy import (
    BaseStrategy, StrategyConfig, TradingSignal, SignalType
)
from app.services.indicators import TechnicalIndicators # Assuming this exists or I'll use pandas_ta if needed

class EMAScalpingStrategy(BaseStrategy):
    """
    9/21 EMA Scalping Strategy
    
    Entry:
    - BUY: 9 EMA crosses ABOVE 21 EMA
    - SELL: 9 EMA crosses BELOW 21 EMA
    
    Exit:
    - Fixed Ratio (1:1.5) or Reverse Cross
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.fast_period = config.params.get('fast_period', 9)
        self.slow_period = config.params.get('slow_period', 21)
        self.sl_pct = config.params.get('sl_pct', 0.005) # 0.5% SL
        self.target_pct = config.params.get('target_pct', 0.01) # 1.0% Target
    
    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        # 1. Update Position
        self.update_position(current_price)
        
        # 2. Risk check
        if not self.check_risk_limits():
            return None
            
        # 3. Exit check
        exit_signal = self.check_exit_conditions(current_price)
        if exit_signal:
            return exit_signal
            
        # 4. No new entries if active
        if self.position is not None:
            return None
            
        if len(df) < self.slow_period + 5:
            return None
            
        # Calculate EMAs
        # Using pandas ewm if TechnicalIndicators not fully robust, but let's assume simple calculation
        df['ema_fast'] = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        timestamp = datetime.now()
        
        # Buy Cross
        if prev['ema_fast'] <= prev['ema_slow'] and curr['ema_fast'] > curr['ema_slow']:
            return TradingSignal(
                timestamp=timestamp,
                symbol=self.config.symbol,
                signal_type=SignalType.BUY,
                price=current_price,
                quantity=0,
                stop_loss=self.calculate_stop_loss(current_price, SignalType.BUY),
                target=self.calculate_target(current_price, SignalType.BUY),
                reason=f"EMA Cross (9 > 21)",
                confidence=0.9
            )
            
        # Sell Cross
        elif prev['ema_fast'] >= prev['ema_slow'] and curr['ema_fast'] < curr['ema_slow']:
            return TradingSignal(
                timestamp=timestamp,
                symbol=self.config.symbol,
                signal_type=SignalType.SELL,
                price=current_price,
                quantity=0,
                stop_loss=self.calculate_stop_loss(current_price, SignalType.SELL),
                target=self.calculate_target(current_price, SignalType.SELL),
                reason=f"EMA Cross (9 < 21)",
                confidence=0.9
            )
            
        return None

    def calculate_stop_loss(self, entry_price: float, signal_type: SignalType) -> float:
        if signal_type == SignalType.BUY:
            return entry_price * (1 - self.sl_pct)
        else:
            return entry_price * (1 + self.sl_pct)

    def calculate_target(self, entry_price: float, signal_type: SignalType) -> float:
        if signal_type == SignalType.BUY:
            return entry_price * (1 + self.target_pct)
        else:
            return entry_price * (1 - self.target_pct)
