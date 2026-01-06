"""
Strategy 2: Price Action Breakout Strategy
Trades breakouts from support/resistance levels with volume confirmation
"""
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
from app.strategies.base_strategy import (
    BaseStrategy, StrategyConfig, TradingSignal, SignalType
)
from app.services.price_action import price_action_service


class BreakoutStrategy(BaseStrategy):
    """
    Price Action Breakout Strategy
    
    Entry Conditions:
    - BUY: Price breaks above resistance with volume > average
    - SELL: Price breaks below support with volume > average
    
    Stop Loss:
    - BUY: Below the broken resistance level
    - SELL: Above the broken support level
    
    Target:
    - BUY: Distance from resistance to next resistance
    - SELL: Distance from support to next support
    - Minimum 1:1.5 risk-reward ratio
    
    Risk Management:
    - Position size based on 2% capital risk
    - Breakout must be confirmed by strong candle close
    - Volume must be above 20-period average
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # Default parameters
        self.lookback_period = config.params.get('lookback_period', 20) if config.params else 20
        self.volume_multiplier = config.params.get('volume_multiplier', 1.2) if config.params else 1.2
        self.min_rr_ratio = config.params.get('min_rr_ratio', 1.5) if config.params else 1.5
        
        # Cached S/R levels
        self.support_levels = []
        self.resistance_levels = []
        self.last_sr_update = None
    
    def _update_sr_levels(self, df: pd.DataFrame):
        """Update support and resistance levels"""
        levels = price_action_service.find_support_resistance(
            df,
            window=self.lookback_period,
            min_touches=2,
            tolerance=0.02
        )
        
        self.support_levels = [l.level for l in levels if l.type == 'support']
        self.resistance_levels = [l.level for l in levels if l.type == 'resistance']
        self.last_sr_update = datetime.now()
    
    def _find_nearest_level(self, price: float, levels: list, direction: str) -> Optional[float]:
        """
        Find nearest support/resistance level
        
        Args:
            price: Current price
            levels: List of price levels
            direction: 'above' or 'below'
            
        Returns:
            Nearest level or None
        """
        if not levels:
            return None
        
        if direction == 'above':
            above_levels = [l for l in levels if l > price]
            return min(above_levels) if above_levels else None
        else:  # below
            below_levels = [l for l in levels if l < price]
            return max(below_levels) if below_levels else None
    
    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        """
        Generate trading signal based on breakout detection
        
        Args:
            df: Historical OHLCV data
            current_price: Current market price
            
        Returns:
            TradingSignal or None
        """
        # Check if we have enough data
        if len(df) < self.lookback_period + 5:
            return None
        
        # Check risk limits
        if not self.check_risk_limits():
            return None
        
        # Update S/R levels
        self._update_sr_levels(df)
        
        # Calculate volume average
        df = df.copy()
        df['volume_avg'] = df['volume'].rolling(window=20).mean()
        
        # Get latest candle
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check volume confirmation
        volume_confirmed = current['volume'] > (current['volume_avg'] * self.volume_multiplier)
        
        if not volume_confirmed:
            return None
        
        # Check for resistance breakout (BUY)
        nearest_resistance = self._find_nearest_level(previous['close'], self.resistance_levels, 'above')
        
        if nearest_resistance and current['close'] > nearest_resistance:
            # Breakout confirmed
            # Find next resistance for target
            next_resistance = self._find_nearest_level(current['close'], self.resistance_levels, 'above')
            
            # Calculate stop-loss (below broken resistance)
            stop_loss = nearest_resistance * 0.995  # 0.5% below
            
            # Calculate target
            if next_resistance:
                target = next_resistance * 0.995  # 0.5% before next resistance
            else:
                # Use risk-reward ratio
                risk = current_price - stop_loss
                target = current_price + (risk * self.min_rr_ratio)
            
            # Verify risk-reward ratio
            risk = current_price - stop_loss
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
                        reason=f"Resistance breakout @ ₹{nearest_resistance:.2f} with volume",
                        confidence=0.85,
                        metadata={
                            "broken_level": nearest_resistance,
                            "volume_ratio": current['volume'] / current['volume_avg'],
                            "rr_ratio": reward / risk
                        }
                    )
        
        # Check for support breakdown (SELL)
        nearest_support = self._find_nearest_level(previous['close'], self.support_levels, 'below')
        
        if nearest_support and current['close'] < nearest_support:
            # Breakdown confirmed
            # Find next support for target
            next_support = self._find_nearest_level(current['close'], self.support_levels, 'below')
            
            # Calculate stop-loss (above broken support)
            stop_loss = nearest_support * 1.005  # 0.5% above
            
            # Calculate target
            if next_support:
                target = next_support * 1.005  # 0.5% after next support
            else:
                # Use risk-reward ratio
                risk = stop_loss - current_price
                target = current_price - (risk * self.min_rr_ratio)
            
            # Verify risk-reward ratio
            risk = stop_loss - current_price
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
                        reason=f"Support breakdown @ ₹{nearest_support:.2f} with volume",
                        confidence=0.85,
                        metadata={
                            "broken_level": nearest_support,
                            "volume_ratio": current['volume'] / current['volume_avg'],
                            "rr_ratio": reward / risk
                        }
                    )
        
        return None
    
    def calculate_stop_loss(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate stop-loss based on broken level
        (This is overridden in generate_signal for more precise placement)
        
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
        Calculate target based on next S/R level
        (This is overridden in generate_signal for more precise placement)
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Target price
        """
        if signal_type == SignalType.BUY:
            return entry_price * 1.03  # 3% above
        else:
            return entry_price * 0.97  # 3% below
