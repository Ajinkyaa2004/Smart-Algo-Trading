# Multi-User Architecture Guide

## Overview

The Smart Algo Trade platform now supports **multiple concurrent users**, with complete data isolation. Each user can:
- Log in with their own Zerodha credentials
- See only their own portfolio, orders, and trades
- Run their own trading bots independently
- Maintain separate paper trading accounts

## Architecture Changes

### 1. Authentication System

#### Session Management (`kite_auth.py`)
- **Multi-Session Support**: Stores multiple user sessions in memory and on disk
- **Session Tokens**: Each login generates a unique `session_token` (UUID)
- **File Persistence**: Sessions saved to `data/sessions/{user_id}.json`
- **Backward Compatibility**: Primary session maintained for legacy single-user code

```python
# Session structure
{
  "session_token": "uuid-string",
  "user_id": "ZX1234",
  "user_name": "John Doe",
  "access_token": "kite_access_token",
  "login_time": "2026-01-07T20:00:00"
}
```

#### Token Flow
1. User logs in via Zerodha OAuth
2. Backend generates `session_token` and returns it in redirect URL
3. Frontend stores token in `localStorage`
4. All subsequent API calls include token in `X-Session-Token` header

### 2. User-Aware APIs

#### Portfolio API (`api/portfolio.py`)
All endpoints now accept optional `session_token`:
- `/api/portfolio/holdings` - User's stock holdings
- `/api/portfolio/positions` - User's open positions
- `/api/portfolio/orders` - User's order history
- `/api/portfolio/margins` - User's account balance

#### Paper Trading API (`api/paper_trading.py`)
Each user has isolated paper trading environment:
- `/api/paper-trading/portfolio` - User's paper portfolio
- `/api/paper-trading/trades` - User's trade history
- `/api/paper-trading/funds` - User's virtual funds
- `/api/paper-trading/stats` - User's performance stats

### 3. Paper Trading Engine

#### Multi-User Paper Trading Manager (`multi_user_paper_trading.py`)
- Maintains separate `PaperTradingEngine` instance per user
- User ID extracted from session token
- Lazy initialization: Engine created on first access

#### User-Specific Data Storage
Each user's paper trading data stored in separate MongoDB collections:
```
user_{user_id}_paper_orders
user_{user_id}_paper_positions
user_{user_id}_paper_trades
user_{user_id}_paper_meta
```

### 4. Frontend Integration

#### API Client (`utils/api.ts`)
Centralized API client that:
- Automatically attaches session token to all requests
- Handles authentication errors
- Provides typed API methods

```typescript
// Usage
import api from '@/utils/api';

const portfolio = await api.getPortfolio();
const trades = await api.getPaperTrades();
```

## Usage Guide

### For Users

#### Logging In
1. Click "Login with Zerodha"
2. Enter your Zerodha credentials
3. You'll be redirected back with your session active

#### Multiple Users
- Each user can log in on different devices/browsers
- Sessions are independent and isolated
- No interference between users

### For Developers

#### Adding User-Aware Endpoints

1. **Import auth utilities**:
```python
from app.utils.auth_utils import get_session_token
from app.services.kite_auth import kite_auth_service
```

2. **Use dependency injection**:
```python
@router.get("/my-endpoint")
async def my_endpoint(session_token: Optional[str] = Depends(get_session_token)):
    # Get user-specific Kite instance
    kite = kite_auth_service.get_kite_instance(session_token)
    
    # Use it to fetch user data
    data = kite.holdings()
    return {"data": data}
```

3. **For paper trading**:
```python
from app.services.multi_user_paper_trading import multi_user_paper_manager

@router.get("/my-paper-endpoint")
async def my_endpoint(session_token: Optional[str] = Depends(get_session_token)):
    # Get user profile
    profile = kite_auth_service.get_user_profile(session_token)
    user_id = profile["user_id"]
    
    # Get user's paper engine
    paper_engine = multi_user_paper_manager.get_engine(user_id)
    
    # Use it
    portfolio = paper_engine.get_portfolio()
    return {"portfolio": portfolio}
```

## Data Isolation

### What's Isolated
✅ **Zerodha Portfolio** - Each user sees their real Zerodha holdings  
✅ **Paper Trading Portfolio** - Separate virtual accounts  
✅ **Trade History** - Independent trade logs  
✅ **Orders** - User-specific order history  
✅ **Performance Stats** - Individual metrics  
✅ **Virtual Funds** - Separate ₹1,00,000 starting capital  

### What's Shared
⚠️ **Market Data** - Live prices, historical data (same for all)  
⚠️ **Strategies** - Available strategy types (same for all)  
⚠️ **System Settings** - API keys, configuration  

## Migration Notes

### Backward Compatibility
- Existing code without session tokens uses "primary" session
- Legacy single-user mode still works
- No breaking changes for existing functionality

### Database Migration
Old collections:
```
paper_orders
paper_positions
paper_trades
paper_meta
```

New collections (per user):
```
user_{user_id}_paper_orders
user_{user_id}_paper_positions
user_{user_id}_paper_trades
user_{user_id}_paper_meta
```

Old data remains accessible as `user_default_*` collections.

## Security Considerations

### Session Tokens
- Stored in `localStorage` (client-side)
- Sent via `X-Session-Token` header
- Valid for 24 hours (Zerodha token expiry)

### Best Practices
1. Always validate session token on backend
2. Never expose other users' data
3. Clear token on logout
4. Handle expired sessions gracefully

## Testing Multi-User

### Test Scenario
1. Open browser 1, log in as User A
2. Open browser 2 (incognito), log in as User B
3. User A places a paper trade
4. User B should NOT see User A's trade
5. Each user sees only their own data

### Verification
```bash
# Check MongoDB collections
mongo smart_algo_trade
db.getCollectionNames().filter(c => c.includes('user_'))

# Should see:
# user_ZX1234_paper_orders
# user_ZX5678_paper_orders
# etc.
```

## Troubleshooting

### "Authentication required" error
- Check if token is in localStorage: `localStorage.getItem('authToken')`
- Verify token is being sent in headers
- Check if session is expired (24 hours)

### Seeing wrong user's data
- Clear localStorage and re-login
- Check browser console for session token
- Verify backend is using correct session

### Paper trading not isolated
- Check MongoDB collection names
- Verify `user_id` is being extracted correctly
- Ensure `multi_user_paper_manager` is being used

## Future Enhancements

### Planned Features
- [ ] Trading bot per-user isolation
- [ ] User-specific strategy configurations
- [ ] Shared strategies marketplace
- [ ] Team/organization support
- [ ] Admin dashboard for user management

### API Improvements
- [ ] WebSocket per-user subscriptions
- [ ] Real-time multi-user notifications
- [ ] User activity logging
- [ ] Rate limiting per user

## Summary

The platform now supports **true multi-user operation** with complete data isolation. Each user has:
- Their own authenticated session
- Isolated paper trading environment
- Private portfolio and trade history
- Independent bot configurations (coming soon)

All changes are backward compatible and require minimal frontend updates (just include session token in headers).
