"""
Simple example matching the reference Kite API code structure

This is a simplified version that closely matches the reference code:
- Get NFO instruments dump
- Filter for futures
- instrumentLookup function
- fetchOHLC function

@reference: Mayank Rasu's Kite API example
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.market_data import market_data_service
import pandas as pd


# Get dump of all NFO instruments (like the reference code)
print("Fetching NFO instruments dump...")
instrument_df = market_data_service.fetch_nfo_instruments()
print(f"Total instruments: {len(instrument_df)}")

# Filter for futures only (like: fut_df = instrument_df[instrument_df["segment"]=="NFO-FUT"])
fut_df = market_data_service.get_nfo_futures()
print(f"Total futures: {len(fut_df)}")


# instrumentLookup function (matches reference code signature)
def instrumentLookup(instrument_df, symbol):
    """
    Looks up instrument token for a given script from instrument dump
    Matches the reference code's instrumentLookup function
    """
    try:
        return instrument_df[instrument_df.tradingsymbol == symbol].instrument_token.values[0]
    except:
        return -1


# fetchOHLC function (matches reference code signature)
def fetchOHLC(ticker, interval, duration):
    """
    Extracts historical data and outputs in the form of dataframe
    Matches the reference code's fetchOHLC function
    """
    try:
        # Use the service method
        df = market_data_service.fetchOHLC(ticker, interval, duration, "NFO")
        return df
    except Exception as e:
        print(f"Error fetching OHLC: {e}")
        return pd.DataFrame()


# Example usage (like the reference code)
if __name__ == "__main__":
    print("\n" + "="*60)
    print("EXAMPLE: Fetching Historical Data")
    print("="*60)
    
    # Show some available futures
    print("\nAvailable NIFTY Futures:")
    nifty_futures = fut_df[fut_df['name'].str.contains('NIFTY', case=False, na=False)]
    print(nifty_futures[['tradingsymbol', 'expiry']].head(10))
    
    # Test instrumentLookup
    if not nifty_futures.empty:
        test_symbol = nifty_futures.iloc[0]['tradingsymbol']
        token = instrumentLookup(instrument_df, test_symbol)
        print(f"\nInstrument Lookup Test:")
        print(f"Symbol: {test_symbol}")
        print(f"Token: {token}")
    
    # Test fetchOHLC (like reference code: fetchOHLC("NIFTY20MAYFUT","5minute",4))
    print("\n" + "-"*60)
    print("Fetching OHLC Data...")
    print("-"*60)
    
    # Get a NIFTY future symbol
    if not nifty_futures.empty:
        # Sort by expiry to get the nearest month
        nifty_futures['expiry'] = pd.to_datetime(nifty_futures['expiry'])
        nifty_futures = nifty_futures.sort_values('expiry')
        ticker = nifty_futures.iloc[0]['tradingsymbol']
        
        print(f"\nFetching: {ticker}")
        print(f"Interval: 5minute")
        print(f"Duration: 4 days")
        
        # Call fetchOHLC (like reference code)
        data = fetchOHLC(ticker, "5minute", 4)
        
        if not data.empty:
            print(f"\n✓ Successfully fetched {len(data)} candles")
            print("\nFirst 5 rows:")
            print(data.head())
            print("\nLast 5 rows:")
            print(data.tail())
            print("\nData shape:", data.shape)
            print("Columns:", list(data.columns))
        else:
            print("✗ No data returned")
    else:
        print("✗ No NIFTY futures found")
    
    print("\n" + "="*60)
    print("EXAMPLE COMPLETED")
    print("="*60)
