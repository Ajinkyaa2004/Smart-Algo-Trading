"""
Renko + MACD Strategy
Real-time tick-based strategy using Renko bricks and MACD confirmation

Strategy Logic:
- Uses Renko bricks to filter out noise and identify significant moves
- MACD provides trend confirmation
- BUY when: MACD bullish AND Renko shows strong uptrend (≥2 bricks)
- SELL when: MACD bearish AND Renko shows strong downtrend (≤-2 bricks)
- Stop-loss based on Renko brick limits
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
from app.services.renko import renko_calculator
from app.services.market_data import market_data_service


class RenkoMACDStrategyConfig(StrategyConfig):
    """Configuration for Renko + MACD Strategy"""
    
    def __init__(
        self,
        symbol: str,
        capital: float = 3000.0,
        renko_brick_threshold: int = 2,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        atr_period: int = 200,
        atr_multiplier: float = 1.5,
        **kwargs
    ):
        super().__init__(
            name="Renko + MACD Strategy",
            symbol=symbol,
            capital=capital,
            **kwargs
        )
        
        # Renko parameters
        self.renko_brick_threshold = renko_brick_threshold  # Minimum bricks for signal
        self.atr_period = atr_period  # For brick size calculation
        self.atr_multiplier = atr_multiplier
        
        # MACD parameters
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal


class RenkoMACDStrategy(BaseStrategy):
    """
    Renko + MACD Strategy Implementation
    
    Combines Renko brick analysis with MACD confirmation for high-probability trades.
    Designed for real-time tick data processing.
    """
    
    def __init__(self, config: RenkoMACDStrategyConfig):
        super().__init__(config)
        self.config: RenkoMACDStrategyConfig = config
        
        # Track MACD crossover status
        self.macd_crossover = None  # "bullish", "bearish", or None
        
        # Initialize renko calculator
        self.renko = renko_calculator
        
        # Calculate and initialize brick size
        self._initialize_brick_size()
    
    def _initialize_brick_size(self):
        """Calculate optimal brick size based on ATR"""
        try:
            # Fetch historical data for ATR calculation
            df = market_data_service.get_historical_data_by_symbol(
                symbol=self.config.symbol,
                exchange=self.config.exchange,
                interval="60minute",
                days_back=60
            )
            
            if df.empty:
                print(f"⚠ No historical data for {self.config.symbol}, using default brick size")
                brick_size = 1.0
            else:
                # Calculate ATR
                atr_value = TechnicalIndicators.atr(df, self.config.atr_period).iloc[-1]
                
                # Brick size = 1.5 * ATR, rounded, min 1, max 10
                brick_size = min(10, max(1, round(self.config.atr_multiplier * atr_value, 0)))
            
            # Initialize renko with calculated brick size
            self.renko.initialize_brick(
                symbol=self.config.symbol,
                brick_size=brick_size
            )
            
            print(f"✓ Brick size for {self.config.symbol}: {brick_size}")
            
        except Exception as e:
            print(f"✗ Error initializing brick size: {str(e)}")
            # Fallback to default
            self.renko.initialize_brick(self.config.symbol, brick_size=1.0)
    
    def update_macd_status(self, df: pd.DataFrame) -> None:
        """
        Update MACD crossover status
        
        Args:
            df: DataFrame with OHLC data
        """
        if len(df) < self.config.macd_slow + self.config.macd_signal:
            return
        
        # Calculate MACD
        macd_line, signal_line, _ = TechnicalIndicators.macd(
            df['close'],
            fast_period=self.config.macd_fast,
            slow_period=self.config.macd_slow,
            signal_period=self.config.macd_signal
        )
        
        # Check crossover
        if not macd_line.empty and not signal_line.empty:
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            
            if current_macd > current_signal:
                self.macd_crossover = "bullish"
            elif current_macd < current_signal:
                self.macd_crossover = "bearish"
    
    def process_tick(self, tick: Dict) -> Optional[Dict]:
        """
        Process real-time tick and update Renko bricks
        
        Args:
            tick: Tick data from WebSocket
            
        Returns:
            Brick update information
        """
        price = tick.get('last_price', tick.get('price'))
        if not price:
            return None
        
        # Update renko brick
        brick_update = self.renko.update_brick(self.config.symbol, price)
        
        if brick_update.get('brick_formed'):
            print(f"{self.config.symbol}: Brick #{brick_update['brick_count']} formed at {price}")
            print(f"  Upper: {brick_update['upper_limit']:.2f}, Lower: {brick_update['lower_limit']:.2f}")
        
        return brick_update
    
    def generate_signal(
        self, 
        df: pd.DataFrame, 
        current_price: float
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal based on Renko + MACD
        
        Args:
            df: Historical OHLC data (5-minute for MACD calculation)
            current_price: Current market price
            
        Returns:
            TradingSignal or None
        """
        # Update MACD status
        self.update_macd_status(df)
        
        # Get renko state
        brick_state = self.renko.get_brick_state(self.config.symbol)
        if not brick_state:
            return None
        
        brick_count = brick_state.brick_count
        
        # Calculate position size
        quantity = int(self.config.capital / current_price)
        if quantity == 0:
            return None
        
        # Check if we have a position
        if self.position is not None:
            return self._check_position_management(brick_state, current_price)
        
        # No position - check for entry signals
        
        # BUY Signal: MACD bullish AND strong uptrend (≥2 green bricks)
        if (self.macd_crossover == "bullish" and 
            brick_count >= self.config.renko_brick_threshold):
            
            return TradingSignal(
                timestamp=datetime.now(),
                symbol=self.config.symbol,
                signal_type=SignalType.BUY,
                price=current_price,
                quantity=quantity,
                stop_loss=brick_state.lower_limit,
                target=None,  # Trail with renko
                reason=f"MACD bullish + {brick_count} green Renko bricks",
                confidence=min(1.0, abs(brick_count) / 5),  # Higher confidence with more bricks
                metadata={
                    'macd_crossover': self.macd_crossover,
                    'brick_count': brick_count,
                    'brick_size': brick_state.brick_size
                }
            )
        
        # SELL Signal: MACD bearish AND strong downtrend (≤-2 red bricks)
        elif (self.macd_crossover == "bearish" and 
              brick_count <= -self.config.renko_brick_threshold):
            
            return TradingSignal(
                timestamp=datetime.now(),
                symbol=self.config.symbol,
                signal_type=SignalType.SELL,
                price=current_price,
                quantity=quantity,
                stop_loss=brick_state.upper_limit,
                target=None,
                reason=f"MACD bearish + {abs(brick_count)} red Renko bricks",
                confidence=min(1.0, abs(brick_count) / 5),
                metadata={
                    'macd_crossover': self.macd_crossover,
                    'brick_count': brick_count,
                    'brick_size': brick_state.brick_size
                }
            )
        
        return None
    
    def calculate_stop_loss(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate stop-loss based on Renko brick limits
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Stop-loss price
        """
        brick_state = self.renko.get_brick_state(self.config.symbol)
        
        if not brick_state:
            # Fallback to 2% SL if no brick state available
            if signal_type == SignalType.BUY:
                return entry_price * 0.98
            else:
                return entry_price * 1.02
        
        # Use brick limits for stop-loss
        if signal_type == SignalType.BUY:
            return brick_state.lower_limit
        else:  # SELL
            return brick_state.upper_limit
    
    def calculate_target(self, entry_price: float, signal_type: SignalType) -> float:
        """
        Calculate target price
        
        For Renko strategy, targets are based on risk:reward ratio of 2:1
        
        Args:
            entry_price: Entry price
            signal_type: BUY or SELL
            
        Returns:
            Target price
        """
        stop_loss = self.calculate_stop_loss(entry_price, signal_type)
        risk = abs(entry_price - stop_loss)
        reward = risk * 2.0  # 2:1 risk:reward
        
        if signal_type == SignalType.BUY:
            return round(entry_price + reward, 1)
        else:  # SELL
            return round(entry_price - reward, 1)
    
    def _check_position_management(
        self,
        brick_state,
        current_price: float
    ) -> Optional[TradingSignal]:
        """
        Check if position needs stop-loss update
        
        Args:
            brick_state: Current renko brick state
            current_price: Current price
            
        Returns:
            Signal for SL update or None
        """
        if self.position is None:
            return None
        
        # Determine new stop-loss based on position type
        if self.position.position_type == PositionType.LONG:
            new_sl = brick_state.lower_limit
        else:  # SHORT
            new_sl = brick_state.upper_limit
        
        # Return signal to update stop-loss
        return TradingSignal(
            timestamp=datetime.now(),
            symbol=self.config.symbol,
            signal_type=SignalType.HOLD,
            price=current_price,
            quantity=self.position.quantity,
            stop_loss=new_sl,
            target=None,
            reason="Update trailing stop-loss (Renko brick)",
            confidence=1.0,
            metadata={'action': 'update_sl', 'brick_count': brick_state.brick_count}
        )
    
    def should_enter(self, df: pd.DataFrame) -> bool:
        """Check if entry conditions are met"""
        brick_state = self.renko.get_brick_state(self.config.symbol)
        if not brick_state:
            return False
        
        brick_count = brick_state.brick_count
        
        return (
            (self.macd_crossover == "bullish" and brick_count >= self.config.renko_brick_threshold) or
            (self.macd_crossover == "bearish" and brick_count <= -self.config.renko_brick_threshold)
        )
    
    def should_exit(self, df: pd.DataFrame, position: Position) -> bool:
        """Check if exit conditions are met"""
        # Exit handled by stop-loss orders
        # Could add reversal logic here
        return False
    
    def calculate_position_size(self, price: float, stop_loss: float) -> int:
        """Calculate position size based on capital"""
        return max(1, int(self.config.capital / price))
    
    def get_status(self) -> Dict:
        """Get current strategy status"""
        brick_state = self.renko.get_brick_state(self.config.symbol)
        
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
            'macd_crossover': self.macd_crossover,
            'renko': {
                'brick_count': brick_state.brick_count if brick_state else 0,
                'brick_size': brick_state.brick_size if brick_state else 0,
                'upper_limit': brick_state.upper_limit if brick_state else None,
                'lower_limit': brick_state.lower_limit if brick_state else None
            },
            'trades_today': self.trades_today,
            'pnl_today': self.pnl_today
        }
