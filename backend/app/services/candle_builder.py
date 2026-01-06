"""
Tick Processor
Converts real-time ticks into OHLC candles for various timeframes
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from collections import defaultdict
import threading


class Candle:
    """OHLC Candle"""
    def __init__(self, timestamp: datetime, interval: str):
        self.timestamp = timestamp
        self.interval = interval
        self.open: Optional[float] = None
        self.high: Optional[float] = None
        self.low: Optional[float] = None
        self.close: Optional[float] = None
        self.volume: int = 0
        self.tick_count: int = 0
        self.is_closed = False
    
    def update(self, price: float, volume: int = 0):
        """Update candle with new tick"""
        if self.open is None:
            self.open = price
            self.high = price
            self.low = price
        else:
            self.high = max(self.high, price)
            self.low = min(self.low, price)
        
        self.close = price
        self.volume += volume
        self.tick_count += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'tick_count': self.tick_count
        }
    
    def __repr__(self):
        return f"Candle({self.timestamp}, O:{self.open}, H:{self.high}, L:{self.low}, C:{self.close}, V:{self.volume})"


class CandleBuilder:
    """
    Builds OHLC candles from real-time ticks
    Supports multiple timeframes: 1min, 3min, 5min, 15min, 30min, 60min
    """
    
    # Interval to minutes mapping
    INTERVALS = {
        '1min': 1,
        '3min': 3,
        '5min': 5,
        '10min': 10,
        '15min': 15,
        '30min': 30,
        '60min': 60
    }
    
    def __init__(self):
        # Current candles: {instrument_token: {interval: Candle}}
        self.current_candles: Dict[int, Dict[str, Candle]] = defaultdict(dict)
        
        # Historical candles: {instrument_token: {interval: [Candle]}}
        self.historical_candles: Dict[int, Dict[str, List[Candle]]] = defaultdict(lambda: defaultdict(list))
        
        # Callbacks for candle close events
        self.candle_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Max historical candles to keep per instrument per interval
        self.max_history = 500
    
    def process_tick(self, tick: Dict):
        """
        Process a single tick and update candles
        
        Args:
            tick: Tick data from KiteTicker
        """
        instrument_token = tick.get('instrument_token')
        if not instrument_token:
            return
        
        # Extract tick data
        timestamp = tick.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        last_price = tick.get('last_price', 0)
        volume = tick.get('volume_traded', 0)
        
        if last_price == 0:
            return
        
        with self.lock:
            # Update candles for all intervals
            for interval in self.INTERVALS.keys():
                self._update_candle(instrument_token, interval, timestamp, last_price, volume)
    
    def _update_candle(self, instrument_token: int, interval: str, timestamp: datetime, price: float, volume: int):
        """Update or create candle for specific interval"""
        # Get candle start time for this interval
        candle_start = self._get_candle_start(timestamp, interval)
        
        # Get or create current candle
        if interval not in self.current_candles[instrument_token]:
            # Create new candle
            candle = Candle(candle_start, interval)
            self.current_candles[instrument_token][interval] = candle
        else:
            candle = self.current_candles[instrument_token][interval]
            
            # Check if we need to close current candle and start new one
            if candle.timestamp != candle_start:
                # Close current candle
                candle.is_closed = True
                
                # Add to historical candles
                self.historical_candles[instrument_token][interval].append(candle)
                
                # Trim history if needed
                if len(self.historical_candles[instrument_token][interval]) > self.max_history:
                    self.historical_candles[instrument_token][interval] = \
                        self.historical_candles[instrument_token][interval][-self.max_history:]
                
                # Trigger callbacks
                self._trigger_callbacks(interval, instrument_token, candle)
                
                # Create new candle
                candle = Candle(candle_start, interval)
                self.current_candles[instrument_token][interval] = candle
        
        # Update candle with tick
        candle.update(price, volume)
    
    def _get_candle_start(self, timestamp: datetime, interval: str) -> datetime:
        """
        Get candle start time for given timestamp and interval
        
        Args:
            timestamp: Current timestamp
            interval: Candle interval
            
        Returns:
            Candle start timestamp
        """
        minutes = self.INTERVALS[interval]
        
        # Round down to nearest interval
        minute = (timestamp.minute // minutes) * minutes
        
        return timestamp.replace(minute=minute, second=0, microsecond=0)
    
    def get_current_candle(self, instrument_token: int, interval: str = '1min') -> Optional[Candle]:
        """
        Get current (incomplete) candle
        
        Args:
            instrument_token: Instrument token
            interval: Candle interval
            
        Returns:
            Current candle or None
        """
        with self.lock:
            return self.current_candles.get(instrument_token, {}).get(interval)
    
    def get_historical_candles(
        self,
        instrument_token: int,
        interval: str = '1min',
        count: int = 100
    ) -> List[Candle]:
        """
        Get historical closed candles
        
        Args:
            instrument_token: Instrument token
            interval: Candle interval
            count: Number of candles to return
            
        Returns:
            List of candles
        """
        with self.lock:
            candles = self.historical_candles.get(instrument_token, {}).get(interval, [])
            return candles[-count:] if candles else []
    
    def get_candles_as_dataframe(
        self,
        instrument_token: int,
        interval: str = '1min',
        count: int = 100,
        include_current: bool = False
    ) -> pd.DataFrame:
        """
        Get candles as pandas DataFrame
        
        Args:
            instrument_token: Instrument token
            interval: Candle interval
            count: Number of candles
            include_current: Include current incomplete candle
            
        Returns:
            DataFrame with OHLCV data
        """
        candles = self.get_historical_candles(instrument_token, interval, count)
        
        # Add current candle if requested
        if include_current:
            current = self.get_current_candle(instrument_token, interval)
            if current and current.open is not None:
                candles.append(current)
        
        if not candles:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert to DataFrame
        data = [c.to_dict() for c in candles]
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def on_candle_close(self, interval: str, callback: Callable):
        """
        Register callback for candle close events
        
        Args:
            interval: Candle interval to monitor
            callback: Function(instrument_token, candle)
        """
        self.candle_callbacks[interval].append(callback)
    
    def _trigger_callbacks(self, interval: str, instrument_token: int, candle: Candle):
        """Trigger callbacks for candle close"""
        for callback in self.candle_callbacks[interval]:
            try:
                callback(instrument_token, candle)
            except Exception as e:
                print(f"✗ Error in candle callback: {str(e)}")
    
    def clear_history(self, instrument_token: Optional[int] = None):
        """
        Clear historical candles
        
        Args:
            instrument_token: Specific token to clear, or None for all
        """
        with self.lock:
            if instrument_token:
                if instrument_token in self.historical_candles:
                    self.historical_candles[instrument_token].clear()
                if instrument_token in self.current_candles:
                    self.current_candles[instrument_token].clear()
            else:
                self.historical_candles.clear()
                self.current_candles.clear()
    
    def get_status(self) -> Dict:
        """Get candle builder status"""
        with self.lock:
            return {
                "instruments_tracked": len(self.current_candles),
                "total_historical_candles": sum(
                    sum(len(candles) for candles in intervals.values())
                    for intervals in self.historical_candles.values()
                ),
                "intervals": list(self.INTERVALS.keys())
            }


# Global singleton instance
candle_builder = CandleBuilder()
