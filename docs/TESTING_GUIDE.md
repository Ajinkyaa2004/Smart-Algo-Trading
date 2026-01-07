# Multi-User Testing Guide

## 🎯 Quick Test (5 Minutes)

### Prerequisites
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- Two different Zerodha accounts (or use same account in different browsers)

### Test Steps

#### 1. Setup User A
```bash
# Browser 1 (Normal mode)
1. Open http://localhost:3000
2. Click "Login with Zerodha"
3. Enter User A credentials
4. You'll be redirected back
5. Check localStorage:
   - Open DevTools (F12)
   - Console: localStorage.getItem('authToken')
   - Should see: "uuid-string"
```

#### 2. Setup User B
```bash
# Browser 2 (Incognito/Private mode)
1. Open http://localhost:3000 (incognito)
2. Click "Login with Zerodha"
3. Enter User B credentials
4. You'll be redirected back
5. Check localStorage (should be different token)
```

#### 3. Test Data Isolation

**User A Actions:**
```
1. Go to Dashboard
2. Note your portfolio holdings
3. Go to Paper Trading
4. Place a test trade (BUY 10 RELIANCE)
5. Check Paper Portfolio - should see the trade
6. Note your paper funds balance
```

**User B Actions:**
```
1. Go to Dashboard
2. Should see DIFFERENT portfolio than User A
3. Go to Paper Trading
4. Should NOT see User A's RELIANCE trade
5. Should have separate ₹1,00,000 balance
6. Place your own trade (BUY 5 INFY)
```

**Verification:**
```
User A Dashboard:
- Shows User A's real Zerodha holdings
- Paper trade: RELIANCE (10 shares)
- Paper funds: ₹1,00,000 - (cost of RELIANCE)

User B Dashboard:
- Shows User B's real Zerodha holdings
- Paper trade: INFY (5 shares)
- Paper funds: ₹1,00,000 - (cost of INFY)

✅ PASS: Each user sees only their own data
❌ FAIL: If User B sees User A's RELIANCE trade
```

## 🔍 Detailed Testing

### Test 1: Portfolio Isolation

**User A:**
```typescript
// Check portfolio
const portfolio = await api.getPortfolio();
console.log('User A Holdings:', portfolio.data);
```

**User B:**
```typescript
// Check portfolio
const portfolio = await api.getPortfolio();
console.log('User B Holdings:', portfolio.data);
```

**Expected:** Different holdings for each user

### Test 2: Paper Trading Isolation

**User A:**
```typescript
// Place paper trade
await api.apiFetch('/api/paper-trading/manual-trade', {
  method: 'POST',
  body: JSON.stringify({
    symbol: 'RELIANCE',
    action: 'BUY',
    quantity: 10
  })
});

// Check trades
const trades = await api.getPaperTrades();
console.log('User A Trades:', trades.trades);
```

**User B:**
```typescript
// Check trades (should NOT see User A's trade)
const trades = await api.getPaperTrades();
console.log('User B Trades:', trades.trades);
```

**Expected:** User B's trades array is empty or contains only their own trades

### Test 3: Funds Isolation

**User A:**
```typescript
const funds = await api.getPaperFunds();
console.log('User A Funds:', funds.funds);
// Should show: available_funds reduced by RELIANCE purchase
```

**User B:**
```typescript
const funds = await api.getPaperFunds();
console.log('User B Funds:', funds.funds);
// Should show: full ₹1,00,000 (or their own trades)
```

**Expected:** Separate fund balances

### Test 4: Session Persistence

**User A:**
```
1. Close browser
2. Reopen browser
3. Go to http://localhost:3000
4. Should auto-login (token in localStorage)
5. Should see same portfolio and trades
```

**Expected:** Session persists across browser restarts

### Test 5: Logout and Re-login

**User A:**
```
1. Logout
2. Check localStorage - token should be cleared
3. Login again
4. Should get NEW token
5. Should see same data (loaded from MongoDB)
```

**Expected:** Data persists even after logout/login

## 🗄️ Database Verification

### Check MongoDB Collections

