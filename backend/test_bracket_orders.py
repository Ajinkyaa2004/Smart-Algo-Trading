"""
Test Bracket Order Functionality
Tests the implementation of bracket orders with stop-loss and targets

Run this script to test:
1. Place bracket order (simulated - won't execute on live market)
2. Demonstrate ATR-based bracket orders as in reference code

Note: This is a demonstration script. Actual order placement requires:
- Active Kite session
- Sufficient margin
- Market hours
"""

import sys
sys.path.append('.')

from app.services.order_service import order_service
from app.services.kite_auth import kite_auth_service


def test_bracket_order_basic():
    """Test basic bracket order placement"""
    print("\n" + "="*70)
    print("TEST 1: Basic Bracket Order")
    print("="*70)
    
    try:
        # Example: Buy RELIANCE with fixed targets
        order_params = {
            "tradingsymbol": "RELIANCE",
            "exchange": "NSE",
            "transaction_type": "BUY",
            "quantity": 1,
            "price": 2550.0,  # Entry price
            "squareoff": 10,  # Target: 2560 (10 points profit)
            "stoploss": 5,    # SL: 2545 (5 points loss)
            "trailing_stoploss": 2,  # Trailing by 2 ticks
            "product": "MIS",
            "tag": "test_bracket_order"
        }
        
        print("\n📋 Order Parameters:")
        print(f"  Symbol: {order_params['tradingsymbol']}")
        print(f"  Type: {order_params['transaction_type']}")
        print(f"  Quantity: {order_params['quantity']}")
        print(f"  Entry Price: ₹{order_params['price']}")
        print(f"  Target: +{order_params['squareoff']} points (₹{order_params['price'] + order_params['squareoff']})")
        print(f"  Stop Loss: -{order_params['stoploss']} points (₹{order_params['price'] - order_params['stoploss']})")
        print(f"  Trailing SL: {order_params['trailing_stoploss']} ticks")
        
        print("\n⚠️  This is a test - order placement commented out")
        print("    Uncomment the line below to place actual order")
        
        # UNCOMMENT TO PLACE ACTUAL ORDER (requires active session & margin)
        # order_id = order_service.place_bracket_order(**order_params)
        # print(f"\n✅ Bracket Order Placed: {order_id}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def test_bracket_order_with_atr():
    """Test ATR-based bracket order (as in reference code)"""
    print("\n" + "="*70)
    print("TEST 2: ATR-Based Bracket Order (Reference Code Style)")
    print("="*70)
    
    try:
        # Simulate ATR calculation (in real scenario, calculate from historical data)
        atr = 10  # Assume ATR is 10 points
        
        # Reference code logic:
        # squareoff = int(6 * atr)
        # stoploss = int(3 * atr)
        # trailing_stoploss = 2
        
        order_params = {
            "tradingsymbol": "NIFTY25DECFUT",
            "exchange": "NFO",
            "transaction_type": "BUY",
            "quantity": 50,
            "price": 24500.0,  # Entry price
            "squareoff": int(6 * atr),  # Target: 6 * ATR = 60 points
            "stoploss": int(3 * atr),   # SL: 3 * ATR = 30 points
            "trailing_stoploss": 2,
            "product": "MIS",
            "tag": "atr_strategy"
        }
        
        print("\n📊 ATR-Based Strategy:")
        print(f"  ATR: {atr} points")
        print(f"  Target: 6 × ATR = {order_params['squareoff']} points")
        print(f"  Stop Loss: 3 × ATR = {order_params['stoploss']} points")
        print(f"  Risk-Reward Ratio: 1:2")
        
        print("\n📋 Order Parameters:")
        print(f"  Symbol: {order_params['tradingsymbol']}")
        print(f"  Type: {order_params['transaction_type']}")
        print(f"  Quantity: {order_params['quantity']}")
        print(f"  Entry Price: ₹{order_params['price']}")
        print(f"  Target: ₹{order_params['price'] + order_params['squareoff']} (+{order_params['squareoff']} points)")
        print(f"  Stop Loss: ₹{order_params['price'] - order_params['stoploss']} (-{order_params['stoploss']} points)")
        print(f"  Trailing SL: {order_params['trailing_stoploss']} ticks")
        
        print("\n⚠️  This is a test - order placement commented out")
        print("    Uncomment the line below to place actual order")
        
        # UNCOMMENT TO PLACE ACTUAL ORDER (requires active session & margin)
        # order_id = order_service.place_bracket_order(**order_params)
        # print(f"\n✅ Bracket Order Placed: {order_id}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def test_bracket_order_sell():
    """Test bracket order for SELL transaction"""
    print("\n" + "="*70)
    print("TEST 3: Bracket Order - SELL")
    print("="*70)
    
    try:
        order_params = {
            "tradingsymbol": "INFY",
            "exchange": "NSE",
            "transaction_type": "SELL",  # Short position
            "quantity": 10,
            "price": 1500.0,
            "squareoff": 8,   # Target: 1492 (8 points profit on short)
            "stoploss": 4,    # SL: 1504 (4 points loss on short)
            "product": "MIS",
            "tag": "sell_bracket_order"
        }
        
        print("\n📋 Order Parameters (SELL):")
        print(f"  Symbol: {order_params['tradingsymbol']}")
        print(f"  Type: {order_params['transaction_type']}")
        print(f"  Quantity: {order_params['quantity']}")
        print(f"  Entry Price: ₹{order_params['price']}")
        print(f"  Target: ₹{order_params['price'] - order_params['squareoff']} (-{order_params['squareoff']} points)")
        print(f"  Stop Loss: ₹{order_params['price'] + order_params['stoploss']} (+{order_params['stoploss']} points)")
        
        print("\n⚠️  This is a test - order placement commented out")
        
        # UNCOMMENT TO PLACE ACTUAL ORDER
        # order_id = order_service.place_bracket_order(**order_params)
        # print(f"\n✅ Bracket Order Placed: {order_id}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def display_comparison():
    """Display comparison with reference code"""
    print("\n" + "="*70)
    print("REFERENCE CODE COMPARISON")
    print("="*70)
    
    print("""
Reference Code (from user):
────────────────────────────
def placeBracketOrder(symbol,buy_sell,quantity,atr,price):    
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
    kite.place_order(
        tradingsymbol=symbol,
        exchange=kite.EXCHANGE_NSE,
        transaction_type=t_type,
        quantity=quantity,
        order_type=kite.ORDER_TYPE_LIMIT,
        price=price,
        product=kite.PRODUCT_MIS,
        variety=kite.VARIETY_BO,
        squareoff=int(6*atr), 
        stoploss=int(3*atr), 
        trailing_stoploss=2
    )

Our Implementation:
────────────────────────────
order_service.place_bracket_order(
    tradingsymbol="SYMBOL",
    exchange="NSE",
    transaction_type="BUY",  # or "SELL"
    quantity=quantity,
    price=price,
    squareoff=int(6*atr),
    stoploss=int(3*atr),
    trailing_stoploss=2,
    product="MIS",
    tag="strategy_name"
)

✅ Key Features Implemented:
  • Bracket order variety (variety="bo")
  • Automatic limit order type
  • ATR-based targets (squareoff = 6*atr)
  • ATR-based stop-loss (stoploss = 3*atr)
  • Trailing stop-loss support
  • MIS product for intraday
  • BUY/SELL transaction types
  • Exchange support (NSE, BSE, NFO)
  • Order tagging for tracking

✅ Enhanced Features:
  • More flexible exchange selection
  • Optional trailing stop-loss
  • Better error handling
  • Detailed logging
  • API endpoint available
  • Type hints and documentation
""")


