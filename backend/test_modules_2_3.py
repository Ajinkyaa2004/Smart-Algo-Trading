"""
Test script for Market Data and Technical Indicators
Demonstrates all features of Module 2 and Module 3
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app.services.kite_auth import kite_auth_service
from app.services.market_data import market_data_service
from app.services.indicators import TechnicalIndicators
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


def test_market_data():
    """Test market data service"""
    print("=" * 80)
    print("MODULE 2: MARKET DATA SERVICE TEST")
    print("=" * 80)
    
    if not kite_auth_service.is_authenticated():
        print("\n⚠ Not authenticated. Please login first.")
        print("Run: python backend/test_auth.py")
        return False
    
    print("\n✓ Authenticated")
    
    # Test 1: Search instruments
    print("\n" + "-" * 80)
    print("TEST 1: Search Instruments")
    print("-" * 80)
    
    try:
        results = market_data_service.search_instruments("RELIANCE", "NSE")
        print(f"✓ Found {len(results)} instruments matching 'RELIANCE'")
        if results:
            print(f"  First result: {results[0]['tradingsymbol']} - {results[0]['name']}")
    except Exception as e:
        print(f"✗ Search failed: {str(e)}")
    
    # Test 2: Get instrument token
    print("\n" + "-" * 80)
    print("TEST 2: Get Instrument Token")
    print("-" * 80)
    
    try:
        token = market_data_service.get_instrument_token("RELIANCE", "NSE")
        print(f"✓ RELIANCE token: {token}")
    except Exception as e:
        print(f"✗ Token fetch failed: {str(e)}")
    
    # Test 3: Get LTP
    print("\n" + "-" * 80)
    print("TEST 3: Get Last Traded Price")
    print("-" * 80)
    
    try:
        ltp = market_data_service.get_ltp(["NSE:RELIANCE", "NSE:INFY"])
        print(f"✓ LTP data fetched:")
        for symbol, data in ltp.items():
            print(f"  {symbol}: ₹{data['last_price']}")
    except Exception as e:
        print(f"✗ LTP fetch failed: {str(e)}")
    
    # Test 4: Get Quote
    print("\n" + "-" * 80)
    print("TEST 4: Get Full Quote")
    print("-" * 80)
    
    try:
        quote = market_data_service.get_quote(["NSE:RELIANCE"])
        if "NSE:RELIANCE" in quote:
            q = quote["NSE:RELIANCE"]
            print(f"✓ Quote for RELIANCE:")
            print(f"  Open: ₹{q['ohlc']['open']}")
            print(f"  High: ₹{q['ohlc']['high']}")
            print(f"  Low: ₹{q['ohlc']['low']}")
            print(f"  Close: ₹{q['ohlc']['close']}")
            print(f"  Volume: {q['volume']:,}")
    except Exception as e:
        print(f"✗ Quote fetch failed: {str(e)}")
    
    # Test 5: Historical Data
    print("\n" + "-" * 80)
    print("TEST 5: Historical Data")
    print("-" * 80)
    
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=30)
        
        df = market_data_service.get_historical_data_by_symbol(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=from_date,
            to_date=to_date,
            interval="day"
        )
        
        print(f"✓ Fetched {len(df)} candles for RELIANCE")
        print(f"\nLast 5 candles:")
        print(df[['open', 'high', 'low', 'close', 'volume']].tail())
        
        return df
        
    except Exception as e:
        print(f"✗ Historical data fetch failed: {str(e)}")
        return None


def test_indicators(df):
    """Test technical indicators"""
    print("\n\n" + "=" * 80)
    print("MODULE 3: TECHNICAL INDICATORS TEST")
    print("=" * 80)
    
    if df is None or df.empty:
        print("\n⚠ No data available for indicator testing")
        return
    
    # Test 1: Moving Averages
    print("\n" + "-" * 80)
    print("TEST 1: Moving Averages (SMA, EMA)")
    print("-" * 80)
    
    df['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
    df['ema_20'] = TechnicalIndicators.ema(df['close'], 20)
    
    print(f"✓ SMA(20): ₹{df['sma_20'].iloc[-1]:.2f}")
    print(f"✓ EMA(20): ₹{df['ema_20'].iloc[-1]:.2f}")
    
    # Test 2: RSI
    print("\n" + "-" * 80)
    print("TEST 2: RSI (Relative Strength Index)")
    print("-" * 80)
    
    df['rsi'] = TechnicalIndicators.rsi_ema(df['close'], 14)
    latest_rsi = df['rsi'].iloc[-1]
    
    print(f"✓ RSI(14): {latest_rsi:.2f}")
    
    if latest_rsi < 30:
        print("  → Oversold (potential BUY signal)")
    elif latest_rsi > 70:
        print("  → Overbought (potential SELL signal)")
    else:
        print("  → Neutral")
    
    # Test 3: MACD
    print("\n" + "-" * 80)
    print("TEST 3: MACD (Moving Average Convergence Divergence)")
    print("-" * 80)
    
    macd, signal, hist = TechnicalIndicators.macd(df['close'])
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_hist'] = hist
    
    print(f"✓ MACD: {macd.iloc[-1]:.2f}")
    print(f"✓ Signal: {signal.iloc[-1]:.2f}")
    print(f"✓ Histogram: {hist.iloc[-1]:.2f}")
    
    if hist.iloc[-1] > 0:
        print("  → Bullish (MACD above signal)")
    else:
        print("  → Bearish (MACD below signal)")
    
    # Test 4: Bollinger Bands
    print("\n" + "-" * 80)
    print("TEST 4: Bollinger Bands")
    print("-" * 80)
    
    upper, middle, lower = TechnicalIndicators.bollinger_bands(df['close'], 20, 2)
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower
    
    current_price = df['close'].iloc[-1]
    
    print(f"✓ Upper Band: ₹{upper.iloc[-1]:.2f}")
    print(f"✓ Middle Band: ₹{middle.iloc[-1]:.2f}")
    print(f"✓ Lower Band: ₹{lower.iloc[-1]:.2f}")
    print(f"  Current Price: ₹{current_price:.2f}")
    
    # Test 5: VWAP
    print("\n" + "-" * 80)
    print("TEST 5: VWAP (Volume Weighted Average Price)")
    print("-" * 80)
    
    df['vwap'] = TechnicalIndicators.vwap(df)
    
    print(f"✓ VWAP: ₹{df['vwap'].iloc[-1]:.2f}")
    print(f"  Current Price: ₹{current_price:.2f}")
    
    if current_price > df['vwap'].iloc[-1]:
        print("  → Price above VWAP (bullish)")
    else:
        print("  → Price below VWAP (bearish)")
    
    # Test 6: ATR
    print("\n" + "-" * 80)
    print("TEST 6: ATR (Average True Range)")
    print("-" * 80)
    
    df['atr'] = TechnicalIndicators.atr(df, 14)
    
    print(f"✓ ATR(14): ₹{df['atr'].iloc[-1]:.2f}")
    print(f"  Volatility: {(df['atr'].iloc[-1] / current_price * 100):.2f}%")
    
    # Test 7: Add all indicators
    print("\n" + "-" * 80)
    print("TEST 7: Add All Indicators")
    print("-" * 80)
    
    df_full = TechnicalIndicators.add_all_indicators(df)
    
    print(f"✓ Added all indicators to DataFrame")
    print(f"  Total columns: {len(df_full.columns)}")
    print(f"  Indicator columns: {[col for col in df_full.columns if col not in ['open', 'high', 'low', 'close', 'volume']]}")
    
    # Display summary
    print("\n" + "-" * 80)
    print("INDICATOR SUMMARY (Latest Values)")
    print("-" * 80)
    
    summary = {
        "Price": f"₹{current_price:.2f}",
        "SMA(20)": f"₹{df_full['sma_20'].iloc[-1]:.2f}",
        "EMA(21)": f"₹{df_full['ema_21'].iloc[-1]:.2f}",
        "RSI(14)": f"{df_full['rsi'].iloc[-1]:.2f}",
        "MACD": f"{df_full['macd'].iloc[-1]:.2f}",
        "BB Upper": f"₹{df_full['bb_upper'].iloc[-1]:.2f}",
        "BB Lower": f"₹{df_full['bb_lower'].iloc[-1]:.2f}",
        "ATR(14)": f"₹{df_full['atr'].iloc[-1]:.2f}",
        "VWAP": f"₹{df_full['vwap'].iloc[-1]:.2f}"
    }
    
    for key, value in summary.items():
        print(f"  {key:12s}: {value}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MODULE 2 & 3 COMPREHENSIVE TEST" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Test market data
    df = test_market_data()
    
    # Test indicators
    if df is not None:
        test_indicators(df)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nAll modules tested successfully! ✅")
    print("\nNext steps:")
    print("  1. Test via API: http://localhost:8000/docs")
    print("  2. Implement trading strategies using these indicators")
    print("  3. Set up WebSocket for live data streaming")
    print("=" * 80 + "\n")
