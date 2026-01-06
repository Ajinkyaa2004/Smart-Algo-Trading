"""
WebSocket Handler for KiteTicker
Manages real-time tick data streaming from Zerodha Kite Connect
"""
from kiteconnect import KiteTicker
from typing import Dict, List, Callable, Optional
from datetime import datetime
import threading
import time
from app.services.kite_auth import kite_auth_service




class WebSocketHandler:
    """
    WebSocket handler for KiteTicker
    Manages connections, subscriptions, and tick data streaming
    """
    
    def __init__(self):
        self.ticker: Optional[KiteTicker] = None
        self.is_connected = False
        self.subscribed_tokens = set()
        
        # Callbacks
        self.tick_callbacks: List[Callable] = []
        self.connect_callbacks: List[Callable] = []
        self.disconnect_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # Reconnection settings
        self.auto_reconnect = True
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        
        # Thread safety
        self.lock = threading.Lock()
    
    def initialize(self):
        """Initialize KiteTicker with authentication"""
        if not kite_auth_service.is_authenticated():
            raise Exception("Not authenticated. Please login first.")
        
        api_key = kite_auth_service.api_key
        access_token = kite_auth_service.access_token
        
        if not api_key or not access_token:
            raise Exception("API key or access token not available")
        
        self.ticker = KiteTicker(api_key, access_token)
        
        # Assign callbacks
        self.ticker.on_ticks = self._on_ticks
        self.ticker.on_connect = self._on_connect
        self.ticker.on_close = self._on_close
        self.ticker.on_error = self._on_error
        self.ticker.on_reconnect = self._on_reconnect
        self.ticker.on_noreconnect = self._on_noreconnect
        
        print("✓ WebSocket initialized")
    
    def connect(self):
        """Start WebSocket connection"""
        if not self.ticker:
            self.initialize()
        
        if self.is_connected:
            print("⚠ Already connected")
            return
        
        print("Connecting to WebSocket...")
        
        # Start in a separate thread
        thread = threading.Thread(target=self.ticker.connect, daemon=True)
        thread.start()
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.ticker and self.is_connected:
            print("Disconnecting WebSocket...")
            self.ticker.close()
            self.is_connected = False
    
    def subscribe(self, tokens: List[int], mode: str = "full"):
        """
        Subscribe to instrument tokens
        
        Args:
            tokens: List of instrument tokens
            mode: 'ltp', 'quote', or 'full'
        """
        if not self.ticker or not self.is_connected:
            print("⚠ Not connected. Storing tokens for later subscription.")
            self.subscribed_tokens.update(tokens)
            return
        
        with self.lock:
            # Set mode
            if mode == "ltp":
                self.ticker.subscribe(tokens)
                self.ticker.set_mode(self.ticker.MODE_LTP, tokens)
            elif mode == "quote":
                self.ticker.subscribe(tokens)
                self.ticker.set_mode(self.ticker.MODE_QUOTE, tokens)
            else:  # full
                self.ticker.subscribe(tokens)
                self.ticker.set_mode(self.ticker.MODE_FULL, tokens)
            
            self.subscribed_tokens.update(tokens)
            print(f"✓ Subscribed to {len(tokens)} instruments in {mode} mode")
    
    def unsubscribe(self, tokens: List[int]):
        """
        Unsubscribe from instrument tokens
        
        Args:
            tokens: List of instrument tokens
        """
        if not self.ticker or not self.is_connected:
            print("⚠ Not connected")
            return
        
        with self.lock:
            self.ticker.unsubscribe(tokens)
            self.subscribed_tokens.difference_update(tokens)
            print(f"✓ Unsubscribed from {len(tokens)} instruments")
    
    def resubscribe(self):
        """Resubscribe to all previously subscribed tokens"""
        if self.subscribed_tokens:
            tokens = list(self.subscribed_tokens)
            self.subscribe(tokens, mode="full")
    
    # ==================== CALLBACK REGISTRATION ====================
    
    def on_tick(self, callback: Callable):
        """Register tick callback"""
        self.tick_callbacks.append(callback)
    
    def on_connect(self, callback: Callable):
        """Register connect callback"""
        self.connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable):
        """Register disconnect callback"""
        self.disconnect_callbacks.append(callback)
    
    def on_error(self, callback: Callable):
        """Register error callback"""
        self.error_callbacks.append(callback)
    
    # ==================== INTERNAL CALLBACKS ====================
    
    def _on_ticks(self, ws, ticks):
        """Handle incoming ticks"""
        # Add timestamp if not present
        for tick in ticks:
            if 'timestamp' not in tick or not tick['timestamp']:
                tick['timestamp'] = datetime.now()
            

        
        # Call registered callbacks
        for callback in self.tick_callbacks:
            try:
                callback(ticks)
            except Exception as e:
                print(f"✗ Error in tick callback: {str(e)}")
    
    def _on_connect(self, ws, response):
        """Handle connection"""
        self.is_connected = True
        self.reconnect_attempts = 0
        
        print(f"✓ WebSocket connected: {response}")
        
        # Resubscribe to tokens
        self.resubscribe()
        
        # Call registered callbacks
        for callback in self.connect_callbacks:
            try:
                callback(response)
            except Exception as e:
                print(f"✗ Error in connect callback: {str(e)}")
    
    def _on_close(self, ws, code, reason):
        """Handle disconnection"""
        self.is_connected = False
        
        print(f"⚠ WebSocket closed: {code} - {reason}")
        
        # Call registered callbacks
        for callback in self.disconnect_callbacks:
            try:
                callback(code, reason)
            except Exception as e:
                print(f"✗ Error in disconnect callback: {str(e)}")
        
        # Auto-reconnect if enabled
        if self.auto_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
            self._attempt_reconnect()
    
    def _on_error(self, ws, code, reason):
        """Handle errors"""
        print(f"✗ WebSocket error: {code} - {reason}")
        
        # Call registered callbacks
        for callback in self.error_callbacks:
            try:
                callback(code, reason)
            except Exception as e:
                print(f"✗ Error in error callback: {str(e)}")
    
    def _on_reconnect(self, ws, attempts_count):
        """Handle reconnection attempt"""
        print(f"↻ Reconnecting... (Attempt {attempts_count})")
    
    def _on_noreconnect(self, ws):
        """Handle reconnection failure"""
        print("✗ Reconnection failed. Max attempts reached.")
        self.is_connected = False
    
    def _attempt_reconnect(self):
        """Attempt to reconnect"""
        self.reconnect_attempts += 1
        
        print(f"Attempting reconnection in {self.reconnect_delay}s... (Attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        
        time.sleep(self.reconnect_delay)
        
        try:
            self.connect()
        except Exception as e:
            print(f"✗ Reconnection failed: {str(e)}")
            
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self._attempt_reconnect()
    
    # ==================== STATUS ====================
    
    def get_status(self) -> Dict:
        """Get WebSocket status"""
        return {
            "connected": self.is_connected,
            "subscribed_tokens": list(self.subscribed_tokens),
            "subscription_count": len(self.subscribed_tokens),
            "reconnect_attempts": self.reconnect_attempts,
            "auto_reconnect": self.auto_reconnect
        }


# Global singleton instance
websocket_handler = WebSocketHandler()
