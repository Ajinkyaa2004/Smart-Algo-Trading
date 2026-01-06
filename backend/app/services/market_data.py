"""
Market Data Service
Handles all market data operations: instruments, quotes, OHLC, historical data
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from kiteconnect import KiteConnect
from app.services.kite_auth import kite_auth_service
import csv
from pathlib import Path


class MarketDataService:
    """
    Service for fetching market data from Kite Connect
    - Instruments master
    - LTP, Quotes, OHLC
    - Historical candle data
    """
    
    def __init__(self):
        self.instruments_file = Path("data/instruments.csv")
        self.nfo_instruments_file = Path("data/nfo_instruments.csv")
        self.instruments_cache: Optional[pd.DataFrame] = None
        self.nfo_instruments_cache: Optional[pd.DataFrame] = None
        self.cache_expiry: Optional[datetime] = None
        self.nfo_cache_expiry: Optional[datetime] = None
    
    def _get_kite(self) -> KiteConnect:
        """Get authenticated Kite instance"""
        return kite_auth_service.get_kite_instance()
    
    # ==================== INSTRUMENTS ====================
    
    def fetch_instruments(self, exchange: str = "NSE", force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetch instruments master from Kite
        
        Args:
            exchange: Exchange name (NSE, NFO, BSE, etc.)
            force_refresh: Force download even if cache exists
            
        Returns:
            DataFrame with instrument details
        """
        # Check cache (valid for 1 day)
        if not force_refresh and self.instruments_cache is not None:
            if self.cache_expiry and datetime.now() < self.cache_expiry:
                return self.instruments_cache
        
        try:
            kite = self._get_kite()
            instruments = kite.instruments(exchange)
            
            # Convert to DataFrame
            df = pd.DataFrame(instruments)
            
            # Save to CSV
            self.instruments_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.instruments_file, index=False)
            
            # Update cache
            self.instruments_cache = df
            self.cache_expiry = datetime.now() + timedelta(days=1)
            
            print(f"✓ Fetched {len(df)} instruments from {exchange}")
            return df
            
        except Exception as e:
            # Try to load from file if API fails
            if self.instruments_file.exists():
                print(f"⚠ API failed, loading from cache: {str(e)}")
                df = pd.read_csv(self.instruments_file)
                self.instruments_cache = df
                return df
            raise Exception(f"Failed to fetch instruments: {str(e)}")
    
    def fetch_nfo_instruments(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetch NFO (Futures & Options) instruments from Kite
        Useful for derivatives trading
        
        Args:
            force_refresh: Force download even if cache exists
            
        Returns:
            DataFrame with NFO instrument details
        """
        # Check cache (valid for 1 day)
        if not force_refresh and self.nfo_instruments_cache is not None:
            if self.nfo_cache_expiry and datetime.now() < self.nfo_cache_expiry:
                return self.nfo_instruments_cache
        
        try:
            kite = self._get_kite()
            instruments = kite.instruments("NFO")
            
            # Convert to DataFrame
            df = pd.DataFrame(instruments)
            
            # Save to CSV
            self.nfo_instruments_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.nfo_instruments_file, index=False)
            
            # Update cache
            self.nfo_instruments_cache = df
            self.nfo_cache_expiry = datetime.now() + timedelta(days=1)
            
            print(f"✓ Fetched {len(df)} NFO instruments")
            return df
            
        except Exception as e:
            # Try to load from file if API fails
            if self.nfo_instruments_file.exists():
                print(f"⚠ API failed, loading NFO from cache: {str(e)}")
                df = pd.read_csv(self.nfo_instruments_file)
                self.nfo_instruments_cache = df
                return df
            raise Exception(f"Failed to fetch NFO instruments: {str(e)}")
    
    def get_nfo_futures(self, underlying: Optional[str] = None) -> pd.DataFrame:
        """
        Get all NFO futures contracts
        
        Args:
            underlying: Filter by underlying (e.g., 'NIFTY', 'BANKNIFTY', 'RELIANCE')
            
        Returns:
            DataFrame with futures contracts
        """
        df = self.fetch_nfo_instruments()
        
        # Filter for futures only
        fut_df = df[df["segment"] == "NFO-FUT"].copy()
        
        # Filter by underlying if specified
        if underlying:
            fut_df = fut_df[fut_df["name"].str.contains(underlying, case=False, na=False)]
        
        return fut_df
    
    def get_nfo_options(self, underlying: Optional[str] = None, option_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get all NFO options contracts
        
        Args:
            underlying: Filter by underlying (e.g., 'NIFTY', 'BANKNIFTY')
            option_type: Filter by option type ('CE' for Call, 'PE' for Put)
            
        Returns:
            DataFrame with options contracts
        """
        df = self.fetch_nfo_instruments()
        
        # Filter for options only
        opt_df = df[df["segment"] == "NFO-OPT"].copy()
        
        # Filter by underlying if specified
        if underlying:
            opt_df = opt_df[opt_df["name"].str.contains(underlying, case=False, na=False)]
        
        # Filter by option type if specified
        if option_type:
            opt_df = opt_df[opt_df["tradingsymbol"].str.contains(option_type, case=False, na=False)]
        
        return opt_df
    
    def search_instruments(self, query: str, exchange: str = "ALL") -> List[Dict]:
        """
        Search for instruments by symbol/name
        
        Args:
            query: Search query (e.g., "RELIANCE", "NIFTY", "SENSEX")
            exchange: Exchange to search in (NSE, BSE, or ALL for both)
            
        Returns:
            List of matching instruments
        """
        results = []
        
        # If exchange is ALL, search both NSE and BSE
        if exchange == "ALL":
            exchanges = ["NSE", "BSE"]
        else:
            exchanges = [exchange]
        
        for exch in exchanges:
            try:
                df = self.fetch_instruments(exch)
                
                # Case-insensitive search
                mask = (
                    df['tradingsymbol'].str.contains(query, case=False, na=False) |
                    df['name'].str.contains(query, case=False, na=False)
                )
                
                matches = df[mask].head(10).to_dict('records')
                results.extend(matches)
            except Exception as e:
                print(f"Error searching {exch}: {e}")
                continue
        
        # Sort by relevance (exact match first, then contains)
        query_lower = query.lower()
        results.sort(key=lambda x: (
            0 if x['tradingsymbol'].lower() == query_lower else
            1 if x['tradingsymbol'].lower().startswith(query_lower) else
            2
        ))
        
        return results[:20]  # Limit to 20 results
    
    def get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """
        Get instrument token for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "RELIANCE", "NIFTY 50")
            exchange: Exchange name
            
        Returns:
            Instrument token or None
        """
        try:
            df = self.fetch_instruments(exchange)
            
            # Try exact match first
            match = df[df['tradingsymbol'].str.strip() == symbol.strip()]
            
            if not match.empty:
                token = int(match.iloc[0]['instrument_token'])
                print(f"✓ Found token for '{symbol}': {token}")
                return token
            
            # Try case-insensitive match
            match = df[df['tradingsymbol'].str.lower().str.strip() == symbol.lower().strip()]
            
            if not match.empty:
                token = int(match.iloc[0]['instrument_token'])
                print(f"✓ Found token for '{symbol}' (case-insensitive): {token}")
                return token
            
            print(f"✗ No token found for '{symbol}' in {exchange}")
            print(f"  Available NIFTY indices: {df[df['tradingsymbol'].str.contains('NIFTY', case=False, na=False)]['tradingsymbol'].head(10).tolist()}")
            return None
            
        except Exception as e:
            print(f"✗ Error getting token for '{symbol}': {str(e)}")
            return None
    
    # ==================== QUOTES & LTP ====================
    
    def get_ltp(self, symbols: List[str]) -> Dict:
        """
        Get Last Traded Price for symbols
        
        Args:
            symbols: List of symbols in format "EXCHANGE:SYMBOL" (e.g., ["NSE:RELIANCE"])
            
        Returns:
            Dictionary with LTP data
        """
        try:
            kite = self._get_kite()
            ltp_data = kite.ltp(symbols)
            return ltp_data
        except Exception as e:
            raise Exception(f"Failed to fetch LTP: {str(e)}")
    
    def get_quote(self, symbols: List[str]) -> Dict:
        """
        Get full quote (OHLC, volume, etc.) for symbols
        
        Args:
            symbols: List of symbols in format "EXCHANGE:SYMBOL"
            
        Returns:
            Dictionary with quote data
        """
        try:
            kite = self._get_kite()
            quotes = kite.quote(symbols)
            return quotes
        except Exception as e:
            raise Exception(f"Failed to fetch quotes: {str(e)}")
    
    def get_ohlc(self, symbols: List[str]) -> Dict:
        """
        Get OHLC data for symbols
        
        Args:
            symbols: List of symbols in format "EXCHANGE:SYMBOL"
            
        Returns:
            Dictionary with OHLC data
        """
        try:
            kite = self._get_kite()
            ohlc_data = kite.ohlc(symbols)
            return ohlc_data
        except Exception as e:
            raise Exception(f"Failed to fetch OHLC: {str(e)}")
    
    # ==================== HISTORICAL DATA ====================
    
    def get_historical_data(
        self,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str = "day",
        continuous: bool = False,
        oi: bool = False
    ) -> pd.DataFrame:
        """
        Fetch historical candle data with automatic chunking for large ranges
        
        Args:
            instrument_token: Instrument token
            from_date: Start date
            to_date: End date
            interval: Candle interval
            continuous: Continuous data for futures
            oi: Include Open Interest
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Define limits (days) based on interval
            # Using conservative limits to be safe
            limits = {
                "minute": 60,
                "3minute": 60,
                "5minute": 60,
                "15minute": 100,
                "30minute": 100,
                "60minute": 200,
                "day": 2000
            }
            limit_days = limits.get(interval, 30)
            
            # Check if chunking is needed
            total_days = (to_date - from_date).days
            
            if total_days <= limit_days:
                return self._fetch_single_chunk(
                    instrument_token, from_date, to_date, interval, continuous, oi
                )
            
            # Chunking required
            print(f"I> Range ({total_days} days) exceeds limit ({limit_days} days). Chunking requests...")
            df_list = []
            curr_from = from_date
            
            while curr_from < to_date:
                curr_to = min(curr_from + timedelta(days=limit_days), to_date)
                
                print(f"  Fetching chunk: {curr_from.date()} to {curr_to.date()}")
                chunk = self._fetch_single_chunk(
                    instrument_token, curr_from, curr_to, interval, continuous, oi
                )
                
                if not chunk.empty:
                    df_list.append(chunk)
                
                # Advance start time
                # Add 1 second or rely on duplicate removal? 
                # Kite ranges are inclusive. We'll start next chunk from next second/day.
                # But safer to just overlap and drop duplicates to ensure no gaps.
                curr_from = curr_to 
                
                if curr_from >= to_date:
                    break
            
            if not df_list:
                return pd.DataFrame()
            
            # Combine and remove duplicates
            df = pd.concat(df_list)
            df = df[~df.index.duplicated(keep='first')]
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            raise Exception(f"Failed to fetch historical data: {str(e)}")
            
    def _fetch_single_chunk(
        self,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str,
        continuous: bool,
        oi: bool
    ) -> pd.DataFrame:
        """Helper to fetch a single chunk from Kite"""
        kite = self._get_kite()
        records = kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
            continuous=continuous,
            oi=oi
        )
        
        df = pd.DataFrame(records)
        if df.empty:
            return df
            
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    
    def get_historical_data_by_symbol(
        self,
        symbol: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime,
        interval: str = "day"
    ) -> pd.DataFrame:
        """
        Fetch historical data by symbol name (convenience method)
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            from_date: Start date
            to_date: End date
            interval: Candle interval
            
        Returns:
            DataFrame with OHLCV data
        """
        token = self.get_instrument_token(symbol, exchange)
        if not token:
            raise ValueError(f"Symbol {symbol} not found on {exchange}")
        
        return self.get_historical_data(token, from_date, to_date, interval)
    
    # ==================== CONVENIENCE METHODS (Similar to reference code) ====================
    
    def instrument_lookup(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """
        Looks up instrument token for a given symbol
        This is a convenience method similar to the reference code's instrumentLookup
        
        Args:
            symbol: Trading symbol (e.g., "RELIANCE", "NIFTY20MAYFUT")
            exchange: Exchange (NSE, NFO, BSE)
            
        Returns:
            Instrument token or None if not found
        """
        try:
            if exchange == "NFO":
                df = self.fetch_nfo_instruments()
            else:
                df = self.fetch_instruments(exchange)
            
            # Try exact match
            match = df[df['tradingsymbol'] == symbol]
            if not match.empty:
                return int(match.iloc[0]['instrument_token'])
            
            # Try case-insensitive
            match = df[df['tradingsymbol'].str.upper() == symbol.upper()]
            if not match.empty:
                return int(match.iloc[0]['instrument_token'])
            
            return None
            
        except Exception as e:
            print(f"Error in instrument_lookup: {e}")
            return None
    
    def fetchOHLC(self, ticker: str, interval: str, duration: int, exchange: str = "NSE") -> pd.DataFrame:
        """
        Convenience method to fetch historical OHLC data
        Similar to the reference code's fetchOHLC function
        
        Args:
            ticker: Trading symbol (e.g., "RELIANCE", "NIFTY20MAYFUT")
            interval: Candle interval (e.g., "5minute", "day", "60minute")
            duration: Number of days of historical data
            exchange: Exchange (NSE, NFO, BSE)
            
        Returns:
            DataFrame with OHLC data indexed by date
            
        Example:
            # Fetch 4 days of 5-minute data for NIFTY futures
            df = market_data_service.fetchOHLC("NIFTY20MAYFUT", "5minute", 4, "NFO")
        """
        try:
            # Get instrument token
            instrument_token = self.instrument_lookup(ticker, exchange)
            
            if not instrument_token:
                raise ValueError(f"Symbol '{ticker}' not found on {exchange}")
            
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=duration)
            
            # Fetch historical data
            df = self.get_historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            return df
            
        except Exception as e:
            raise Exception(f"fetchOHLC failed for {ticker}: {str(e)}")


# Global singleton instance
market_data_service = MarketDataService()
