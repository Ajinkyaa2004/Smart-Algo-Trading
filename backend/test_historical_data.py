"""
Test script for historical data fetching
Similar to the reference Kite API example

This demonstrates:
1. Fetching NFO instruments
2. Looking up instrument tokens
3. Fetching historical OHLC data using the convenience methods

Usage:
    python test_historical_data.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.market_data import market_data_service
from datetime import datetime, timedelta
import pandas as pd


def test_nfo_instruments():
    """Test fetching NFO instruments"""
    print("\n" + "="*60)
    print("TEST 1: Fetching NFO Instruments")
    print("="*60)
    
    try:
        # Get all NFO instruments
        nfo_df = market_data_service.fetch_nfo_instruments()
        print(f"✓ Total NFO instruments: {len(nfo_df)}")
        
        # Filter for futures only (like the reference code)
        fut_df = market_data_service.get_nfo_futures()
        print(f"✓ Total NFO Futures: {len(fut_df)}")
        
        # Show some NIFTY futures
        nifty_futures = fut_df[fut_df['name'].str.contains('NIFTY', case=False, na=False)]
        print(f"✓ NIFTY Futures found: {len(nifty_futures)}")
        print("\nSample NIFTY Futures:")
        print(nifty_futures[['tradingsymbol', 'expiry', 'strike']].head(10))
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_instrument_lookup():
    """Test instrument lookup function (like reference code's instrumentLookup)"""
    print("\n" + "="*60)
    print("TEST 2: Instrument Lookup")
    print("="*60)
    
    test_symbols = [
        ("RELIANCE", "NSE"),
        ("NIFTY 50", "NSE"),
        ("INFY", "NSE"),
    ]
    
    # Add a futures contract if available
    try:
        fut_df = market_data_service.get_nfo_futures("NIFTY")
        if not fut_df.empty:
            latest_future = fut_df.iloc[0]['tradingsymbol']
            test_symbols.append((latest_future, "NFO"))
    except:
        pass
    
    for symbol, exchange in test_symbols:
        try:
            token = market_data_service.instrument_lookup(symbol, exchange)
            if token:
                print(f"✓ {symbol:20} ({exchange}): {token}")
            else:
                print(f"✗ {symbol:20} ({exchange}): Not found")
        except Exception as e:
            print(f"✗ {symbol:20} ({exchange}): Error - {e}")


def test_fetch_ohlc():
    """Test fetchOHLC convenience method (like reference code's fetchOHLC)"""
    print("\n" + "="*60)
    print("TEST 3: Fetch OHLC Data (like reference code)")
    print("="*60)
    
    # Test 1: NSE stock (5-minute data for 4 days)
    try:
        print("\n--- Fetching RELIANCE 5-minute data (4 days) ---")
        df = market_data_service.fetchOHLC(
            ticker="RELIANCE",
            interval="5minute",
            duration=4,
            exchange="NSE"
        )
        
        if not df.empty:
            print(f"✓ Retrieved {len(df)} candles")
            print("\nLast 5 candles:")
            print(df[['open', 'high', 'low', 'close', 'volume']].tail())
        else:
            print("✗ No data returned")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: NFO Future (like reference code's NIFTY20MAYFUT example)
    try:
        print("\n--- Fetching NIFTY Future 5-minute data (4 days) ---")
        
        # Get the latest NIFTY future
        fut_df = market_data_service.get_nfo_futures("NIFTY")
        
        if not fut_df.empty:
            # Sort by expiry and get the nearest
            fut_df['expiry'] = pd.to_datetime(fut_df['expiry'])
            fut_df = fut_df.sort_values('expiry')
            latest_future = fut_df.iloc[0]['tradingsymbol']
            
            print(f"Using symbol: {latest_future}")
            
            df = market_data_service.fetchOHLC(
                ticker=latest_future,
                interval="5minute",
                duration=4,
                exchange="NFO"
            )
            
            if not df.empty:
                print(f"✓ Retrieved {len(df)} candles")
                print("\nLast 5 candles:")
                print(df[['open', 'high', 'low', 'close', 'volume']].tail())
            else:
                print("✗ No data returned")
        else:
            print("✗ No NIFTY futures found")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Daily data
    try:
        print("\n--- Fetching INFY daily data (30 days) ---")
        df = market_data_service.fetchOHLC(
            ticker="INFY",
            interval="day",
            duration=30,
            exchange="NSE"
        )
        
        if not df.empty:
            print(f"✓ Retrieved {len(df)} candles")
            print("\nLast 5 days:")
            print(df[['open', 'high', 'low', 'close', 'volume']].tail())
        else:
            print("✗ No data returned")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_direct_historical_api():
    """Test the direct historical data API (existing method)"""
    print("\n" + "="*60)
    print("TEST 4: Direct Historical Data API")
    print("="*60)
    
    try:
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        
        print(f"\nFetching TCS daily data from {from_date.date()} to {to_date.date()}")
        
        df = market_data_service.get_historical_data_by_symbol(
            symbol="TCS",
            exchange="NSE",
            from_date=from_date,
            to_date=to_date,
            interval="day"
        )
        
        if not df.empty:
            print(f"✓ Retrieved {len(df)} candles")
            print("\nData:")
            print(df[['open', 'high', 'low', 'close', 'volume']])
        else:
            print("✗ No data returned")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("HISTORICAL DATA TESTING SUITE")
    print("Reference: Kite API Historical Data Example")
    print("="*60)
    
    # Check authentication
    try:
        kite = market_data_service._get_kite()
        print("✓ Kite authentication successful")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print("\nPlease ensure you are logged in:")
        print("1. Run the backend server: python main.py")
        print("2. Visit http://localhost:8000/auth/login")
        print("3. Complete the Zerodha login")
        return
    
    # Run tests
    test_nfo_instruments()
    test_instrument_lookup()
    test_fetch_ohlc()
    test_direct_historical_api()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
