"""
Candlestick Pattern Scanner
Detects common candlestick patterns in historical data
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from app.services.price_action import PriceActionService


@dataclass
class PatternMatch:
    """Candlestick pattern match"""
    timestamp: str
    symbol: str
    pattern: str
    direction: str  # 'bullish' or 'bearish'
    confidence: float  # 0.0 to 1.0
    price: float
    description: str


class CandlestickPatternScanner:
    """
    Scanner for candlestick patterns
    Detects: Doji, Hammer, Hanging Man, Engulfing, Morning/Evening Star
    """
    
    def __init__(self):
        self.price_action = PriceActionService()
    
    # ==================== SINGLE CANDLE PATTERNS ====================
    
    @staticmethod
    def is_doji(
        row: pd.Series,
        body_threshold: float = 0.1,
        prev_row: Optional[pd.Series] = None
    ) -> bool:
        """
        Detect Doji pattern
        Small body (< 10% of range), indicates indecision
        
        Args:
            row: Current candle
            body_threshold: Maximum body percentage
            prev_row: Previous candle (optional)
            
        Returns:
            True if Doji pattern detected
        """
        total_range = row['high'] - row['low']
        if total_range == 0:
            return False
        
        body = abs(row['close'] - row['open'])
        body_percentage = body / total_range
        
        return body_percentage < body_threshold
    
    @staticmethod
    def is_hammer(
        row: pd.Series,
        prev_row: Optional[pd.Series] = None,
        lower_wick_ratio: float = 2.0,
        body_position: float = 0.3
    ) -> bool:
        """
        Detect Hammer pattern (bullish reversal)
        Long lower wick, small body at top, little/no upper wick
        
        Args:
            row: Current candle
            prev_row: Previous candle
            lower_wick_ratio: Lower wick must be this times body size
            body_position: Body must be in top 30% of range
            
        Returns:
            True if Hammer pattern detected
        """
        total_range = row['high'] - row['low']
        if total_range == 0:
            return False
        
        body = abs(row['close'] - row['open'])
        lower_wick = min(row['open'], row['close']) - row['low']
        upper_wick = row['high'] - max(row['open'], row['close'])
        
        # Conditions for Hammer
        long_lower_wick = lower_wick >= (body * lower_wick_ratio)
        small_upper_wick = upper_wick < (body * 0.5)
        body_at_top = (row['high'] - max(row['open'], row['close'])) / total_range < body_position
        
        # Optional: Check if in downtrend
        in_downtrend = True
        if prev_row is not None:
            in_downtrend = row['close'] < prev_row['close']
        
        return long_lower_wick and small_upper_wick and body_at_top
    
    @staticmethod
    def is_hanging_man(
        row: pd.Series,
        prev_row: Optional[pd.Series] = None,
        lower_wick_ratio: float = 2.0,
        body_position: float = 0.3
    ) -> bool:
        """
        Detect Hanging Man pattern (bearish reversal)
        Same structure as Hammer but appears in uptrend
        
        Args:
            row: Current candle
            prev_row: Previous candle
            lower_wick_ratio: Lower wick ratio
            body_position: Body position threshold
            
        Returns:
            True if Hanging Man pattern detected
        """
        total_range = row['high'] - row['low']
        if total_range == 0:
            return False
        
        body = abs(row['close'] - row['open'])
        lower_wick = min(row['open'], row['close']) - row['low']
        upper_wick = row['high'] - max(row['open'], row['close'])
        
        # Same structure as Hammer
        long_lower_wick = lower_wick >= (body * lower_wick_ratio)
        small_upper_wick = upper_wick < (body * 0.5)
        body_at_top = (row['high'] - max(row['open'], row['close'])) / total_range < body_position
        
        # But in uptrend
        in_uptrend = True
        if prev_row is not None:
            in_uptrend = row['close'] > prev_row['close']
        
        return long_lower_wick and small_upper_wick and body_at_top and in_uptrend
    
    @staticmethod
    def is_shooting_star(
        row: pd.Series,
        prev_row: Optional[pd.Series] = None,
        upper_wick_ratio: float = 2.0
    ) -> bool:
        """
        Detect Shooting Star pattern (bearish reversal)
        Long upper wick, small body at bottom
        
        Args:
            row: Current candle
            prev_row: Previous candle
            upper_wick_ratio: Upper wick ratio
            
        Returns:
            True if Shooting Star detected
        """
        total_range = row['high'] - row['low']
        if total_range == 0:
            return False
        
        body = abs(row['close'] - row['open'])
        upper_wick = row['high'] - max(row['open'], row['close'])
        lower_wick = min(row['open'], row['close']) - row['low']
        
        long_upper_wick = upper_wick >= (body * upper_wick_ratio)
        small_lower_wick = lower_wick < (body * 0.5)
        
        return long_upper_wick and small_lower_wick
    
    # ==================== TWO CANDLE PATTERNS ====================
    
    @staticmethod
    def is_bullish_engulfing(row: pd.Series, prev_row: pd.Series) -> bool:
        """
        Detect Bullish Engulfing pattern
        Large bullish candle completely engulfs previous bearish candle
        
        Args:
            row: Current candle
            prev_row: Previous candle
            
        Returns:
            True if Bullish Engulfing detected
        """
        # Previous candle is bearish
        prev_bearish = prev_row['close'] < prev_row['open']
        
        # Current candle is bullish
        curr_bullish = row['close'] > row['open']
        
        # Current candle engulfs previous
        engulfs = (row['open'] <= prev_row['close'] and 
                  row['close'] >= prev_row['open'])
        
        # Current body is larger
        curr_body = abs(row['close'] - row['open'])
        prev_body = abs(prev_row['close'] - prev_row['open'])
        larger_body = curr_body > prev_body
        
        return prev_bearish and curr_bullish and engulfs and larger_body
    
    @staticmethod
    def is_bearish_engulfing(row: pd.Series, prev_row: pd.Series) -> bool:
        """
        Detect Bearish Engulfing pattern
        Large bearish candle completely engulfs previous bullish candle
        
        Args:
            row: Current candle
            prev_row: Previous candle
            
        Returns:
            True if Bearish Engulfing detected
        """
        # Previous candle is bullish
        prev_bullish = prev_row['close'] > prev_row['open']
        
        # Current candle is bearish
        curr_bearish = row['close'] < row['open']
        
        # Current candle engulfs previous
        engulfs = (row['open'] >= prev_row['close'] and 
                  row['close'] <= prev_row['open'])
        
        # Current body is larger
        curr_body = abs(row['close'] - row['open'])
        prev_body = abs(prev_row['close'] - prev_row['open'])
        larger_body = curr_body > prev_body
        
        return prev_bullish and curr_bearish and engulfs and larger_body
    
    @staticmethod
    def is_piercing_line(row: pd.Series, prev_row: pd.Series) -> bool:
        """
        Detect Piercing Line pattern (bullish reversal)
        Bullish candle closes above midpoint of previous bearish candle
        
        Args:
            row: Current candle
            prev_row: Previous candle
            
        Returns:
            True if Piercing Line detected
        """
        prev_bearish = prev_row['close'] < prev_row['open']
        curr_bullish = row['close'] > row['open']
        
        # Opens below previous close
        opens_below = row['open'] < prev_row['close']
        
        # Closes above midpoint of previous candle
        prev_midpoint = (prev_row['open'] + prev_row['close']) / 2
        closes_above_mid = row['close'] > prev_midpoint
        
        return prev_bearish and curr_bullish and opens_below and closes_above_mid
    
    @staticmethod
    def is_dark_cloud_cover(row: pd.Series, prev_row: pd.Series) -> bool:
        """
        Detect Dark Cloud Cover pattern (bearish reversal)
        Bearish candle closes below midpoint of previous bullish candle
        
        Args:
            row: Current candle
            prev_row: Previous candle
            
        Returns:
            True if Dark Cloud Cover detected
        """
        prev_bullish = prev_row['close'] > prev_row['open']
        curr_bearish = row['close'] < row['open']
        
        # Opens above previous close
        opens_above = row['open'] > prev_row['close']
        
        # Closes below midpoint
        prev_midpoint = (prev_row['open'] + prev_row['close']) / 2
        closes_below_mid = row['close'] < prev_midpoint
        
        return prev_bullish and curr_bearish and opens_above and closes_below_mid
    
    # ==================== THREE CANDLE PATTERNS ====================
    
    @staticmethod
    def is_morning_star(
        row: pd.Series,
        prev_row: pd.Series,
        prev_prev_row: pd.Series
    ) -> bool:
        """
        Detect Morning Star pattern (bullish reversal)
        3-candle pattern: bearish, small body (star), bullish
        
        Args:
            row: Current candle (3rd)
            prev_row: Previous candle (2nd - star)
            prev_prev_row: 2 candles ago (1st)
            
        Returns:
            True if Morning Star detected
        """
        # First candle: bearish
        first_bearish = prev_prev_row['close'] < prev_prev_row['open']
        
        # Second candle: small body (star)
        second_body = abs(prev_row['close'] - prev_row['open'])
        second_range = prev_row['high'] - prev_row['low']
        is_star = second_body < (second_range * 0.3) if second_range > 0 else False
        
        # Star gaps down
        gaps_down = prev_row['high'] < prev_prev_row['close']
        
        # Third candle: bullish
        third_bullish = row['close'] > row['open']
        
        # Third closes above midpoint of first
        first_midpoint = (prev_prev_row['open'] + prev_prev_row['close']) / 2
        closes_above = row['close'] > first_midpoint
        
        return first_bearish and is_star and third_bullish and closes_above
    
    @staticmethod
    def is_evening_star(
        row: pd.Series,
        prev_row: pd.Series,
        prev_prev_row: pd.Series
    ) -> bool:
        """
        Detect Evening Star pattern (bearish reversal)
        3-candle pattern: bullish, small body (star), bearish
        
        Args:
            row: Current candle (3rd)
            prev_row: Previous candle (2nd - star)
            prev_prev_row: 2 candles ago (1st)
            
        Returns:
            True if Evening Star detected
        """
        # First candle: bullish
        first_bullish = prev_prev_row['close'] > prev_prev_row['open']
        
        # Second candle: small body (star)
        second_body = abs(prev_row['close'] - prev_row['open'])
        second_range = prev_row['high'] - prev_row['low']
        is_star = second_body < (second_range * 0.3) if second_range > 0 else False
        
        # Star gaps up
        gaps_up = prev_row['low'] > prev_prev_row['close']
        
        # Third candle: bearish
        third_bearish = row['close'] < row['open']
        
        # Third closes below midpoint of first
        first_midpoint = (prev_prev_row['open'] + prev_prev_row['close']) / 2
        closes_below = row['close'] < first_midpoint
        
        return first_bullish and is_star and third_bearish and closes_below
    
    # ==================== SCANNER ====================
    
    def scan_patterns(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        patterns: Optional[List[str]] = None
    ) -> List[PatternMatch]:
        """
        Scan DataFrame for candlestick patterns
        
        Args:
            df: DataFrame with OHLC data
            symbol: Trading symbol
            patterns: List of pattern names to scan (None = all)
            
        Returns:
            List of PatternMatch objects
        """
        if patterns is None:
            patterns = [
                'doji', 'hammer', 'hanging_man', 'shooting_star',
                'bullish_engulfing', 'bearish_engulfing',
                'piercing_line', 'dark_cloud_cover',
                'morning_star', 'evening_star'
            ]
        
        matches = []
        
        for i in range(2, len(df)):  # Start from 2 to have prev_prev_row
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            prev_prev_row = df.iloc[i-2]
            
            timestamp = str(row.name) if hasattr(row, 'name') else str(i)
            
            # Single candle patterns
            if 'doji' in patterns and self.is_doji(row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Doji',
                    direction='neutral',
                    confidence=0.7,
                    price=row['close'],
                    description='Indecision candle, potential reversal'
                ))
            
            if 'hammer' in patterns and self.is_hammer(row, prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Hammer',
                    direction='bullish',
                    confidence=0.8,
                    price=row['close'],
                    description='Bullish reversal signal'
                ))
            
            if 'hanging_man' in patterns and self.is_hanging_man(row, prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Hanging Man',
                    direction='bearish',
                    confidence=0.75,
                    price=row['close'],
                    description='Bearish reversal signal'
                ))
            
            if 'shooting_star' in patterns and self.is_shooting_star(row, prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Shooting Star',
                    direction='bearish',
                    confidence=0.8,
                    price=row['close'],
                    description='Bearish reversal signal'
                ))
            
            # Two candle patterns
            if 'bullish_engulfing' in patterns and self.is_bullish_engulfing(row, prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Bullish Engulfing',
                    direction='bullish',
                    confidence=0.85,
                    price=row['close'],
                    description='Strong bullish reversal'
                ))
            
            if 'bearish_engulfing' in patterns and self.is_bearish_engulfing(row, prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Bearish Engulfing',
                    direction='bearish',
                    confidence=0.85,
                    price=row['close'],
                    description='Strong bearish reversal'
                ))
            
            if 'piercing_line' in patterns and self.is_piercing_line(row, prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Piercing Line',
                    direction='bullish',
                    confidence=0.75,
                    price=row['close'],
                    description='Bullish reversal pattern'
                ))
            
            if 'dark_cloud_cover' in patterns and self.is_dark_cloud_cover(row, prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Dark Cloud Cover',
                    direction='bearish',
                    confidence=0.75,
                    price=row['close'],
                    description='Bearish reversal pattern'
                ))
            
            # Three candle patterns
            if 'morning_star' in patterns and self.is_morning_star(row, prev_row, prev_prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Morning Star',
                    direction='bullish',
                    confidence=0.9,
                    price=row['close'],
                    description='Strong bullish reversal (3-candle)'
                ))
            
            if 'evening_star' in patterns and self.is_evening_star(row, prev_row, prev_prev_row):
                matches.append(PatternMatch(
                    timestamp=timestamp,
                    symbol=symbol,
                    pattern='Evening Star',
                    direction='bearish',
                    confidence=0.9,
                    price=row['close'],
                    description='Strong bearish reversal (3-candle)'
                ))
        
        # Advanced pattern detection (for latest candle)
        if len(df) >= 10:
            advanced_pattern = self.detect_advanced_pattern(df, symbol)
            if advanced_pattern:
                matches.append(advanced_pattern)
        
        return matches
    
    def scan_latest(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        lookback: int = 10
    ) -> List[PatternMatch]:
        """
        Scan only recent candles for patterns
        
        Args:
            df: DataFrame with OHLC data
            symbol: Trading symbol
            lookback: Number of recent candles to scan
            
        Returns:
            List of recent pattern matches
        """
        recent_df = df.tail(lookback + 2)  # +2 for prev candles
        return self.scan_patterns(recent_df, symbol)
    
    # ==================== ENHANCED PATTERN DETECTION ====================
    
    @staticmethod
    def detect_maru_bozu(df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Maru Bozu candles (no wicks)
        Returns dataframe with maru_bozu column
        """
        result = df.copy()
        avg_candle_size = abs(df["close"] - df["open"]).median()
        result["h-c"] = df["high"] - df["close"]
        result["l-o"] = df["low"] - df["open"]
        result["h-o"] = df["high"] - df["open"]
        result["l-c"] = df["low"] - df["close"]
        
        result["maru_bozu"] = np.where(
            (df["close"] - df["open"] > 2 * avg_candle_size) & 
            (result[["h-c", "l-o"]].max(axis=1) < 0.005 * avg_candle_size),
            "maru_bozu_green",
            np.where(
                (df["open"] - df["close"] > 2 * avg_candle_size) & 
                (abs(result[["h-o", "l-c"]]).max(axis=1) < 0.005 * avg_candle_size),
                "maru_bozu_red",
                False
            )
        )
        result.drop(["h-c", "l-o", "h-o", "l-c"], axis=1, inplace=True)
        return result
    
    @staticmethod
    def detect_trend(df: pd.DataFrame, n: int = 7) -> Optional[str]:
        """
        Assess trend by analyzing recent candles
        Returns 'uptrend', 'downtrend', or None
        """
        if len(df) < n:
            return None
            
        temp_df = df.copy()
        temp_df["up"] = np.where(temp_df["low"] >= temp_df["low"].shift(1), 1, 0)
        temp_df["dn"] = np.where(temp_df["high"] <= temp_df["high"].shift(1), 1, 0)
        
        if df["close"].iloc[-1] > df["open"].iloc[-1]:
            if temp_df["up"].iloc[-n:].sum() >= 0.7 * n:
                return "uptrend"
        elif df["open"].iloc[-1] > df["close"].iloc[-1]:
            if temp_df["dn"].iloc[-n:].sum() >= 0.7 * n:
                return "downtrend"
        return None
    
    def get_candle_type(self, df: pd.DataFrame) -> Optional[str]:
        """
        Returns the candle type of the last candle
        """
        if len(df) < 2:
            return None
            
        row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else None
        
        if self.is_doji(row, prev_row=prev_row):
            return "doji"
        
        maru_df = self.detect_maru_bozu(df)
        maru_value = maru_df["maru_bozu"].iloc[-1]
        if maru_value == "maru_bozu_green":
            return "maru_bozu_green"
        if maru_value == "maru_bozu_red":
            return "maru_bozu_red"
            
        if self.is_shooting_star(row, prev_row):
            return "shooting_star"
            
        if self.is_hammer(row, prev_row):
            return "hammer"
            
        return None
    
    def detect_advanced_pattern(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN"
    ) -> Optional[PatternMatch]:
        """
        Detect advanced candlestick patterns with trend context
        Returns pattern match with significance level
        """
        if len(df) < 10:
            return None
            
        row = df.iloc[-1]
        prev_row = df.iloc[-2]
        avg_candle_size = abs(df["close"] - df["open"]).median()
        candle = self.get_candle_type(df)
        trend = self.detect_trend(df.iloc[:-1])
        
        pattern = None
        direction = None
        confidence = 0.6
        
        # Doji patterns
        if candle == 'doji':
            if row['close'] > prev_row['close'] and row['close'] > row['open']:
                pattern = "Doji Bullish"
                direction = "bullish"
                confidence = 0.65
            elif row['close'] < prev_row['close'] and row['close'] < row['open']:
                pattern = "Doji Bearish"
                direction = "bearish"
                confidence = 0.65
        
        # Maru Bozu patterns
        if candle == "maru_bozu_green":
            pattern = "Maru Bozu Bullish"
            direction = "bullish"
            confidence = 0.85
        
        if candle == "maru_bozu_red":
            pattern = "Maru Bozu Bearish"
            direction = "bearish"
            confidence = 0.85
        
        # Hanging Man (hammer in uptrend)
        if trend == "uptrend" and candle == "hammer":
            pattern = "Hanging Man"
            direction = "bearish"
            confidence = 0.75
        
        # Hammer in downtrend
        if trend == "downtrend" and candle == "hammer":
            pattern = "Hammer Bullish"
            direction = "bullish"
            confidence = 0.80
        
        # Shooting Star in uptrend
        if trend == "uptrend" and candle == "shooting_star":
            pattern = "Shooting Star"
            direction = "bearish"
            confidence = 0.80
        
        # Harami Cross patterns
        if trend == "uptrend" and candle == "doji":
            if (row['high'] < prev_row['close'] and row['low'] > prev_row['open']):
                pattern = "Harami Cross Bearish"
                direction = "bearish"
                confidence = 0.75
        
        if trend == "downtrend" and candle == "doji":
            if (row['high'] < prev_row['open'] and row['low'] > prev_row['close']):
                pattern = "Harami Cross Bullish"
                direction = "bullish"
                confidence = 0.75
        
        # Engulfing patterns
        if trend == "uptrend" and candle != "doji":
            if (row['open'] > prev_row['high'] and row['close'] < prev_row['low']):
                pattern = "Engulfing Bearish"
                direction = "bearish"
                confidence = 0.90
        
        if trend == "downtrend" and candle != "doji":
            if (row['close'] > prev_row['high'] and row['open'] < prev_row['low']):
                pattern = "Engulfing Bullish"
                direction = "bullish"
                confidence = 0.90
        
        if pattern:
            return PatternMatch(
                timestamp=str(df.index[-1]),
                symbol=symbol,
                pattern=pattern,
                direction=direction,
                confidence=confidence,
                price=row['close'],
                description=f"{pattern} pattern detected"
            )
        
        return None


# Global singleton instance
pattern_scanner = CandlestickPatternScanner()
