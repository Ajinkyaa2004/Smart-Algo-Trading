"""
Trading Bot Controller
Orchestrates all components for automated trading
"""
from typing import Dict, List, Optional, Callable
from datetime import datetime, time as datetime_time
import threading
import time
from enum import Enum

from app.services.kite_auth import kite_auth_service
from app.services.market_hours import market_hours
from app.services.tick_processor import tick_processor
from app.services.order_service import order_service
from app.services.market_data import market_data_service
from app.services.paper_trading import paper_engine, PAPER_TRADING_MODE
from app.strategies.supertrend_strategy import SupertrendStrategy, SupertrendStrategyConfig
from app.strategies.ema_rsi_strategy import EMA_RSI_Strategy, StrategyConfig
from app.strategies.renko_macd_strategy import RenkoMACDStrategy, RenkoMACDStrategyConfig
from app.strategies.breakout_strategy import BreakoutStrategy
from app.strategies.pattern_strategy import PatternConfirmationStrategy
from app.config import DEFAULT_STRATEGY


class BotStatus(Enum):
    """Trading bot status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class TradingBot:
    """
    Main Trading Bot Controller
    
    Manages:
    - Strategy lifecycle
    - Market hours monitoring
    - Tick data processing
    - Signal generation
    - Order execution
    - Position management
    - Auto square-off
    """
    
    def __init__(self):
        self.status = BotStatus.STOPPED
        self.strategies: Dict[str, any] = {}
        self.active_positions: Dict[str, any] = {}
        
        # Settings
        self.auto_square_off_time = datetime_time(15, 15)  # 3:15 PM
        self.check_interval = 60  # Check every 60 seconds
        
        # Statistics
        self.trades_today = 0
        self.pnl_today = 0.0
        self.signals_generated = 0
        self.orders_placed = 0
        
        # Threading
        self.bot_thread = None
        self.stop_flag = threading.Event()
        self.lock = threading.Lock()
        
        # Callbacks
        self.on_signal_callbacks: List[Callable] = []
        self.on_order_callbacks: List[Callable] = []
        self.on_status_change_callbacks: List[Callable] = []
    
    # ==================== BOT CONTROL ====================
    
    def start(
        self,
        symbols: List[str],
        strategy_type: str = DEFAULT_STRATEGY,
        capital_per_symbol: float = 3000.0,
        enable_tick_storage: bool = False,
        **strategy_params
    ) -> Dict:
        """
        Start the trading bot
        
        Args:
            symbols: List of symbols to trade
            strategy_type: Strategy to use (supertrend, ema_rsi, renko_macd)
            capital_per_symbol: Capital allocation per symbol
            enable_tick_storage: Store ticks in database
            **strategy_params: Additional strategy parameters
            
        Returns:
            Status dictionary
        """
        if self.status == BotStatus.RUNNING:
            return {"success": False, "message": "Bot already running"}
        
        # Check authentication
        if not kite_auth_service.is_authenticated():
            return {"success": False, "message": "Not authenticated. Please login first."}
        
        print("=" * 60)
        print("STARTING TRADING BOT")
        print("=" * 60)
        
        # CRITICAL: Display trading mode
        if PAPER_TRADING_MODE:
            print("🛡️  MODE: PAPER TRADING (Simulated)")
            print("✓ No real orders will be placed")
            print("✓ Safe for zero-balance accounts")
            print("✓ All trades are simulated")
        else:
            print("⚠️  MODE: LIVE TRADING (REAL MONEY!)")
            print("⚠️  REAL ORDERS WILL BE PLACED ON ZERODHA!")
            print("⚠️  YOU ARE TRADING WITH REAL CAPITAL!")
        
        print("=" * 60)
        
        self._update_status(BotStatus.STARTING)
        
        try:
            # Initialize strategies for each symbol
            total_allocated_capital = 0.0
            
            for symbol in symbols:
                strategy = self._create_strategy(
                    symbol=symbol,
                    strategy_type=strategy_type,
                    capital=capital_per_symbol,
                    **strategy_params
                )
                self.strategies[symbol] = strategy
                total_allocated_capital += capital_per_symbol
                print(f"✓ Strategy initialized for {symbol}")
            
            # ALLOCATE FUNDS in Paper Trading Engine
            if PAPER_TRADING_MODE:
                print(f"💰 Allocating ₹{total_allocated_capital:,.2f} to Bot Strategies...")
                success = paper_engine.allocate_funds(total_allocated_capital)
                if not success:
                    raise Exception(f"Insufficient paper funds. Available: ₹{paper_engine.available_funds:,.2f}")
            
            # Start tick processor
            tick_processor.start(
                symbols=symbols,
                mode="full",
                enable_storage=enable_tick_storage
            )
            
            # Register tick callback
            for symbol in symbols:
                tick_processor.strategy_callbacks[symbol] = [
                    lambda tick, s=symbol: self._on_tick_received(s, tick)
                ]
            
            # Start monitoring thread
            self.stop_flag.clear()
            self.bot_thread = threading.Thread(target=self._bot_loop, daemon=True)
            self.bot_thread.start()
            
            self._update_status(BotStatus.RUNNING)
            
            print("=" * 60)
            print(f"✓ TRADING BOT STARTED")
            print(f"  Symbols: {', '.join(symbols)}")
            print(f"  Strategy: {strategy_type}")
            print(f"  Capital per symbol: ₹{capital_per_symbol}")
            print(f"  Total Allocated: ₹{total_allocated_capital}")
            print("=" * 60)
            
            return {
                "success": True,
                "message": "Trading bot started successfully",
                "symbols": symbols,
                "strategy": strategy_type
            }
            
        except Exception as e:
            self._update_status(BotStatus.ERROR)
            print(f"✗ ERROR starting bot: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Failed to start bot: {str(e)}"
            }
    
    def stop(self, square_off_positions: bool = True) -> Dict:
        """
        Stop the trading bot
        
        Args:
            square_off_positions: Whether to close all positions
            
        Returns:
            Status dictionary
        """
        if self.status == BotStatus.STOPPED:
            return {"success": False, "message": "Bot not running"}
        
        print("=" * 60)
        print("STOPPING TRADING BOT")
        print("=" * 60)
        
        self._update_status(BotStatus.STOPPING)
        
        try:
            # Stop monitoring thread
            self.stop_flag.set()
            if self.bot_thread:
                self.bot_thread.join(timeout=5)
            
            # Stop tick processor
            tick_processor.stop()
            
            # Square off positions if requested
            square_off_result = None
            if square_off_positions:
                square_off_result = order_service.auto_square_off()
            
            # RECLAIM FUNDS in Paper Trading Engine
            if PAPER_TRADING_MODE:
                print("💰 Reclaiming reserved bot funds...")
                paper_engine.reclaim_reserved_funds()
            
            # Clear strategies
            self.strategies.clear()
            self.active_positions.clear()
            
            self._update_status(BotStatus.STOPPED)
            
            print("=" * 60)
            print("✓ TRADING BOT STOPPED")
            print("=" * 60)
            
            return {
                "success": True,
                "message": "Trading bot stopped successfully",
                "square_off": square_off_result
            }
            
        except Exception as e:
            self._update_status(BotStatus.ERROR)
            return {
                "success": False,
                "message": f"Error stopping bot: {str(e)}"
            }
    
    def pause(self) -> Dict:
        """Pause trading (stop generating new signals)"""
        if self.status != BotStatus.RUNNING:
            return {"success": False, "message": "Bot not running"}
        
        self._update_status(BotStatus.PAUSED)
        print("⏸ Trading bot paused")
        
        return {"success": True, "message": "Bot paused"}
    
    def resume(self) -> Dict:
        """Resume trading"""
        if self.status != BotStatus.PAUSED:
            return {"success": False, "message": "Bot not paused"}
        
        self._update_status(BotStatus.RUNNING)
        print("▶ Trading bot resumed")
        
        return {"success": True, "message": "Bot resumed"}
    
    def reset_state(self):
        """
        Reset bot state
        Clears active positions and resets strategy states.
        Called when Paper Portfolio is reset.
        """
        try:
            print("🔄 Resetting Bot Internal State...")
            
            # Clear bot positions
            self.active_positions.clear()
            self.trades_today = 0
            self.pnl_today = 0.0
            self.signals_generated = 0
            self.orders_placed = 0
            
            # Reset each strategy
            for symbol, strategy in self.strategies.items():
                if hasattr(strategy, 'position'):
                    strategy.position = None
                if hasattr(strategy, 'trades_today'):
                    strategy.trades_today = 0
                if hasattr(strategy, 'pnl_today'):
                    strategy.pnl_today = 0.0
                if hasattr(strategy, 'st_directions'):
                    # specific to Supertrend, but good to reset if possible
                    # We can't easily access specific implementation details of every strategy here
                    # unless we define a common reset() in BaseStrategy.
                    # For now, clearing position is the most critical part.
                    pass
            
            print("✓ Bot state reset successfully")
            return {"success": True, "message": "Bot state reset"}
            
        except Exception as e:
            print(f"✗ Error resetting bot state: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    # ==================== STRATEGY CREATION ====================
    
    def _create_strategy(
        self,
        symbol: str,
        strategy_type: str,
        capital: float,
        **params
    ):
        """Create strategy instance based on type"""
        
        if strategy_type == "supertrend":
            config = SupertrendStrategyConfig(
                symbol=symbol,
                capital=capital,
                **params
            )
            return SupertrendStrategy(config)
        
        elif strategy_type == "scalping":
            from app.strategies.scal_strategy import ScalpingStrategy
            config = StrategyConfig(
                name=f"Scalping_{symbol}",
                symbol=symbol,
                capital=capital,
                params=params
            )
            return ScalpingStrategy(config)
            
        elif strategy_type == "ema_scalping":
            from app.strategies.ema_scalping_strategy import EMAScalpingStrategy
            config = StrategyConfig(
                name=f"EMA_Scalping_{symbol}",
                symbol=symbol,
                capital=capital,
                params=params
            )
            return EMAScalpingStrategy(config)
            
        elif strategy_type == "orb":
            from app.strategies.orb_strategy import ORBStrategy
            config = StrategyConfig(
                name=f"ORB_{symbol}",
                symbol=symbol,
                capital=capital,
                params=params
            )
            return ORBStrategy(config)

        elif strategy_type == "ema_rsi":
            config = StrategyConfig(
                name=f"EMA_RSI_{symbol}",
                symbol=symbol,
                capital=capital,
                params=params
            )
            return EMA_RSI_Strategy(config)
        
        elif strategy_type == "renko_macd":
            config = RenkoMACDStrategyConfig(
                symbol=symbol,
                capital=capital,
                **params
            )
            return RenkoMACDStrategy(config)
        
        elif strategy_type == "breakout":
            config = StrategyConfig(
                name=f"Breakout_{symbol}",
                symbol=symbol,
                capital=capital,
                params=params
            )
            return BreakoutStrategy(config)
        
        elif strategy_type == "pattern":
            config = StrategyConfig(
                name=f"Pattern_{symbol}",
                symbol=symbol,
                capital=capital,
                params=params
            )
            return PatternConfirmationStrategy(config)
        
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    # ==================== BOT LOOP ====================
    
    def _bot_loop(self):
        """Main bot monitoring loop"""
        print("Bot monitoring loop started")
        
        while not self.stop_flag.is_set():
            try:
                # 1. Update Paper Trading P&L (Always run this so dashboard stays alive)
                if PAPER_TRADING_MODE:
                    self._update_paper_trading_ltps()

                # 2. Check if market is open
                if not market_hours.is_market_open():
                    # Check if we should override for testing
                    # For now just log and wait
                    if self.signals_generated == 0 and self.trades_today == 0:
                         print(f"⏳ Market closed ({datetime.now().strftime('%H:%M')}). Bot waiting for market open...")
                    time.sleep(60)
                    continue
                
                # 3. Check for auto square-off time
                now = datetime.now().time()
                if now >= self.auto_square_off_time:
                    print("🕒 Auto square-off time reached")
                    self._auto_square_off()
                    break
                
                # 4. Process strategies (if not paused)
                if self.status == BotStatus.RUNNING:
                    self._process_strategies()
                
                # 5. Update statistics
                self._update_statistics()
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"✗ Error in bot loop: {str(e)}")
                time.sleep(10)  # Wait before retry
        
        print("Bot monitoring loop stopped")

    def _update_paper_trading_ltps(self):
        """
        Update LTP for all active symbols in Paper Trading Engine.
        This ensures P&L is visible even if market is closed or strategies aren't processing.
        """
        try:
            # Get all symbols from active strategies + working positions
            symbols = set(self.strategies.keys())
            
            # Add symbols from active positions
            positions = order_service.get_positions()
            if 'net' in positions:
                for pos in positions['net']:
                    symbols.add(pos['tradingsymbol'])
            
            if not symbols:
                return

            # Fetch LTPs in batch
            ltp_map = market_data_service.get_ltp([f"NSE:{s}" for s in symbols])
            
            # Update Paper Engine
            count = 0
            for full_symbol, data in ltp_map.items():
                if 'last_price' in data:
                    symbol = full_symbol.split(':')[1]
                    paper_engine.update_ltp(symbol, "NSE", data['last_price'])
                    count += 1
            
            # print(f"✓ Updated P&L for {count} symbols")
            
        except Exception as e:
            # Fail silently to avoid spamming logs
            pass
    
    def _process_strategies(self):
        """Process all active strategies"""
        for symbol, strategy in self.strategies.items():
            try:
                # Fetch latest OHLC data
                df = market_data_service.get_historical_data_by_symbol(
                    symbol=symbol,
                    exchange="NSE",
                    interval="5minute",
                    days_back=5
                )
                
                if df.empty:
                    continue
                
                # Get current price
                ltp = market_data_service.get_ltp(symbol, "NSE")
                if not ltp:
                    continue
                
                current_price = ltp.get('last_price', 0)
                
                # Update paper trading engine with LTP
                if PAPER_TRADING_MODE:
                    paper_engine.update_ltp(symbol, "NSE", current_price)
                
                # Generate signal
                signal = strategy.generate_signal(df, current_price)
                
                if signal:
                    self.signals_generated += 1
                    self._execute_signal(signal)
                
            except Exception as e:
                print(f"✗ Error processing strategy for {symbol}: {str(e)}")
    
    def _on_tick_received(self, symbol: str, tick: Dict):
        """Handle tick data for real-time strategies (e.g., Renko+MACD)"""
        if symbol not in self.strategies:
            return
        
        strategy = self.strategies[symbol]
        
        # Update paper trading engine with latest price for live P&L calculation
        if PAPER_TRADING_MODE and 'last_price' in tick:
            exchange = tick.get('exchange', 'NSE')
            paper_engine.update_ltp(symbol, exchange, tick['last_price'])
        
        # Process tick in strategy (e.g., update Renko bricks)
        if hasattr(strategy, 'process_tick'):
            try:
                strategy.process_tick(tick)
            except Exception as e:
                print(f"✗ Error processing tick for {symbol}: {str(e)}")
    
    # ==================== SIGNAL EXECUTION ====================
    
    def _execute_signal(self, signal):
        """Execute trading signal"""
        try:
            print(f"\n📊 SIGNAL GENERATED: {signal.signal_type.value} {signal.symbol}")
            print(f"   Price: ₹{signal.price:.2f}")
            print(f"   Quantity: {signal.quantity}")
            print(f"   Reason: {signal.reason}")
            
            # Notify callbacks
            for callback in self.on_signal_callbacks:
                callback(signal)
            
            # Execute based on signal type
            if signal.signal_type.value == "BUY":
                result = order_service.place_market_order_with_sl(
                    tradingsymbol=signal.symbol,
                    exchange="NSE",
                    transaction_type="BUY",
                    quantity=signal.quantity,
                    sl_price=signal.stop_loss,
                    tag=f"BOT_{signal.symbol}"
                )
                
                if result['success']:
                    self.orders_placed += 1
                    self.active_positions[signal.symbol] = {
                        'entry_price': signal.price,
                        'quantity': signal.quantity,
                        'stop_loss': signal.stop_loss,
                        'order_ids': result
                    }
                    print(f"✓ BUY order executed for {signal.symbol}")
                
            elif signal.signal_type.value == "SELL":
                result = order_service.place_market_order_with_sl(
                    tradingsymbol=signal.symbol,
                    exchange="NSE",
                    transaction_type="SELL",
                    quantity=signal.quantity,
                    sl_price=signal.stop_loss,
                    tag=f"BOT_{signal.symbol}"
                )
                
                if result['success']:
                    self.orders_placed += 1
                    self.active_positions[signal.symbol] = {
                        'entry_price': signal.price,
                        'quantity': -signal.quantity,
                        'stop_loss': signal.stop_loss,
                        'order_ids': result
                    }
                    print(f"✓ SELL order executed for {signal.symbol}")
            
            elif signal.signal_type.value == "HOLD":
                # Update stop-loss if needed
                if signal.metadata and signal.metadata.get('action') == 'update_sl':
                    self._update_stop_loss(signal)
            
            # Notify callbacks
            for callback in self.on_order_callbacks:
                callback(signal)
            
        except Exception as e:
            print(f"✗ Error executing signal: {str(e)}")
    
    def _update_stop_loss(self, signal):
        """Update stop-loss for active position"""
        try:
            position = self.active_positions.get(signal.symbol)
            if not position:
                return
            
            # Get pending SL order
            orders = order_service.get_orders()
            for order in orders:
                if (order['tradingsymbol'] == signal.symbol and 
                    order['status'] in ['TRIGGER PENDING', 'OPEN'] and
                    order['order_type'] in ['SL', 'SL-M']):
                    
                    # Modify SL order
                    order_service.modify_order(
                        order_id=order['order_id'],
                        price=signal.stop_loss,
                        trigger_price=signal.stop_loss
                    )
                    
                    position['stop_loss'] = signal.stop_loss
                    print(f"✓ Stop-loss updated for {signal.symbol}: ₹{signal.stop_loss:.2f}")
                    break
        
        except Exception as e:
            print(f"✗ Error updating stop-loss: {str(e)}")
    
    # ==================== AUTO SQUARE-OFF ====================
    
    def _auto_square_off(self):
        """Auto square-off all positions at end of day"""
        print("\n🔔 Executing auto square-off...")
        
        try:
            result = order_service.auto_square_off(
                close_positions=True,
                cancel_orders=True
            )
            
            print("✓ Auto square-off completed")
            
            # Stop the bot
            self.stop(square_off_positions=False)
            
        except Exception as e:
            print(f"✗ Error in auto square-off: {str(e)}")
    
    # ==================== STATISTICS ====================
    
    def _update_statistics(self):
        """Update bot statistics"""
        try:
            # Fetch positions
            positions = order_service.get_positions()
            day_positions = positions.get('day', [])
            
            # Calculate P&L
            total_pnl = sum(pos.get('pnl', 0) for pos in day_positions)
            self.pnl_today = total_pnl
            
            # Count trades
            trades = order_service.get_trades()
            self.trades_today = len(trades)
            
        except Exception as e:
            print(f"✗ Error updating statistics: {str(e)}")
    
    # ==================== STATUS & INFO ====================
    
    def _update_status(self, new_status: BotStatus):
        """Update bot status and notify callbacks"""
        self.status = new_status
        
        for callback in self.on_status_change_callbacks:
            try:
                callback(new_status)
            except Exception as e:
                print(f"✗ Error in status callback: {str(e)}")
    
    def get_status(self) -> Dict:
        """Get current bot status"""
        return {
            "status": self.status.value,
            "active_strategies": len(self.strategies),
            "active_positions": len(self.active_positions),
            "signals_generated": self.signals_generated,
            "orders_placed": self.orders_placed,
            "trades_today": self.trades_today,
            "pnl_today": self.pnl_today,
            "strategies": {
                symbol: strategy.get_status()
                for symbol, strategy in self.strategies.items()
            }
        }
    
    def get_positions(self) -> Dict:
        """Get active positions"""
        return self.active_positions.copy()
    
    # ==================== CALLBACKS ====================
    
    def on_signal(self, callback: Callable):
        """Register signal callback"""
        self.on_signal_callbacks.append(callback)
    
    def on_order(self, callback: Callable):
        """Register order callback"""
        self.on_order_callbacks.append(callback)
    
    def on_status_change(self, callback: Callable):
        """Register status change callback"""
        self.on_status_change_callbacks.append(callback)


# Global singleton instance
trading_bot = TradingBot()
