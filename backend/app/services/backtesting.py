"""
Backtesting Service
Runs trading strategies on historical data to evaluate performance
Uses REAL historical data from Kite Connect API
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import uuid
from dataclasses import dataclass, asdict
import json

from app.services.market_data import MarketDataService
from app.services.indicators import TechnicalIndicators
from app.services.pattern_scanner import pattern_scanner
from app.services.price_action import price_action_service
# Note: Strategy classes are not directly imported as we use strategy logic inline
# from app.strategies.supertrend_strategy import SupertrendStrategy
# from app.strategies.ema_rsi_strategy import EMA_RSI_Strategy
# from app.strategies.renko_macd_strategy import RenkoMacdStrategy


@dataclass
class BacktestTrade:
    """Represents a single backtest trade"""
    entry_time: str
    exit_time: str
    symbol: str
    direction: str  # BUY or SELL
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    pnl_percent: float
    holding_period: str  # in hours/minutes
    
    
@dataclass
class BacktestMetrics:
    """Performance metrics from backtesting"""
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    loss_rate: float
    
    # P&L metrics
    total_pnl: float
    total_pnl_percent: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    
    # Trade statistics
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_holding_period: str
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    expectancy: float
    
    # Additional metrics
    consecutive_wins: int
    consecutive_losses: int
    avg_trades_per_day: float
    
    
@dataclass
class BacktestResult:
    """Complete backtest result"""
    backtest_id: str
    strategy_type: str
    symbol: str
    start_date: str
    end_date: str
    interval: str
    initial_capital: float
    final_capital: float
    
    metrics: BacktestMetrics
    trades: List[BacktestTrade]
    equity_curve: List[Dict]  # [{date, equity, drawdown}]
    
    # Strategy parameters used
    strategy_params: Dict
    
    # Execution details
    total_candles: int
    execution_time: float  # in seconds
    created_at: str


class BacktestingService:
    """
    Backtesting service for evaluating trading strategies
    Uses REAL historical data from Kite Connect API
    """
    
    def __init__(self):
        self.market_data = MarketDataService()
        self.indicators = TechnicalIndicators()
        self.backtest_results = {}  # Store results in memory
        
    def run_backtest(
        self,
        symbol: str,
        exchange: str,
        strategy_type: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "15minute",
        initial_capital: float = 100000.0,
        strategy_params: Optional[Dict] = None
    ) -> BacktestResult:
        """
        Run backtest on historical data
        
        Args:
            symbol: Trading symbol (e.g., "RELIANCE")
            exchange: Exchange (NSE, BSE)
            strategy_type: Strategy to test (supertrend, ema_rsi, renko_macd)
            start_date: Backtest start date
            end_date: Backtest end date
            interval: Candle interval (minute, 3minute, 5minute, 15minute, 30minute, 60minute, day)
            initial_capital: Starting capital
            strategy_params: Strategy-specific parameters
            
        Returns:
            BacktestResult with complete performance analysis
        """
        start_time = datetime.now()
        
        # Fetch REAL historical data from Kite API
        print(f"Fetching historical data for {symbol} from {start_date} to {end_date}...")
        df = self.market_data.get_historical_data_by_symbol(
            symbol=symbol,
            exchange=exchange,
            from_date=start_date,
            to_date=end_date,
            interval=interval
        )
        
        if df is None or df.empty:
            raise ValueError(f"No historical data available for {symbol}")
        
        print(f"Fetched {len(df)} candles for backtesting")
        
        # Add technical indicators
        df = self._add_indicators(df, strategy_type, strategy_params)
        
        # Run strategy simulation
        trades, equity_curve = self._simulate_strategy(
            df=df,
            symbol=symbol,
            strategy_type=strategy_type,
            initial_capital=initial_capital,
            strategy_params=strategy_params or {}
        )
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=initial_capital,
            total_days=(end_date - start_date).days
        )
        
        # Create backtest result
        execution_time = (datetime.now() - start_time).total_seconds()
        backtest_id = str(uuid.uuid4())
        
        result = BacktestResult(
            backtest_id=backtest_id,
            strategy_type=strategy_type,
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            interval=interval,
            initial_capital=initial_capital,
            final_capital=equity_curve[-1]['equity'] if equity_curve else initial_capital,
            metrics=metrics,
            trades=trades,
            equity_curve=equity_curve,
            strategy_params=strategy_params or {},
            total_candles=len(df),
            execution_time=execution_time,
            created_at=datetime.now().isoformat()
        )
        
        # Store result
        self.backtest_results[backtest_id] = result
        
        print(f"Backtest completed in {execution_time:.2f}s")
        print(f"Total Trades: {metrics.total_trades}, Win Rate: {metrics.win_rate:.2f}%")
        
        return result
    
    def _add_indicators(self, df: pd.DataFrame, strategy_type: str = None, strategy_params: Dict = None) -> pd.DataFrame:
        """Add all technical indicators to the dataframe"""
        strategy_params = strategy_params or {}
        
        # DEFAULT Indicators (always needed for basic analysis)
        # Moving averages
        df['ema_9'] = self.indicators.ema(df['close'], 9)
        df['ema_21'] = self.indicators.ema(df['close'], 21)
        df['ema_50'] = self.indicators.ema(df['close'], 50)
        df['sma_200'] = self.indicators.sma(df['close'], 200)
        
        # RSI
        df['rsi'] = self.indicators.rsi(df['close'], 14)
        
        # MACD
        macd, signal, hist = self.indicators.macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist
        
        # Bollinger Bands
        upper, middle, lower = self.indicators.bollinger_bands(df['close'])
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        
        # ATR and Supertrend
        df['atr'] = self.indicators.atr(df, 10)
        df['supertrend'] = self.indicators.supertrend(df, period=10, multiplier=3.0)
        
        # STRATEGY SPECIFIC INDICATORS
        if strategy_type == 'ema_scalping':
            fast = int(strategy_params.get('fast_period', 9))
            slow = int(strategy_params.get('slow_period', 21))
            df['ema_fast'] = self.indicators.ema(df['close'], fast)
            df['ema_slow'] = self.indicators.ema(df['close'], slow)
            
        elif strategy_type == 'breakout':
            # Volume average for breakout
            df['volume_avg'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def _simulate_strategy(
        self,
        df: pd.DataFrame,
        symbol: str,
        strategy_type: str,
        initial_capital: float,
        strategy_params: Dict
    ) -> Tuple[List[BacktestTrade], List[Dict]]:
        """
        Simulate strategy execution on historical data
        
        Returns:
            Tuple of (trades, equity_curve)
        """
        trades = []
        equity_curve = []
        
        current_capital = initial_capital
        position = None  # Current open position
        strategy_state = {}  # State for stateful strategies (like ORB)
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Generate signal based on strategy
            signal = self._generate_signal(
                df=df,
                index=i,
                strategy_type=strategy_type,
                strategy_params=strategy_params,
                state=strategy_state
            )
            
            # Execute trades based on signal
            if signal and position is None:
                # Open new position
                if signal['action'] in ['BUY', 'SELL']:
                    quantity = int(current_capital * 0.95 / row['close'])  # Use 95% of capital
                    position = {
                        'entry_time': row.name,
                        'direction': signal['action'],
                        'entry_price': row['close'],
                        'quantity': quantity,
                        'stop_loss': signal.get('stop_loss'),
                        'target': signal.get('target')
                    }
            
            elif position is not None:
                # Check exit conditions
                exit_signal = False
                exit_reason = None
                
                # Check stop loss
                if position['stop_loss']:
                    if position['direction'] == 'BUY' and row['low'] <= position['stop_loss']:
                        exit_signal = True
                        exit_reason = 'stop_loss'
                    elif position['direction'] == 'SELL' and row['high'] >= position['stop_loss']:
                        exit_signal = True
                        exit_reason = 'stop_loss'
                
                # Check target
                if position['target']:
                    if position['direction'] == 'BUY' and row['high'] >= position['target']:
                        exit_signal = True
                        exit_reason = 'target'
                    elif position['direction'] == 'SELL' and row['low'] <= position['target']:
                        exit_signal = True
                        exit_reason = 'target'
                
                # Check reverse signal
                if signal and signal['action'] != position['direction']:
                    exit_signal = True
                    exit_reason = 'reverse_signal'
                
                # Exit position
                if exit_signal:
                    exit_price = row['close']
                    if exit_reason == 'stop_loss':
                        exit_price = position['stop_loss']
                    elif exit_reason == 'target':
                        exit_price = position['target']
                    
                    # Calculate P&L
                    if position['direction'] == 'BUY':
                        pnl = (exit_price - position['entry_price']) * position['quantity']
                    else:  # SELL
                        pnl = (position['entry_price'] - exit_price) * position['quantity']
                    
                    pnl_percent = (pnl / (position['entry_price'] * position['quantity'])) * 100
                    
                    # Calculate holding period
                    holding_period = row.name - position['entry_time']
                    holding_hours = holding_period.total_seconds() / 3600
                    
                    # Create trade record
                    trade = BacktestTrade(
                        entry_time=position['entry_time'].strftime("%Y-%m-%d %H:%M:%S"),
                        exit_time=row.name.strftime("%Y-%m-%d %H:%M:%S"),
                        symbol=symbol,
                        direction=position['direction'],
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        quantity=position['quantity'],
                        pnl=pnl,
                        pnl_percent=pnl_percent,
                        holding_period=f"{holding_hours:.1f}h"
                    )
                    trades.append(trade)
                    
                    # Update capital
                    current_capital += pnl
                    position = None
            
            # Record equity curve
            equity_curve.append({
                'date': row.name.strftime("%Y-%m-%d %H:%M:%S"),
                'equity': current_capital,
                'drawdown': 0.0  # Will calculate later
            })
        
        # Calculate drawdown for equity curve
        if equity_curve:
            peak = equity_curve[0]['equity']
            for point in equity_curve:
                if point['equity'] > peak:
                    peak = point['equity']
                point['drawdown'] = ((peak - point['equity']) / peak) * 100
        
        return trades, equity_curve
    
    def _generate_signal(
        self,
        df: pd.DataFrame,
        index: int,
        strategy_type: str,
        strategy_params: Dict,
        state: Dict = None
    ) -> Optional[Dict]:
        """
        Generate trading signal based on strategy type
        
        Returns:
            Signal dictionary or None
        """
        if index < 50:  # Need enough data for indicators
            return None
        
        state = state if state is not None else {}
        row = df.iloc[index]
        prev_row = df.iloc[index - 1]
        
        if strategy_type == 'supertrend':
            return self._supertrend_signal(row, prev_row, strategy_params)
        elif strategy_type == 'ema_rsi':
            return self._ema_rsi_signal(row, prev_row, strategy_params)
        elif strategy_type == 'renko_macd':
            return self._renko_macd_signal(row, prev_row, strategy_params)
        elif strategy_type == 'orb':
            return self._orb_signal(df, index, strategy_params, state)
        elif strategy_type == 'ema_scalping':
            return self._ema_scalping_signal(row, prev_row, strategy_params)
        elif strategy_type == 'breakout':
            return self._breakout_signal(df, index, strategy_params, state)
        elif strategy_type == 'pattern':
            return self._pattern_signal(df, index, strategy_params)
        
        return None
    
    def _supertrend_signal(self, row, prev_row, params: Dict) -> Optional[Dict]:
        """Supertrend strategy signal"""
        # Buy signal: Price crosses above supertrend
        if prev_row['close'] < prev_row['supertrend'] and row['close'] > row['supertrend']:
            return {
                'action': 'BUY',
                'stop_loss': row['supertrend'],
                'target': row['close'] + (row['close'] - row['supertrend']) * 2
            }
        
        # Sell signal: Price crosses below supertrend
        if prev_row['close'] > prev_row['supertrend'] and row['close'] < row['supertrend']:
            return {
                'action': 'SELL',
                'stop_loss': row['supertrend'],
                'target': row['close'] - (row['supertrend'] - row['close']) * 2
            }
        
        return None
    
    def _ema_rsi_signal(self, row, prev_row, params: Dict) -> Optional[Dict]:
        """EMA + RSI strategy signal"""
        # Buy signal: EMA crossover + RSI confirmation
        if (prev_row['ema_9'] < prev_row['ema_21'] and 
            row['ema_9'] > row['ema_21'] and 
            row['rsi'] > 50):
            return {
                'action': 'BUY',
                'stop_loss': row['close'] * 0.98,  # 2% stop loss
                'target': row['close'] * 1.04  # 4% target
            }
        
        # Sell signal: EMA crossunder + RSI confirmation
        if (prev_row['ema_9'] > prev_row['ema_21'] and 
            row['ema_9'] < row['ema_21'] and 
            row['rsi'] < 50):
            return {
                'action': 'SELL',
                'stop_loss': row['close'] * 1.02,
                'target': row['close'] * 0.96
            }
        
        return None
    
    def _renko_macd_signal(self, row, prev_row, params: Dict) -> Optional[Dict]:
        """Renko + MACD strategy signal"""
        # Buy signal: MACD crossover
        if (prev_row['macd'] < prev_row['macd_signal'] and 
            row['macd'] > row['macd_signal'] and
            row['macd'] < 0):  # Buying from oversold
            return {
                'action': 'BUY',
                'stop_loss': row['close'] * 0.97,
                'target': row['close'] * 1.05
            }
        
        # Sell signal: MACD crossunder
        if (prev_row['macd'] > prev_row['macd_signal'] and 
            row['macd'] < row['macd_signal'] and
            row['macd'] > 0):  # Selling from overbought
            return {
                'action': 'SELL',
                'stop_loss': row['close'] * 1.03,
                'target': row['close'] * 0.95
            }
        
        return None

    def _orb_signal(self, df: pd.DataFrame, index: int, params: Dict, state: Dict) -> Optional[Dict]:
        """ORB Strategy Signal"""
        range_minutes = int(params.get('range_minutes', 15))
        sl_pct = float(params.get('sl_pct', 0.005))
        target_pct = float(params.get('target_pct', 0.01))
        
        row = df.iloc[index]
        current_time = row.name
        
        # Reset state on new day
        if 'current_date' not in state or state['current_date'] != current_time.date():
            state['current_date'] = current_time.date()
            state['range_set'] = False
            state['range_high'] = None
            state['range_low'] = None
            
            # Start time of the session (approx 9:15 for NSE)
            state['session_start'] = current_time.replace(hour=9, minute=15, second=0, microsecond=0)
            state['range_end'] = state['session_start'] + timedelta(minutes=range_minutes)
            
        # If range not set, check if we are past range end time
        if not state['range_set']:
            if current_time > state['range_end']:
                # Calculate range from today's data so far
                day_data = df[
                    (df.index >= pd.Timestamp(state['session_start'])) & 
                    (df.index < pd.Timestamp(state['range_end']))
                ]
                
                if not day_data.empty:
                    state['range_high'] = day_data['high'].max()
                    state['range_low'] = day_data['low'].min()
                    state['range_set'] = True
                    
        # Check for breakout if range is set
        if state['range_set']:
            # Signal logic
            if row['close'] > state['range_high']:
                # Buy
                return {
                    'action': 'BUY',
                    'stop_loss': state['range_low'],
                    'target': row['close'] * (1 + target_pct),
                    'reason': f"ORB Breakout High: {state['range_high']}"
                }
            elif row['close'] < state['range_low']:
                # Sell
                return {
                    'action': 'SELL',
                    'stop_loss': state['range_high'],
                    'target': row['close'] * (1 - target_pct),
                    'reason': f"ORB Breakout Low: {state['range_low']}"
                }
                
        return None

    def _ema_scalping_signal(self, row, prev_row, params: Dict) -> Optional[Dict]:
        """EMA Scalping Signal (9/21 EMA)"""
        # Params handled in _add_indicators
        sl_pct = float(params.get('sl_pct', 0.005))
        target_pct = float(params.get('target_pct', 0.01))
        
        # Check if custom EMA columns exist (added in _add_indicators)
        # If not, fallback to default ema_9 and ema_21
        ema_fast_col = 'ema_fast' if 'ema_fast' in row else 'ema_9'
        ema_slow_col = 'ema_slow' if 'ema_slow' in row else 'ema_21'
        
        # Buy Cross
        if (prev_row[ema_fast_col] <= prev_row[ema_slow_col] and 
            row[ema_fast_col] > row[ema_slow_col]):
            return {
                'action': 'BUY',
                'stop_loss': row['close'] * (1 - sl_pct),
                'target': row['close'] * (1 + target_pct),
                'reason': "EMA Cross Buy"
            }
            
        # Sell Cross
        if (prev_row[ema_fast_col] >= prev_row[ema_slow_col] and 
            row[ema_fast_col] < row[ema_slow_col]):
            return {
                'action': 'SELL',
                'stop_loss': row['close'] * (1 + sl_pct),
                'target': row['close'] * (1 - target_pct),
                'reason': "EMA Cross Sell"
            }
            
        return None
        
    def _breakout_signal(self, df: pd.DataFrame, index: int, params: Dict, state: Dict) -> Optional[Dict]:
        """Breakout Strategy Signal"""
        # Only update levels periodically to save time
        if index % 10 == 0 or 'support_levels' not in state:
             # Use a window of data to find levels
             lookback = int(params.get('lookback_period', 20))
             window_data = df.iloc[max(0, index-lookback-50):index] # Optimization: small window
             levels = price_action_service.find_support_resistance(window_data, window=lookback)
             state['support_levels'] = [l.level for l in levels if l.type == 'support']
             state['resistance_levels'] = [l.level for l in levels if l.type == 'resistance']
             
        row = df.iloc[index]
        prev_row = df.iloc[index-1]
        
        # Volume confirm
        volume_mult = float(params.get('volume_multiplier', 1.2))
        if row['volume'] <= row['volume_avg'] * volume_mult:
            return None
            
        # Breakout Buy
        for level in state['resistance_levels']:
            if prev_row['close'] <= level and row['close'] > level:
                 return {
                    'action': 'BUY',
                    'stop_loss': level * 0.995,
                    'target': row['close'] * 1.03, # Simplified target
                    'reason': f"Resistance breakout: {level}"
                }
                
        # Breakout Sell
        for level in state['support_levels']:
             if prev_row['close'] >= level and row['close'] < level:
                 return {
                    'action': 'SELL',
                    'stop_loss': level * 1.005,
                    'target': row['close'] * 0.97,
                    'reason': f"Support breakdown: {level}"
                }
                
        return None

    def _pattern_signal(self, df: pd.DataFrame, index: int, params: Dict) -> Optional[Dict]:
        """Candlestick Pattern Signal"""
        # Uses pattern scanner service
        # Scan just the recent window
        lookback = 5
        if index < lookback: return None
        
        # We need to simulate scanning on historical data. 
        # pattern_scanner.scan_latest extracts data from df.
        # We pass the slice ending at index.
        data_slice = df.iloc[:index+1]
        
        # This might be slow if called every candle. 
        # Optimization: Scan only if some pre-condition met? 
        # Or just rely on Python's speed.
        
        patterns = pattern_scanner.scan_latest(data_slice, "BACKTEST", lookback=lookback)
        
        min_confidence = float(params.get('min_confidence', 0.8))
        
        for p in patterns:
            if p.confidence >= min_confidence:
                if p.direction == 'bullish':
                    return {
                        'action': 'BUY',
                        'stop_loss': df.iloc[index]['low'] * 0.995,
                        'target': df.iloc[index]['close'] * 1.02,
                        'reason': f"{p.pattern} Pattern"
                    }
                elif p.direction == 'bearish':
                    return {
                        'action': 'SELL',
                        'stop_loss': df.iloc[index]['high'] * 1.005,
                        'target': df.iloc[index]['close'] * 0.98,
                        'reason': f"{p.pattern} Pattern"
                    }
                    
        return None
    
    def _calculate_metrics(
        self,
        trades: List[BacktestTrade],
        equity_curve: List[Dict],
        initial_capital: float,
        total_days: int
    ) -> BacktestMetrics:
        """Calculate comprehensive performance metrics"""
        
        if not trades:
            return BacktestMetrics(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0.0, loss_rate=0.0,
                total_pnl=0.0, total_pnl_percent=0.0,
                gross_profit=0.0, gross_loss=0.0, profit_factor=0.0,
                avg_win=0.0, avg_loss=0.0,
                largest_win=0.0, largest_loss=0.0,
                avg_holding_period="0h",
                max_drawdown=0.0, max_drawdown_percent=0.0,
                sharpe_ratio=0.0, expectancy=0.0,
                consecutive_wins=0, consecutive_losses=0,
                avg_trades_per_day=0.0
            )
        
        # Basic counts
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        
        # Win/Loss rates
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        loss_rate = (losing_trades / total_trades * 100) if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(t.pnl for t in trades)
        total_pnl_percent = (total_pnl / initial_capital) * 100
        
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Trade statistics
        winning_pnls = [t.pnl for t in trades if t.pnl > 0]
        losing_pnls = [t.pnl for t in trades if t.pnl < 0]
        
        avg_win = np.mean(winning_pnls) if winning_pnls else 0
        avg_loss = np.mean(losing_pnls) if losing_pnls else 0
        largest_win = max(winning_pnls) if winning_pnls else 0
        largest_loss = min(losing_pnls) if losing_pnls else 0
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) + (loss_rate/100 * avg_loss)
        
        # Drawdown
        max_drawdown = 0.0
        max_drawdown_percent = 0.0
        if equity_curve:
            max_drawdown_percent = max(point['drawdown'] for point in equity_curve)
            peak = max(point['equity'] for point in equity_curve)
            trough = min(point['equity'] for point in equity_curve)
            max_drawdown = peak - trough
        
        # Sharpe Ratio (simplified - using daily returns)
        returns = [trades[i].pnl_percent - trades[i-1].pnl_percent 
                   for i in range(1, len(trades))]
        if returns:
            sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        current_streak = 0
        current_type = None
        
        for trade in trades:
            if trade.pnl > 0:
                if current_type == 'win':
                    current_streak += 1
                else:
                    current_streak = 1
                    current_type = 'win'
                consecutive_wins = max(consecutive_wins, current_streak)
            else:
                if current_type == 'loss':
                    current_streak += 1
                else:
                    current_streak = 1
                    current_type = 'loss'
                consecutive_losses = max(consecutive_losses, current_streak)
        
        # Average trades per day
        avg_trades_per_day = total_trades / total_days if total_days > 0 else 0
        
        # Average holding period
        avg_holding_period = "0h"
        if trades:
            # Extract hours from holding period strings
            total_hours = sum(float(t.holding_period.replace('h', '')) for t in trades)
            avg_hours = total_hours / len(trades)
            avg_holding_period = f"{avg_hours:.1f}h"
        
        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            loss_rate=round(loss_rate, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_percent=round(total_pnl_percent, 2),
            gross_profit=round(gross_profit, 2),
            gross_loss=round(gross_loss, 2),
            profit_factor=round(profit_factor, 2),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            avg_holding_period=avg_holding_period,
            max_drawdown=round(max_drawdown, 2),
            max_drawdown_percent=round(max_drawdown_percent, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            expectancy=round(expectancy, 2),
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            avg_trades_per_day=round(avg_trades_per_day, 2)
        )
    
    def get_result(self, backtest_id: str) -> Optional[BacktestResult]:
        """Get backtest result by ID"""
        return self.backtest_results.get(backtest_id)
    
    def get_all_results(self) -> List[BacktestResult]:
        """Get all backtest results"""
        return list(self.backtest_results.values())


# Global singleton
backtesting_service = BacktestingService()
