"""
Backtesting API Endpoints
Provides REST API for running backtests and retrieving results
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import asdict

from app.services.backtesting import backtesting_service


router = APIRouter(prefix="/api/backtest", tags=["backtesting"])


class BacktestRequest(BaseModel):
    """Request model for running a backtest"""
    symbol: str
    exchange: str = "NSE"
    strategy_type: str  # supertrend, ema_rsi, renko_macd
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    interval: str = "15minute"  # minute, 3minute, 5minute, 15minute, 30minute, 60minute, day
    initial_capital: float = 100000.0
    strategy_params: Optional[Dict] = None


class BacktestResponse(BaseModel):
    """Response model for backtest results"""
    status: str
    message: str
    backtest_id: Optional[str] = None
    result: Optional[Dict] = None


@router.post("/run")
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest on historical data
    
    This endpoint fetches REAL historical data from Kite Connect API
    and simulates the strategy execution to provide accurate performance metrics.
    """
    try:
        # Parse dates
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        # Validate dates
        if start_date >= end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before end date"
            )
        
        if end_date > datetime.now():
            raise HTTPException(
                status_code=400,
                detail="End date cannot be in the future"
            )
        
        # Validate strategy type
        valid_strategies = ['supertrend', 'ema_rsi', 'renko_macd', 'orb', 'ema_scalping', 'breakout', 'pattern']
        if request.strategy_type not in valid_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy type. Must be one of: {', '.join(valid_strategies)}"
            )
        
        # Run backtest
        result = backtesting_service.run_backtest(
            symbol=request.symbol,
            exchange=request.exchange,
            strategy_type=request.strategy_type,
            start_date=start_date,
            end_date=end_date,
            interval=request.interval,
            initial_capital=request.initial_capital,
            strategy_params=request.strategy_params
        )
        
        # Convert result to dict
        result_dict = {
            'backtest_id': result.backtest_id,
            'strategy_type': result.strategy_type,
            'symbol': result.symbol,
            'start_date': result.start_date,
            'end_date': result.end_date,
            'interval': result.interval,
            'initial_capital': result.initial_capital,
            'final_capital': result.final_capital,
            'metrics': asdict(result.metrics),
            'trades': [asdict(trade) for trade in result.trades],
            'equity_curve': result.equity_curve,
            'strategy_params': result.strategy_params,
            'total_candles': result.total_candles,
            'execution_time': result.execution_time,
            'created_at': result.created_at
        }
        
        return {
            "status": "success",
            "message": f"Backtest completed successfully. {result.metrics.total_trades} trades executed.",
            "backtest_id": result.backtest_id,
            "result": result_dict
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backtest failed: {str(e)}"
        )


