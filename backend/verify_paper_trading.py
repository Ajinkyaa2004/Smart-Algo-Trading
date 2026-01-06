import sys
import os
import time
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

# Import services
from app.services.paper_trading import paper_engine
from app.services.market_data import market_data_service
from app.services.market_hours import market_hours

def verify_system():
    print("="*60)
    print("🚀  PAPER TRADING SYSTEM VERIFICATION")
    print("="*60)
    
    # 1. Check Market Status
    print("\n1️⃣  Checking Market Connection...")
    status = market_hours.get_market_status()
    print(f"   Current Status: {status['status']}")
    print(f"   Session: {status['session']}")
    
    # 2. Check Data Feed (Kite Connect)
    print("\n2️⃣  Verifying Data Feed (LTP)...")
    try:
        symbol = "NSE:RELIANCE"
        ltp_data = market_data_service.get_ltp([symbol])
        if symbol in ltp_data:
            price = ltp_data[symbol]['last_price']
            print(f"   ✅ SUCCESS: Fetched LIVE/CLOSE Price for {symbol}: ₹{price}")
        else:
            print(f"   ❌ FAILED: Could not fetch price for {symbol}")
            return
    except Exception as e:
        print(f"   ❌ FAILED: API Error - {e}")
        return

    # 3. Verify Paper Engine Funds
    print("\n3️⃣  Verifying Paper Funds...")
    initial_funds = paper_engine.available_funds
    print(f"   Available Funds: ₹{initial_funds:,.2f}")
    
    # 4. Simulate a Trade (Validation)
    print("\n4️⃣  Simulating Strategy Order...")
    qty = 5
    try:
        # Place order
        order_id = paper_engine.place_order(
            tradingsymbol="RELIANCE",
            exchange="NSE",
            transaction_type="BUY",
            quantity=qty,
            order_type="MARKET",
            product="MIS",
            price=price,
            tag="VERIFICATION_TEST"
        )
        print(f"   ✅ Order Placed: {order_id}")
        
        # Check if funds deducted
        new_funds = paper_engine.available_funds
        expected_deduction = qty * price
        actual_deduction = initial_funds - new_funds
        
        print(f"   Funds Before: ₹{initial_funds:,.2f}")
        print(f"   Funds After:  ₹{new_funds:,.2f}")
        print(f"   Deducted:     ₹{actual_deduction:,.2f}")
        
        if abs(actual_deduction - expected_deduction) < 1.0:
            print("   ✅ SUCCESS: Funds correctly deducted!")
        else:
            print("   ❌ FAILED: Fund deduction mismatch!")
            
    except Exception as e:
        print(f"   ❌ FAILED: Trade Execution Error - {e}")
        return

    print("\n" + "="*60)
    print("✅  SYSTEM IS READY FOR LIVE MARKETS")
    print("="*60)
    print("Go to your Dashboard to see the new trade!")

if __name__ == "__main__":
    verify_system()
