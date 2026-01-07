"""
Paper Trading API Endpoints
Provides portfolio, funds, and trade history for paper trading
**USER-AWARE**: Each user sees only their own paper trading data
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Optional
from pydantic import BaseModel
from app.services.paper_trading import PAPER_TRADING_MODE
from app.services.multi_user_paper_trading import multi_user_paper_manager
from app.services.tick_processor import tick_processor
from app.services.kite_auth import kite_auth_service
from app.utils.auth_utils import get_session_token

router = APIRouter()

class ManualTradeRequest(BaseModel):
    symbol: str
    action: str = "BUY"
    quantity: int = 1
    price: Optional[float] = None
    strategy: str = "MANUAL"


def get_user_paper_engine(session_token: Optional[str] = Depends(get_session_token)):
    """
    Get paper trading engine for the authenticated user
    """
    try:
        # Get user profile to extract user_id
        user_profile = kite_auth_service.get_user_profile(session_token)
        user_id = user_profile.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in session")
        
        # Get or create engine for this user
        return multi_user_paper_manager.get_engine(user_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.get("/portfolio")
async def get_paper_portfolio(paper_engine = Depends(get_user_paper_engine)):
    """
    Get complete paper trading portfolio for the authenticated user
    
    Returns:
        - paper_funds: Virtual capital, available, invested, realized P&L
        - paper_portfolio: Current holdings with live unrealized P&L
        - statistics: Overall metrics
    """
    try:
        if not PAPER_TRADING_MODE:
            raise HTTPException(
                status_code=400,
                detail="Paper trading mode is disabled. This endpoint is only available in paper trading mode."
            )
        
        portfolio = paper_engine.get_portfolio()
        
        return {
            "status": "success",
            "portfolio": portfolio
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades")
async def get_trade_history(paper_engine = Depends(get_user_paper_engine)):
    """
    Get paper trading history for the authenticated user
    
    Returns all completed buy/sell trades with timestamps, prices, and P&L
    """
    try:
        if not PAPER_TRADING_MODE:
            raise HTTPException(
                status_code=400,
                detail="Paper trading mode is disabled. This endpoint is only available in paper trading mode."
            )
        
        trades = paper_engine.get_trade_history()
        
        return {
            "status": "success",
            "trades": trades,
            "total_trades": len(trades)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(paper_engine = Depends(get_user_paper_engine)):
    """
    Get complete paper trading history for the authenticated user (alias for /trades)
    
    Returns all completed buy/sell trades with timestamps, prices, and P&L
    Simple endpoint name for easy access
    """
    try:
        if not PAPER_TRADING_MODE:
            raise HTTPException(
                status_code=400,
                detail="Paper trading mode is disabled. This endpoint is only available in paper trading mode."
            )
        
        trades = paper_engine.get_trade_history()
        
        return {
            "status": "success",
            "history": trades,
            "total_trades": len(trades)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/funds")
async def get_paper_funds(paper_engine = Depends(get_user_paper_engine)):
    """
    Get paper trading funds summary for the authenticated user
    
    Returns:
        Virtual capital, available, invested, and P&L breakdown
    """
    try:
        if not PAPER_TRADING_MODE:
            raise HTTPException(
                status_code=400,
                detail="Paper trading mode is disabled. This endpoint is only available in paper trading mode."
            )
        
        portfolio = paper_engine.get_portfolio()
        
        return {
            "status": "success",
            "funds": portfolio["paper_funds"],
            "statistics": portfolio["statistics"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_performance_stats(paper_engine = Depends(get_user_paper_engine)):
    """
    Get performance statistics for the authenticated user
    
    Returns:
        Win rate, avg profit/loss, best/worst trades, profit factor
    """
    try:
        if not PAPER_TRADING_MODE:
            raise HTTPException(
                status_code=400,
                detail="Paper trading mode is disabled. This endpoint is only available in paper trading mode."
            )
        
        stats = paper_engine.get_performance_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_paper_portfolio(paper_engine = Depends(get_user_paper_engine)):
    """
    Reset paper trading portfolio to initial state for the authenticated user
    
    WARNING: This will clear all positions and reset funds to ₹1,00,000
    """
    try:
        if not PAPER_TRADING_MODE:
            raise HTTPException(
                status_code=400,
                detail="Paper trading mode is disabled. This endpoint is only available in paper trading mode."
            )
        
        # Reset to initial state
        paper_engine.VIRTUAL_CAPITAL = 100000.0
        paper_engine.available_funds = 100000.0
        paper_engine.invested_funds = 0.0
        paper_engine.reserved_funds = 0.0
        paper_engine.realized_pnl = 0.0
        paper_engine.daily_pnl = 0.0
        paper_engine.total_pnl = 0.0
        paper_engine.trades_today = 0
        
        paper_engine.orders.clear()
        paper_engine.positions.clear()
        paper_engine.trades.clear()
        
        # Save to database
        paper_engine._save_meta()
        
        return {
            "status": "success",
            "message": "Paper portfolio reset to ₹1,00,000",
            "funds": {
                "virtual_capital": paper_engine.VIRTUAL_CAPITAL,
                "available_funds": paper_engine.available_funds,
                "invested_funds": paper_engine.invested_funds,
                "realized_pnl": paper_engine.realized_pnl
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-trade")
async def place_test_trade(paper_engine = Depends(get_user_paper_engine)):
    """
    Place a test trade to verify dashboard functionality for the authenticated user
    """
    try:
        if not PAPER_TRADING_MODE:
            raise HTTPException(status_code=400, detail="Paper trading is disabled")
            
        # Place a mock BUY order for RELIANCE
        import random
        price = 2500.0 + random.uniform(-10, 10)
        
        order_id = paper_engine.place_order(
            tradingsymbol="RELIANCE",
            exchange="NSE",
            transaction_type="BUY",
            quantity=10,
            order_type="MARKET",
            product="MIS",
            price=price,
            tag="TEST_TRADE"
        )
        
        return {
            "status": "success",
            "message": f"Test trade placed: {order_id}",
            "order_id": order_id,
            "details": f"Bought 10 RELIANCE @ {price:.2f}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual-trade")
async def place_manual_trade(trade: ManualTradeRequest, paper_engine = Depends(get_user_paper_engine)):
    """
    Place a manual paper trade for the authenticated user
    """
    try:
        if not PAPER_TRADING_MODE:
            raise HTTPException(status_code=400, detail="Paper trading is disabled")
            
        # Upper case symbol and action
        symbol = trade.symbol.upper()
        action = trade.action.upper()
        
        # Place order
        print(f"Manual trade request: {symbol} {action} {trade.quantity}")
        
        # Ensure we are subscribed to ticks for this symbol so P&L updates
        try:
            tick_processor.subscribe_symbol(symbol, "NSE")
        except Exception as e:
            print(f"Warning: Could not subscribe to {symbol} ticks: {e}")

        order_id = paper_engine.place_order(
            tradingsymbol=symbol,
            exchange="NSE",
            transaction_type=action,
            quantity=trade.quantity,
            order_type="MARKET",
            product="MIS",
            price=trade.price,
            tag=trade.strategy
        )
        
        return {
            "status": "success",
            "message": f"Manual trade placed: {order_id}",
            "order_id": order_id,
            "details": f"{action} {trade.quantity} {symbol}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
