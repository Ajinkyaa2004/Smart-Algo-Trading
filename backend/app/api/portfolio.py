"""
Portfolio & Account API Routes
Endpoints for user profile, holdings, positions, orders, margins, and GTT
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.services.kite_auth import kite_auth_service

router = APIRouter()


@router.get("/profile")
async def get_user_profile():
    """
    Get user profile information
    
    Returns:
        User profile data
    """
    try:
        kite = kite_auth_service.get_kite_instance()
        profile = kite.profile()
        
        return {
            "status": "success",
            "data": profile
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holdings")
async def get_holdings():
    """
    Get user's stock holdings (portfolio)
    
    Returns:
        List of holdings with P&L
    """
    try:
        kite = kite_auth_service.get_kite_instance()
        holdings = kite.holdings()
        
        return {
            "status": "success",
            "data": holdings,
            "count": len(holdings)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions():
    """
    Get current positions (open trades)
    
    Returns:
        Net and day positions with P&L
    """
    try:
        kite = kite_auth_service.get_kite_instance()
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
async def get_orders():
    """
    Get order history
    
    Returns:
        List of all orders
    """
    try:
        kite = kite_auth_service.get_kite_instance()
        orders = kite.orders()
        
        return {
            "status": "success",
            "data": orders,
            "count": len(orders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/margins")
async def get_margins():
    """
    Get account margins (balance)
    
    Returns:
        Margin details for all segments
    """
    try:
        kite = kite_auth_service.get_kite_instance()
        margins = kite.margins()
        
        return {
            "status": "success",
            "data": margins
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/margins/{segment}")
async def get_segment_margins(segment: str):
    """
    Get margins for specific segment
    
    Args:
        segment: 'equity' or 'commodity'
        
    Returns:
        Segment margin details
    """
    try:
        kite = kite_auth_service.get_kite_instance()
        margins = kite.margins(segment)
        
        return {
            "status": "success",
            "data": margins
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gtt")
async def get_gtt_orders():
    """
    Get GTT (Good Till Triggered) orders
    
    Returns:
        List of GTT orders
    """
    try:
        kite = kite_auth_service.get_kite_instance()
        gtt = kite.get_gtts()
        
        return {
            "status": "success",
            "data": gtt,
            "count": len(gtt)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
