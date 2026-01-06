from app.services.kite_auth import kite_auth_service
import os

# Helper to verify clean state
def force_logout():
    print("Forcing logout...")
    kite_auth_service.logout()
    print("Logout complete. Session cleared.")

if __name__ == "__main__":
    force_logout()