if __name__ == "__main__":
    print("\n" + "╔"+"═"*68+"╗")
    print("║" + " "*20 + "BRACKET ORDER TEST SUITE" + " "*24 + "║")
    print("╚"+"═"*68+"╝")
    
    print("\n⚠️  WARNING: These tests demonstrate bracket order functionality")
    print("   Actual order placement is COMMENTED OUT to prevent accidental execution")
    print("   Uncomment order placement lines if you want to place real orders")
    print("   Ensure you have:")
    print("   • Active Kite session")
    print("   • Sufficient margin")
    print("   • Market is open")
    
    # Check authentication status
    try:
        kite_instance = kite_auth_service.get_kite_instance()
        print("\n✅ Kite session active - ready for order placement")
    except Exception as e:
        print(f"\n❌ Kite session not active: {str(e)}")
        print("   Run authentication first: python backend/test_auth.py")
    
    # Run tests
    test_bracket_order_basic()
    test_bracket_order_with_atr()
    test_bracket_order_sell()
    display_comparison()
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)
    print("\n💡 Next Steps:")
    print("   1. Uncomment order placement lines to test with real orders")
    print("   2. Use the API endpoint: POST /api/orders/place/bracket")
    print("   3. Integrate into your trading strategies")
    print("   4. Calculate ATR from historical data for dynamic targets")
    print("\n")
