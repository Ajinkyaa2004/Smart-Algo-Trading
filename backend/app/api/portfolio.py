"""
Portfolio & Account API Routes
Endpoints for user profile, holdings, positions, orders, margins, and GTT
**USER-AWARE**: Each user sees only their own data
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from app.services.kite_auth import kite_auth_service
from app.utils.auth_utils import get_session_token

router = APIRouter()


@router.get("/profile")
async def get_user_profile(session_token: Optional[str] = Depends(get_session_token)):
    """
    Get user profile information
    
    Returns:
        User profile data for the authenticated user
    """
    try:
        kite = kite_auth_service.get_kite_instance(session_token)
        profile = kite.profile()
        
        return {
            "status": "success",
            "data": profile
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holdings")
async def get_holdings(session_token: Optional[str] = Depends(get_session_token)):
    """
    Get user's stock holdings (portfolio)
    
    Returns:
        List of holdings with P&L for the authenticated user
    """
    try:
        kite = kite_auth_service.get_kite_instance(session_token)
        holdings = kite.holdings()
        
        return {
            "status": "success",
            "data": holdings,
            "count": len(holdings)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(session_token: Optional[str] = Depends(get_session_token)):
    """
    Get current positions (open trades)
    
    Returns:
        Net and day positions with P&L for the authenticated user
    """
    try:
        kite = kite_auth_service.get_kite_instance(session_token)
        positions = kite.positions()
        
        return {
            "status": "success",
            "data": positions,
            "net_count": len(positions.get('net', [])),
            "day_count": len(positions.get('day', []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(session_token: Optional[str] = Depends(get_session_token)):
    """
    Get order history
    
    Returns:
        List of all orders for the authenticated user
    """
    try:
        kite = kite_auth_service.get_kite_instance(session_token)
        orders = kite.orders()
        
        return {
            "status": "success",
            "data": orders,
            "count": len(orders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/margins")
async def get_margins(session_token: Optional[str] = Depends(get_session_token)):
    """
    Get account margins (balance)
    
    Returns:
        Margin details for all segments for the authenticated user
    """
    try:
        kite = kite_auth_service.get_kite_instance(session_token)
        margins = kite.margins()
        
        return {
            "status": "success",
            "data": margins
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/margins/{segment}")
async def get_segment_margins(segment: str, session_token: Optional[str] = Depends(get_session_token)):
    """
    Get margins for specific segment
    
    Args:
        segment: 'equity' or 'commodity'
        
    Returns:
        Segment margin details for the authenticated user
    """
    try:
        kite = kite_auth_service.get_kite_instance(session_token)
        margins = kite.margins(segment)
        
        return {
            "status": "success",
            "data": margins
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gtt")
async def get_gtt_orders(session_token: Optional[str] = Depends(get_session_token)):
    """
    Get GTT (Good Till Triggered) orders
    
    Returns:
        List of GTT orders for the authenticated user
    """
    try:
        kite = kite_auth_service.get_kite_instance(session_token)
        gtt = kite.get_gtts()
        
        return {
            "status": "success",
            "data": gtt,
            "count": len(gtt)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
