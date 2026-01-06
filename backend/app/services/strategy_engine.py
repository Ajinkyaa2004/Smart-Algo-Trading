import pandas as pd
import numpy as np

class StrategyEngine:
    def calculate_indicators(self, df: pd.DataFrame):
        """Calculates common indicators (SMA, RSI, MACD)"""
        if df.empty:
            return df
        
        # SMA
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    def evaluate_strategy(self, df: pd.DataFrame, strategy_type: str, risk_profile: str):
        """
        Evaluates the latest signals based on strategy type and risk profile.
        Returns: 'BUY', 'SELL', or None
        """
        if df.empty or len(df) < 50:
            return None

        # Calculate indicators
        df = self.calculate_indicators(df)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        signal = None

        if strategy_type == 'trend': # MA Crossover
            # Aggressive: Fast crossover (e.g., 5/10) - simplifying to 20/50 for demo
            if prev_row['sma_20'] <= prev_row['sma_50'] and last_row['sma_20'] > last_row['sma_50']:
                signal = 'BUY'
            elif prev_row['sma_20'] >= prev_row['sma_50'] and last_row['sma_20'] < last_row['sma_50']:
                signal = 'SELL'

        elif strategy_type == 'reversion': # RSI
            oversold = 30 if risk_profile == 'high' else 35
            overbought = 70 if risk_profile == 'high' else 65
            
            if last_row['rsi'] < oversold:
                signal = "BUY"
            elif last_row['rsi'] > overbought:
                signal = "SELL"
        
        # Add Scalp logic etc.

        return signal

strategy_engine = StrategyEngine()
