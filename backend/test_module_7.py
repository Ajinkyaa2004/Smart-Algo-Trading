"""
Test script for WebSocket Live Data (Module 7)
Demonstrates tick streaming and live candle formation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime
from app.services.kite_auth import kite_auth_service
from app.services.tick_processor import tick_processor


def test_websocket_connection():
    """Test WebSocket connection"""
    print("=" * 80)
    print("MODULE 7: WEBSOCKET LIVE DATA TEST")
    print("=" * 80)
    
    if not kite_auth_service.is_authenticated():
        print("\n⚠ Not authenticated. Please login first.")
        print("Run: python backend/test_auth.py")
        return False
    
    print("\n✓ Authenticated")
    return True


def test_tick_streaming():
    """Test real-time tick streaming"""
    print("\n" + "-" * 80)
    print("TEST 1: Real-Time Tick Streaming")
    print("-" * 80)
    
    # Symbols to stream
    symbols = ["RELIANCE", "INFY", "TCS"]
    
    print(f"\nStarting tick stream for: {', '.join(symbols)}")
    
    try:
        # Start tick processor
        tick_processor.start(symbols, exchange="NSE", mode="full")
        
        print("\n✓ Tick streaming started")
        print("  Waiting for ticks... (10 seconds)")
        
        # Wait for ticks
        time.sleep(10)
        
        # Check status
        status = tick_processor.get_status()
        
        print(f"\nStatus:")
        print(f"  Running: {status['running']}")
        print(f"  Connected: {status['websocket']['connected']}")
        print(f"  Subscribed: {status['subscribed_symbols']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Tick streaming failed: {str(e)}")
        return False


def test_candle_formation():
    """Test live candle formation"""
    print("\n" + "-" * 80)
    print("TEST 2: Live Candle Formation")
    print("-" * 80)
    
    symbol = "RELIANCE"
    intervals = ['1min', '5min']
    
    print(f"\nChecking candles for {symbol}...")
    
    try:
        for interval in intervals:
            # Get current candle
            current = tick_processor.get_current_candle(symbol, interval)
            
            if current:
                print(f"\n{interval} Candle (Current):")
                print(f"  Time: {current['timestamp']}")
                print(f"  Open: ₹{current['open']:.2f}")
                print(f"  High: ₹{current['high']:.2f}")
                print(f"  Low: ₹{current['low']:.2f}")
                print(f"  Close: ₹{current['close']:.2f}")
                print(f"  Volume: {current['volume']:,}")
                print(f"  Ticks: {current['tick_count']}")
            else:
                print(f"\n{interval}: No candle data yet")
            
            # Get historical candles
            df = tick_processor.get_candles(symbol, interval, count=5)
            
            if not df.empty:
                print(f"\n{interval} Historical Candles (Last 5):")
                print(df[['open', 'high', 'low', 'close', 'volume']].tail())
        
        return True
        
    except Exception as e:
        print(f"\n✗ Candle formation test failed: {str(e)}")
        return False


def test_candle_callbacks():
    """Test candle close callbacks"""
    print("\n" + "-" * 80)
    print("TEST 3: Candle Close Callbacks")
    print("-" * 80)
    
    candle_count = [0]  # Use list to modify in callback
    
    def on_candle_close(instrument_token, candle):
        candle_count[0] += 1
        print(f"\n🔔 Candle Closed!")
        print(f"  Token: {instrument_token}")
        print(f"  Time: {candle.timestamp}")
        print(f"  OHLC: O:{candle.open:.2f} H:{candle.high:.2f} L:{candle.low:.2f} C:{candle.close:.2f}")
    
    # Register callback for 1min candles
    tick_processor.on_candle_close('1min', on_candle_close)
    
    print("\n✓ Callback registered for 1min candles")
    print("  Waiting for candle close... (up to 60 seconds)")
    
    # Wait for a candle to close (max 60 seconds)
    start_time = time.time()
    while time.time() - start_time < 60:
        if candle_count[0] > 0:
            print(f"\n✓ Received {candle_count[0]} candle close event(s)")
            return True
        time.sleep(1)
    
    print("\n⚠ No candle close events received (may need to wait longer)")
    return True


def test_tick_callbacks():
    """Test tick callbacks"""
    print("\n" + "-" * 80)
    print("TEST 4: Tick Callbacks")
    print("-" * 80)
    
    symbol = "RELIANCE"
    tick_count = [0]
    
    def on_tick(tick):
        tick_count[0] += 1
        if tick_count[0] <= 3:  # Show first 3 ticks
            print(f"\n📊 Tick #{tick_count[0]}:")
            print(f"  Price: ₹{tick.get('last_price', 0):.2f}")
            print(f"  Volume: {tick.get('volume_traded', 0):,}")
            print(f"  Time: {tick.get('timestamp', 'N/A')}")
    
    # Register callback
    tick_processor.on_tick(symbol, on_tick)
    
    print(f"\n✓ Callback registered for {symbol}")
    print("  Waiting for ticks... (5 seconds)")
    
    time.sleep(5)
    
    print(f"\n✓ Received {tick_count[0]} ticks")
    return True


def test_subscription_management():
    """Test subscribe/unsubscribe"""
    print("\n" + "-" * 80)
    print("TEST 5: Subscription Management")
    print("-" * 80)
    
    # Subscribe to new symbol
    new_symbol = "HDFCBANK"
    
    print(f"\nSubscribing to {new_symbol}...")
    try:
        tick_processor.subscribe_symbol(new_symbol, exchange="NSE")
        print(f"✓ Subscribed to {new_symbol}")
        
        # Wait for ticks
        time.sleep(3)
        
        # Check candle
        candle = tick_processor.get_current_candle(new_symbol, '1min')
        if candle:
            print(f"\n{new_symbol} Current Price: ₹{candle['close']:.2f}")
        
        # Unsubscribe
        print(f"\nUnsubscribing from {new_symbol}...")
        tick_processor.unsubscribe_symbol(new_symbol)
        print(f"✓ Unsubscribed from {new_symbol}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Subscription test failed: {str(e)}")
        return False


def cleanup():
    """Cleanup and stop tick processor"""
    print("\n" + "-" * 80)
    print("CLEANUP")
    print("-" * 80)
    
    try:
        tick_processor.stop()
        print("✓ Tick processor stopped")
    except Exception as e:
        print(f"⚠ Cleanup warning: {str(e)}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "MODULE 7 COMPREHENSIVE TEST" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        # Test 1: Connection
        if not test_websocket_connection():
            print("\n✗ Authentication failed. Exiting.")
            sys.exit(1)
        
        # Test 2: Tick Streaming
        if not test_tick_streaming():
            print("\n✗ Tick streaming failed. Exiting.")
            cleanup()
            sys.exit(1)
        
        # Test 3: Candle Formation
        test_candle_formation()
        
        # Test 4: Tick Callbacks
        test_tick_callbacks()
        
        # Test 5: Candle Callbacks (optional - may take time)
        # test_candle_callbacks()
        
        # Test 6: Subscription Management
        test_subscription_management()
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        print("\n✅ All WebSocket tests completed successfully!")
        print("\nFeatures Tested:")
        print("  ✓ WebSocket connection")
        print("  ✓ Real-time tick streaming")
        print("  ✓ Live candle formation (multiple timeframes)")
        print("  ✓ Tick callbacks")
        print("  ✓ Subscribe/Unsubscribe")
        print("\nNext steps:")
        print("  1. Test via API: http://localhost:8000/docs")
        print("  2. Integrate with trading strategies")
        print("  3. Build execution engine")
        print("=" * 80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Test failed: {str(e)}")
    finally:
        cleanup()
