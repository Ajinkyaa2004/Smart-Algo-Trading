# Multi-User Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SMART ALGO TRADE PLATFORM                          │
│                         Multi-User Architecture                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐                              ┌──────────────────┐
│   User A         │                              │   User B         │
│   (Browser 1)    │                              │   (Browser 2)    │
└────────┬─────────┘                              └────────┬─────────┘
         │                                                 │
         │ 1. Login with Zerodha                          │ 1. Login with Zerodha
         │                                                 │
         ▼                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ZERODHA OAUTH                                     │
│                    (Authentication Provider)                                │
└────────┬───────────────────────────────────────────────┬────────────────────┘
         │                                                 │
         │ 2. Request Token                               │ 2. Request Token
         │                                                 │
         ▼                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND SERVER                                     │
│                     (FastAPI + Python)                                      │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │              AUTHENTICATION SERVICE                                 │   │
│  │              (kite_auth.py)                                        │   │
│  │                                                                     │   │
│  │  ┌──────────────────┐              ┌──────────────────┐          │   │
│  │  │  User A Session  │              │  User B Session  │          │   │
│  │  │  token: uuid-a   │              │  token: uuid-b   │          │   │
│  │  │  user_id: ZX1234 │              │  user_id: ZX5678 │          │   │
│  │  │  access_token: a │              │  access_token: b │          │   │
│  │  └──────────────────┘              └──────────────────┘          │   │
│  │                                                                     │   │
│  │  Files: data/sessions/ZX1234.json  data/sessions/ZX5678.json     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  3. Generate session_token                                                 │
│  4. Return token to frontend                                               │
│                                                                             │
└────────┬───────────────────────────────────────────────┬────────────────────┘
         │                                                 │
         │ token=uuid-a                                   │ token=uuid-b
         │                                                 │
         ▼                                                 ▼
┌──────────────────┐                              ┌──────────────────┐
│   User A         │                              │   User B         │
│   localStorage:  │                              │   localStorage:  │
│   authToken=     │                              │   authToken=     │
│   uuid-a         │                              │   uuid-b         │
└────────┬─────────┘                              └────────┬─────────┘
         │                                                 │
         │ 5. API Calls                                   │ 5. API Calls
         │ Header: X-Session-Token: uuid-a                │ Header: X-Session-Token: uuid-b
         │                                                 │
         ▼                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API ENDPOINTS                                      │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  PORTFOLIO API (api/portfolio.py)                                  │   │
│  │  - /api/portfolio/holdings                                         │   │
│  │  - /api/portfolio/positions                                        │   │
│  │  - /api/portfolio/orders                                           │   │
│  │                                                                     │   │
│  │  Extracts token → Gets user_id → Fetches user's Kite instance     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  PAPER TRADING API (api/paper_trading.py)                          │   │
│  │  - /api/paper-trading/portfolio                                    │   │
│  │  - /api/paper-trading/trades                                       │   │
│  │  - /api/paper-trading/funds                                        │   │
│  │                                                                     │   │
│  │  Extracts token → Gets user_id → Gets user's paper engine         │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└────────┬───────────────────────────────────────────────┬────────────────────┘
         │                                                 │
         ▼                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-USER PAPER TRADING MANAGER                         │
│                  (multi_user_paper_trading.py)                             │
│                                                                             │
│  ┌──────────────────────────┐        ┌──────────────────────────┐         │
│  │  User A Paper Engine     │        │  User B Paper Engine     │         │
│  │  user_id: ZX1234         │        │  user_id: ZX5678         │         │
│  │                          │        │                          │         │
│  │  Virtual Capital: 100k   │        │  Virtual Capital: 100k   │         │
│  │  Available: 95k          │        │  Available: 98k          │         │
│  │  Invested: 5k            │        │  Invested: 2k            │         │
│  │  Positions: [RELIANCE]   │        │  Positions: [INFY]       │         │
│  │  Trades: [...]           │        │  Trades: [...]           │         │
│  └──────────────────────────┘        └──────────────────────────┘         │
│                                                                             │
└────────┬───────────────────────────────────────────────┬────────────────────┘
         │                                                 │
         ▼                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MONGODB DATABASE                                   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  User A Collections                                                 │   │
│  │  - user_ZX1234_paper_orders                                        │   │
│  │  - user_ZX1234_paper_positions                                     │   │
│  │  - user_ZX1234_paper_trades                                        │   │
│  │  - user_ZX1234_paper_meta                                          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  User B Collections                                                 │   │
│  │  - user_ZX5678_paper_orders                                        │   │
│  │  - user_ZX5678_paper_positions                                     │   │
│  │  - user_ZX5678_paper_trades                                        │   │
│  │  - user_ZX5678_paper_meta                                          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          ZERODHA KITE API                                   │
│                     (Real Trading Platform)                                 │
│                                                                             │
│  ┌──────────────────────────┐        ┌──────────────────────────┐         │
│  │  User A Account          │        │  User B Account          │         │
│  │  user_id: ZX1234         │        │  user_id: ZX5678         │         │
│  │                          │        │                          │         │
│  │  Real Holdings: [...]    │        │  Real Holdings: [...]    │         │
│  │  Real Positions: [...]   │        │  Real Positions: [...]   │         │
│  │  Real Orders: [...]      │        │  Real Orders: [...]      │         │
│  │  Real Balance: ₹X        │        │  Real Balance: ₹Y        │         │
│  └──────────────────────────┘        └──────────────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

KEY POINTS:
═══════════

1. COMPLETE ISOLATION
   ✅ Each user has their own session token
   ✅ Each user has their own paper trading engine
   ✅ Each user has their own MongoDB collections
   ✅ Each user sees only their own data

2. DATA FLOW
   User → Token in Header → Backend validates → User-specific data → Response

3. STORAGE
   - Sessions: data/sessions/{user_id}.json
   - Paper Trading: MongoDB user_{user_id}_* collections
   - Real Trading: Zerodha API (already isolated by account)

4. SECURITY
   - Token stored in localStorage (client-side)
   - Token sent via X-Session-Token header
   - Backend validates token on every request
   - No cross-user data leakage

5. SCALABILITY
   - Unlimited concurrent users
   - Each user independent
   - No interference between users
   - Thread-safe operations
```
