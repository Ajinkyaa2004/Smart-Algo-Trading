"""
Price Action Analysis Service
Implements support/resistance detection, trend identification, and breakout logic
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False


@dataclass
class SupportResistance:
    """Support or Resistance level"""
    level: float
    type: str  # 'support' or 'resistance'
    strength: int  # Number of touches
    first_touch: str  # Timestamp
    last_touch: str  # Timestamp


@dataclass
class CandleAnatomy:
    """Detailed candlestick anatomy"""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    body: float  # abs(close - open)
    upper_wick: float  # high - max(open, close)
    lower_wick: float  # min(open, close) - low
    total_range: float  # high - low
    body_percentage: float  # body / total_range * 100
    is_bullish: bool
    is_bearish: bool
    is_doji: bool  # body < 10% of range


class PriceActionService:
    """
    Service for price action analysis
    - Support & Resistance detection
    - Trend identification
    - Breakout & rejection logic
    - Candlestick anatomy analysis
    """
    
    # ==================== CANDLESTICK ANATOMY ====================
    
    @staticmethod
    def analyze_candle(row: pd.Series) -> CandleAnatomy:
        """
        Analyze a single candlestick's anatomy
        
        Args:
            row: DataFrame row with OHLC data
            
        Returns:
            CandleAnatomy object with detailed analysis
        """
        open_price = row['open']
        high = row['high']
        low = row['low']
        close = row['close']
        
        # Calculate components
        body = abs(close - open_price)
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low
        total_range = high - low
        
        # Avoid division by zero
        body_percentage = (body / total_range * 100) if total_range > 0 else 0
        
        # Determine candle type
        is_bullish = close > open_price
        is_bearish = close < open_price
        is_doji = body_percentage < 10  # Doji: small body
        
        return CandleAnatomy(
            timestamp=str(row.name) if hasattr(row, 'name') else '',
            open=open_price,
            high=high,
            low=low,
            close=close,
            body=body,
            upper_wick=upper_wick,
            lower_wick=lower_wick,
            total_range=total_range,
            body_percentage=body_percentage,
            is_bullish=is_bullish,
            is_bearish=is_bearish,
            is_doji=is_doji
        )
    
    @staticmethod
    def add_candle_anatomy(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add candlestick anatomy columns to DataFrame
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with anatomy columns added
        """
        df = df.copy()
        
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        df['total_range'] = df['high'] - df['low']
        df['body_percentage'] = (df['body'] / df['total_range'] * 100).fillna(0)
        df['is_bullish'] = df['close'] > df['open']
        df['is_bearish'] = df['close'] < df['open']
        df['is_doji'] = df['body_percentage'] < 10
        
        return df
    
    # ==================== SUPPORT & RESISTANCE ====================
    
    @staticmethod
    def find_support_resistance(
        df: pd.DataFrame,
        window: int = 20,
        min_touches: int = 2,
        tolerance: float = 0.02
    ) -> List[SupportResistance]:
        """
        Detect support and resistance levels
        
        Args:
            df: DataFrame with OHLC data
            window: Lookback window for pivot detection
            min_touches: Minimum touches to confirm level
            tolerance: Price tolerance (2% = 0.02)
            
        Returns:
            List of SupportResistance objects
        """
        levels = []
        
        # Find local highs and lows (pivot points)
        df = df.copy()
        df['pivot_high'] = df['high'] == df['high'].rolling(window=window, center=True).max()
        df['pivot_low'] = df['low'] == df['low'].rolling(window=window, center=True).min()
        
        # Extract pivot points
        pivot_highs = df[df['pivot_high']]['high'].tolist()
        pivot_lows = df[df['pivot_low']]['low'].tolist()
        
        # Cluster pivot highs (resistance)
        resistance_levels = PriceActionService._cluster_levels(
            pivot_highs, tolerance, min_touches
        )
        
        for level, touches, timestamps in resistance_levels:
            levels.append(SupportResistance(
                level=level,
                type='resistance',
                strength=touches,
                first_touch=timestamps[0],
                last_touch=timestamps[-1]
            ))
        
        # Cluster pivot lows (support)
        support_levels = PriceActionService._cluster_levels(
            pivot_lows, tolerance, min_touches
        )
        
        for level, touches, timestamps in support_levels:
            levels.append(SupportResistance(
                level=level,
                type='support',
                strength=touches,
                first_touch=timestamps[0],
                last_touch=timestamps[-1]
            ))
        
        return levels
    
    @staticmethod
    def _cluster_levels(
        prices: List[float],
        tolerance: float,
        min_touches: int
    ) -> List[Tuple[float, int, List[str]]]:
        """
        Cluster similar price levels
        
        Args:
            prices: List of price levels
            tolerance: Clustering tolerance
            min_touches: Minimum cluster size
            
        Returns:
            List of (average_level, touch_count, timestamps)
        """
        if not prices:
            return []
        
        clusters = []
        sorted_prices = sorted(prices)
        
        current_cluster = [sorted_prices[0]]
        
        for price in sorted_prices[1:]:
            # Check if price is within tolerance of cluster average
            cluster_avg = np.mean(current_cluster)
            if abs(price - cluster_avg) / cluster_avg <= tolerance:
                current_cluster.append(price)
            else:
                # Save cluster if it meets minimum touches
                if len(current_cluster) >= min_touches:
                    clusters.append((
                        np.mean(current_cluster),
                        len(current_cluster),
                        [''] * len(current_cluster)  # Timestamps placeholder
                    ))
                current_cluster = [price]
        
        # Don't forget the last cluster
        if len(current_cluster) >= min_touches:
            clusters.append((
                np.mean(current_cluster),
                len(current_cluster),
                [''] * len(current_cluster)
            ))
        
        return clusters
    
    # ==================== TREND IDENTIFICATION ====================
    
    @staticmethod
    def identify_trend(
        df: pd.DataFrame,
        period: int = 20,
        method: str = 'ma'
    ) -> pd.Series:
        """
        Identify trend direction
        
        Args:
            df: DataFrame with OHLC data
            period: Period for trend calculation
            method: 'ma' (moving average) or 'highs_lows' (higher highs/lows)
            
        Returns:
            Series with trend values: 1 (uptrend), -1 (downtrend), 0 (sideways)
        """
        if method == 'ma':
            # Moving average method
            ma = df['close'].rolling(window=period).mean()
            trend = pd.Series(0, index=df.index)
            trend[df['close'] > ma] = 1  # Uptrend
            trend[df['close'] < ma] = -1  # Downtrend
            
        elif method == 'highs_lows':
            # Higher highs / Lower lows method
            trend = pd.Series(0, index=df.index)
            
            for i in range(period, len(df)):
                recent_highs = df['high'].iloc[i-period:i]
                recent_lows = df['low'].iloc[i-period:i]
                
                # Check if making higher highs and higher lows
                if (df['high'].iloc[i] > recent_highs.max() and 
                    df['low'].iloc[i] > recent_lows.min()):
                    trend.iloc[i] = 1  # Uptrend
                
                # Check if making lower lows and lower highs
                elif (df['low'].iloc[i] < recent_lows.min() and 
                      df['high'].iloc[i] < recent_highs.max()):
                    trend.iloc[i] = -1  # Downtrend
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return trend
    
    @staticmethod
    def calculate_trend_strength(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate trend strength using ADX-like logic
        
        Args:
            df: DataFrame with OHLC data
            period: Calculation period
            
        Returns:
            Series with trend strength (0-100)
        """
        # Calculate directional movement
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        # Calculate True Range
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smooth using EMA
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        
        return adx
    
    # ==================== BREAKOUT & REJECTION ====================
    
    @staticmethod
    def detect_breakout(
        df: pd.DataFrame,
        level: float,
        direction: str = 'up',
        confirmation_candles: int = 1
    ) -> pd.Series:
        """
        Detect breakouts above/below a level
        
        Args:
            df: DataFrame with OHLC data
            level: Price level to monitor
            direction: 'up' or 'down'
            confirmation_candles: Number of candles to confirm breakout
            
        Returns:
            Boolean series indicating breakout points
        """
        breakout = pd.Series(False, index=df.index)
        
        if direction == 'up':
            # Breakout above level
            above_level = df['close'] > level
            # Confirm with multiple candles
            confirmed = above_level.rolling(window=confirmation_candles).sum() == confirmation_candles
            # First breakout point
            breakout = confirmed & ~confirmed.shift(1).fillna(False)
            
        elif direction == 'down':
            # Breakout below level
            below_level = df['close'] < level
            confirmed = below_level.rolling(window=confirmation_candles).sum() == confirmation_candles
            breakout = confirmed & ~confirmed.shift(1).fillna(False)
        
        return breakout
    
    @staticmethod
    def detect_rejection(
        df: pd.DataFrame,
        level: float,
        rejection_type: str = 'resistance',
        wick_ratio: float = 0.5
    ) -> pd.Series:
        """
        Detect price rejections at support/resistance
        
        Args:
            df: DataFrame with OHLC data
            level: Price level
            rejection_type: 'resistance' or 'support'
            wick_ratio: Minimum wick size as ratio of total range
            
        Returns:
            Boolean series indicating rejection points
        """
        df = PriceActionService.add_candle_anatomy(df)
        
        rejection = pd.Series(False, index=df.index)
        
        if rejection_type == 'resistance':
            # Price touched level but closed below with long upper wick
            touched = df['high'] >= level
            closed_below = df['close'] < level
            long_wick = (df['upper_wick'] / df['total_range']) > wick_ratio
            rejection = touched & closed_below & long_wick
            
        elif rejection_type == 'support':
            # Price touched level but closed above with long lower wick
            touched = df['low'] <= level
            closed_above = df['close'] > level
            long_wick = (df['lower_wick'] / df['total_range']) > wick_ratio
            rejection = touched & closed_above & long_wick
        
        return rejection
    
    @staticmethod
    def detect_false_breakout(
        df: pd.DataFrame,
        level: float,
        direction: str = 'up',
        retracement_candles: int = 3
    ) -> pd.Series:
        """
        Detect false breakouts (breakout followed by reversal)
        
        Args:
            df: DataFrame with OHLC data
            level: Price level
            direction: 'up' or 'down'
            retracement_candles: Candles to wait for reversal
            
        Returns:
            Boolean series indicating false breakout points
        """
        false_breakout = pd.Series(False, index=df.index)
        
        if direction == 'up':
            # Broke above but closed back below
            broke_above = df['high'] > level
            closed_below = df['close'].shift(-retracement_candles) < level
            false_breakout = broke_above & closed_below
            
        elif direction == 'down':
            # Broke below but closed back above
            broke_below = df['low'] < level
            closed_above = df['close'].shift(-retracement_candles) > level
            false_breakout = broke_below & closed_above
        
        return false_breakout
    
    # ==================== CANDLESTICK PATTERNS ====================
    
    @staticmethod
    def identify_doji(df: pd.DataFrame, tolerance: float = 0.05) -> pd.DataFrame:
        """
        Identify Doji candlestick pattern
        
        A Doji forms when the open and close prices are virtually equal.
        It signals indecision in the market.
        
        Args:
            df: DataFrame with OHLC data
            tolerance: Body size tolerance as ratio of median candle size (0.05 = 5%)
            
        Returns:
            DataFrame with 'doji' boolean column added
        """
        df = df.copy()
        
        # Calculate average candle body size (median is more robust than mean)
        avg_candle_size = abs(df["close"] - df["open"]).median()
        
        # Doji: body is very small compared to average candle
        df["doji"] = abs(df["close"] - df["open"]) <= (tolerance * avg_candle_size)
        
        return df
    
    @staticmethod
    def identify_hammer(df: pd.DataFrame, body_ratio: float = 3.0, 
                       tail_ratio: float = 0.6, body_size_min: float = 0.1) -> pd.DataFrame:
        """
        Identify Hammer candlestick pattern
        
        A Hammer is a bullish reversal pattern with:
        - Long lower shadow (at least 2x the body)
        - Small body near the top
        - Little to no upper shadow
        
        Args:
            df: DataFrame with OHLC data
            body_ratio: Minimum ratio of (high-low) to body (default: 3.0)
            tail_ratio: Minimum ratio of lower tail to total range (default: 0.6)
            body_size_min: Minimum body size as ratio of total range (default: 0.1)
            
        Returns:
            DataFrame with 'hammer' boolean column added
        """
        df = df.copy()
        
        # Calculate components
        total_range = df["high"] - df["low"]
        body = abs(df["close"] - df["open"])
        lower_tail_close = df["close"] - df["low"]
        lower_tail_open = df["open"] - df["low"]
        
        # Avoid division by zero
        safe_range = total_range + 0.001
        
        # Hammer conditions:
        # 1. Total range is at least 3x the body size
        condition1 = total_range > (body_ratio * body)
        
        # 2. Lower tail is at least 60% of total range (both from open and close)
        condition2 = (lower_tail_close / safe_range) > tail_ratio
        condition3 = (lower_tail_open / safe_range) > tail_ratio
        
        # 3. Body is at least 10% of total range (not too small)
        condition4 = body > (body_size_min * total_range)
        
        # Combine all conditions
        df["hammer"] = condition1 & condition2 & condition3 & condition4
        
        return df
    
    @staticmethod
    def identify_shooting_star(df: pd.DataFrame, body_ratio: float = 3.0, 
                               tail_ratio: float = 0.6, body_size_min: float = 0.1) -> pd.DataFrame:
        """
        Identify Shooting Star candlestick pattern
        
        A Shooting Star is a bearish reversal pattern (inverted hammer) with:
        - Long upper shadow (at least 2x the body)
        - Small body near the bottom
        - Little to no lower shadow
        
        Args:
            df: DataFrame with OHLC data
            body_ratio: Minimum ratio of (high-low) to body (default: 3.0)
            tail_ratio: Minimum ratio of upper tail to total range (default: 0.6)
            body_size_min: Minimum body size as ratio of total range (default: 0.1)
            
        Returns:
            DataFrame with 'shooting_star' boolean column added
        """
        df = df.copy()
        
        # Calculate components
        total_range = df["high"] - df["low"]
        body = abs(df["close"] - df["open"])
        upper_tail_close = df["high"] - df["close"]
        upper_tail_open = df["high"] - df["open"]
        
        # Avoid division by zero
        safe_range = total_range + 0.001
        
        # Shooting Star conditions (opposite of hammer):
        # 1. Total range is at least 3x the body size
        condition1 = total_range > (body_ratio * body)
        
        # 2. Upper tail is at least 60% of total range (both from open and close)
        condition2 = (upper_tail_close / safe_range) > tail_ratio
        condition3 = (upper_tail_open / safe_range) > tail_ratio
        
        # 3. Body is at least 10% of total range (not too small)
        condition4 = body > (body_size_min * total_range)
        
        # Combine all conditions
        df["shooting_star"] = condition1 & condition2 & condition3 & condition4
        
        return df
    
    @staticmethod
    def identify_marubozu(df: pd.DataFrame, body_multiplier: float = 2.0, 
                          wick_tolerance: float = 0.005) -> pd.DataFrame:
        """
        Identify Marubozu candlestick pattern
        
        A Marubozu is a strong trending candle with little to no wicks:
        - Green Marubozu: Strong bullish candle (close >> open, minimal wicks)
        - Red Marubozu: Strong bearish candle (open >> close, minimal wicks)
        
        Args:
            df: DataFrame with OHLC data
            body_multiplier: Body must be at least this times the median candle (default: 2.0)
            wick_tolerance: Maximum wick size as ratio of median candle (default: 0.005 = 0.5%)
            
        Returns:
            DataFrame with 'marubozu' column ('green', 'red', or False)
        """
        df = df.copy()
        
        # Calculate median candle size
        avg_candle_size = abs(df["close"] - df["open"]).median()
        
        # Calculate wick components
        df["h-c"] = df["high"] - df["close"]  # Upper wick for green
        df["l-o"] = df["low"] - df["open"]    # Lower wick for green
        df["h-o"] = df["high"] - df["open"]   # Upper wick for red
        df["l-c"] = df["low"] - df["close"]   # Lower wick for red
        
        # Green Marubozu conditions:
        # 1. Strong bullish body (close > open by at least 2x median)
        # 2. Both upper and lower wicks are very small
        green_condition = (
            (df["close"] - df["open"] > body_multiplier * avg_candle_size) &
            (df[["h-c", "l-o"]].max(axis=1) < wick_tolerance * avg_candle_size)
        )
        
        # Red Marubozu conditions:
        # 1. Strong bearish body (open > close by at least 2x median)
        # 2. Both upper and lower wicks are very small
        red_condition = (
            (df["open"] - df["close"] > body_multiplier * avg_candle_size) &
            (df[["h-o", "l-c"]].abs().max(axis=1) < wick_tolerance * avg_candle_size)
        )
        
        # Assign pattern type
        df["marubozu"] = np.where(green_condition, "green",
                                   np.where(red_condition, "red", False))
        
        # Clean up temporary columns
        df.drop(["h-c", "l-o", "h-o", "l-c"], axis=1, inplace=True)
        
        return df
    
    # ==================== PIVOT POINTS ====================
    
    @staticmethod
    def calculate_pivot_points(ohlc_day: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate pivot point and support/resistance levels
        
        Uses classic pivot point formula based on previous day's price action:
        - PP = (High + Low + Close) / 3
        - R1 = 2*PP - Low, R2 = PP + (High - Low), R3 = High + 2*(PP - Low)
        - S1 = 2*PP - High, S2 = PP - (High - Low), S3 = Low - 2*(High - PP)
        
        Args:
            ohlc_day: DataFrame with daily OHLC data
            
        Returns:
            Dictionary with pivot levels: {pivot, r1, r2, r3, s1, s2, s3}
        """
        # Get last completed day's data
        high = round(ohlc_day["high"].iloc[-1], 2)
        low = round(ohlc_day["low"].iloc[-1], 2)
        close = round(ohlc_day["close"].iloc[-1], 2)
        
        # Calculate pivot point
        pivot = round((high + low + close) / 3, 2)
        
        # Calculate resistance levels
        r1 = round((2 * pivot - low), 2)
        r2 = round((pivot + (high - low)), 2)
        r3 = round((high + 2 * (pivot - low)), 2)
        
        # Calculate support levels
        s1 = round((2 * pivot - high), 2)
        s2 = round((pivot - (high - low)), 2)
        s3 = round((low - 2 * (high - pivot)), 2)
        
        return {
            "pivot": pivot,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "s1": s1,
            "s2": s2,
            "s3": s3
        }
    
    @staticmethod
    def calculate_pivot_points_range(df: pd.DataFrame, daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add pivot point levels to intraday data based on daily OHLC
        
        Args:
            df: Intraday DataFrame with OHLC data
            daily_df: Daily DataFrame with OHLC data
            
        Returns:
            DataFrame with pivot point columns added
        """
        df = df.copy()
        
        # Calculate pivot points from previous day
        if len(daily_df) > 0:
            levels = PriceActionService.calculate_pivot_points(daily_df.iloc[:-1])
            
            # Add as constant columns for the trading day
            df["pivot"] = levels["pivot"]
            df["r1"] = levels["r1"]
            df["r2"] = levels["r2"]
            df["r3"] = levels["r3"]
            df["s1"] = levels["s1"]
            df["s2"] = levels["s2"]
            df["s3"] = levels["s3"]
        
        return df
    
    # ==================== SLOPE & REGRESSION ANALYSIS ====================
    
    @staticmethod
    def calculate_slope(ohlc_df: pd.DataFrame, n: int = 7) -> float:
        """
        Calculate the slope of regression line for last n candles
        
        Uses linear regression on scaled price data to determine trend angle.
        Positive slope = uptrend, negative slope = downtrend
        
        Args:
            ohlc_df: DataFrame with OHLC data
            n: Number of recent candles to analyze (default: 7)
            
        Returns:
            Slope angle in degrees (-90 to +90)
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels is required for slope calculation. Install with: pip install statsmodels")
        
        # Get last n candles
        df = ohlc_df.iloc[-1 * n:, :]
        
        # Use average of open and close as representative price
        y = ((df["open"] + df["close"]) / 2).values
        x = np.array(range(n))
        
        # Scale both x and y to 0-1 range for stable regression
        y_scaled = (y - y.min()) / (y.max() - y.min()) if y.max() != y.min() else y
        x_scaled = (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else x
        
        # Add constant term for regression
        x_scaled = sm.add_constant(x_scaled)
        
        # Fit OLS regression model
        model = sm.OLS(y_scaled, x_scaled)
        results = model.fit()
        
        # Convert slope to degrees using arctan
        slope_degrees = np.rad2deg(np.arctan(results.params[-1]))
        
        return slope_degrees
    
    @staticmethod
    def analyze_trend_pattern(ohlc_df: pd.DataFrame, n: int = 7, 
                             threshold: float = 0.7) -> Optional[str]:
        """
        Analyze trend by checking if candles are making higher lows or lower highs
        
        Args:
            ohlc_df: DataFrame with OHLC data
            n: Number of recent candles to analyze (default: 7)
            threshold: Percentage of candles that must confirm trend (default: 0.7 = 70%)
            
        Returns:
            "uptrend", "downtrend", or None if no clear trend
        """
        df = ohlc_df.copy()
        
        # Check for higher lows (uptrend signal)
        df["up"] = np.where(df["low"] >= df["low"].shift(1), 1, 0)
        
        # Check for lower highs (downtrend signal)
        df["dn"] = np.where(df["high"] <= df["high"].shift(1), 1, 0)
        
        # Get last candle direction
        last_candle = df.iloc[-1]
        is_bullish_candle = last_candle["close"] > last_candle["open"]
        is_bearish_candle = last_candle["open"] > last_candle["close"]
        
        # Check if enough candles confirm the trend
        if is_bullish_candle:
            # If last candle is bullish, check for uptrend (higher lows)
            higher_lows_count = df["up"].iloc[-1 * n:].sum()
            if higher_lows_count >= threshold * n:
                return "uptrend"
        
        elif is_bearish_candle:
            # If last candle is bearish, check for downtrend (lower highs)
            lower_highs_count = df["dn"].iloc[-1 * n:].sum()
            if lower_highs_count >= threshold * n:
                return "downtrend"
        
        # No clear trend
        return None
    
    @staticmethod
    def add_slope_indicator(df: pd.DataFrame, period: int = 7) -> pd.DataFrame:
        """
        Add rolling slope indicator to DataFrame
        
        Args:
            df: DataFrame with OHLC data
            period: Period for slope calculation
            
        Returns:
            DataFrame with 'slope' column added
        """
        df = df.copy()
        slopes = []
        
        for i in range(len(df)):
            if i < period - 1:
                slopes.append(np.nan)
            else:
                try:
                    slope_val = PriceActionService.calculate_slope(
                        df.iloc[:i + 1], n=period
                    )
                    slopes.append(slope_val)
                except:
                    slopes.append(np.nan)
        
        df['slope'] = slopes
        return df


# Global singleton instance
price_action_service = PriceActionService()
