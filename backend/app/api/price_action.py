"""
Price Action & Pattern Scanner API Routes
Endpoints for support/resistance, trend analysis, and pattern detection
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.services.market_data import market_data_service
from app.services.price_action import price_action_service
from app.services.pattern_scanner import pattern_scanner

router = APIRouter()


# ==================== REQUEST MODELS ====================

class PriceActionRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    from_date: str  # YYYY-MM-DD
    to_date: str  # YYYY-MM-DD
    interval: str = "day"


class PatternScanRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    from_date: str
    to_date: str
    interval: str = "day"
    patterns: Optional[List[str]] = None  # None = scan all


# ==================== SUPPORT & RESISTANCE ====================

@router.post("/support-resistance")
async def find_support_resistance(request: PriceActionRequest):
    """
    Detect support and resistance levels
    
    Args:
        request: Price action request parameters
        
    Returns:
        Support and resistance levels with strength
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
            raise HTTPException(status_code=404, detail="No data available")
        
        # Find support/resistance levels
        levels = price_action_service.find_support_resistance(df)
        
        # Convert to dict
        levels_dict = [
            {
                "level": level.level,
                "type": level.type,
                "strength": level.strength,
                "first_touch": level.first_touch,
                "last_touch": level.last_touch
            }
            for level in levels
        ]
        
        # Sort by strength
        levels_dict.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "count": len(levels_dict),
            "levels": levels_dict
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TREND ANALYSIS ====================

@router.post("/trend")
async def analyze_trend(
    request: PriceActionRequest,
    method: str = Query("ma", description="Trend method: 'ma' or 'highs_lows'")
):
    """
    Identify trend direction
    
    Args:
        request: Price action request
        method: Trend detection method
        
    Returns:
        Trend analysis with direction and strength
    """
    try:
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
            raise HTTPException(status_code=404, detail="No data available")
        
        # Identify trend
        trend = price_action_service.identify_trend(df, method=method)
        trend_strength = price_action_service.calculate_trend_strength(df)
        
        # Get latest values
        latest_trend = trend.iloc[-1]
        latest_strength = trend_strength.iloc[-1]
        
        trend_direction = "uptrend" if latest_trend == 1 else ("downtrend" if latest_trend == -1 else "sideways")
        
        # Add to dataframe
        df['trend'] = trend
        df['trend_strength'] = trend_strength
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        df_reset = df_reset[['date', 'close', 'trend', 'trend_strength']].tail(50)
        df_reset = df_reset.where(df_reset.notna(), None)
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "current_trend": trend_direction,
            "trend_strength": float(latest_strength) if not pd.isna(latest_strength) else None,
            "data": df_reset.to_dict('records')
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BREAKOUT DETECTION ====================

@router.post("/breakout")
async def detect_breakout(
    request: PriceActionRequest,
    level: float = Query(..., description="Price level to monitor"),
    direction: str = Query("up", description="Breakout direction: 'up' or 'down'")
):
    """
    Detect breakouts above/below a price level
    
    Args:
        request: Price action request
        level: Price level
        direction: Breakout direction
        
    Returns:
        Breakout points
    """
    try:
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
            raise HTTPException(status_code=404, detail="No data available")
        
        # Detect breakouts
        breakouts = price_action_service.detect_breakout(df, level, direction)
        
        # Get breakout points
        breakout_points = df[breakouts].copy()
        breakout_points = breakout_points.reset_index()
        breakout_points['date'] = breakout_points['date'].astype(str)
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "level": level,
            "direction": direction,
            "breakout_count": len(breakout_points),
            "breakouts": breakout_points[['date', 'open', 'high', 'low', 'close']].to_dict('records')
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CANDLESTICK ANATOMY ====================

