"""
Supertrend Strategy
Multi-timeframe supertrend strategy with trailing stop-loss

Strategy Logic:
- Uses 3 Supertrend indicators with different parameters
- BUY when all 3 supertrends are green (below price)
- SELL when all 3 supertrends are red (above price)
- Dynamic stop-loss based on weighted supertrend values
"""
from typing import Optional, Dict, List
import pandas as pd
import numpy as np
from datetime import datetime

from app.strategies.base_strategy import (
    BaseStrategy, TradingSignal, Position, StrategyConfig,
    SignalType, PositionType
)
from app.services.indicators import TechnicalIndicators


class SupertrendStrategyConfig(StrategyConfig):
    """Configuration for Supertrend Strategy"""
    
    def __init__(
        self,
        symbol: str,
        capital: float = 3000.0,
        st1_period: int = 7,
        st1_multiplier: float = 3.0,
        st2_period: int = 10,
        st2_multiplier: float = 3.0,
        st3_period: int = 11,
        st3_multiplier: float = 2.0,
        **kwargs
    ):
        super().__init__(
            name="Supertrend Strategy",
            symbol=symbol,
            capital=capital,
            **kwargs
        )
        
        # Supertrend parameters
        self.st1_period = st1_period
        self.st1_multiplier = st1_multiplier
        self.st2_period = st2_period
        self.st2_multiplier = st2_multiplier
        self.st3_period = st3_period
        self.st3_multiplier = st3_multiplier


