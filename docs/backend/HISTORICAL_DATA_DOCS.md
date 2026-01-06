# Historical Data Implementation

This document explains the implementation of historical data fetching functionality based on the Kite API reference code.

## Overview

The reference code demonstrates how to:
1. Fetch NFO (derivatives) instruments
2. Look up instrument tokens by symbol
3. Fetch historical OHLC data for any instrument

Our implementation provides the same functionality with improvements:
- Better error handling
- Caching for performance
- RESTful API endpoints
- Both service layer and API layer access

---

## Reference Code Analysis

### Original Code Structure

```python
# 1. Get NFO instruments dump
instrument_dump = kite.instruments("NFO")
instrument_df = pd.DataFrame(instrument_dump)
fut_df = instrument_df[instrument_df["segment"]=="NFO-FUT"]

# 2. Instrument lookup function
def instrumentLookup(instrument_df, symbol):
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1

# 3. Fetch OHLC function
def fetchOHLC(ticker, interval, duration):
    instrument = instrumentLookup(instrument_df, ticker)
    data = pd.DataFrame(kite.historical_data(
        instrument,
        dt.date.today()-dt.timedelta(duration),
        dt.date.today(),
        interval
    ))
    data.set_index("date", inplace=True)
    return data

# 4. Usage
fetchOHLC("NIFTY20MAYFUT", "5minute", 4)
```

---

## Our Implementation

### Service Layer (`app/services/market_data.py`)

#### 1. NFO Instruments

```python
# Fetch all NFO instruments
nfo_df = market_data_service.fetch_nfo_instruments()

# Get only futures
futures_df = market_data_service.get_nfo_futures()

# Get futures for specific underlying
nifty_futures = market_data_service.get_nfo_futures("NIFTY")

# Get options
nifty_options = market_data_service.get_nfo_options("NIFTY", "CE")
```

#### 2. Instrument Lookup

```python
# Direct method (matches reference code)
token = market_data_service.instrument_lookup("NIFTY20MAYFUT", "NFO")

# Alternative method
token = market_data_service.get_instrument_token("RELIANCE", "NSE")
```

#### 3. Fetch OHLC (Convenience Method)

```python
# Simple interface (matches reference code)
df = market_data_service.fetchOHLC(
    ticker="NIFTY20MAYFUT",
    interval="5minute",
    duration=4,
    exchange="NFO"
)

# Returns DataFrame with date index, just like reference code
```

#### 4. Advanced Historical Data

```python
# More control over date ranges
df = market_data_service.get_historical_data_by_symbol(
    symbol="RELIANCE",
    exchange="NSE",
    from_date=datetime(2024, 1, 1),
    to_date=datetime(2024, 12, 25),
    interval="day"
)
```

---

## API Endpoints

### NFO Instruments

```http
GET /market-data/nfo/instruments
```

Get all NFO instruments.

**Query Parameters:**
- `force_refresh` (bool): Force API refresh

**Example Response:**
```json
{
  "status": "success",
  "exchange": "NFO",
  "count": 5000,
  "instruments": [...]
}
```

---

```http
GET /market-data/nfo/futures?underlying=NIFTY
```

Get NFO futures contracts.

**Query Parameters:**
- `underlying` (string): Filter by underlying (e.g., NIFTY, BANKNIFTY)

---

```http
GET /market-data/nfo/options?underlying=NIFTY&option_type=CE
```

Get NFO options contracts.

**Query Parameters:**
- `underlying` (string): Filter by underlying
- `option_type` (string): CE (Call) or PE (Put)

---

### Instrument Lookup

```http
GET /market-data/instrument-lookup/NIFTY20MAYFUT?exchange=NFO
```

Look up instrument token for a symbol.

**Response:**
```json
{
  "status": "success",
  "symbol": "NIFTY20MAYFUT",
  "exchange": "NFO",
  "instrument_token": 12345678
}
```

---

### Historical Data (Convenience)

```http
POST /market-data/fetchOHLC
Content-Type: application/json

{
  "ticker": "NIFTY20MAYFUT",
  "interval": "5minute",
  "duration": 4,
  "exchange": "NFO"
}
```

**Intervals:**
- `minute`, `3minute`, `5minute`, `10minute`, `15minute`, `30minute`, `60minute`, `day`

**Response:**
```json
{
  "status": "success",
  "ticker": "NIFTY20MAYFUT",
  "interval": "5minute",
  "duration": 4,
  "count": 250,
  "data": [
    {
      "date": "2024-12-25 09:15:00",
      "open": 23500.0,
      "high": 23520.0,
      "low": 23495.0,
      "close": 23510.0,
      "volume": 50000
    },
    ...
  ]
}
```