@router.get("/candle-anatomy")
async def analyze_candle_anatomy(
    symbol: str,
    exchange: str = "NSE",
    days: int = Query(30, description="Number of days")
):
    """
    Analyze candlestick anatomy (body, wicks, range)
    
    Args:
        symbol: Trading symbol
        exchange: Exchange
        days: Number of days
        
    Returns:
        Candle anatomy data
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
        
        # Add anatomy columns
        df = price_action_service.add_candle_anatomy(df)
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['date'] = df_reset['date'].astype(str)
        df_reset = df_reset.where(df_reset.notna(), None)
        
        # Get latest candle anatomy
        latest = df.iloc[-1]
        latest_anatomy = {
            "body": float(latest['body']),
            "upper_wick": float(latest['upper_wick']),
            "lower_wick": float(latest['lower_wick']),
            "total_range": float(latest['total_range']),
            "body_percentage": float(latest['body_percentage']),
            "is_bullish": bool(latest['is_bullish']),
            "is_bearish": bool(latest['is_bearish']),
            "is_doji": bool(latest['is_doji'])
        }
        
        return {
            "status": "success",
            "symbol": symbol,
            "latest_anatomy": latest_anatomy,
            "data": df_reset.to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PATTERN SCANNER ====================

@router.post("/scan-patterns")
async def scan_patterns(request: PatternScanRequest):
    """
    Scan for candlestick patterns
    
    Args:
        request: Pattern scan request
        
    Returns:
        List of detected patterns with timestamp, symbol, pattern name
    """
    try:
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
            raise HTTPException(status_code=404, detail="No data available")
        
        # Scan for patterns
        matches = pattern_scanner.scan_patterns(
            df=df,
            symbol=request.symbol,
            patterns=request.patterns
        )
        
        # Convert to dict
        patterns_dict = [
            {
                "timestamp": match.timestamp,
                "symbol": match.symbol,
                "pattern": match.pattern,
                "direction": match.direction,
                "confidence": match.confidence,
                "price": match.price,
                "description": match.description
            }
            for match in matches
        ]
        
        return {
            "status": "success",
            "symbol": request.symbol,
            "patterns_found": len(patterns_dict),
            "patterns": patterns_dict
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan-latest")
async def scan_latest_patterns(
    symbol: str,
    exchange: str = "NSE",
    days: int = Query(30, description="Number of days to scan"),
    lookback: int = Query(10, description="Recent candles to check")
):
    """
    Scan recent candles for patterns
    
    Args:
        symbol: Trading symbol
        exchange: Exchange
        days: Days of historical data
        lookback: Recent candles to scan
        
    Returns:
        Recent pattern matches
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
        
        # Scan latest candles
        matches = pattern_scanner.scan_latest(df, symbol, lookback)
        
        patterns_dict = [
            {
                "timestamp": match.timestamp,
                "symbol": match.symbol,
                "pattern": match.pattern,
                "direction": match.direction,
                "confidence": match.confidence,
                "price": match.price,
                "description": match.description
            }
            for match in matches
        ]
        
        return {
            "status": "success",
            "symbol": symbol,
            "patterns_found": len(patterns_dict),
            "patterns": patterns_dict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-patterns")
async def get_available_patterns():
    """
    Get list of all available candlestick patterns
    
    Returns:
        List of pattern names and descriptions
    """
    patterns = [
        {
            "name": "doji",
            "display_name": "Doji",
            "type": "single",
            "direction": "neutral",
            "description": "Indecision candle, potential reversal"
        },
        {
            "name": "hammer",
            "display_name": "Hammer",
            "type": "single",
            "direction": "bullish",
            "description": "Bullish reversal with long lower wick"
        },
        {
            "name": "hanging_man",
            "display_name": "Hanging Man",
            "type": "single",
            "direction": "bearish",
            "description": "Bearish reversal in uptrend"
        },
        {
            "name": "shooting_star",
            "display_name": "Shooting Star",
            "type": "single",
            "direction": "bearish",
            "description": "Bearish reversal with long upper wick"
        },
        {
            "name": "bullish_engulfing",
            "display_name": "Bullish Engulfing",
            "type": "two_candle",
            "direction": "bullish",
            "description": "Strong bullish reversal pattern"
        },
        {
            "name": "bearish_engulfing",
            "display_name": "Bearish Engulfing",
            "type": "two_candle",
            "direction": "bearish",
            "description": "Strong bearish reversal pattern"
        },
        {
            "name": "piercing_line",
            "display_name": "Piercing Line",
            "type": "two_candle",
            "direction": "bullish",
            "description": "Bullish reversal pattern"
        },
        {
            "name": "dark_cloud_cover",
            "display_name": "Dark Cloud Cover",
            "type": "two_candle",
            "direction": "bearish",
            "description": "Bearish reversal pattern"
        },
        {
            "name": "morning_star",
            "display_name": "Morning Star",
            "type": "three_candle",
            "direction": "bullish",
            "description": "Strong bullish reversal (3-candle)"
        },
        {
            "name": "evening_star",
            "display_name": "Evening Star",
            "type": "three_candle",
            "direction": "bearish",
            "description": "Strong bearish reversal (3-candle)"
        }
    ]
    
    return {
        "status": "success",
        "count": len(patterns),
        "patterns": patterns
    }


# Import pandas for type hints
import pandas as pd
