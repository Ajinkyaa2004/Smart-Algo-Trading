"""
Tick Processor
Integrates WebSocket handler, candle builder, and tick storage for complete tick processing
"""
from typing import List, Dict, Callable, Optional
from datetime import datetime
import pandas as pd
from app.services.websocket_handler import websocket_handler
from app.services.candle_builder import candle_builder
from app.services.market_data import market_data_service
from app.services.paper_trading import paper_engine


class TickProcessor:
    """
    Main tick processing service
    Manages WebSocket connection, tick streaming, candle formation, and storage
    """
    
    def __init__(self):
        self.ws_handler = websocket_handler
        self.candle_builder = candle_builder
        self.is_running = False
        
        # Tick storage (lazy import to avoid circular dependency)
        self._tick_storage = None
        
        # Instrument mapping: {symbol: token}
        self.instrument_map: Dict[str, int] = {}
        
        # Strategy callbacks: {symbol: [callbacks]}
        self.strategy_callbacks: Dict[str, List[Callable]] = {}
        
        # Token metadata for quick lookup: {token: {'symbol': str, 'exchange': str}}
        self.token_meta: Dict[int, Dict] = {}
        
        # Storage enabled flag
        self.storage_enabled = False
    
    @property
    def tick_storage(self):
        """Lazy load tick storage service"""
        if self._tick_storage is None:
            from app.services.tick_storage import tick_storage_service
            self._tick_storage = tick_storage_service
        return self._tick_storage
    
    def start(self, symbols: List[str], exchange: str = "NSE", mode: str = "full", enable_storage: bool = False):
        """
        Start tick processing for given symbols
        
        Args:
            symbols: List of trading symbols
            exchange: Exchange name (can be overridden per symbol)
            mode: Tick mode ('ltp', 'quote', 'full')
            enable_storage: Enable SQLite storage of ticks
        """
        if self.is_running:
            print("⚠ Tick processor already running")
            return
        
        print(f"Starting tick processor for {len(symbols)} symbols...")
        
        self.storage_enabled = enable_storage
        
        # Get instrument tokens
        tokens = []
        for symbol in symbols:
            # Determine the exchange for this symbol (default to NSE)
            symbol_exchange = exchange
            
            # Try to get token
            token = market_data_service.get_instrument_token(symbol, symbol_exchange)
            
            if token:
                self.instrument_map[symbol] = token
                self.token_meta[token] = {'symbol': symbol, 'exchange': symbol_exchange}
                tokens.append(token)
                print(f"  ✓ {symbol} ({symbol_exchange}): {token}")
            else:
                print(f"  ✗ {symbol} ({symbol_exchange}): Token not found")
                # Provide helpful alternatives
                print(f"    Try checking if the symbol exists in the exchange")
        
        if not tokens:
            print("✗ No valid tokens found")
            print("  Make sure:")
            print("  1. Symbols are spelled correctly (e.g., 'NIFTY 50', 'NIFTY BANK')")
            print("  2. Exchange is correct (NSE, BSE, NFO, etc.)")
            print("  3. instruments.csv is up to date")
            return
        
        # Create database tables if storage is enabled
        if self.storage_enabled:
            print("Initializing tick storage...")
            self.tick_storage.create_tables(tokens)
        
        # Register tick callback
        self.ws_handler.on_tick(self._process_ticks)
        
        # Connect WebSocket
        self.ws_handler.connect()
        
        # Wait for connection (give it a moment)
        import time
        time.sleep(2)
        
        # Subscribe to tokens
        self.ws_handler.subscribe(tokens, mode=mode)
        
        self.is_running = True
        storage_status = "with storage" if self.storage_enabled else "without storage"
        print(f"✓ Tick processor started for {len(tokens)} instruments {storage_status}")
    
    def stop(self):
        """Stop tick processing"""
        if not self.is_running:
            print("⚠ Tick processor not running")
            return
        
        print("Stopping tick processor...")
        
        # Disconnect WebSocket
        self.ws_handler.disconnect()
        
        self.is_running = False
        # Store ticks in database if enabled
        if self.storage_enabled:
            try:
                self.tick_storage.insert_ticks(ticks)
            except Exception as e:
                print(f"✗ Error storing ticks: {str(e)}")
        
        print("✓ Tick processor stopped")
    
    def _process_ticks(self, ticks: List[Dict]):
        """
        Process incoming ticks
        
        Args:
            ticks: List of tick data
        """
        for tick in ticks:
            # Update candle builder
            self.candle_builder.process_tick(tick)
            
            # Trigger strategy callbacks
            instrument_token = tick.get('instrument_token')
            if instrument_token:
                # Find symbol for this token
                symbol = self._get_symbol_by_token(instrument_token)
                if symbol and symbol in self.strategy_callbacks:
                    for callback in self.strategy_callbacks[symbol]:
                        try:
                            callback(tick)
                        except Exception as e:
                            print(f"✗ Error in strategy callback: {str(e)}")

            # Update paper trading LTP
            if instrument_token and instrument_token in self.token_meta:
                meta = self.token_meta[instrument_token]
                if 'last_price' in tick:
                    try:
                        paper_engine.update_ltp(
                            meta['symbol'],
                            meta['exchange'],
                            tick['last_price']
                        )
                    except Exception as e:
                        # Fail silently? Or log?
                        pass
    
    def _get_symbol_by_token(self, token: int) -> Optional[str]:
        """Get symbol for instrument token"""
        for symbol, t in self.instrument_map.items():
            if t == token:
                return symbol
        return None
    
    def subscribe_symbol(self, symbol: str, exchange: str = "NSE", mode: str = "full"):
        """
        Subscribe to additional symbol
        
        Args:
            symbol: Trading symbol
            exchange: Exchange
            mode: Tick mode
        """
        # Ensure we are running
        if not self.is_running:
            self.start([], exchange, mode)

        token = market_data_service.get_instrument_token(symbol, exchange)
        if not token:
            print(f"✗ Token not found for {symbol}")
            return
        
        self.instrument_map[symbol] = token
        self.token_meta[token] = {'symbol': symbol, 'exchange': exchange}
        self.ws_handler.subscribe([token], mode=mode)
        print(f"✓ Subscribed to {symbol}")
    
    def unsubscribe_symbol(self, symbol: str):
        """
        Unsubscribe from symbol
        
        Args:
            symbol: Trading symbol
        """
        if symbol not in self.instrument_map:
            print(f"⚠ {symbol} not subscribed")
            return
        
        token = self.instrument_map[symbol]
        self.ws_handler.unsubscribe([token])
        del self.instrument_map[symbol]
        if token in self.token_meta:
            del self.token_meta[token]
        print(f"✓ Unsubscribed from {symbol}")
    
    def get_current_candle(
        self,
        symbol: str,
        interval: str = '1min'
    ) -> Optional[Dict]:
        """
        Get current candle for symbol
        
        Args:
            symbol: Trading symbol
            interval: Candle interval
            
        Returns:
            Candle data or None
        """
        if symbol not in self.instrument_map:
            return None
        
        token = self.instrument_map[symbol]
        candle = self.candle_builder.get_current_candle(token, interval)
        
        return candle.to_dict() if candle else None
    
    def get_candles(
        self,
        symbol: str,
        interval: str = '1min',
        count: int = 100,
        include_current: bool = False
    ) -> pd.DataFrame:
        """
        Get historical candles as DataFrame
        
        Args:
            symbol: Trading symbol
            interval: Candle interval
            count: Number of candles
            include_current: Include current incomplete candle
            
        Returns:
            DataFrame with OHLCV data
        """
        if symbol not in self.instrument_map:
            return pd.DataFrame()
        
        token = self.instrument_map[symbol]
        return self.candle_builder.get_candles_as_dataframe(
            token, interval, count, include_current
        )
    
    def on_candle_close(self, interval: str, callback: Callable):
        """
        Register callback for candle close events
        
        Args:
            interval: Candle interval
            callback: Function(instrument_token, candle)
        """
        self.candle_builder.on_candle_close(interval, callback)
    
    def on_tick(self, symbol: str, callback: Callable):
        """
        Register callback for tick events for specific symbol
        
        Args:
            symbol: Trading symbol
            callback: Function(tick)
        """
        if symbol not in self.strategy_callbacks:
            self.strategy_callbacks[symbol] = []
        
        self.strategy_callbacks[symbol].append(callback)
    
    def get_latest_tick(self, symbol: str) -> Optional[Dict]:
        """
        Get latest tick for symbol (from current candle)
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Latest tick data or None
        """
        candle = self.get_current_candle(symbol)
        if not candle:
            return None
        
        return {
            'symbol': symbol,
            'last_price': candle['close'],
            'timestamp': candle['timestamp'],
            'volume': candle['volume']
        }
    
    def get_status(self) -> Dict:
        """Get tick processor status"""
        return {
            "running": self.is_running,
            "websocket": self.ws_handler.get_status(),
            "candle_builder": self.candle_builder.get_status(),
            "subscribed_symbols": list(self.instrument_map.keys()),
            "symbol_count": len(self.instrument_map)
        }


# Global singleton instance
tick_processor = TickProcessor()