@router.get("/result/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """
    Get backtest result by ID
    """
    try:
        result = backtesting_service.get_result(backtest_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Backtest result not found: {backtest_id}"
            )
        
        # Convert result to dict
        result_dict = {
            'backtest_id': result.backtest_id,
            'strategy_type': result.strategy_type,
            'symbol': result.symbol,
            'start_date': result.start_date,
            'end_date': result.end_date,
            'interval': result.interval,
            'initial_capital': result.initial_capital,
            'final_capital': result.final_capital,
            'metrics': asdict(result.metrics),
            'trades': [asdict(trade) for trade in result.trades],
            'equity_curve': result.equity_curve,
            'strategy_params': result.strategy_params,
            'total_candles': result.total_candles,
            'execution_time': result.execution_time,
            'created_at': result.created_at
        }
        
        return {
            "status": "success",
            "result": result_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve backtest result: {str(e)}"
        )


@router.get("/history")
async def get_backtest_history():
    """
    Get all backtest results
    """
    try:
        results = backtesting_service.get_all_results()
        
        # Convert to summary format
        history = []
        for result in results:
            history.append({
                'backtest_id': result.backtest_id,
                'strategy_type': result.strategy_type,
                'symbol': result.symbol,
                'start_date': result.start_date,
                'end_date': result.end_date,
                'interval': result.interval,
                'total_trades': result.metrics.total_trades,
                'win_rate': result.metrics.win_rate,
                'total_pnl': result.metrics.total_pnl,
                'total_pnl_percent': result.metrics.total_pnl_percent,
                'profit_factor': result.metrics.profit_factor,
                'max_drawdown_percent': result.metrics.max_drawdown_percent,
                'created_at': result.created_at
            })
        
        return {
            "status": "success",
            "count": len(history),
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve backtest history: {str(e)}"
        )


@router.get("/strategies")
async def get_available_strategies():
    """
    Get list of available strategies for backtesting
    """
    strategies = [
        {
            "type": "supertrend",
            "name": "Supertrend Strategy",
            "description": "Multi-timeframe supertrend with trailing stop-loss",
            "parameters": {
                "period": {"type": "int", "default": 10, "min": 5, "max": 20},
                "multiplier": {"type": "float", "default": 3.0, "min": 1.0, "max": 5.0}
            }
        },
        {
            "type": "ema_rsi",
            "name": "EMA + RSI Strategy",
            "description": "EMA crossover with RSI confirmation",
            "parameters": {
                "ema_fast": {"type": "int", "default": 9, "min": 5, "max": 20},
                "ema_slow": {"type": "int", "default": 21, "min": 15, "max": 50},
                "rsi_period": {"type": "int", "default": 14, "min": 10, "max": 20}
            }
        },
        {
            "type": "renko_macd",
            "name": "Renko + MACD Strategy",
            "description": "Renko bricks with MACD signals",
            "parameters": {
                "brick_size": {"type": "float", "default": 0.5, "min": 0.1, "max": 2.0},
                "macd_fast": {"type": "int", "default": 12, "min": 8, "max": 16},
                "macd_slow": {"type": "int", "default": 26, "min": 20, "max": 35}
            }
        },
        {
            "type": "orb",
            "name": "Opening Range Breakout (ORB)",
            "description": "Trades the breakout of the first N-minute candle",
            "parameters": {
                "range_minutes": {"type": "int", "default": 15, "min": 5, "max": 60},
                "sl_pct": {"type": "float", "default": 0.005, "min": 0.001, "max": 0.05},
                "target_pct": {"type": "float", "default": 0.01, "min": 0.005, "max": 0.1}
            }
        },
        {
            "type": "ema_scalping",
            "name": "EMA Scalping (9/21 EMA)",
            "description": "Classic crossover strategy for high-frequency scalping",
            "parameters": {
                "fast_period": {"type": "int", "default": 9, "min": 3, "max": 15},
                "slow_period": {"type": "int", "default": 21, "min": 10, "max": 50},
                "sl_pct": {"type": "float", "default": 0.005, "min": 0.001, "max": 0.05},
                "target_pct": {"type": "float", "default": 0.01, "min": 0.005, "max": 0.1}
            }
        },
        {
            "type": "breakout",
            "name": "Price Action Breakout",
            "description": "Trades breakouts from support/resistance levels with volume",
            "parameters": {
                "lookback_period": {"type": "int", "default": 20, "min": 10, "max": 100},
                "volume_multiplier": {"type": "float", "default": 1.2, "min": 1.0, "max": 3.0},
                "min_rr_ratio": {"type": "float", "default": 1.5, "min": 1.0, "max": 5.0}
            }
        },
        {
            "type": "pattern",
            "name": "Candlestick Pattern",
            "description": "Trades high-confidence candlestick patterns with trend confirmation",
            "parameters": {
                "min_confidence": {"type": "float", "default": 0.8, "min": 0.5, "max": 0.99},
                "trend_ema": {"type": "int", "default": 50, "min": 20, "max": 200},
                "min_rr_ratio": {"type": "float", "default": 2.0, "min": 1.0, "max": 5.0}
            }
        }
    ]
    
    return {
        "status": "success",
        "strategies": strategies
    }


@router.get("/intervals")
async def get_available_intervals():
    """
    Get list of available candle intervals for backtesting
    """
    intervals = [
        {"value": "minute", "label": "1 Minute", "recommended_for": "Scalping"},
        {"value": "3minute", "label": "3 Minutes", "recommended_for": "Scalping"},
        {"value": "5minute", "label": "5 Minutes", "recommended_for": "Intraday"},
        {"value": "15minute", "label": "15 Minutes", "recommended_for": "Intraday"},
        {"value": "30minute", "label": "30 Minutes", "recommended_for": "Swing Trading"},
        {"value": "60minute", "label": "1 Hour", "recommended_for": "Swing Trading"},
        {"value": "day", "label": "1 Day", "recommended_for": "Positional Trading"}
    ]
    
    return {
        "status": "success",
        "intervals": intervals
    }
