# Historical Data - Quick Reference Guide

## Summary

✅ **Implementation Complete**: All functionality from the reference Kite API code has been implemented and tested.

---

## What Was Implemented

Based on the reference code, we implemented:

1. **NFO Instruments Fetching** - Get all derivatives instruments (futures & options)
2. **Instrument Lookup** - Find instrument tokens by symbol
3. **fetchOHLC Method** - Convenient historical data fetching
4. **Additional Features** - Filtering, caching, API endpoints

---

## Quick Start

### Python Service Layer

```python
from app.services.market_data import market_data_service

# 1. Get NFO instruments
nfo_df = market_data_service.fetch_nfo_instruments()
futures_df = market_data_service.get_nfo_futures("NIFTY")

# 2. Look up instrument token
token = market_data_service.instrument_lookup("NIFTY25DECFUT", "NFO")

# 3. Fetch historical data (like reference code)
df = market_data_service.fetchOHLC(
    ticker="NIFTY25DECFUT",
    interval="5minute",
    duration=4,
    exchange="NFO"
)
```

### API Endpoints

```bash
# Get NFO futures
curl http://localhost:8000/market-data/nfo/futures?underlying=NIFTY

# Look up instrument
curl http://localhost:8000/market-data/instrument-lookup/RELIANCE?exchange=NSE

# Fetch OHLC data
curl -X POST http://localhost:8000/market-data/fetchOHLC \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "NIFTY25DECFUT",
    "interval": "5minute",
    "duration": 4,
    "exchange": "NFO"
  }'
```

---

## Example Scripts

### 1. Simple Example (Matches Reference Code)

```bash
cd backend
/Users/ajinkya/Desktop/smart-algo-trade/venv/bin/python example_historical_data.py
```

This script closely matches the reference code structure.

### 2. Comprehensive Tests

```bash
cd backend
/Users/ajinkya/Desktop/smart-algo-trade/venv/bin/python test_historical_data.py
```

Tests all functionality.

---

## Reference Code Comparison

| Reference Code | Our Implementation |
|----------------|-------------------|
| `kite.instruments("NFO")` | `market_data_service.fetch_nfo_instruments()` |
| `instrument_df[instrument_df["segment"]=="NFO-FUT"]` | `market_data_service.get_nfo_futures()` |
| `instrumentLookup(df, symbol)` | `market_data_service.instrument_lookup(symbol, exchange)` |
| `fetchOHLC(ticker, interval, duration)` | `market_data_service.fetchOHLC(ticker, interval, duration, exchange)` |

---

## Key Features

### Service Methods

```python
# NFO Instruments
fetch_nfo_instruments()           # All NFO instruments
get_nfo_futures(underlying)       # Futures only
get_nfo_options(underlying, type) # Options only

# Instrument Lookup
instrument_lookup(symbol, exchange)     # Get token
get_instrument_token(symbol, exchange)  # Alternative method

# Historical Data
fetchOHLC(ticker, interval, duration, exchange)  # Convenience method
get_historical_data_by_symbol(...)               # Advanced method
```

### API Endpoints

```
GET  /market-data/nfo/instruments
GET  /market-data/nfo/futures
GET  /market-data/nfo/options
GET  /market-data/instrument-lookup/{symbol}
POST /market-data/fetchOHLC
POST /market-data/historical
GET  /market-data/historical/quick
```

---

## Supported Intervals

- `minute` - 1 minute candles
- `3minute` - 3 minute candles
- `5minute` - 5 minute candles
- `10minute` - 10 minute candles
- `15minute` - 15 minute candles
- `30minute` - 30 minute candles
- `60minute` - 60 minute candles
- `day` - Daily candles

---

## Supported Exchanges

- `NSE` - National Stock Exchange (equities)
- `BSE` - Bombay Stock Exchange (equities)
- `NFO` - National Stock Exchange F&O (futures & options)

---

## Test Results

✅ All tests passed:

```
✓ NFO instruments fetched: 37,889 instruments
✓ NFO futures: 630 contracts
✓ Instrument lookup: Working
✓ fetchOHLC (5-minute data): 225 candles retrieved
✓ fetchOHLC (daily data): 22 candles retrieved
✓ Historical data API: Working
```

---

## Files Created/Modified

### New Files
- `backend/test_historical_data.py` - Comprehensive test suite
- `backend/example_historical_data.py` - Simple example (matches reference)
- `backend/HISTORICAL_DATA_DOCS.md` - Full documentation
- `backend/HISTORICAL_DATA_QUICK_REF.md` - This file

### Modified Files
- `backend/app/services/market_data.py` - Added NFO support, convenience methods
- `backend/app/api/market_data.py` - Added NFO endpoints, fetchOHLC endpoint

### Cache Files
- `backend/data/nfo_instruments.csv` - NFO instruments cache

---

## Common Use Cases

### 1. Get Latest NIFTY Future

```python
futures = market_data_service.get_nfo_futures("NIFTY")
futures = futures.sort_values('expiry')
latest = futures.iloc[0]['tradingsymbol']  # e.g., "NIFTY25DECFUT"
```

### 2. Fetch Intraday Data

```python
df = market_data_service.fetchOHLC("RELIANCE", "5minute", 1, "NSE")
```

### 3. Fetch Historical Data for Backtesting

```python
df = market_data_service.fetchOHLC("INFY", "day", 365, "NSE")
```

### 4. Get Options Chain

```python
calls = market_data_service.get_nfo_options("NIFTY", "CE")
puts = market_data_service.get_nfo_options("NIFTY", "PE")
```

---

## Next Steps

1. **Use in Strategies**: Integrate with strategy backtesting
2. **Pattern Analysis**: Analyze patterns in historical data
3. **Technical Indicators**: Calculate RSI, MACD, etc. from OHLC
4. **Live Data**: Combine with WebSocket for real-time updates

---

## Support

For detailed documentation, see:
- `HISTORICAL_DATA_DOCS.md` - Complete documentation
- Reference Code - Original Kite API example

For issues:
- Check authentication (must be logged in)
- Verify market hours (data only during trading)
- Check symbol names (futures change monthly)

---

## Performance Notes

- Instruments cached for 1 day
- Historical data subject to Kite API rate limits
- NFO instruments: ~38,000 (large file)
- Cache files stored in `data/` directory

---

**Status**: ✅ Fully implemented and tested (Dec 25, 2025)
