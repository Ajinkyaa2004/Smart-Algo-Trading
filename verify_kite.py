"""
Quick verification script for Kite Connect API
Tests authentication and displays available features
"""
import sys
sys.path.append('backend')

from app.services.kite_auth import kite_auth_service

print("=" * 60)
print("KITE CONNECT API VERIFICATION")
print("=" * 60)

# Check authentication status
if kite_auth_service.is_authenticated():
    print("\n✓ Already authenticated!")
    profile = kite_auth_service.get_user_profile()
    print(f"  User: {profile.get('user_name')}")
    print(f"  User ID: {profile.get('user_id')}")
else:
    print("\n⚠ Not authenticated")
    login_url = kite_auth_service.get_login_url()
    print(f"\nLogin URL: {login_url}")

print("\n" + "=" * 60)
print("WHAT THIS API PROVIDES:")
print("=" * 60)
print("1. Market Data: Real-time prices for NIFTY, BANKNIFTY, Stocks")
print("2. Orders: Automated Buy/Sell order placement")
print("3. Portfolio: Access to Holdings and Positions")
print("4. Historical Data: OHLC data for backtesting")
print("5. WebSocket: Live tick-by-tick data streaming")
print("=" * 60)

