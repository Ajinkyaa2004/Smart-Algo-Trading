# Frontend Migration Guide

## Quick Start

The new API client (`src/utils/api.ts`) automatically handles session tokens for all requests.

## Before (Old Way)

```typescript
// Manual fetch with no token
const response = await fetch('http://localhost:8000/api/portfolio/holdings');
const data = await response.json();
```

## After (New Way)

```typescript
import api from '@/utils/api';

// Automatic token handling
const data = await api.getPortfolio();
```

## Available API Methods

### Authentication
```typescript
api.getAuthStatus()  // Check if user is authenticated
```

### Portfolio (Real Zerodha Data)
```typescript
api.getPortfolio()   // Get holdings
api.getPositions()   // Get open positions
api.getOrders()      // Get order history
api.getMargins()     // Get account balance
```

### Paper Trading
```typescript
api.getPaperPortfolio()      // Get paper trading portfolio
api.getPaperTrades()         // Get paper trade history
api.getPaperFunds()          // Get virtual funds
api.getPaperStats()          // Get performance stats
api.resetPaperPortfolio()    // Reset paper account
```

### Trading Bot
```typescript
api.getBotStatus()           // Get bot status
api.startBot(config)         // Start trading bot
api.stopBot(config)          // Stop trading bot
```

### Market Data
```typescript
api.getLTP(['RELIANCE', 'INFY'])  // Get last traded prices
api.getHistoricalData(params)     // Get historical candles
```

## Component Migration Examples

### Example 1: Portfolio Component

**Before:**
```typescript
const fetchPortfolio = async () => {
  const response = await fetch('http://localhost:8000/api/portfolio/holdings');
  const data = await response.json();
  setHoldings(data.data);
};
```

**After:**
```typescript
import api from '@/utils/api';

const fetchPortfolio = async () => {
  const data = await api.getPortfolio();
  setHoldings(data.data);
};
```

### Example 2: Paper Trading Dashboard

**Before:**
```typescript
const fetchPaperData = async () => {
  const portfolioRes = await fetch('http://localhost:8000/api/paper-trading/portfolio');
  const portfolio = await portfolioRes.json();
  
  const tradesRes = await fetch('http://localhost:8000/api/paper-trading/trades');
  const trades = await tradesRes.json();
  
  setPortfolio(portfolio.portfolio);
  setTrades(trades.trades);
};
```

**After:**
```typescript
import api from '@/utils/api';

const fetchPaperData = async () => {
  const [portfolio, trades] = await Promise.all([
    api.getPaperPortfolio(),
    api.getPaperTrades()
  ]);
  
  setPortfolio(portfolio.portfolio);
  setTrades(trades.trades);
};
```

### Example 3: Trading Bot Control

**Before:**
```typescript
const startBot = async (config) => {
  const response = await fetch('http://localhost:8000/api/bot/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  const data = await response.json();
  return data;
};
```

**After:**
```typescript
import api from '@/utils/api';

const startBot = async (config) => {
  return await api.startBot(config);
};
```

## Error Handling

The API client automatically handles errors:

```typescript
try {
  const portfolio = await api.getPortfolio();
  setData(portfolio.data);
} catch (error) {
  console.error('Failed to fetch portfolio:', error.message);
  // Handle authentication errors
  if (error.message.includes('Authentication')) {
    // Redirect to login
    window.location.href = '/login';
  }
}
```

## Custom Endpoints

For endpoints not yet in the API client:

```typescript
import { apiFetch } from '@/utils/api';

// GET request
const data = await apiFetch('/api/custom/endpoint');

// POST request
const result = await apiFetch('/api/custom/endpoint', {
  method: 'POST',
  body: JSON.stringify({ key: 'value' })
});
```

## Components to Update

### High Priority (User-Specific Data)
- ✅ `Dashboard.tsx` - Portfolio overview
- ✅ `Portfolio.tsx` - Holdings and positions
- ✅ `Orders.tsx` - Order history
- ✅ `TradingBot.tsx` - Bot control and stats
- ✅ Paper trading components

### Medium Priority (Shared Data)
- ⚠️ `LiveMarket.tsx` - Market data (shared, but needs token)
- ⚠️ `HistoricalData.tsx` - Historical data
- ⚠️ `Strategies.tsx` - Strategy info

### Low Priority (Public Data)
- ℹ️ Login page - No token needed
- ℹ️ Static pages - No API calls

## Testing Checklist

After migration, test:
- [ ] Login with your account
- [ ] View portfolio - should see your holdings
- [ ] View paper trading - should see your paper trades
- [ ] Place paper trade - should update your account only
- [ ] Open incognito, login with different account
- [ ] Verify data is isolated between users
- [ ] Logout and re-login - should maintain session

## Common Issues

### Issue: "Authentication required" error
**Solution:** Check if token is stored:
```typescript
console.log(localStorage.getItem('authToken'));
```

### Issue: Seeing old data
**Solution:** Clear localStorage and re-login:
```typescript
localStorage.clear();
window.location.reload();
```

### Issue: Token not being sent
**Solution:** Ensure using `api` or `apiFetch` from `@/utils/api`:
```typescript
import api from '@/utils/api';  // ✅ Correct
import { apiFetch } from '@/utils/api';  // ✅ Also correct

// ❌ Wrong - no token
fetch('http://localhost:8000/api/...')
```

## Next Steps

1. Update components to use new API client
2. Test with multiple users
3. Remove old fetch calls
4. Add error boundaries for auth failures
5. Implement token refresh logic (optional)

---

**Remember:** All API calls now automatically include the session token, ensuring each user sees only their own data!
