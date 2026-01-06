# Historical Data - Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HISTORICAL DATA SYSTEM                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Python Scripts              2. REST API              3. Frontend     │
│  ┌──────────────────┐          ┌──────────────┐        ┌──────────────┐ │
│  │ from services    │          │ POST /api/   │        │ fetch(...)   │ │
│  │ import market_   │          │ market/      │        │              │ │
│  │ data_service     │          │ fetchOHLC    │        │              │ │
│  │                  │          │              │        │              │ │
│  │ df = service.    │          │ GET /api/    │        │              │ │
│  │ fetchOHLC(...)   │          │ market/nfo/  │        │              │ │
│  └──────────────────┘          │ futures      │        └──────────────┘ │
│                                 └──────────────┘                         │
└───────────────────┬─────────────────────┬────────────────┬──────────────┘
                    │                     │                │
                    ▼                     ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API LAYER (FastAPI)                            │
├─────────────────────────────────────────────────────────────────────────┤
│  app/api/market_data.py                                                  │
│                                                                          │
│  Endpoints:                                                              │
│  ├─ GET  /nfo/instruments         # Get all NFO instruments             │
│  ├─ GET  /nfo/futures             # Get futures contracts               │
│  ├─ GET  /nfo/options             # Get options contracts               │
│  ├─ GET  /instrument-lookup/{sym} # Look up instrument token            │
│  ├─ POST /fetchOHLC               # Convenience endpoint (ref code)     │
│  ├─ POST /historical              # Advanced historical data            │
│  └─ GET  /historical/quick        # Quick historical data               │
│                                                                          │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          SERVICE LAYER (Business Logic)                  │
├─────────────────────────────────────────────────────────────────────────┤
│  app/services/market_data.py                                             │
│                                                                          │
│  Class: MarketDataService                                                │
│  ├─ NFO Methods                                                          │
│  │  ├─ fetch_nfo_instruments()      # Fetch all NFO instruments         │
│  │  ├─ get_nfo_futures(underlying)  # Get futures only                  │
│  │  └─ get_nfo_options(...)         # Get options only                  │
│  │                                                                        │
│  ├─ Lookup Methods                                                       │
│  │  ├─ instrument_lookup(sym, exch) # Get token (ref code style)        │
│  │  └─ get_instrument_token(...)    # Alternative method                │
│  │                                                                        │
│  ├─ Historical Data Methods                                              │
│  │  ├─ fetchOHLC(ticker, ...)       # Convenience (ref code style)      │
│  │  ├─ get_historical_data(...)     # Low-level method                  │
│  │  └─ get_historical_data_by_symbol(...) # By symbol name              │
│  │                                                                        │
│  └─ Cache Management                                                     │
│     ├─ instruments_cache             # NSE/BSE cache                     │
│     ├─ nfo_instruments_cache         # NFO cache                         │
│     └─ cache_expiry (1 day)          # Auto-refresh                      │
│                                                                          │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│  app/services/kite_auth.py                                               │
│                                                                          │
│  Class: KiteAuthService                                                  │
│  ├─ get_kite_instance()              # Returns authenticated Kite       │
│  ├─ Token persistence                # Saves to data/kite_session.json  │
│  └─ Session management               # Auto-restore on restart           │
│                                                                          │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      KITE CONNECT API (Zerodha)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  KiteConnect Library                                                     │
│                                                                          │
│  Methods Used:                                                           │
│  ├─ instruments(exchange)            # Get instrument master            │
│  └─ historical_data(token, ...)      # Get historical candles           │
│                                                                          │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER (Cache)                             │
├─────────────────────────────────────────────────────────────────────────┤
│  data/                                                                   │
│  ├─ instruments.csv                  # NSE/BSE instruments (cached)     │
│  ├─ nfo_instruments.csv              # NFO instruments (cached)         │
│  └─ kite_session.json                # Auth session (persisted)         │
│                                                                          │
│  Cache Behavior:                                                         │
│  ├─ Valid for 1 day                                                      │
│  ├─ Auto-refresh after expiry                                            │
│  └─ Fallback to file if API fails                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Flow 1: Fetch Historical Data

```
User Request
     │
     ▼
API Endpoint: POST /api/market/fetchOHLC
     │
     ├─ Validate request (ticker, interval, duration, exchange)
     │
     ▼
Service: market_data_service.fetchOHLC()
     │
     ├─ Step 1: instrument_lookup()
     │     │
     │     ├─ Check cache (in-memory)
     │     │     ├─ Cache valid? → Use cached data
     │     │     └─ Cache expired? → Fetch from API
     │     │
     │     ├─ Try: fetch_nfo_instruments() OR fetch_instruments()
     │     │     │
     │     │     ├─ Call: kite.instruments(exchange)
     │     │     ├─ Save to: data/nfo_instruments.csv
     │     │     └─ Cache: nfo_instruments_cache (1 day)
     │     │
     │     ├─ Match: df[df.tradingsymbol == ticker]
     │     │
     │     └─ Return: instrument_token
     │
     ├─ Step 2: get_historical_data(token, from_date, to_date, interval)
     │     │
     │     ├─ Calculate dates: today - duration days
     │     │
     │     ├─ Call: kite.historical_data(...)
     │     │
     │     ├─ Convert to DataFrame
     │     │
     │     └─ Set index to 'date'
     │
     └─ Return: DataFrame with OHLC data
          │
          ▼
Response to User: JSON with OHLC data
```

