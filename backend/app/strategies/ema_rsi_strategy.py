"""
Strategy 1: EMA + RSI Indicator-Based Strategy
Combines EMA crossover with RSI for trend-following entries
"""
import pandas as pd
from typing import Optional
from datetime import datetime
from app.strategies.base_strategy import (
    BaseStrategy, StrategyConfig, TradingSignal, SignalType
)
from app.services.indicators import TechnicalIndicators


class EMA_RSI_Strategy(BaseStrategy):
    """
    EMA + RSI Indicator Strategy
    
    Entry Conditions:
    - BUY: EMA(9) crosses above EMA(21) AND RSI < 70
    - SELL: EMA(9) crosses below EMA(21) AND RSI > 30
    
    Stop Loss:
    - BUY: 2% below entry
    - SELL: 2% above entry
    
    Target:
    - BUY: 1:2 risk-reward (4% above entry)
    - SELL: 1:2 risk-reward (4% below entry)
    
    Risk Management:
    - Position size based on 2% capital risk
    - Maximum 3 positions
    - Daily loss limit: ₹5000
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # Default parameters
        self.fast_ema = config.params.get('fast_ema', 9) if config.params else 9
        self.slow_ema = config.params.get('slow_ema', 21) if config.params else 21
        self.rsi_period = config.params.get('rsi_period', 14) if config.params else 14
        self.rsi_overbought = config.params.get('rsi_overbought', 70) if config.params else 70
        self.rsi_oversold = config.params.get('rsi_oversold', 30) if config.params else 30
        
        # Stop-loss and target percentages
        self.stop_loss_pct = config.params.get('stop_loss_pct', 0.02) if config.params else 0.02  # 2%
        self.target_pct = config.params.get('target_pct', 0.04) if config.params else 0.04  # 4% (1:2 RR)
    
    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        """
        Generate trading signal based on EMA crossover and RSI
        
        Args:
            df: Historical OHLCV data with at least 50 candles
            current_price: Current market price
            
        Returns:
            TradingSignal or None
        """
        # Check if we have enough data
        if len(df) < max(self.slow_ema, self.rsi_period) + 5:
            return None
        
        # Check risk limits
        if not self.check_risk_limits():
            return None
        
        # Calculate indicators
        df = df.copy()
        df['ema_fast'] = TechnicalIndicators.ema(df['close'], self.fast_ema)
        df['ema_slow'] = TechnicalIndicators.ema(df['close'], self.slow_ema)
        df['rsi'] = TechnicalIndicators.rsi_ema(df['close'], self.rsi_period)
        
        # Get latest values
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check for EMA crossover
        bullish_cross = (previous['ema_fast'] <= previous['ema_slow'] and 
                        current['ema_fast'] > current['ema_slow'])
        
        bearish_cross = (previous['ema_fast'] >= previous['ema_slow'] and 
                        current['ema_fast'] < current['ema_slow'])
        
        # Generate BUY signal
        if bullish_cross and current['rsi'] < self.rsi_overbought:
            stop_loss = self.calculate_stop_loss(current_price, SignalType.BUY)
            target = self.calculate_target(current_price, SignalType.BUY)
            quantity = self.calculate_position_size(current_price, stop_loss)
            
            if quantity > 0:
                return TradingSignal(
                    timestamp=datetime.now(),
                    symbol=self.config.symbol,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    target=target,
                    reason=f"EMA bullish crossover + RSI {current['rsi']:.1f}",
                    confidence=0.8,
                    metadata={
                        "ema_fast": current['ema_fast'],
                        "ema_slow": current['ema_slow'],
                        "rsi": current['rsi']
                    }
                )
        
        # Generate SELL signal
        elif bearish_cross and current['rsi'] > self.rsi_oversold:
            stop_loss = self.calculate_stop_loss(current_price, SignalType.SELL)
            target = self.calculate_target(current_price, SignalType.SELL)
            quantity = self.calculate_position_size(current_price, stop_loss)
            
            if quantity > 0:
                return TradingSignal(
                    timestamp=datetime.now(),
                    symbol=self.config.symbol,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    target=target,
                    reason=f"EMA bearish crossover + RSI {current['rsi']:.1f}",
                    confidence=0.8,
                    metadata={
                        "ema_fast": current['ema_fast'],
                        "ema_slow": current['ema_slow'],
                        "rsi": current['rsi']
                    }
                )
        
        return None
    
    def calculate_stop_loss(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate stop-loss: 2% from entry
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Stop-loss price
        """
        if signal_type == SignalType.BUY:
            return entry_price * (1 - self.stop_loss_pct)
        else:  # SELL
            return entry_price * (1 + self.stop_loss_pct)
    
    def calculate_target(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate target: 4% from entry (1:2 risk-reward)
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Target price
        """
        if signal_type == SignalType.BUY:
            return entry_price * (1 + self.target_pct)
        else:  # SELL
            return entry_price * (1 - self.target_pct)