```bash
# Connect to MongoDB
mongo smart_algo_trade

# List all collections
db.getCollectionNames()

# Should see:
# user_ZX1234_paper_orders
# user_ZX1234_paper_positions
# user_ZX1234_paper_trades
# user_ZX1234_paper_meta
# user_ZX5678_paper_orders
# user_ZX5678_paper_positions
# user_ZX5678_paper_trades
# user_ZX5678_paper_meta
```

### Check User A's Data

```javascript
// In mongo shell
db.user_ZX1234_paper_trades.find().pretty()

// Should show User A's trades only
```

### Check User B's Data

```javascript
// In mongo shell
db.user_ZX5678_paper_trades.find().pretty()

// Should show User B's trades only
```

## 🐛 Troubleshooting Tests

### Test Fails: User B sees User A's data

**Debug Steps:**
```typescript
// In User B's browser console
console.log('Token:', localStorage.getItem('authToken'));

// Check if token is being sent
// Open Network tab in DevTools
// Look for API calls
// Check Headers → X-Session-Token
// Should be User B's token, not User A's
```

**Fix:**
```typescript
// Clear localStorage and re-login
localStorage.clear();
window.location.reload();
```

### Test Fails: "Authentication required" error

**Debug Steps:**
```typescript
// Check token
console.log('Token:', localStorage.getItem('authToken'));

// If null, re-login
// If exists, check if expired (24 hours)
```

**Fix:**
```typescript
// Re-login to get fresh token
window.location.href = '/login';
```

### Test Fails: Same token for both users

**Debug Steps:**
```bash
# Check backend logs
# Should see:
# "✓ Session saved for ZX1234"
# "✓ Session saved for ZX5678"

# Check session files
ls -la backend/data/sessions/
# Should see:
# ZX1234.json
# ZX5678.json
```

**Fix:**
- Ensure using different browsers/incognito
- Clear localStorage in both browsers
- Re-login both users

## 📊 Success Criteria

### ✅ All Tests Pass If:

1. **Authentication**
   - Each user gets unique session token
   - Token stored in localStorage
   - Token sent with all API requests

2. **Portfolio Isolation**
   - User A sees their Zerodha holdings
   - User B sees their Zerodha holdings
   - No cross-contamination

3. **Paper Trading Isolation**
   - User A has separate paper account
   - User B has separate paper account
   - Each starts with ₹1,00,000
   - Trades don't mix

4. **Database Isolation**
   - Separate MongoDB collections per user
   - User A's data in user_ZX1234_* collections
   - User B's data in user_ZX5678_* collections

5. **Session Persistence**
   - Sessions survive browser restart
   - Data persists after logout/login
   - No data loss

## 🎉 Expected Results

After successful testing:

```
User A:
✅ Unique session token
✅ Own portfolio visible
✅ Own paper trades visible
✅ Own funds balance
✅ Cannot see User B's data

User B:
✅ Unique session token
✅ Own portfolio visible
✅ Own paper trades visible
✅ Own funds balance
✅ Cannot see User A's data

Database:
✅ Separate collections per user
✅ No data mixing
✅ Proper isolation

System:
✅ Multiple users can use simultaneously
✅ No interference
✅ Complete data isolation
```

## 📝 Test Report Template

```markdown
# Multi-User Test Report

**Date:** [Date]
**Tester:** [Your Name]

## Test Environment
- Backend: Running ✅ / Not Running ❌
- Frontend: Running ✅ / Not Running ❌
- MongoDB: Running ✅ / Not Running ❌

## Test Results

### User A
- Login: ✅ / ❌
- Portfolio: ✅ / ❌
- Paper Trading: ✅ / ❌
- Token: [token-value]

### User B
- Login: ✅ / ❌
- Portfolio: ✅ / ❌
- Paper Trading: ✅ / ❌
- Token: [token-value]

### Data Isolation
- Portfolio Isolation: ✅ / ❌
- Paper Trading Isolation: ✅ / ❌
- Database Isolation: ✅ / ❌

### Issues Found
1. [Issue description]
2. [Issue description]

### Conclusion
- Overall Status: PASS ✅ / FAIL ❌
- Notes: [Additional notes]
```

---

**Ready to test?** Follow the Quick Test steps above and verify that each user sees only their own data!
