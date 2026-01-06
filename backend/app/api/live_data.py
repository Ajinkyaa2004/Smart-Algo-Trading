"""
WebSocket & Live Data API Routes
Endpoints for managing real-time tick data and live candles
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
from pydantic import BaseModel
from app.services.tick_processor import tick_processor
from app.services.websocket_handler import websocket_handler
import json
from urllib.parse import unquote

router = APIRouter()


# ==================== REQUEST MODELS ====================

class StartTicksRequest(BaseModel):
    symbols: List[str]
    exchange: str = "NSE"
    mode: str = "full"  # ltp, quote, full


class SubscribeRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    mode: str = "full"


# ==================== TICK STREAMING ====================

@router.post("/start")
async def start_tick_stream(request: StartTicksRequest):
    """
    Start real-time tick streaming
    
    Args:
        request: Start request with symbols and mode
        
    Returns:
        Status message
    """
    try:
        tick_processor.start(
            symbols=request.symbols,
            exchange=request.exchange,
            mode=request.mode
        )
        
        return {
            "status": "success",
            "message": "Tick streaming started",
            "symbols": request.symbols,
            "mode": request.mode
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_tick_stream():
    """
    Stop real-time tick streaming
    
    Returns:
        Status message
    """
    try:
        tick_processor.stop()
        
        return {
            "status": "success",
            "message": "Tick streaming stopped"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscribe")
async def subscribe_symbol(request: SubscribeRequest):
    """
    Subscribe to additional symbol
    
    Args:
        request: Subscribe request
        
    Returns:
        Status message
    """
    try:
        tick_processor.subscribe_symbol(
            symbol=request.symbol,
            exchange=request.exchange,
            mode=request.mode
        )
        
        return {
            "status": "success",
            "message": f"Subscribed to {request.symbol}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unsubscribe/{symbol}")
async def unsubscribe_symbol(symbol: str):
    """
    Unsubscribe from symbol
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Status message
    """
    try:
        tick_processor.unsubscribe_symbol(symbol)
        
        return {
            "status": "success",
            "message": f"Unsubscribed from {symbol}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LIVE CANDLES ====================

@router.get("/candle/current/{symbol}")
async def get_current_candle(
    symbol: str,
    interval: str = "1min"
):
    """
    Get current (incomplete) candle
    
    Args:
        symbol: Trading symbol
        interval: Candle interval
        
    Returns:
        Current candle data
    """
    try:
        candle = tick_processor.get_current_candle(symbol, interval)
        
        if not candle:
            raise HTTPException(status_code=404, detail=f"No candle data for {symbol}")
        
        return {
            "status": "success",
            "symbol": symbol,
            "interval": interval,
            "candle": candle
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candles/{symbol}")
async def get_live_candles(
    symbol: str,
    interval: str = "1min",
    count: int = 100,
    include_current: bool = False
):
    """
    Get historical live candles
    
    Args:
        symbol: Trading symbol
        interval: Candle interval
        count: Number of candles
        include_current: Include current incomplete candle
        
    Returns:
        Candle data
    """
    try:
        df = tick_processor.get_candles(symbol, interval, count, include_current)
        
        if df.empty:
            return {
                "status": "success",
                "symbol": symbol,
                "interval": interval,
                "count": 0,
                "candles": []
            }
        
        # Convert to records
        df_reset = df.reset_index()
        df_reset['timestamp'] = df_reset['timestamp'].astype(str)
        candles = df_reset.to_dict('records')
        
        return {
            "status": "success",
            "symbol": symbol,
            "interval": interval,
            "count": len(candles),
            "candles": candles
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tick/latest/{symbol}")
async def get_latest_tick(symbol: str):
    """
    Get latest tick for symbol
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Latest tick data
    """
    try:
        tick = tick_processor.get_latest_tick(symbol)
        
        if not tick:
            raise HTTPException(status_code=404, detail=f"No tick data for {symbol}")
        
        return {
            "status": "success",
            "tick": tick
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATUS ====================

@router.get("/status")
async def get_status():
    """
    Get tick processor status
    
    Returns:
        Status information
    """
    try:
        status = tick_processor.get_status()
        
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WEBSOCKET ENDPOINT ====================

@router.websocket("/ws/ticks/{symbol:path}")
async def websocket_ticks(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time tick streaming
    
    Args:
        websocket: WebSocket connection
        symbol: Trading symbol (URL-decoded automatically)
    """
    # Decode symbol (handles spaces and special characters)
    decoded_symbol = unquote(symbol)
    print(f"WebSocket connection request for symbol: {decoded_symbol}")
    
    await websocket.accept()
    
    try:
        # Register callback for this symbol
        async def send_tick(tick):
            try:
                await websocket.send_json({
                    "type": "tick",
                    "symbol": decoded_symbol,
                    "data": tick
                })
            except:
                pass
        
        tick_processor.on_tick(decoded_symbol, send_tick)
        print(f"WebSocket connected for {decoded_symbol}")
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            try:
                data = await websocket.receive_text()
                
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for {decoded_symbol}")
                break
                
    except Exception as e:
        print(f"WebSocket error for {decoded_symbol}: {str(e)}")
    finally:
        await websocket.close()


@router.websocket("/ws/candles/{symbol:path}")
async def websocket_candles(
    websocket: WebSocket,
    symbol: str,
    interval: str = "1min"
):
    """
    WebSocket endpoint for real-time candle streaming
    
    Args:
        websocket: WebSocket connection
        symbol: Trading symbol (URL-decoded automatically)
        interval: Candle interval
    """
    # Decode symbol (handles spaces and special characters)
    decoded_symbol = unquote(symbol)
    print(f"WebSocket candle connection for: {decoded_symbol}, interval: {interval}")
    
    await websocket.accept()
    
    try:
        # Get instrument token
        if decoded_symbol not in tick_processor.instrument_map:
            await websocket.send_json({
                "type": "error",
                "message": f"Symbol {decoded_symbol} not subscribed"
            })
            await websocket.close()
            return
        
        token = tick_processor.instrument_map[decoded_symbol]
        
        # Register callback for candle close
        async def send_candle(instrument_token, candle):
            if instrument_token == token:
                try:
                    await websocket.send_json({
                        "type": "candle",
                        "symbol": decoded_symbol,
                        "interval": interval,
                        "data": candle.to_dict()
                    })
                except:
                    pass
        
        tick_processor.on_candle_close(interval, send_candle)
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()
