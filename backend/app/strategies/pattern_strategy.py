"""
Strategy 3: Candlestick Pattern Confirmation Strategy
Trades high-confidence candlestick patterns with trend confirmation
"""
import pandas as pd
from typing import Optional
from datetime import datetime
from app.strategies.base_strategy import (
    BaseStrategy, StrategyConfig, TradingSignal, SignalType
)
from app.services.pattern_scanner import pattern_scanner
from app.services.price_action import price_action_service
from app.services.indicators import TechnicalIndicators


class PatternConfirmationStrategy(BaseStrategy):
    """
    Candlestick Pattern Confirmation Strategy
    
    Entry Conditions:
    - BUY: Bullish pattern (confidence ≥ 80%) + uptrend confirmation
    - SELL: Bearish pattern (confidence ≥ 80%) + downtrend confirmation
    
    Pattern Priority (High to Low):
    1. Morning Star / Evening Star (90% confidence)
    2. Bullish/Bearish Engulfing (85% confidence)
    3. Hammer / Shooting Star (80% confidence)
    
    Trend Confirmation:
    - Price above/below 50 EMA
    - ADX > 20 (trending market)
    
    Stop Loss:
    - BUY: Below pattern low
    - SELL: Above pattern high
    
    Target:
    - Minimum 1:2 risk-reward ratio
    - Based on recent swing high/low
    
    Risk Management:
    - Only trade high-confidence patterns
    - Require trend alignment
    - Position size based on 2% capital risk
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # Default parameters
        self.min_confidence = config.params.get('min_confidence', 0.80) if config.params else 0.80
        self.trend_ema = config.params.get('trend_ema', 50) if config.params else 50
        self.min_adx = config.params.get('min_adx', 20) if config.params else 20
        self.min_rr_ratio = config.params.get('min_rr_ratio', 2.0) if config.params else 2.0
        
        # Patterns to trade
        self.bullish_patterns = [
            'morning_star', 'bullish_engulfing', 'hammer', 'piercing_line'
        ]
        self.bearish_patterns = [
            'evening_star', 'bearish_engulfing', 'shooting_star', 'dark_cloud_cover'
        ]
    
    def _check_trend_confirmation(self, df: pd.DataFrame, direction: str) -> bool:
        """
        Check if trend aligns with pattern direction
        
        Args:
            df: Historical data
            direction: 'bullish' or 'bearish'
            
        Returns:
            True if trend confirmed
        """
        # Calculate EMA
        ema = TechnicalIndicators.ema(df['close'], self.trend_ema)
        current_price = df['close'].iloc[-1]
        current_ema = ema.iloc[-1]
        
        # Calculate ADX for trend strength
        adx, plus_di, minus_di = TechnicalIndicators.adx(df)
        current_adx = adx.iloc[-1]
        
        # Check trend strength
        if current_adx < self.min_adx:
            return False  # Not trending enough
        
        # Check trend direction
        if direction == 'bullish':
            return current_price > current_ema
        else:  # bearish
            return current_price < current_ema
    
    def _find_swing_high_low(self, df: pd.DataFrame, lookback: int = 10) -> tuple:
        """
        Find recent swing high and low
        
        Args:
            df: Historical data
            lookback: Lookback period
            
        Returns:
            (swing_high, swing_low)
        """
        recent = df.tail(lookback)
        swing_high = recent['high'].max()
        swing_low = recent['low'].min()
        
        return swing_high, swing_low
    
    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        """
        Generate trading signal based on candlestick patterns
        
        Args:
            df: Historical OHLCV data
            current_price: Current market price
            
        Returns:
            TradingSignal or None
        """
        # Check if we have enough data
        if len(df) < self.trend_ema + 20:
            return None
        
        # Check risk limits
        if not self.check_risk_limits():
            return None
        
        # Scan for patterns in recent candles
        recent_patterns = pattern_scanner.scan_latest(df, self.config.symbol, lookback=5)
        
        if not recent_patterns:
            return None
        
        # Filter high-confidence patterns
        high_conf_patterns = [p for p in recent_patterns if p.confidence >= self.min_confidence]
        
        if not high_conf_patterns:
            return None
        
        # Get the most recent high-confidence pattern
        latest_pattern = high_conf_patterns[-1]
        
        # Check for bullish patterns
        if latest_pattern.direction == 'bullish' and latest_pattern.pattern.lower().replace(' ', '_') in [p.lower() for p in self.bullish_patterns]:
            # Check trend confirmation
            if not self._check_trend_confirmation(df, 'bullish'):
                return None
            
            # Find swing low for stop-loss
            swing_high, swing_low = self._find_swing_high_low(df)
            
            # Calculate stop-loss (below recent swing low)
            stop_loss = swing_low * 0.995  # 0.5% buffer
            
            # Calculate target (minimum 1:2 RR)
            risk = current_price - stop_loss
            target = current_price + (risk * self.min_rr_ratio)
            
            # Adjust target if swing high is closer
            if swing_high > current_price:
                potential_target = swing_high * 0.995
                if potential_target > target:
                    target = potential_target
            
            # Verify risk-reward
            reward = target - current_price
            if reward / risk >= self.min_rr_ratio:
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
                        reason=f"{latest_pattern.pattern} pattern with trend confirmation",
                        confidence=latest_pattern.confidence,
                        metadata={
                            "pattern": latest_pattern.pattern,
                            "pattern_confidence": latest_pattern.confidence,
                            "swing_low": swing_low,
                            "swing_high": swing_high,
                            "rr_ratio": reward / risk
                        }
                    )
        
        # Check for bearish patterns
        elif latest_pattern.direction == 'bearish' and latest_pattern.pattern.lower().replace(' ', '_') in [p.lower() for p in self.bearish_patterns]:
            # Check trend confirmation
            if not self._check_trend_confirmation(df, 'bearish'):
                return None
            
            # Find swing high for stop-loss
            swing_high, swing_low = self._find_swing_high_low(df)
            
            # Calculate stop-loss (above recent swing high)
            stop_loss = swing_high * 1.005  # 0.5% buffer
            
            # Calculate target (minimum 1:2 RR)
            risk = stop_loss - current_price
            target = current_price - (risk * self.min_rr_ratio)
            
            # Adjust target if swing low is closer
            if swing_low < current_price:
                potential_target = swing_low * 1.005
                if potential_target < target:
                    target = potential_target
            
            # Verify risk-reward
            reward = current_price - target
            if reward / risk >= self.min_rr_ratio:
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
                        reason=f"{latest_pattern.pattern} pattern with trend confirmation",
                        confidence=latest_pattern.confidence,
                        metadata={
                            "pattern": latest_pattern.pattern,
                            "pattern_confidence": latest_pattern.confidence,
                            "swing_low": swing_low,
                            "swing_high": swing_high,
                            "rr_ratio": reward / risk
                        }
                    )
        
        return None
    
    def calculate_stop_loss(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate stop-loss based on pattern structure
        (Overridden in generate_signal for precise placement)
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Stop-loss price
        """
        if signal_type == SignalType.BUY:
            return entry_price * 0.98  # 2% below
        else:
            return entry_price * 1.02  # 2% above
    
    def calculate_target(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate target based on risk-reward ratio
        (Overridden in generate_signal for precise placement)
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Target price
        """
        stop_loss = self.calculate_stop_loss(entry_price, signal_type)
        risk = abs(entry_price - stop_loss)
        
        if signal_type == SignalType.BUY:
            return entry_price + (risk * self.min_rr_ratio)
        else:
            return entry_price - (risk * self.min_rr_ratio)
