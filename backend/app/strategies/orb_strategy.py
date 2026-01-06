"""
Opening Range Breakout (ORB) Strategy
Trades the breakout of the first N-minute candle.
"""
import pandas as pd
from typing import Optional
from datetime import datetime, time
from app.strategies.base_strategy import (
    BaseStrategy, StrategyConfig, TradingSignal, SignalType
)

class ORBStrategy(BaseStrategy):
    """
    ORB Strategy
    - Logic: Define High/Low of the first 'range_minutes' of the session.
    - Buy if price breaks Range High.
    - Sell if price breaks Range Low.
    - Stop Loss: Midpoint or Opposite End.
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.range_minutes = config.params.get('range_minutes', 15)
        self.sl_pct = config.params.get('sl_pct', 0.005)
        self.target_pct = config.params.get('target_pct', 0.01)
        
        self.range_high = None
        self.range_low = None
        self.range_set = False
        
    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        self.update_position(current_price)
        
        if not self.check_risk_limits():
            return None
            
        exit_signal = self.check_exit_conditions(current_price)
        if exit_signal:
            return exit_signal
            
        if self.position is not None:
            return None
            
        # Determine Range (Simplified Logic for Intraday Data)
        # In a real system, we'd check timestamps. 
        # Here, assuming df is today's data starting at 9:15
        
        if not self.range_set:
            # Need enough data to cover range
            # Assuming 1-min candles (or 5-min)
            # If interval is 5-min, range_minutes=15 => need 3 candles
            # If df doesn't have timestamps easy to parse, we might need robust logic.
            # For now, let's look at the first X candles of the DataFrame if it represents "today"
            
            # Better approach: Use time check
            now = datetime.now().time()
            start_time = time(9, 15)
            range_end_time = (datetime.combine(datetime.today(), start_time) + pd.Timedelta(minutes=self.range_minutes)).time()
            
            if now < range_end_time:
                # Still forming range
                return None
            
            # Range is formed. Calculate High/Low of the opening range
            # Filtering DF for time between 9:15 and range_end_time
            # This requires df index to be datetime or a 'date' column
            # If not available, we can't reliably backtest ORB without timestamps.
            # Assuming live streaming: we can just track high/low in memory during that window?
            # But the Strategy class might be re-instantiated or stateless.
            # Better to rely on DF.
            
            # Simple fallback: Take the high/low of the first N rows? 
            # Risk: DF might include yesterday.
            # Let's assume DF is handled by the bot to be relevant context.
            
            # Let's try to parse index
            try:
                if isinstance(df.index, pd.DatetimeIndex):
                    today = datetime.now().date()
                    todays_data = df[df.index.date == today]
                    
                    # Filter for opening range
                    mask = (todays_data.index.time >= start_time) & (todays_data.index.time < range_end_time)
                    range_data = todays_data[mask]
                    
                    if not range_data.empty:
                        self.range_high = range_data['high'].max()
                        self.range_low = range_data['low'].min()
                        self.range_set = True
                        print(f"[{self.config.symbol}] ORB Set: {self.range_low} - {self.range_high}")
            except Exception as e:
                # Fallback logic if index isn't datetime or other issue
                print(f"ORB Error: {e}")
                pass
                
        if not self.range_set:
             return None
             
        timestamp = datetime.now()
        
        # Breakout Signals
        if current_price > self.range_high:
             return TradingSignal(
                timestamp=timestamp,
                symbol=self.config.symbol,
                signal_type=SignalType.BUY,
                price=current_price,
                quantity=0,
                stop_loss=self.range_low, # SL at range low? Or Midpoint? User preference.
                target=current_price * (1 + self.target_pct),
                reason=f"ORB Breakout High ({self.range_high})",
                confidence=0.8
            )
            
        elif current_price < self.range_low:
             return TradingSignal(
                timestamp=timestamp,
                symbol=self.config.symbol,
                signal_type=SignalType.SELL,
                price=current_price,
                quantity=0,
                stop_loss=self.range_high,
                target=current_price * (1 - self.target_pct),
                reason=f"ORB Breakout Low ({self.range_low})",
                confidence=0.8
            )
            
        return None

    def calculate_stop_loss(self, entry_price: float, signal_type: SignalType) -> float:
        # Fallback if not set in generate_signal
        if signal_type == SignalType.BUY:
            return entry_price * (1 - self.sl_pct)
        else:
            return entry_price * (1 + self.sl_pct)

    def calculate_target(self, entry_price: float, signal_type: SignalType) -> float:
        if signal_type == SignalType.BUY:
            return entry_price * (1 + self.target_pct)
        else:
            return entry_price * (1 - self.target_pct)
