
import sys
import os
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.market_data import market_data_service
from app.services.kite_auth import kite_auth_service

try:
    print("--- Checking Kite Authentication ---")
    print(f"Is Authenticated: {kite_auth_service.is_authenticated()}")
    
    print("\n--- Checking NSE Instruments ---")
    # Force refresh to be sure
    df_nse = market_data_service.fetch_instruments("NSE", force_refresh=True)
    print(f"NSE Instruments Count: {len(df_nse)}")
    
    symbol_nse = "RELIANCE"
    token_nse = market_data_service.get_instrument_token(symbol_nse, "NSE")
    print(f"Token for {symbol_nse} (NSE): {token_nse}")
    
    print("\n--- Checking NFO Instruments ---")
    # This might take a while
    df_nfo = market_data_service.fetch_nfo_instruments(force_refresh=True)
    print(f"NFO Instruments Count: {len(df_nfo)}")
    
    # Try to find a NIFTY Future
    # Filter for NIFTY FUT
    nifty_futs = df_nfo[(df_nfo['name'] == 'NIFTY') & (df_nfo['segment'] == 'NFO-FUT')]
    if not nifty_futs.empty:
        sample_fut = nifty_futs.iloc[0]['tradingsymbol']
        print(f"Sample NIFTY Future: {sample_fut}")
        token_nfo = market_data_service.get_instrument_token(sample_fut, "NFO")
        print(f"Token for {sample_fut} (NFO): {token_nfo}")
    else:
        print("No NIFTY Futures found!")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