class SupertrendStrategy(BaseStrategy):
    """
    Supertrend Strategy Implementation
    
    Uses 3 Supertrend indicators to confirm trend direction.
    Places orders with stop-loss when all 3 supertrends align.
    """
    
    def __init__(self, config: SupertrendStrategyConfig):
        super().__init__(config)
        self.config: SupertrendStrategyConfig = config
        
        # Track supertrend directions
        self.st_directions = {
            'st1': None,  # "green" or "red"
            'st2': None,
            'st3': None
        }
        
        # Track previous values for reversal detection
        self.prev_close = None
        self.prev_st1 = None
        self.prev_st2 = None
        self.prev_st3 = None
    
    def calculate_supertrends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate 3 Supertrend indicators with different parameters
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with supertrend columns added
        """
        df = df.copy()
        
        # Calculate 3 supertrends
        df['st1'] = TechnicalIndicators.supertrend(
            df, 
            period=self.config.st1_period,
            multiplier=self.config.st1_multiplier
        )
        
        df['st2'] = TechnicalIndicators.supertrend(
            df,
            period=self.config.st2_period,
            multiplier=self.config.st2_multiplier
        )
        
        df['st3'] = TechnicalIndicators.supertrend(
            df,
            period=self.config.st3_period,
            multiplier=self.config.st3_multiplier
        )
        
        return df
    
    def update_st_directions(self, df: pd.DataFrame) -> None:
        """
        Update supertrend direction tracking based on price crossovers
        
        Args:
            df: DataFrame with OHLC and supertrend data
        """
        if len(df) < 2:
            return
        
        current_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        
        current_st1 = df['st1'].iloc[-1]
        prev_st1 = df['st1'].iloc[-2]
        
        current_st2 = df['st2'].iloc[-1]
        prev_st2 = df['st2'].iloc[-2]
        
        current_st3 = df['st3'].iloc[-1]
        prev_st3 = df['st3'].iloc[-2]
        
        # Check for ST1 reversal
        if not pd.isna(current_st1) and not pd.isna(prev_st1):
            # Bearish reversal: price crosses below supertrend
            if current_st1 > current_close and prev_st1 < prev_close:
                self.st_directions['st1'] = "red"
            # Bullish reversal: price crosses above supertrend
            elif current_st1 < current_close and prev_st1 > prev_close:
                self.st_directions['st1'] = "green"
        
        # Check for ST2 reversal
        if not pd.isna(current_st2) and not pd.isna(prev_st2):
            if current_st2 > current_close and prev_st2 < prev_close:
                self.st_directions['st2'] = "red"
            elif current_st2 < current_close and prev_st2 > prev_close:
                self.st_directions['st2'] = "green"
        
        # Check for ST3 reversal
        if not pd.isna(current_st3) and not pd.isna(prev_st3):
            if current_st3 > current_close and prev_st3 < prev_close:
                self.st_directions['st3'] = "red"
            elif current_st3 < current_close and prev_st3 > prev_close:
                self.st_directions['st3'] = "green"
    
    def calculate_stop_loss(self, df: pd.DataFrame) -> float:
        """
        Calculate dynamic stop-loss based on supertrend values
        
        Uses weighted average of supertrend values:
        - 60% weight to closest ST
        - 40% weight to second closest ST
        
        Args:
            df: DataFrame with supertrend data
            
        Returns:
            Stop-loss price
        """
        if len(df) == 0:
            return 0.0
        
        current_close = df['close'].iloc[-1]
        st_values = df[['st1', 'st2', 'st3']].iloc[-1]
        
        # Remove NaN values
        st_values = st_values.dropna()
        
        if len(st_values) == 0:
            return current_close * 0.98  # Default 2% SL
        
        # All STs above price (short scenario)
        if st_values.min() > current_close:
            sorted_st = st_values.sort_values(ascending=True)
            sl = (0.6 * sorted_st.iloc[0]) + (0.4 * sorted_st.iloc[1] if len(sorted_st) > 1 else 0.4 * sorted_st.iloc[0])
        
        # All STs below price (long scenario)
        elif st_values.max() < current_close:
            sorted_st = st_values.sort_values(ascending=False)
            sl = (0.6 * sorted_st.iloc[0]) + (0.4 * sorted_st.iloc[1] if len(sorted_st) > 1 else 0.4 * sorted_st.iloc[0])
        
        # Mixed scenario - use mean
        else:
            sl = st_values.mean()
        
        return round(sl, 1)
    
    def calculate_target(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate target price
        
        For Supertrend strategy, we use trailing stop-loss instead of fixed targets.
        This returns a default 3% target, but actual exits are managed by trailing SL.
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Target price (nominal, not strictly enforced)
        """
        if signal_type == SignalType.BUY:
            # 3% profit target for longs
            return round(entry_price * 1.03, 1)
        elif signal_type == SignalType.SELL:
            # 3% profit target for shorts
            return round(entry_price * 0.97, 1)
        else:
            return entry_price
    
    def all_green(self) -> bool:
        """Check if all 3 supertrends are green"""
        return all(direction == "green" for direction in self.st_directions.values())
    
    def all_red(self) -> bool:
        """Check if all 3 supertrends are red"""
        return all(direction == "red" for direction in self.st_directions.values())
    
    def generate_signal(
        self, 
        df: pd.DataFrame, 
        current_price: float
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal based on supertrend alignment
        
        Args:
            df: Historical OHLC data
            current_price: Current market price
            
        Returns:
            TradingSignal or None
        """
        # Calculate supertrends
        df = self.calculate_supertrends(df)
        
        # Update directions
        self.update_st_directions(df)
        
        # Calculate quantity based on capital
        quantity = int(self.config.capital / current_price)
        if quantity == 0:
            return None
        
        # Calculate stop-loss
        stop_loss = self.calculate_stop_loss(df)
        
        # Check if we have a position
        if self.position is not None:
            # Position exists - check for stop-loss update or exit
            return self._check_position_management(df, current_price, stop_loss)
        
        # No position - check for entry signals
        if self.all_green():
            # All supertrends are bullish - BUY signal
            return TradingSignal(
                timestamp=datetime.now(),
                symbol=self.config.symbol,
                signal_type=SignalType.BUY,
                price=current_price,
                quantity=quantity,
                stop_loss=stop_loss,
                target=None,  # No fixed target, trail with supertrend
                reason="All 3 Supertrends GREEN - Bullish alignment",
                confidence=1.0,
                metadata={
                    'st1': self.st_directions['st1'],
                    'st2': self.st_directions['st2'],
                    'st3': self.st_directions['st3']
                }
            )
        
        elif self.all_red():
            # All supertrends are bearish - SELL signal
            return TradingSignal(
                timestamp=datetime.now(),
                symbol=self.config.symbol,
                signal_type=SignalType.SELL,
                price=current_price,
                quantity=quantity,
                stop_loss=stop_loss,
                target=None,
                reason="All 3 Supertrends RED - Bearish alignment",
                confidence=1.0,
                metadata={
                    'st1': self.st_directions['st1'],
                    'st2': self.st_directions['st2'],
                    'st3': self.st_directions['st3']
                }
            )
        
        return None
    
    def _check_position_management(
        self,
        df: pd.DataFrame,
        current_price: float,
        new_stop_loss: float
    ) -> Optional[TradingSignal]:
        """
        Check if position needs stop-loss update or exit
        
        Args:
            df: DataFrame with OHLC data
            current_price: Current price
            new_stop_loss: New calculated stop-loss
            
        Returns:
            Signal for SL update or None
        """
        if self.position is None:
            return None
        
        # Return signal to update stop-loss
        # The strategy engine should handle modifying the SL order
        return TradingSignal(
            timestamp=datetime.now(),
            symbol=self.config.symbol,
            signal_type=SignalType.HOLD,  # HOLD but update SL
            price=current_price,
            quantity=self.position.quantity,
            stop_loss=new_stop_loss,
            target=None,
            reason="Update trailing stop-loss",
            confidence=1.0,
            metadata={'action': 'update_sl'}
        )
    
    def should_enter(self, df: pd.DataFrame) -> bool:
        """
        Check if entry conditions are met
        
        Args:
            df: DataFrame with indicator data
            
        Returns:
            True if should enter trade
        """
        return self.all_green() or self.all_red()
    
    def should_exit(self, df: pd.DataFrame, position: Position) -> bool:
        """
        Check if exit conditions are met
        
        Args:
            df: DataFrame with indicator data
            position: Current position
            
        Returns:
            True if should exit trade
        """
        # Exit handled by stop-loss orders
        # Could add additional exit logic here (e.g., reversal signals)
        return False
    
    def calculate_position_size(self, price: float, stop_loss: float) -> int:
        """
        Calculate position size based on risk management
        
        Args:
            price: Entry price
            stop_loss: Stop-loss price
            
        Returns:
            Position size (quantity)
        """
        # Simple capital-based sizing
        quantity = int(self.config.capital / price)
        
        # Could enhance with risk-based sizing:
        # risk_amount = self.config.capital * self.config.risk_per_trade
        # risk_per_share = abs(price - stop_loss)
        # quantity = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        
        return max(1, quantity)
    
    def get_status(self) -> Dict:
        """
        Get current strategy status
        
        Returns:
            Status dictionary
        """
        return {
            'strategy': self.config.name,
            'symbol': self.config.symbol,
            'active': self.is_active,
            'has_position': self.position is not None,
            'position': {
                'type': self.position.position_type.value if self.position else None,
                'quantity': self.position.quantity if self.position else 0,
                'entry_price': self.position.entry_price if self.position else 0,
                'stop_loss': self.position.stop_loss if self.position else 0,
                'pnl': self.position.pnl if self.position else 0
            } if self.position else None,
            'supertrend_directions': self.st_directions,
            'trades_today': self.trades_today,
            'pnl_today': self.pnl_today
        }
