"""
Technical Indicators API Routes
Endpoints for calculating technical indicators on historical data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.services.market_data import market_data_service
from app.services.indicators import TechnicalIndicators

router = APIRouter()


# ==================== REQUEST MODELS ====================

class IndicatorRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    from_date: str  # YYYY-MM-DD
    to_date: str  # YYYY-MM-DD
    interval: str = "day"
    indicators: list[str]  # List of indicator names


# ==================== CALCULATE INDICATORS ====================

@router.get("/available")
async def get_available_indicators():
    """
    Get list of available technical indicators
    
    Returns:
        List of indicator names and descriptions
    """
    return {
        "status": "success",
        "count": len(TechnicalIndicators.get_available_indicators()),
        "indicators": TechnicalIndicators.get_available_indicators()
    }


@router.post("/calculate")
async def calculate_indicators(request: IndicatorRequest):
    """
    Calculate technical indicators on historical data
    
    Args:
        request: Indicator calculation request
        
    Returns:
        Historical data with indicators
    """
    try:
        # Fetch historical data
        from_date = datetime.strptime(request.from_date, "%Y-%m-%d")
        to_date = datetime.strptime(request.to_date, "%Y-%m-%d")
        
        df = market_data_service.get_historical_data_by_symbol(
            symbol=request.symbol,
            exchange=request.exchange,
            from_date=from_date,
            to_date=to_date,
            interval=request.interval
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available for the specified period")
        
        # Calculate requested indicators
        for indicator in request.indicators:
            indicator_lower = indicator.lower()
            
            if indicator_lower == "sma_20":
                df['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
            elif indicator_lower == "sma_50":
                df['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
            elif indicator_lower == "ema_9":
                df['ema_9'] = TechnicalIndicators.ema(df['close'], 9)
            elif indicator_lower == "ema_21":
                df['ema_21'] = TechnicalIndicators.ema(df['close'], 21)
            elif indicator_lower == "rsi":
                df['rsi'] = TechnicalIndicators.rsi_ema(df['close'], 14)
            elif indicator_lower == "macd":
                macd, signal, hist = TechnicalIndicators.macd(df['close'])
                df['macd'] = macd
                df['macd_signal'] = signal
                df['macd_hist'] = hist
            elif indicator_lower == "bollinger":
                upper, middle, lower = TechnicalIndicators.bollinger_bands(df['close'])
                df['bb_upper'] = upper
                df['bb_middle'] = middle
                df['bb_lower'] = lower
            elif indicator_lower == "vwap":
                df['vwap'] = TechnicalIndicators.vwap(df)
            elif indicator_lower == "atr":
                df['atr'] = TechnicalIndicators.atr(df, 14)
            elif indicator_lower == "stochastic":
                k, d = TechnicalIndicators.stochastic(df)
                df['stoch_k'] = k
                df['stoch_d'] = d
            elif indicator_lower == "adx":
                adx, plus_di, minus_di = TechnicalIndicators.adx(df)
                df['adx'] = adx
                df['plus_di'] = plus_di
                df['minus_di'] = minus_di
            elif indicator_lower == "supertrend":
                df['supertrend'] = TechnicalIndicators.supertrend(df)
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        
        # Replace NaN with None for JSON serialization
        df_reset = df_reset.where(df_reset.notna(), None)
        
        records = df_reset.to_dict('records')
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "exchange": request.exchange,
            "interval": request.interval,
            "indicators": request.indicators,
            "count": len(records),
            "data": records
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calculate/all")
async def calculate_all_indicators(
    symbol: str,
    exchange: str = "NSE",
    days: int = Query(100, description="Number of days of data"),
    interval: str = "day"
):
    """
    Calculate all common indicators on historical data
    
    Args:
        symbol: Trading symbol
        exchange: Exchange
        days: Number of days of historical data
        interval: Candle interval
        
    Returns:
        Historical data with all indicators
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
            raise HTTPException(status_code=404, detail="No data available")
        
        # Add all indicators
        df = TechnicalIndicators.add_all_indicators(df)
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        df_reset = df_reset.where(df_reset.notna(), None)
        
        records = df_reset.to_dict('records')
        
        return {
            "status": "success",
            "symbol": symbol,
            "exchange": exchange,
            "interval": interval,
            "days": days,
            "count": len(records),
            "indicators": ["sma_20", "sma_50", "sma_200", "ema_9", "ema_21", "rsi", "macd", "bollinger", "atr", "vwap"],
            "data": records
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rsi")
async def get_rsi(
    symbol: str,
    exchange: str = "NSE",
    days: int = 30,
    period: int = 14
):
    """
    Calculate RSI for a symbol
    
    Args:
        symbol: Trading symbol
        exchange: Exchange
        days: Number of days of data
        period: RSI period
        
    Returns:
        RSI values
    """
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        df = market_data_service.get_historical_data_by_symbol(
            symbol=symbol,
            exchange=exchange,
            from_date=from_date,
            to_date=to_date,
            interval="day"
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        df['rsi'] = TechnicalIndicators.rsi_ema(df['close'], period)
        
        # Get latest value
        latest_rsi = df['rsi'].iloc[-1]
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        df_reset = df_reset[['date', 'close', 'rsi']].where(df_reset.notna(), None)
        
        return {
            "status": "success",
            "symbol": symbol,
            "latest_rsi": latest_rsi,
            "period": period,
            "data": df_reset.to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macd")
async def get_macd(
    symbol: str,
    exchange: str = "NSE",
    days: int = 60
):
    """
    Calculate MACD for a symbol
    
    Args:
        symbol: Trading symbol
        exchange: Exchange
        days: Number of days of data
        
    Returns:
        MACD values
    """
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        df = market_data_service.get_historical_data_by_symbol(
            symbol=symbol,
            exchange=exchange,
            from_date=from_date,
            to_date=to_date,
            interval="day"
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        macd, signal, hist = TechnicalIndicators.macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist
        
        # Get latest values
        latest = {
            "macd": df['macd'].iloc[-1],
            "signal": df['macd_signal'].iloc[-1],
            "histogram": df['macd_hist'].iloc[-1]
        }
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        df_reset = df_reset[['date', 'close', 'macd', 'macd_signal', 'macd_hist']].where(df_reset.notna(), None)
        
        return {
            "status": "success",
            "symbol": symbol,
            "latest": latest,
            "data": df_reset.to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
