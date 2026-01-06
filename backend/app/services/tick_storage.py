"""
Tick Data Storage Service
Stores real-time tick data to SQLite database and retrieves it for analysis
"""
import sqlite3
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import threading
from app.services.market_data import market_data_service


class TickStorageService:
    """
    Service for storing and retrieving tick-level data
    - Stores ticks in SQLite database
    - One table per instrument token
    - Converts stored ticks to OHLC candles
    """
    
    def __init__(self, db_path: str = "data/ticks.db"):
        """
        Initialize tick storage service
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()
        
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Allow multi-threaded access
                timeout=10.0
            )
            print(f"✓ Tick database connected: {self.db_path}")
        except Exception as e:
            print(f"✗ Failed to connect to tick database: {str(e)}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("✓ Tick database connection closed")
    
    # ==================== TABLE MANAGEMENT ====================
    
    def create_tables(self, tokens: List[int]):
        """
        Create tables for storing tick data
        
        Args:
            tokens: List of instrument tokens
        """
        with self.lock:
            cursor = self.connection.cursor()
            
            for token in tokens:
                table_name = f"TOKEN{token}"
                
                # Create table if not exists
                create_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    ts DATETIME PRIMARY KEY,
                    price REAL(15,5),
                    volume INTEGER,
                    bid REAL(15,5),
                    ask REAL(15,5),
                    oi INTEGER
                )
                """
                
                try:
                    cursor.execute(create_query)
                    print(f"  ✓ Table created: {table_name}")
                except Exception as e:
                    print(f"  ✗ Error creating table {table_name}: {str(e)}")
            
            try:
                self.connection.commit()
                print(f"✓ Created tables for {len(tokens)} instruments")
            except Exception as e:
                self.connection.rollback()
                print(f"✗ Failed to commit table creation: {str(e)}")
    
    def table_exists(self, token: int) -> bool:
        """Check if table exists for token"""
        cursor = self.connection.cursor()
        table_name = f"TOKEN{token}"
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        
        return cursor.fetchone() is not None
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tick tables"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'TOKEN%'
        """)
        
        return [row[0] for row in cursor.fetchall()]
    
    # ==================== TICK STORAGE ====================
    
    def insert_ticks(self, ticks: List[Dict]):
        """
        Insert tick data into database
        
        Args:
            ticks: List of tick dictionaries from KiteTicker
        """
        with self.lock:
            cursor = self.connection.cursor()
            
            for tick in ticks:
                try:
                    token = tick.get('instrument_token')
                    if not token:
                        continue
                    
                    table_name = f"TOKEN{token}"
                    
                    # Ensure table exists
                    if not self.table_exists(token):
                        self.create_tables([token])
                    
                    # Extract tick data
                    timestamp = tick.get('exchange_timestamp', tick.get('timestamp', datetime.now()))
                    if isinstance(timestamp, datetime):
                        timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    
                    price = tick.get('last_price', 0.0)
                    volume = tick.get('last_traded_quantity', 0)
                    bid = tick.get('depth', {}).get('buy', [{}])[0].get('price', 0.0) if 'depth' in tick else 0.0
                    ask = tick.get('depth', {}).get('sell', [{}])[0].get('price', 0.0) if 'depth' in tick else 0.0
                    oi = tick.get('oi', 0)
                    
                    # Insert query
                    query = f"""
                    INSERT OR REPLACE INTO {table_name}
                    (ts, price, volume, bid, ask, oi)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(query, [timestamp, price, volume, bid, ask, oi])
                    
                except Exception as e:
                    # Continue with other ticks even if one fails
                    print(f"✗ Error inserting tick for token {token}: {str(e)}")
                    pass
            
            try:
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                print(f"✗ Failed to commit ticks: {str(e)}")
    
    def insert_tick(self, tick: Dict):
        """Insert single tick (convenience method)"""
        self.insert_ticks([tick])
    
    # ==================== TICK RETRIEVAL ====================
    
    def get_ticks(
        self,
        symbol: str,
        exchange: str = "NSE",
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        days_back: int = 12
    ) -> pd.DataFrame:
        """
        Retrieve tick data from database
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            from_date: Start date (optional)
            to_date: End date (optional)
            days_back: Days to look back if dates not specified
            
        Returns:
            DataFrame with tick data
        """
        # Get instrument token
        token = market_data_service.get_instrument_token(symbol, exchange)
        if not token:
            raise ValueError(f"Token not found for {symbol} on {exchange}")
        
        table_name = f"TOKEN{token}"
        
        # Check if table exists
        if not self.table_exists(token):
            print(f"⚠ No data table found for {symbol} (token: {token})")
            return pd.DataFrame()
        
        # Build query
        if from_date and to_date:
            query = f"""
            SELECT * FROM {table_name}
            WHERE ts >= ? AND ts <= ?
            ORDER BY ts
            """
            params = (from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d'))
        else:
            # Use days_back
            query = f"""
            SELECT * FROM {table_name}
            WHERE ts >= date('now', '-{days_back} day')
            ORDER BY ts
            """
            params = ()
        
        try:
            df = pd.read_sql(query, con=self.connection, params=params)
            
            if df.empty:
                print(f"⚠ No tick data found for {symbol}")
                return df
            
            # Set timestamp as index
            df['ts'] = pd.to_datetime(df['ts'])
            df.set_index('ts', inplace=True)
            
            print(f"✓ Retrieved {len(df)} ticks for {symbol}")
            return df
            
        except Exception as e:
            print(f"✗ Error retrieving ticks for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    # ==================== TICK TO CANDLE CONVERSION ====================
    
    def ticks_to_candles(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: str = "5min",
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        days_back: int = 12
    ) -> pd.DataFrame:
        """
        Convert stored tick data to OHLC candles
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            interval: Candle interval (1min, 3min, 5min, 15min, etc.)
            from_date: Start date
            to_date: End date
            days_back: Days to look back
            
        Returns:
            DataFrame with OHLC candles
        """
        # Get tick data
        ticks_df = self.get_ticks(
            symbol=symbol,
            exchange=exchange,
            from_date=from_date,
            to_date=to_date,
            days_back=days_back
        )
        
        if ticks_df.empty:
            return pd.DataFrame()
        
        # Resample to OHLC
        try:
            # Extract price column
            price_series = ticks_df['price']
            
            # Resample to desired interval
            ohlc = price_series.resample(interval).ohlc()
            
            # Add volume if available
            if 'volume' in ticks_df.columns:
                volume = ticks_df['volume'].resample(interval).sum()
                ohlc['volume'] = volume
            
            # Drop rows with NaN values
            ohlc = ohlc.dropna()
            
            print(f"✓ Converted {len(ticks_df)} ticks to {len(ohlc)} {interval} candles")
            return ohlc
            
        except Exception as e:
            print(f"✗ Error converting ticks to candles: {str(e)}")
            return pd.DataFrame()
    
    def get_historical_ohlc(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: str = "5min",
        days_back: int = 12
    ) -> pd.DataFrame:
        """
        Convenience method to get historical OHLC from ticks
        
        Args:
            symbol: Trading symbol
            exchange: Exchange
            interval: Candle interval
            days_back: Days to look back
            
        Returns:
            DataFrame with OHLC data
        """
        return self.ticks_to_candles(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            days_back=days_back
        )
    
    # ==================== DATABASE MAINTENANCE ====================
    
    def clear_old_data(self, days_to_keep: int = 30):
        """
        Clear tick data older than specified days
        
        Args:
            days_to_keep: Number of days to retain
        """
        with self.lock:
            cursor = self.connection.cursor()
            tables = self.get_all_tables()
            
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
            
            for table in tables:
                try:
                    query = f"DELETE FROM {table} WHERE ts < ?"
                    cursor.execute(query, (cutoff_date,))
                    deleted = cursor.rowcount
                    if deleted > 0:
                        print(f"  ✓ Deleted {deleted} old ticks from {table}")
                except Exception as e:
                    print(f"  ✗ Error clearing {table}: {str(e)}")
            
            try:
                self.connection.commit()
                print(f"✓ Cleared data older than {days_to_keep} days")
            except Exception as e:
                self.connection.rollback()
                print(f"✗ Failed to commit cleanup: {str(e)}")
    
    def get_database_size(self) -> Dict:
        """Get database statistics"""
        cursor = self.connection.cursor()
        
        tables = self.get_all_tables()
        stats = {
            'total_tables': len(tables),
            'table_stats': {}
        }
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT MIN(ts), MAX(ts) FROM {table}")
            date_range = cursor.fetchone()
            
            stats['table_stats'][table] = {
                'tick_count': count,
                'from_date': date_range[0],
                'to_date': date_range[1]
            }
        
        return stats


# Global singleton instance
tick_storage_service = TickStorageService()
