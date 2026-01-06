"""
Test Paper Trading Dashboard Update Issue
This script simulates a trade and checks if the dashboard is updated
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_paper_trading_flow():
    """Test complete paper trading flow"""
    
    print("=" * 60)
    print("📊 Testing Paper Trading Dashboard Update")
    print("=" * 60)
    
    # 1. Get initial portfolio state
    print("\n1️⃣ Fetching initial portfolio state...")
    response = requests.get(f"{BASE_URL}/api/paper-trading/portfolio")
    if response.status_code == 200:
        data = response.json()
        initial_funds = data['portfolio']['paper_funds']
        print(f"   ✓ Initial Available Funds: ₹{initial_funds['available_funds']:,.2f}")
        print(f"   ✓ Initial Invested: ₹{initial_funds['invested_funds']:,.2f}")
        print(f"   ✓ Initial Realized P&L: ₹{initial_funds['realized_pnl']:,.2f}")
    else:
        print(f"   ✗ Failed to fetch portfolio: {response.status_code}")
        return
    
    # 2. Place a BUY order
    print("\n2️⃣ Placing a BUY order...")
    order_payload = {
        "tradingsymbol": "RELIANCE",
        "exchange": "NSE",
        "transaction_type": "BUY",
        "quantity": 10,
        "order_type": "MARKET",
        "product": "MIS",
        "tag": "test_dashboard"
    }
    
    response = requests.post(f"{BASE_URL}/api/orders/place", json=order_payload)
    if response.status_code == 200:
        order_data = response.json()
        print(f"   ✓ Order placed: {order_data.get('order_id')}")
    else:
        print(f"   ✗ Failed to place order: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # 3. Wait a moment for order to execute
    print("\n3️⃣ Waiting for order execution...")
    time.sleep(2)
    
    # 4. Check updated portfolio
    print("\n4️⃣ Checking updated portfolio...")
    response = requests.get(f"{BASE_URL}/api/paper-trading/portfolio")
    if response.status_code == 200:
        data = response.json()
        updated_funds = data['portfolio']['paper_funds']
        portfolio = data['portfolio']['paper_portfolio']
        stats = data['portfolio']['statistics']
        
        print(f"\n   📊 Updated Portfolio:")
        print(f"   Available Funds: ₹{updated_funds['available_funds']:,.2f}")
        print(f"   Invested Funds: ₹{updated_funds['invested_funds']:,.2f}")
        print(f"   Realized P&L: ₹{updated_funds['realized_pnl']:,.2f}")
        print(f"   Total Positions: {stats['total_positions']}")
        print(f"   Unrealized P&L: ₹{stats['total_unrealized_pnl']:,.2f}")
        
        # Check if funds were deducted
        funds_changed = updated_funds['available_funds'] != initial_funds['available_funds']
        invested_changed = updated_funds['invested_funds'] != initial_funds['invested_funds']
        
        if funds_changed and invested_changed:
            print(f"\n   ✅ SUCCESS: Funds were updated!")
            print(f"   Deducted: ₹{initial_funds['available_funds'] - updated_funds['available_funds']:,.2f}")
            print(f"   Invested: ₹{updated_funds['invested_funds']:,.2f}")
        else:
            print(f"\n   ❌ ISSUE FOUND: Funds were NOT updated!")
            print(f"   Expected: Available funds should decrease, Invested should increase")
            print(f"   Actual: Available={updated_funds['available_funds']}, Invested={updated_funds['invested_funds']}")
        
        # Show portfolio holdings
        if portfolio:
            print(f"\n   📈 Portfolio Holdings:")
            for holding in portfolio:
                print(f"   - {holding['symbol']}: {holding['quantity']} @ ₹{holding['average_price']:.2f}")
        else:
            print(f"\n   ⚠️  No holdings found in portfolio!")
    else:
        print(f"   ✗ Failed to fetch updated portfolio: {response.status_code}")
    
    # 5. Check trade history
    print("\n5️⃣ Checking trade history...")
    response = requests.get(f"{BASE_URL}/api/paper-trading/trades")
    if response.status_code == 200:
        data = response.json()
        trades = data.get('trades', [])
        print(f"   Total Trades: {len(trades)}")
        if trades:
            print(f"\n   📜 Recent Trades:")
            for trade in trades[-3:]:  # Show last 3 trades
                print(f"   - {trade['action']} {trade['quantity']} {trade['symbol']} @ ₹{trade['price']:.2f}")
        else:
            print(f"   ⚠️  No trades found in history!")
    else:
        print(f"   ✗ Failed to fetch trade history: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_paper_trading_flow()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
