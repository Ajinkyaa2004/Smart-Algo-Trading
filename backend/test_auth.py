"""
Test script for Kite Connect Authentication
Run this to verify the authentication flow works correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.kite_auth import kite_auth_service

def test_authentication():
    print("=" * 60)
    print("KITE CONNECT AUTHENTICATION TEST")
    print("=" * 60)
    
    # Check if already authenticated
    if kite_auth_service.is_authenticated():
        print("\n✓ Already authenticated!")
        profile = kite_auth_service.get_user_profile()
        print(f"  User: {profile.get('user_name')} ({profile.get('user_id')})")
        print(f"  Email: {profile.get('email')}")
        print(f"  Login Time: {profile.get('login_time')}")
        
        # Test connection
        try:
            kite = kite_auth_service.get_kite_instance()
            live_profile = kite.profile()
            print(f"\n✓ Connection verified with Zerodha")
            print(f"  Broker: {live_profile.get('broker')}")
            print(f"  Products: {', '.join(live_profile.get('products', []))}")
            print(f"  Exchanges: {', '.join(live_profile.get('exchanges', []))}")
        except Exception as e:
            print(f"\n✗ Connection test failed: {str(e)}")
        
        return True
    
    # Need to login
    print("\n⚠ Not authenticated. Starting login flow...\n")
    
    try:
        login_url = kite_auth_service.get_login_url()
        print("Step 1: Open this URL in your browser:")
        print(f"\n{login_url}\n")
        print("Step 2: Login with your Zerodha credentials")
        print("Step 3: After redirect, copy the 'request_token' from URL")
        print("        URL format: http://localhost:5173/?request_token=XXXXX&action=login&status=success")
        
        request_token = input("\nPaste the request_token here: ").strip()
        
        if not request_token:
            print("✗ No token provided")
            return False
        
        print("\nExchanging token for session...")
        result = kite_auth_service.generate_session(request_token)
        
        print("\n✓ Authentication successful!")
        print(f"  User: {result['user']['user_name']}")
        print(f"  User ID: {result['user']['user_id']}")
        print(f"  Email: {result['user']['email']}")
        print("\n✓ Session saved. You won't need to login again today.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Authentication failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_authentication()
    print("\n" + "=" * 60)
    if success:
        print("STATUS: READY FOR TRADING")
    else:
        print("STATUS: AUTHENTICATION REQUIRED")
    print("=" * 60)