### Flow 2: NFO Instruments with Cache

```
User: Get NIFTY futures
     │
     ▼
API: GET /api/market/nfo/futures?underlying=NIFTY
     │
     ▼
Service: get_nfo_futures("NIFTY")
     │
     ├─ Call: fetch_nfo_instruments()
     │     │
     │     ├─ Check: nfo_cache_expiry
     │     │     ├─ Cache valid? → Return nfo_instruments_cache
     │     │     └─ Cache expired? → Continue...
     │     │
     │     ├─ Try: API call
     │     │     ├─ Success?
     │     │     │   ├─ kite.instruments("NFO")
     │     │     │   ├─ Save: data/nfo_instruments.csv
     │     │     │   ├─ Cache: nfo_instruments_cache
     │     │     │   └─ Set expiry: now + 1 day
     │     │     │
     │     │     └─ Failed?
     │     │         └─ Load: data/nfo_instruments.csv (fallback)
     │     │
     │     └─ Return: DataFrame
     │
     ├─ Filter: df[df["segment"] == "NFO-FUT"]
     │
     ├─ Filter: df[df["name"].contains("NIFTY")]
     │
     └─ Return: Filtered DataFrame
          │
          ▼
Response: List of NIFTY futures
```

---

## Component Responsibilities

### 1. API Layer (`app/api/market_data.py`)
- ✅ Handle HTTP requests/responses
- ✅ Validate request parameters
- ✅ Format responses as JSON
- ✅ Error handling and status codes

### 2. Service Layer (`app/services/market_data.py`)
- ✅ Business logic
- ✅ Data fetching and processing
- ✅ Cache management
- ✅ DataFrame manipulation
- ✅ Integration with Kite API

### 3. Auth Layer (`app/services/kite_auth.py`)
- ✅ Authentication management
- ✅ Token persistence
- ✅ Session restoration
- ✅ Kite instance creation

### 4. Data Layer (Files)
- ✅ Cache storage
- ✅ Session persistence
- ✅ Instrument master files

---

## Reference Code Comparison

### Original Code
```python
# All in one file, direct API calls
instrument_dump = kite.instruments("NFO")
instrument_df = pd.DataFrame(instrument_dump)

def instrumentLookup(instrument_df, symbol):
    return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]

def fetchOHLC(ticker, interval, duration):
    instrument = instrumentLookup(instrument_df, ticker)
    data = kite.historical_data(instrument, from_date, to_date, interval)
    return pd.DataFrame(data)
```

### Our Implementation
```python
# Layered architecture with caching and API
class MarketDataService:
    def fetch_nfo_instruments(self):
        # With caching, error handling, persistence
        
    def instrument_lookup(self, symbol, exchange):
        # With exchange support, case-insensitive match
        
    def fetchOHLC(self, ticker, interval, duration, exchange):
        # With validation, better error messages
```

**Advantages:**
- Separation of concerns
- Reusable across the app
- Caching for performance
- Better error handling
- API endpoints for frontend
- Type safety

---

## Usage Pattern Matrix

| Use Case | Method | Example |
|----------|--------|---------|
| Quick script | Service Layer | `market_data_service.fetchOHLC(...)` |
| Frontend | REST API | `POST /api/market/fetchOHLC` |
| Backtesting | Service Layer | Loop with `fetchOHLC()` |
| Real-time | WebSocket + Service | Combine with live data |
| Analysis | Service Layer | Get data → Calculate indicators |
| Screening | Service Layer | Loop through instruments |

---

## Performance Optimization

```
Request Flow:
1. Check in-memory cache → O(1) - Instant
2. Cache expired? Load from file → O(n) - Fast (CSV read)
3. File missing/expired? API call → O(n) - Slow (network)
4. Save to file + cache → O(n) - One-time cost
```

**Cache Hit Rate:**
- First request of day: Cache miss (API call)
- Subsequent requests: Cache hit (instant)
- Next day: Auto-refresh

---

## Error Handling Strategy

```
API Call
   ├─ Success → Cache → Return data
   │
   └─ Failure
       ├─ Check file cache
       │   ├─ Exists → Load → Return data (with warning)
       │   └─ Missing → Raise exception
       │
       └─ Log error for debugging
```

This ensures graceful degradation and resilience.

---

**Architecture Status**: ✅ Production-Ready
