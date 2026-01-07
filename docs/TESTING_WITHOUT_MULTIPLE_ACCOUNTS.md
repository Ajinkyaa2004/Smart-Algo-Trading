# Multi-User Testing Without Multiple Zerodha Accounts

## Problem
Zerodha Kite Connect apps only allow authorized users. Testing multi-user functionality requires multiple Zerodha accounts, which may not be practical.

## Solution: Mock User Mode

### Option A: Same Account, Different Sessions (Simple Test)

You can test session isolation using the same Zerodha account in different browsers:

1. **Browser 1 (Normal mode)**
   - Login with your account
   - Session Token: `uuid-1`
   - User ID: `ZX1234`

2. **Browser 2 (Incognito mode)**
   - Logout first (clear localStorage)
   - Login again with same account
   - Session Token: `uuid-2` (different!)
   - User ID: `ZX1234` (same)

**What This Tests:**
- ✅ Session token isolation
- ✅ Multiple concurrent sessions
- ✅ Session persistence
- ❌ Different user data (same user, so same portfolio)

### Option B: Mock Second User (Development Mode)

Add a development-only endpoint to simulate a second user:

#### Backend: Add Mock User Endpoint

```python
# backend/app/api/auth.py

@router.post("/mock-login")
async def mock_login(user_id: str = "MOCK_USER"):
    """
    Development-only: Create mock session for testing
    WARNING: Remove in production!
    """
    import os
    if os.getenv("ENVIRONMENT") != "development":
        raise HTTPException(status_code=403, detail="Only available in development")
    
    # Create mock session
    session_token = str(uuid.uuid4())
    
    session_data = {
        "session_token": session_token,
        "user_id": user_id,
        "user_name": f"Mock User {user_id}",
        "email": f"{user_id}@mock.com",
        "broker": "ZERODHA",
        "access_token": "MOCK_TOKEN",
        "login_time": datetime.now().isoformat(),
        "api_key": "MOCK_KEY"
    }
    
    # Store in memory only (not in kite_auth_service)
    # This is just for paper trading testing
    
    return {
        "status": "success",
        "message": "Mock session created",
        "user": session_data,
        "session_token": session_token
    }
```

#### Frontend: Mock Login Button

```typescript
// For development only
const mockLogin = async (userId: string) => {
  const response = await fetch('http://localhost:8000/api/auth/mock-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId })
  });
  
  const data = await response.json();
  localStorage.setItem('authToken', data.session_token);
  window.location.reload();
};

// In your Login component (development only)
<button onClick={() => mockLogin('USER_A')}>Mock Login as User A</button>
<button onClick={() => mockLogin('USER_B')}>Mock Login as User B</button>
```

**What This Tests:**
- ✅ Different user IDs
- ✅ Separate paper trading accounts
- ✅ Data isolation
- ❌ Real Zerodha portfolio (mock users don't have real accounts)

### Option C: Paper Trading Only Mode

Since paper trading doesn't require real Zerodha data, you can test multi-user isolation purely with paper trading:

1. **User A (Browser 1)**
   - Login with your real Zerodha account
   - Use paper trading features
   - Place paper trades

2. **User B (Browser 2 - Mock)**
   - Use mock login (if implemented)
   - Use paper trading features
   - Place paper trades

**What This Tests:**
- ✅ Paper trading isolation
- ✅ Separate virtual funds
- ✅ Independent trade history
- ✅ Performance stats isolation

## Recommended Testing Strategy

### For Development/Testing:
1. **Use same account in different browsers** to test session isolation
2. **Implement mock login** for testing paper trading isolation
3. **Focus on paper trading features** (don't need real portfolio)

### For Production:
1. **Add authorized users** to your Kite app on Zerodha portal
2. **Test with real users** who have been added to your app
3. **Verify real portfolio isolation** works correctly

## Testing Checklist (Without Multiple Real Accounts)

### Session Isolation (Same Account, Different Browsers)
- [ ] Browser 1: Login → Get token A
- [ ] Browser 2: Login → Get token B
- [ ] Verify: Token A ≠ Token B
- [ ] Verify: Both sessions work independently
- [ ] Verify: Logout in Browser 1 doesn't affect Browser 2

### Paper Trading Isolation (Mock Users)
- [ ] Mock User A: Place paper trade
- [ ] Mock User B: Check trades → Should NOT see User A's trade
- [ ] Verify: Separate MongoDB collections created
- [ ] Verify: Separate fund balances
- [ ] Verify: Independent P&L calculations

### Database Isolation
- [ ] Check MongoDB collections
- [ ] Verify: `user_ZX1234_paper_*` (real user)
- [ ] Verify: `user_MOCK_USER_A_paper_*` (mock user A)
- [ ] Verify: `user_MOCK_USER_B_paper_*` (mock user B)
- [ ] Verify: No data mixing between collections

## Production Deployment

When deploying to production with real users:

1. **Remove mock endpoints** (security risk)
2. **Add users to Kite app** on Zerodha portal
3. **Test with real authorized users**
4. **Monitor for unauthorized access attempts**

## Environment Variable

Add to `.env`:
```bash
ENVIRONMENT=development  # or production
```

This allows mock endpoints only in development mode.

---

**Summary:** You can fully test multi-user isolation using mock users for paper trading, even without multiple real Zerodha accounts!
