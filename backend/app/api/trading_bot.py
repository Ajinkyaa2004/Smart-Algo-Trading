"""
Trading Bot API Endpoints
Control and monitor automated trading bot
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.services.trading_bot import trading_bot
from app.services.market_hours import market_hours
from app.services.paper_trading import paper_engine
from app.config import DEFAULT_STRATEGY

router = APIRouter()


# ==================== REQUEST MODELS ====================

class StartBotRequest(BaseModel):
    symbols: List[str]
    strategy_type: str = DEFAULT_STRATEGY  # supertrend, ema_rsi, renko_macd
    capital_per_symbol: float = 3000.0
    enable_tick_storage: bool = False
    strategy_params: Optional[Dict] = None


class StopBotRequest(BaseModel):
    square_off_positions: bool = True


# ==================== BOT CONTROL ====================

@router.post("/start")
async def start_bot(request: StartBotRequest):
    """
    Start the trading bot
    
    Args:
        request: Bot start configuration
        
    Returns:
        Status and configuration
    """
    try:
        strategy_params = request.strategy_params or {}
        
        result = trading_bot.start(
            symbols=request.symbols,
            strategy_type=request.strategy_type,
            capital_per_symbol=request.capital_per_symbol,
            enable_tick_storage=request.enable_tick_storage,
            **strategy_params
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "status": "success",
            "message": result['message'],
            "bot_status": trading_bot.get_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_bot(request: StopBotRequest):
    """
    Stop the trading bot
    
    Args:
        request: Stop configuration
        
    Returns:
        Status
    """
    try:
        result = trading_bot.stop(
            square_off_positions=request.square_off_positions
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "status": "success",
            "message": result['message'],
            "square_off": result.get('square_off')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause")
async def pause_bot():
    """Pause the trading bot (stop generating new signals)"""
    try:
        result = trading_bot.pause()
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "status": "success",
            "message": result['message']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume")
async def resume_bot():
    """Resume the trading bot"""
    try:
        result = trading_bot.resume()
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "status": "success",
            "message": result['message']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BOT STATUS ====================

@router.get("/status")
async def get_bot_status():
    """
    Get current bot status and statistics
    
    Returns:
        Bot status, strategies, positions, and statistics
    """
    try:
        return {
            "status": "success",
            "bot": trading_bot.get_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_bot_positions():
    """
    Get active bot positions
    
    Returns:
        Active positions managed by bot
    """
    try:
        return {
            "status": "success",
            "positions": trading_bot.get_positions()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def get_available_strategies():
    """
    Get list of available trading strategies
    
    Returns:
        Available strategy types and their parameters
    """
    return {
        "status": "success",
        "strategies": [
            {
                "type": "supertrend",
                "name": "Supertrend Strategy",
                "description": "Multi-timeframe supertrend with trailing stop-loss",
                "parameters": {
                    "st1_period": {"type": "int", "default": 7, "description": "ST1 period"},
                    "st1_multiplier": {"type": "float", "default": 3.0, "description": "ST1 multiplier"},
                    "st2_period": {"type": "int", "default": 10, "description": "ST2 period"},
                    "st2_multiplier": {"type": "float", "default": 3.0, "description": "ST2 multiplier"},
                    "st3_period": {"type": "int", "default": 11, "description": "ST3 period"},
                    "st3_multiplier": {"type": "float", "default": 2.0, "description": "ST3 multiplier"}
                }
            },
            {
                "type": "scalping",
                "name": "High-Frequency Scalping (Test)",
                "description": "Rapid testing strategy based on aggressive RSI thresholds",
                "parameters": {
                    "rsi_period": {"type": "int", "default": 7, "description": "RSI period (Fast)"},
                    "rsi_buy": {"type": "int", "default": 60, "description": "Buy Trigger (RSI < 60)"},
                    "rsi_sell": {"type": "int", "default": 40, "description": "Sell Trigger (RSI > 40)"}
                }
            },
            {
                "type": "orb",
                "name": "Opening Range Breakout (ORB)",
                "description": "Breaks the High/Low of the first N minutes range",
                "parameters": {
                    "range_minutes": {"type": "int", "default": 15, "description": "Opening Range (mins)"},
                    "sl_pct": {"type": "float", "default": 0.005, "description": "Stop Loss % (0.5%)"},
                    "target_pct": {"type": "float", "default": 0.01, "description": "Target % (1.0%)"}
                }
            },
            {
                "type": "ema_scalping",
                "name": "EMA Scalping (9/21)",
                "description": "Quick scalping on 9 EMA / 21 EMA Crossover",
                "parameters": {
                    "fast_period": {"type": "int", "default": 9, "description": "Fast EMA"},
                    "slow_period": {"type": "int", "default": 21, "description": "Slow EMA"},
                    "sl_pct": {"type": "float", "default": 0.005, "description": "Stop Loss %"},
                    "target_pct": {"type": "float", "default": 0.01, "description": "Target %"}
                }
            },
            {
                "type": "ema_rsi",
                "name": "EMA + RSI Strategy",
                "description": "EMA crossover with RSI confirmation",
                "parameters": {
                    "ema_fast": {"type": "int", "default": 9, "description": "Fast EMA period"},
                    "ema_slow": {"type": "int", "default": 21, "description": "Slow EMA period"},
                    "rsi_period": {"type": "int", "default": 14, "description": "RSI period"},
                    "rsi_overbought": {"type": "int", "default": 70, "description": "RSI overbought level"},
                    "rsi_oversold": {"type": "int", "default": 30, "description": "RSI oversold level"}
                }
            },
            {
                "type": "renko_macd",
                "name": "Renko + MACD Strategy",
                "description": "Renko brick analysis with MACD confirmation",
                "parameters": {
                    "renko_brick_threshold": {"type": "int", "default": 2, "description": "Minimum bricks for signal"},
                    "atr_period": {"type": "int", "default": 200, "description": "ATR period for brick size"},
                    "atr_multiplier": {"type": "float", "default": 1.5, "description": "ATR multiplier"},
                    "macd_fast": {"type": "int", "default": 12, "description": "MACD fast period"},
                    "macd_slow": {"type": "int", "default": 26, "description": "MACD slow period"},
                    "macd_signal": {"type": "int", "default": 9, "description": "MACD signal period"}
                }
            },
            {
                "type": "breakout",
                "name": "Breakout Strategy",
                "description": "Price action breakout with volume confirmation",
                "parameters": {
                    "lookback_period": {"type": "int", "default": 20, "description": "Lookback period for S/R levels"},
                    "volume_multiplier": {"type": "float", "default": 1.2, "description": "Volume confirmation multiplier"},
                    "min_rr_ratio": {"type": "float", "default": 1.5, "description": "Minimum risk-reward ratio"}
                }
            },
            {
                "type": "pattern",
                "name": "Pattern Strategy",
                "description": "Candlestick pattern confirmation with trend",
                "parameters": {
                    "min_confidence": {"type": "float", "default": 0.80, "description": "Minimum pattern confidence"},
                    "trend_ema": {"type": "int", "default": 50, "description": "Trend confirmation EMA period"},
                    "min_adx": {"type": "int", "default": 20, "description": "Minimum ADX for trend strength"},
                    "min_rr_ratio": {"type": "float", "default": 2.0, "description": "Minimum risk-reward ratio"}
                }
            }
        ]
    }


@router.get("/market-conditions")
async def get_market_conditions():
    """
    Get current market conditions and status
    
    Returns:
        Market status, session, timing, and trend information
    """
    try:
        market_status = market_hours.get_market_status()
        
        # Get paper trading stats for trend analysis
        stats = paper_engine.get_performance_stats()
        
        # Determine market trend based on recent performance
        trend = "NEUTRAL"
        if stats.get('total_trades', 0) > 0:
            win_rate = stats.get('win_rate', 0)
            if win_rate > 60:
                trend = "BULLISH"
            elif win_rate < 40:
                trend = "BEARISH"
        
        return {
            "status": "success",
            "market": {
                **market_status,
                "trend": trend,
                "is_tradable": market_hours.should_stream_data()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-metrics")
async def get_performance_metrics():
    """
    Get real-time performance metrics
    
    Returns:
        Win rate, P&L stats, best/worst trades, etc.
    """
    try:
        stats = paper_engine.get_performance_stats()
        portfolio = paper_engine.get_portfolio()
        
        # Calculate additional metrics
        total_trades = stats.get('total_trades', 0)
        winning_trades = stats.get('winning_trades', 0)
        losing_trades = stats.get('losing_trades', 0)
        
        win_rate = stats.get('win_rate', 0)
        loss_rate = (losing_trades / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = stats.get('avg_profit', 0)
        avg_loss = abs(stats.get('avg_loss', 0))
        
        profit_factor = stats.get('profit_factor', 0)
        
        # Get current streak (simplified - positive if last trade was win)
        current_streak = 0
        if total_trades > 0:
            if winning_trades > losing_trades:
                current_streak = 1
            elif losing_trades > winning_trades:
                current_streak = -1
        
        return {
            "status": "success",
            "metrics": {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "loss_rate": round(loss_rate, 2),
                "total_pnl": portfolio['statistics'].get('total_pnl', 0),
                "total_profit": stats.get('total_profit', 0),
                "total_loss": stats.get('total_loss', 0),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "largest_win": stats.get('best_trade', 0),
                "largest_loss": stats.get('worst_trade', 0),
                "current_streak": current_streak,
                "max_drawdown": 0  # TODO: Implement max drawdown tracking
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy-parameters/{strategy_type}")
async def get_strategy_parameters(strategy_type: str):
    """
    Get parameters for a specific strategy
    
    Args:
        strategy_type: Type of strategy (supertrend, ema_rsi, etc.)
        
    Returns:
        Strategy parameters with defaults and descriptions
    """
    try:
        # Get all strategies
        response = await get_available_strategies()
        strategies = response.get("strategies", [])
        
        # Find the requested strategy
        for strategy in strategies:
            if strategy["type"] == strategy_type:
                return {
                    "status": "success",
                    "strategy": strategy
                }
        
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_type}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
