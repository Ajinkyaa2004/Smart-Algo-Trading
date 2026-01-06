"""
Technical Indicators Engine
Vectorized, reusable technical indicator functions for algorithmic trading

All functions work on pandas DataFrames with OHLCV data
All calculations are vectorized using pandas/numpy for performance
"""
import pandas as pd
import numpy as np
from typing import Optional, Tuple


class TechnicalIndicators:
    """
    Collection of technical indicators for trading strategies
    All methods are static and work on OHLCV DataFrames
    """
    
    # ==================== MOVING AVERAGES ====================
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """
        Simple Moving Average
        
        Args:
            data: Price series (typically 'close')
            period: Number of periods
            
        Returns:
            SMA series
        """
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """
        Exponential Moving Average
        
        Args:
            data: Price series (typically 'close')
            period: Number of periods
            
        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def wma(data: pd.Series, period: int) -> pd.Series:
        """
        Weighted Moving Average
        
        Args:
            data: Price series
            period: Number of periods
            
        Returns:
            WMA series
        """
        weights = np.arange(1, period + 1)
        
        def weighted_mean(x):
            return np.dot(x, weights) / weights.sum()
        
        return data.rolling(window=period).apply(weighted_mean, raw=True)
    
    # ==================== RSI ====================
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Relative Strength Index
        
        Args:
            data: Price series (typically 'close')
            period: RSI period (default: 14)
            
        Returns:
            RSI series (0-100)
        """
        # Calculate price changes
        delta = data.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def rsi_ema(data: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI using EMA (Wilder's smoothing)
        More accurate than simple RSI
        
        Args:
            data: Price series
            period: RSI period
            
        Returns:
            RSI series
        """
        delta = data.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Use EMA for smoothing (Wilder's method)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    # ==================== MACD ====================
    
    @staticmethod
    def macd(
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence
        
        Args:
            data: Price series (typically 'close')
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        # Calculate EMAs
        ema_fast = data.ewm(span=fast_period, adjust=False).mean()
        ema_slow = data.ewm(span=slow_period, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    # ==================== BOLLINGER BANDS ====================
    
    @staticmethod
    def bollinger_bands(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands
        
        Args:
            data: Price series (typically 'close')
            period: Moving average period (default: 20)
            std_dev: Number of standard deviations (default: 2)
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        # Middle band (SMA)
        middle_band = data.rolling(window=period).mean()
        
        # Standard deviation
        std = data.rolling(window=period).std()
        
        # Upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def bollinger_bandwidth(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.Series:
        """
        Bollinger Band Width (volatility indicator)
        
        Args:
            data: Price series
            period: BB period
            std_dev: Standard deviations
            
        Returns:
            Bandwidth series
        """
        upper, middle, lower = TechnicalIndicators.bollinger_bands(data, period, std_dev)
        bandwidth = (upper - lower) / middle
        return bandwidth
    
    # ==================== VWAP ====================
    
    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        """
        Volume Weighted Average Price
        
        Args:
            df: DataFrame with 'high', 'low', 'close', 'volume' columns
            
        Returns:
            VWAP series
        """
        # Typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # VWAP calculation
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        return vwap
    
    @staticmethod
    def vwap_intraday(df: pd.DataFrame) -> pd.Series:
        """
        Intraday VWAP (resets daily)
        
        Args:
            df: DataFrame with datetime index and OHLCV columns
            
        Returns:
            VWAP series
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Group by date and calculate cumulative VWAP
        df_copy = df.copy()
        df_copy['typical_price'] = typical_price
        df_copy['date'] = df_copy.index.date
        
        df_copy['pv'] = df_copy['typical_price'] * df_copy['volume']
        df_copy['cumulative_pv'] = df_copy.groupby('date')['pv'].cumsum()
        df_copy['cumulative_volume'] = df_copy.groupby('date')['volume'].cumsum()
        
        vwap = df_copy['cumulative_pv'] / df_copy['cumulative_volume']
        
        return vwap
    
    # ==================== ATR ====================
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average True Range (volatility indicator)
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period (default: 14)
            
        Returns:
            ATR series
        """
        # True Range calculation
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR is EMA of True Range
        atr = true_range.ewm(alpha=1/period, adjust=False).mean()
        
        return atr
    
    @staticmethod
    def supertrend(
        df: pd.DataFrame,
        period: int = 10,
        multiplier: float = 3.0
    ) -> pd.Series:
        """
        Supertrend Indicator
        
        Args:
            df: DataFrame with OHLC columns
            period: ATR period
            multiplier: ATR multiplier
            
        Returns:
            Supertrend series
        """
        # Calculate ATR
        atr = TechnicalIndicators.atr(df, period)
        
        # Basic upper and lower bands
        hl_avg = (df['high'] + df['low']) / 2
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        # Initialize
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        
        for i in range(period, len(df)):
            if i == period:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            else:
                # Uptrend
                if direction.iloc[i-1] == 1:
                    if df['close'].iloc[i] <= supertrend.iloc[i-1]:
                        supertrend.iloc[i] = upper_band.iloc[i]
                        direction.iloc[i] = -1
                    else:
                        supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i-1])
                        direction.iloc[i] = 1
                # Downtrend
                else:
                    if df['close'].iloc[i] >= supertrend.iloc[i-1]:
                        supertrend.iloc[i] = lower_band.iloc[i]
                        direction.iloc[i] = 1
                    else:
                        supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i-1])
                        direction.iloc[i] = -1
        
        return supertrend

    @staticmethod
    def get_available_indicators() -> list[str]:
        """
        Get list of available technical indicators
        
        Returns:
            List of indicator names
        """
        return [
            "SMA (Simple Moving Average)",
            "EMA (Exponential Moving Average)",
            "WMA (Weighted Moving Average)",
            "RSI (Relative Strength Index)",
            "MACD (Moving Average Convergence Divergence)",
            "Bollinger Bands",
            "VWAP (Volume Weighted Average Price)",
            "ATR (Average True Range)",
            "Supertrend",
            "Stochastic Oscillator",
            "ADX (Average Directional Index)"
        ]
    
    # ==================== HELPER METHODS ====================
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all common indicators to a DataFrame
        
        Args:
            df: DataFrame with OHLCV columns
            
        Returns:
            DataFrame with all indicators added
        """
        df = df.copy()
        
        # Moving Averages
        df['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
        df['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
        df['sma_200'] = TechnicalIndicators.sma(df['close'], 200)
        df['ema_9'] = TechnicalIndicators.ema(df['close'], 9)
        df['ema_21'] = TechnicalIndicators.ema(df['close'], 21)
        
        # RSI
        df['rsi'] = TechnicalIndicators.rsi_ema(df['close'], 14)
        
        # MACD
        macd, signal, hist = TechnicalIndicators.macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist
        
        # Bollinger Bands
        upper, middle, lower = TechnicalIndicators.bollinger_bands(df['close'])
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        
        # ATR
        df['atr'] = TechnicalIndicators.atr(df, 14)
        
        # VWAP (if volume exists)
        if 'volume' in df.columns:
            df['vwap'] = TechnicalIndicators.vwap(df)
        
        return df


# Convenience alias
indicators = TechnicalIndicators()
