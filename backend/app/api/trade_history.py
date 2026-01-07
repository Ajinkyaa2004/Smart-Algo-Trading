"""
Trade History API Endpoints
Provides comprehensive trade history, analytics, and visualizations
**USER-AWARE**: Each user sees only their own trade history
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.services.trade_history import trade_history_service
from app.services.kite_auth import kite_auth_service
from app.utils.auth_utils import get_session_token

router = APIRouter()


def get_user_id(session_token: Optional[str] = Depends(get_session_token)) -> str:
    """
    Extract user ID from session token
    
    Returns:
        User ID string
    """
    try:
        user_profile = kite_auth_service.get_user_profile(session_token)
        user_id = user_profile.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in session")
        
        return user_id
    except Exception as e:
        print(f"❌ Auth Failed for token {session_token[:8] if session_token else 'None'}... : {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.get("/trades")
async def get_trade_history(
    user_id: str = Depends(get_user_id),
    limit: Optional[int] = Query(None, description="Maximum number of trades to return"),
    skip: int = Query(0, description="Number of trades to skip"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN/CLOSED)"),
    days: Optional[int] = Query(None, description="Filter by last N days")
):
    """
    Get trade history for the authenticated user
    
    Returns:
        List of trades with filters applied
    """
    try:
        # Calculate date range if days specified
        start_date = None
        if days:
            start_date = datetime.now() - timedelta(days=days)
        # ... build query and call service ...
        print(f"🕵️‍♀️ DEBUG API: Fetching trades for user_id: {user_id}")
        trades = await trade_history_service.get_user_trades(
            user_id=user_id,
            limit=limit,
            skip=skip,
            strategy=strategy,
            symbol=symbol,
            status=status,
            start_date=start_date
        )
        
        return {
            "status": "success",
            "trades": trades,
            "total": len(trades)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    user_id: str = Depends(get_user_id),
    days: Optional[int] = Query(None, description="Calculate stats for last N days")
):
    """
    Get comprehensive trade statistics for the authenticated user
    
    Returns:
        Statistics including win rate, P&L, best/worst trades, etc.
    """
    try:
        stats = await trade_history_service.get_trade_statistics(
            user_id=user_id,
            days=days
        )
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy-performance")
async def get_strategy_performance(user_id: str = Depends(get_user_id)):
    """
    Get performance breakdown by strategy for the authenticated user
    
    Returns:
        List of strategies with their performance metrics
    """
    try:
        strategies = await trade_history_service.get_strategy_performance(user_id=user_id)
        
        return {
            "status": "success",
            "strategies": strategies,
            "total": len(strategies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pnl-over-time")
async def get_pnl_over_time(
    user_id: str = Depends(get_user_id),
    days: int = Query(30, description="Number of days to look back"),
    interval: str = Query("daily", description="Interval: daily, weekly, or monthly")
):
    """
    Get P&L over time for charting
    
    Returns:
        Time series data with P&L and cumulative P&L
    """
    try:
        if interval not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Invalid interval. Use: daily, weekly, or monthly")
        
        pnl_data = await trade_history_service.get_pnl_over_time(
            user_id=user_id,
            days=days,
            interval=interval
        )
        
        return {
            "status": "success",
            "data": pnl_data,
            "interval": interval,
            "days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_history_summary(user_id: str = Depends(get_user_id)):
    """
    Get complete history summary including all metrics and visualizations
    
    Returns:
        Comprehensive summary with statistics, strategy performance, and P&L data
    """
    try:
        # Fetch all data in parallel
        stats = await trade_history_service.get_trade_statistics(user_id=user_id)
        strategies = await trade_history_service.get_strategy_performance(user_id=user_id)
        pnl_data = await trade_history_service.get_pnl_over_time(user_id=user_id, days=30)
        recent_trades = await trade_history_service.get_user_trades(user_id=user_id, limit=10)
        
        return {
            "status": "success",
            "summary": {
                "statistics": stats,
                "strategy_performance": strategies,
                "pnl_over_time": pnl_data,
                "recent_trades": recent_trades
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seed")
async def seed_data(user_id: str = Depends(get_user_id)):
    """Generate demo data for the current user"""
    try:
        result = await trade_history_service.seed_demo_data(user_id)
        return {
            "status": "success",
            "message": result["message"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
