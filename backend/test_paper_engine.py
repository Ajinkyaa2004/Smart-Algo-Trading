"""
Test Paper Trading Engine
Quick script to verify paper trading works correctly
"""
from app.services.paper_trading import paper_engine

# Test 1: Check initial state
print("\n=== TEST 1: Initial State ===")
print(f"Virtual Capital: ₹{paper_engine.VIRTUAL_CAPITAL:,.2f}")
print(f"Available Funds: ₹{paper_engine.available_funds:,.2f}")
print(f"Invested Funds: ₹{paper_engine.invested_funds:,.2f}")

# Test 2: Update LTP (simulate market data)
print("\n=== TEST 2: Update LTP ===")
paper_engine.update_ltp("RELIANCE", "NSE", 2550.50)
print(f"LTP cached for RELIANCE: ₹{paper_engine.ltp_cache.get('NSE:RELIANCE', 0):.2f}")

# Test 3: Place a BUY order
print("\n=== TEST 3: Place BUY Order ===")
try:
    order_id = paper_engine.place_order(
        tradingsymbol="RELIANCE",
        exchange="NSE",
        transaction_type="BUY",
        quantity=1,
        order_type="MARKET",
        product="MIS",
        tag="TEST_ORDER"
    )
    print(f"Order placed successfully: {order_id}")
except Exception as e:
    print(f"Error placing order: {e}")

# Test 4: Check portfolio
print("\n=== TEST 4: Check Portfolio ===")
portfolio = paper_engine.get_portfolio()
print(f"Available Funds: ₹{portfolio['paper_funds']['available_funds']:,.2f}")
print(f"Invested Funds: ₹{portfolio['paper_funds']['invested_funds']:,.2f}")
print(f"Positions: {len(portfolio['paper_portfolio'])}")

if portfolio['paper_portfolio']:
    for pos in portfolio['paper_portfolio']:
        print(f"  - {pos['symbol']}: {pos['quantity']} @ ₹{pos['average_price']:.2f}, P&L: ₹{pos['unrealized_pnl']:.2f}")

# Test 5: Check trades
print("\n=== TEST 5: Check Trades ===")
trades = paper_engine.get_trade_history()
print(f"Total Trades: {len(trades)}")
for trade in trades:
    print(f"  - {trade['action']} {trade['quantity']} {trade['symbol']} @ ₹{trade['price']:.2f}")

print("\n✅ Tests Complete!")
