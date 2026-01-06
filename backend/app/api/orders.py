"""
Order Management API Routes
Endpoints for placing, modifying, canceling orders and fetching portfolio data
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.services.order_service import order_service

router = APIRouter()


# ==================== REQUEST MODELS ====================

class PlaceOrderRequest(BaseModel):
    tradingsymbol: str
    exchange: str
    transaction_type: str  # BUY or SELL
    quantity: int
    order_type: str = "MARKET"  # MARKET, LIMIT, SL, SL-M
    product: str = "MIS"  # CNC, MIS, NRML
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    validity: str = "DAY"
    tag: Optional[str] = None


class ModifyOrderRequest(BaseModel):
    order_id: str
    quantity: Optional[int] = None
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    order_type: Optional[str] = None
    validity: Optional[str] = None


class ConvertPositionRequest(BaseModel):
    tradingsymbol: str
    exchange: str
    transaction_type: str
    position_type: str  # day or overnight
    quantity: int
    old_product: str
    new_product: str


class PlaceBracketOrderRequest(BaseModel):
    tradingsymbol: str
    exchange: str
    transaction_type: str  # BUY or SELL
    quantity: int
    price: float  # Limit price (required for bracket orders)
    squareoff: int  # Target profit in absolute points
    stoploss: int  # Stop-loss in absolute points
    trailing_stoploss: Optional[int] = None  # Trailing SL in ticks
    product: str = "MIS"  # Only MIS supported for BO
    tag: Optional[str] = None


# ==================== ORDER PLACEMENT ====================

@router.post("/place")
async def place_order(request: PlaceOrderRequest):
    """
    Place a new order
    
    Args:
        request: Order parameters
        
    Returns:
        Order ID
    """
    try:
        order_id = order_service.place_order(
            tradingsymbol=request.tradingsymbol,
            exchange=request.exchange,
            transaction_type=request.transaction_type,
            quantity=request.quantity,
            order_type=request.order_type,
            product=request.product,
            price=request.price,
            trigger_price=request.trigger_price,
            validity=request.validity,
            tag=request.tag
        )
        
        return {
            "status": "success",
            "message": "Order placed successfully",
            "order_id": order_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/place/market")
async def place_market_order(
    tradingsymbol: str,
    exchange: str,
    transaction_type: str,
    quantity: int,
    product: str = "MIS",
    tag: Optional[str] = None
):
    """
    Place a market order (convenience endpoint)
    
    Args:
        tradingsymbol: Trading symbol
        exchange: Exchange
        transaction_type: BUY or SELL
        quantity: Order quantity
        product: CNC, MIS, NRML
        tag: Custom tag
        
    Returns:
        Order ID
    """
    try:
        order_id = order_service.place_market_order(
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            transaction_type=transaction_type,
            quantity=quantity,
            product=product,
            tag=tag
        )
        
        return {
            "status": "success",
            "message": "Market order placed",
            "order_id": order_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/buy")
async def buy_order(
    symbol: str,
    quantity: int,
    exchange: str = "NSE",
    product: str = "MIS",
    tag: Optional[str] = "paper_trading"
):
    """
    Simple BUY endpoint for paper trading
    
    Places a market BUY order at current market price
    
    Args:
        symbol: Trading symbol (e.g., RELIANCE, INFY)
        quantity: Number of shares to buy
        exchange: Exchange (NSE, BSE, NFO)
        product: Product type (MIS, CNC, NRML)
        tag: Custom tag for tracking
        
    Returns:
        Order details with entry price and order ID
    """
    try:
        order_id = order_service.place_market_order(
            tradingsymbol=symbol,
            exchange=exchange,
            transaction_type="BUY",
            quantity=quantity,
            product=product,
            tag=tag
        )
        
        return {
            "status": "success",
            "message": f"Paper trade: BUY {quantity} {symbol}",
            "order_id": order_id,
            "details": {
                "symbol": symbol,
                "action": "BUY",
                "quantity": quantity,
                "exchange": exchange,
                "product": product,
                "tag": tag
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sell")
async def sell_order(
    symbol: str,
    quantity: int,
    exchange: str = "NSE",
    product: str = "MIS",
    tag: Optional[str] = "paper_trading"
):
    """
    Simple SELL endpoint for paper trading
    
    Places a market SELL order at current market price
    Calculates P&L automatically if closing a position
    
    Args:
        symbol: Trading symbol (e.g., RELIANCE, INFY)
        quantity: Number of shares to sell
        exchange: Exchange (NSE, BSE, NFO)
        product: Product type (MIS, CNC, NRML)
        tag: Custom tag for tracking
        
    Returns:
        Order details with exit price, P&L calculation
    """
    try:
        order_id = order_service.place_market_order(
            tradingsymbol=symbol,
            exchange=exchange,
            transaction_type="SELL",
            quantity=quantity,
            product=product,
            tag=tag
        )
        
        return {
            "status": "success",
            "message": f"Paper trade: SELL {quantity} {symbol}",
            "order_id": order_id,
            "details": {
                "symbol": symbol,
                "action": "SELL",
                "quantity": quantity,
                "exchange": exchange,
                "product": product,
                "tag": tag
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/place/bracket")
async def place_bracket_order(request: PlaceBracketOrderRequest):
    """
    Place a bracket order with automatic stop-loss and target
    
    Bracket orders (BO) are advanced intraday orders that automatically place:
    - Main order (limit order at specified price)
    - Target order (square-off at profit level)
    - Stop-loss order (exit at loss level)
    - Optional trailing stop-loss
    
    Args:
        request: Bracket order parameters
        
    Request Body:
        {
            "tradingsymbol": "RELIANCE",
            "exchange": "NSE",
            "transaction_type": "BUY",
            "quantity": 1,
            "price": 2550.0,
            "squareoff": 10,  # Target: +10 points (2560)
            "stoploss": 5,    # SL: -5 points (2545)
            "trailing_stoploss": 2,  # Optional: trailing by 2 ticks
            "product": "MIS",
            "tag": "my_strategy"
        }
        
    Returns:
        Order ID
        
    Example:
        # Place BO for NIFTY with ATR-based targets
        POST /api/orders/place/bracket
        {
            "tradingsymbol": "NIFTY25DECFUT",
            "exchange": "NFO",
            "transaction_type": "BUY",
            "quantity": 50,
            "price": 24500.0,
            "squareoff": 60,  # 6 * ATR of 10
            "stoploss": 30,   # 3 * ATR of 10
            "trailing_stoploss": 2
        }
    """
    try:
        order_id = order_service.place_bracket_order(
            tradingsymbol=request.tradingsymbol,
            exchange=request.exchange,
            transaction_type=request.transaction_type,
            quantity=request.quantity,
            price=request.price,
            squareoff=request.squareoff,
            stoploss=request.stoploss,
            trailing_stoploss=request.trailing_stoploss,
            product=request.product,
            tag=request.tag
        )
        
        return {
            "status": "success",
            "message": "Bracket order placed successfully",
            "order_id": order_id,
            "details": {
                "symbol": request.tradingsymbol,
                "type": request.transaction_type,
                "quantity": request.quantity,
                "entry_price": request.price,
                "target": f"+{request.squareoff} points",
                "stoploss": f"-{request.stoploss} points",
                "trailing_sl": f"{request.trailing_stoploss} ticks" if request.trailing_stoploss else "None"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ORDER MODIFICATION ====================

@router.put("/modify")
async def modify_order(request: ModifyOrderRequest):
    """
    Modify an existing order
    
    Args:
        request: Modification parameters
        
    Returns:
        Order ID
    """
    try:
        order_id = order_service.modify_order(
            order_id=request.order_id,
            quantity=request.quantity,
            price=request.price,
            trigger_price=request.trigger_price,
            order_type=request.order_type,
            validity=request.validity
        )
        
        return {
            "status": "success",
            "message": "Order modified successfully",
            "order_id": order_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ORDER CANCELLATION ====================

@router.delete("/cancel/{order_id}")
async def cancel_order(order_id: str, variety: str = "regular"):
    """
    Cancel an order
    
    Args:
        order_id: Order ID to cancel
        variety: Order variety
        
    Returns:
        Cancellation confirmation
    """
    try:
        result = order_service.cancel_order(order_id, variety)
        
        return {
            "status": "success",
            "message": "Order cancelled successfully",
            "order_id": order_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ORDER QUERIES ====================

@router.get("/orders")
async def get_orders():
    """
    Get all orders for the day
    
    Returns:
        List of orders
    """
    try:
        orders = order_service.get_orders()
        
        return {
            "status": "success",
            "count": len(orders),
            "orders": orders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}/history")
async def get_order_history(order_id: str):
    """
    Get order history (all modifications)
    
    Args:
        order_id: Order ID
        
    Returns:
        Order history
    """
    try:
        history = order_service.get_order_history(order_id)
        
        return {
            "status": "success",
            "order_id": order_id,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades")
async def get_trades():
    """
    Get all executed trades for the day
    
    Returns:
        List of trades
    """
    try:
        trades = order_service.get_trades()
        
        return {
            "status": "success",
            "count": len(trades),
            "trades": trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PORTFOLIO ====================

@router.get("/positions")
async def get_positions():
    """
    Get current positions (day and net)
    
    Returns:
        Positions data
    """
    try:
        positions = order_service.get_positions()
        
        return {
            "status": "success",
            "positions": positions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holdings")
async def get_holdings():
    """
    Get long-term holdings
    
    Returns:
        Holdings data
    """
    try:
        holdings = order_service.get_holdings()
        
        return {
            "status": "success",
            "count": len(holdings),
            "holdings": holdings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions/convert")
async def convert_position(request: ConvertPositionRequest):
    """
    Convert position product type (e.g., MIS to CNC)
    
    Args:
        request: Conversion parameters
        
    Returns:
        Conversion confirmation
    """
    try:
        result = order_service.convert_position(
            tradingsymbol=request.tradingsymbol,
            exchange=request.exchange,
            transaction_type=request.transaction_type,
            position_type=request.position_type,
            quantity=request.quantity,
            old_product=request.old_product,
            new_product=request.new_product
        )
        
        return {
            "status": "success",
            "message": "Position converted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