---

### Historical Data (Advanced)

```http
POST /market-data/historical
Content-Type: application/json

{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "from_date": "2024-12-01",
  "to_date": "2024-12-25",
  "interval": "day"
}
```

---

```http
GET /market-data/historical/quick?symbol=RELIANCE&days=30&interval=day
```

Quick fetch of last N days.

---

## Usage Examples

### Example 1: Fetch NFO Futures (Like Reference Code)

```python
from app.services.market_data import market_data_service

# Get NFO instruments
instrument_df = market_data_service.fetch_nfo_instruments()

# Filter for futures
fut_df = market_data_service.get_nfo_futures()

# Fetch OHLC data
data = market_data_service.fetchOHLC("NIFTY20MAYFUT", "5minute", 4, "NFO")
print(data)
```

### Example 2: Using the API

```bash
# Get NIFTY futures
curl http://localhost:8000/market-data/nfo/futures?underlying=NIFTY

# Fetch historical data
curl -X POST http://localhost:8000/market-data/fetchOHLC \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "NIFTY20MAYFUT",
    "interval": "5minute",
    "duration": 4,
    "exchange": "NFO"
  }'
```

### Example 3: Python Script (Standalone)

See `example_historical_data.py` for a script that matches the reference code structure.

```bash
cd backend
python example_historical_data.py
```

---

## Testing

### Run Test Suite

```bash
cd backend
python test_historical_data.py
```

This will test:
1. NFO instruments fetching
2. Instrument lookup
3. fetchOHLC convenience method
4. Direct historical data API

### Run Simple Example

```bash
cd backend
python example_historical_data.py
```

This runs a script similar to the reference code.

---

## Key Improvements Over Reference Code

1. **Caching**: Instruments are cached for 1 day to reduce API calls
2. **Error Handling**: Better error messages and fallback to cached data
3. **Multiple Exchanges**: Supports NSE, BSE, NFO seamlessly
4. **RESTful API**: Can be used from frontend or other services
5. **Type Safety**: Proper type hints and validation
6. **Documentation**: Comprehensive docstrings and examples

---

## File Structure

```
backend/
├── app/
│   ├── services/
│   │   └── market_data.py          # Service layer implementation
│   └── api/
│       └── market_data.py          # API endpoints
├── data/
│   ├── instruments.csv             # NSE/BSE instruments cache
│   └── nfo_instruments.csv         # NFO instruments cache
├── test_historical_data.py         # Comprehensive test suite
└── example_historical_data.py      # Simple example (like reference)
```

---

## Configuration

No additional configuration needed. The service uses the existing Kite authentication from `kite_auth.py`.

Ensure you're authenticated:
1. Run backend: `python main.py`
2. Visit: `http://localhost:8000/auth/login`
3. Complete Zerodha login

---

## API Response Format

All endpoints return consistent format:

```json
{
  "status": "success",
  "data": [...],
  "count": 100
}
```

Error format:
```json
{
  "detail": "Error message"
}
```

---

## Performance Considerations

1. **Caching**: Instruments are cached for 1 day
2. **Pagination**: Large responses are limited (100 items default)
3. **Date Ranges**: Historical data limited to Kite API constraints
4. **Rate Limiting**: Subject to Zerodha API rate limits

---

## Common Issues & Solutions

### Symbol Not Found

**Problem**: `Symbol 'NIFTY20MAYFUT' not found`

**Solution**: 
- Futures symbols change monthly (e.g., NIFTY24DECFUT, NIFTY25JANFUT)
- Use `get_nfo_futures("NIFTY")` to see available contracts
- Sort by expiry to get nearest month

### No Data Returned

**Problem**: Empty DataFrame returned

**Solution**:
- Check market hours (data only available during/after trading)
- Verify symbol exists for the date range
- Check if it's a trading day (not weekend/holiday)

### Authentication Error

**Problem**: `Authentication failed`

**Solution**:
- Ensure you're logged in via `/auth/login`
- Check if access token is valid (expires daily)
- Re-authenticate if necessary

---

## Next Steps

1. **Strategy Integration**: Use historical data in strategy backtesting
2. **Pattern Detection**: Analyze historical data for patterns
3. **Indicators**: Calculate technical indicators from OHLC data
4. **Live Data**: Combine with WebSocket for real-time updates

---

## References

- Reference Code: Mayank Rasu (http://rasuquant.com/wp/)
- Kite Connect Docs: https://kite.trade/docs/connect/v3/
- Historical Data API: https://kite.trade/docs/connect/v3/market-quotes/#historical-data
