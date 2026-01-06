"""
Market Data API Routes
Endpoints for instruments, quotes, OHLC, and historical data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta, time as dt_time
from pydantic import BaseModel
from app.services.market_data import market_data_service
from app.services.market_hours import market_hours
import pytz

router = APIRouter()


# ==================== REQUEST MODELS ====================

class HistoricalDataRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    from_date: str  # YYYY-MM-DD
    to_date: str  # YYYY-MM-DD
    interval: str = "day"  # minute, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute, day


class FetchOHLCRequest(BaseModel):
    """Request model for fetchOHLC convenience endpoint"""
    ticker: str
    interval: str = "5minute"  # minute, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute, day
    duration: int = 4  # Number of days
    exchange: str = "NSE"  # NSE, NFO, BSE


# ==================== MARKET STATUS ====================

@router.get("/status")
async def get_market_status():
    """
    Get current market status (OPEN/CLOSED/PRE-OPEN)
    
    NSE/BSE Trading Hours (IST):
    - Pre-market: 9:00 AM - 9:15 AM
    - Normal Trading: 9:15 AM - 3:30 PM
    - Post-market: 3:40 PM - 4:00 PM
    
    Market is closed on weekends and public holidays
    """
    try:
        # Use the new market_hours utility
        status = market_hours.get_market_status()
        
        return {
            "status": "success",
            "market_status": status["status"],
            "session": status.get("session", ""),
            "current_time": status.get("current_time", ""),
            "is_streaming_recommended": market_hours.should_stream_data(),
            **{k: v for k, v in status.items() if k not in ["status", "session", "current_time"]}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INSTRUMENTS ====================

@router.get("/instruments/{exchange}")
async def get_instruments(
    exchange: str = "NSE",
    force_refresh: bool = False
):
    """
    Fetch instruments master for an exchange
    
    Args:
        exchange: Exchange name (NSE, NFO, BSE, etc.)
        force_refresh: Force refresh from API
        
    Returns:
        List of instruments
    """
    try:
        df = market_data_service.fetch_instruments(exchange, force_refresh)
        
        # Convert to dict for JSON response
        instruments = df.to_dict('records')
        
        return {
            "status": "success",
            "exchange": exchange,
            "count": len(instruments),
            "instruments": instruments[:100]  # Limit response size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instruments/search/{query}")
async def search_instruments(
    query: str,
    exchange: str = Query("ALL", description="Exchange to search in (NSE, BSE, or ALL)")
):
    """
    Search for instruments by symbol or name across NSE and BSE
    
    Args:
        query: Search query (e.g., "RELIANCE", "NIFTY", "SENSEX")
        exchange: Exchange to search in (NSE, BSE, or ALL for both exchanges)
        
    Returns:
        Matching instruments from specified exchange(s)
    """
    try:
        results = market_data_service.search_instruments(query, exchange)
        
        return {
            "status": "success",
            "query": query,
            "exchange": exchange,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instruments/token/{symbol}")
async def get_instrument_token(
    symbol: str,
    exchange: str = Query("NSE")
):
    """
    Get instrument token for a symbol
    
    Args:
        symbol: Trading symbol
        exchange: Exchange
        
    Returns:
        Instrument token
    """
    try:
        token = market_data_service.get_instrument_token(symbol, exchange)
        
        if token is None:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found on {exchange}")
        
        return {
            "status": "success",
            "symbol": symbol,
            "exchange": exchange,
            "instrument_token": token
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== QUOTES & LTP ====================

@router.get("/prices")
async def get_prices(symbols: str = Query(..., description="Comma-separated symbols (e.g., NSE:RELIANCE,NSE:INFY)")):
    """
    Get latest market prices (LTP) for symbols - Simple endpoint for paper trading
    
    Args:
        symbols: Comma-separated symbols in format EXCHANGE:SYMBOL
                 Example: NSE:RELIANCE,NSE:INFY,BSE:SENSEX
        
    Returns:
        Latest prices with symbol, LTP, and timestamp
        
    Example:
        /api/market/prices?symbols=NSE:RELIANCE,NSE:INFY
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        ltp_data = market_data_service.get_ltp(symbol_list)
        
        # Format for simple consumption
        prices = {}
        for symbol_key, data in ltp_data.items():
            prices[symbol_key] = {
                "symbol": symbol_key,
                "last_price": data.get("last_price", 0),
                "timestamp": data.get("timestamp", "")
            }
        
        return {
            "status": "success",
            "count": len(prices),
            "prices": prices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ltp")
async def get_ltp(symbols: str = Query(..., description="Comma-separated symbols (e.g., NSE:RELIANCE,NSE:INFY)")):
    """
    Get Last Traded Price for symbols
    
    Args:
        symbols: Comma-separated symbols in format EXCHANGE:SYMBOL
        
    Returns:
        LTP data
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        ltp_data = market_data_service.get_ltp(symbol_list)
        
        return {
            "status": "success",
            "data": ltp_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote")
async def get_quote(symbols: str = Query(..., description="Comma-separated symbols")):
    """
    Get full quote (OHLC, volume, etc.) for symbols
    
    Args:
        symbols: Comma-separated symbols in format EXCHANGE:SYMBOL
        
    Returns:
        Quote data
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        quote_data = market_data_service.get_quote(symbol_list)
        
        return {
            "status": "success",
            "data": quote_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ohlc")
async def get_ohlc(symbols: str = Query(..., description="Comma-separated symbols")):
    """
    Get OHLC data for symbols
    
    Args:
        symbols: Comma-separated symbols in format EXCHANGE:SYMBOL
        
    Returns:
        OHLC data
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        ohlc_data = market_data_service.get_ohlc(symbol_list)
        
        return {
            "status": "success",
            "data": ohlc_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HISTORICAL DATA ====================

@router.post("/historical")
async def get_historical_data(request: HistoricalDataRequest):
    """
    Fetch historical candle data
    
    Args:
        request: Historical data request parameters
        
    Returns:
        Historical OHLCV data
    """
    try:
        # Parse dates
        from_date = datetime.strptime(request.from_date, "%Y-%m-%d")
        to_date = datetime.strptime(request.to_date, "%Y-%m-%d")
        
        # Fetch data
        df = market_data_service.get_historical_data_by_symbol(
            symbol=request.symbol,
            exchange=request.exchange,
            from_date=from_date,
            to_date=to_date,
            interval=request.interval
        )
        
        if df.empty:
            return {
                "status": "success",
                "message": "No data available for the specified period",
                "data": []
            }
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        records = df_reset.to_dict('records')
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "exchange": request.exchange,
            "interval": request.interval,
            "from_date": request.from_date,
            "to_date": request.to_date,
            "count": len(records),
            "data": records
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical/quick")
async def get_historical_quick(
    symbol: str,
    exchange: str = "NSE",
    days: int = Query(30, description="Number of days of data"),
    interval: str = Query("day", description="Candle interval")
):
    """
    Quick historical data fetch (last N days)
    
    Args:
        symbol: Trading symbol
        exchange: Exchange
        days: Number of days of historical data
        interval: Candle interval
        
    Returns:
        Historical data
    """
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        df = market_data_service.get_historical_data_by_symbol(
            symbol=symbol,
            exchange=exchange,
            from_date=from_date,
            to_date=to_date,
            interval=interval
        )
        
        if df.empty:
            return {
                "status": "success",
                "message": "No data available",
                "data": []
            }
        
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        records = df_reset.to_dict('records')
        
        return {
            "status": "success",
            "symbol": symbol,
            "exchange": exchange,
            "interval": interval,
            "days": days,
            "count": len(records),
            "data": records
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NFO (FUTURES & OPTIONS) ====================

@router.get("/nfo/instruments")
async def get_nfo_instruments(force_refresh: bool = False):
    """
    Fetch all NFO (Futures & Options) instruments
    
    Args:
        force_refresh: Force refresh from API
        
    Returns:
        List of NFO instruments
    """
    try:
        df = market_data_service.fetch_nfo_instruments(force_refresh)
        
        # Convert to dict for JSON response
        instruments = df.to_dict('records')
        
        return {
            "status": "success",
            "exchange": "NFO",
            "count": len(instruments),
            "instruments": instruments[:100]  # Limit response size for performance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nfo/futures")
async def get_nfo_futures(
    underlying: Optional[str] = Query(None, description="Filter by underlying (e.g., NIFTY, BANKNIFTY, RELIANCE)")
):
    """
    Get all NFO futures contracts
    
    Args:
        underlying: Optional filter by underlying symbol
        
    Returns:
        List of futures contracts
    """
    try:
        df = market_data_service.get_nfo_futures(underlying)
        
        futures = df.to_dict('records')
        
        return {
            "status": "success",
            "segment": "NFO-FUT",
            "underlying": underlying,
            "count": len(futures),
            "data": futures
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nfo/options")
async def get_nfo_options(
    underlying: Optional[str] = Query(None, description="Filter by underlying (e.g., NIFTY, BANKNIFTY)"),
    option_type: Optional[str] = Query(None, description="Filter by option type (CE for Call, PE for Put)")
):
    """
    Get all NFO options contracts
    
    Args:
        underlying: Optional filter by underlying symbol
        option_type: Optional filter by option type (CE/PE)
        
    Returns:
        List of options contracts
    """
    try:
        df = market_data_service.get_nfo_options(underlying, option_type)
        
        options = df.to_dict('records')
        
        return {
            "status": "success",
            "segment": "NFO-OPT",
            "underlying": underlying,
            "option_type": option_type,
            "count": len(options),
            "data": options
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONVENIENCE ENDPOINTS ====================

@router.get("/instrument-lookup/{symbol}")
async def instrument_lookup(
    symbol: str,
    exchange: str = Query("NSE", description="Exchange (NSE, NFO, BSE)")
):
    """
    Look up instrument token for a symbol
    Similar to the instrumentLookup function in the reference code
    
    Args:
        symbol: Trading symbol (e.g., RELIANCE, NIFTY20MAYFUT)
        exchange: Exchange
        
    Returns:
        Instrument token
    """
    try:
        token = market_data_service.instrument_lookup(symbol, exchange)
        
        if token is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Symbol '{symbol}' not found on {exchange}"
            )
        
        return {
            "status": "success",
            "symbol": symbol,
            "exchange": exchange,
            "instrument_token": token
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetchOHLC")
async def fetch_ohlc(request: FetchOHLCRequest):
    """
    Convenience endpoint to fetch historical OHLC data
    Similar to the fetchOHLC function in the reference code
    
    Args:
        request: FetchOHLC request parameters
        
    Returns:
        Historical OHLC data
        
    Example:
        POST /market-data/fetchOHLC
        {
            "ticker": "NIFTY20MAYFUT",
            "interval": "5minute",
            "duration": 4,
            "exchange": "NFO"
        }
    """
    try:
        df = market_data_service.fetchOHLC(
            ticker=request.ticker,
            interval=request.interval,
            duration=request.duration,
            exchange=request.exchange
        )
        
        if df.empty:
            return {
                "status": "success",
                "message": "No data available for the specified period",
                "data": []
            }
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        records = df_reset.to_dict('records')
        
        return {
            "status": "success",
            "ticker": request.ticker,
            "exchange": request.exchange,
            "interval": request.interval,
            "duration": request.duration,
            "count": len(records),
            "data": records
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

