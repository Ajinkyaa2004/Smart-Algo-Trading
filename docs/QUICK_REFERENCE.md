# ⚡ Smart Algo Trade - Quick Reference

## 🚀 How to Run
**1. Backend:**
```bash
cd backend && source ../venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**2. Frontend:**
```bash
npm run dev
```

**ACCESS:** [http://localhost:3000](http://localhost:3000)

## 📁 System Architecture
- **Backend:** FastAPI (Port 8000)
- **Frontend:** React + Vite (Port 3000)
- **Database:** SQLite (SQLAlchemy)
- **Live Data:** WebSocket (KiteTicker)

---

### 2. Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs

## 📚 Module Overview

### Module 1: Authentication ✅
- Login flow with Kite Connect
- Token persistence (24-hour sessions)
- Auto-restoration on restart

### Module 2: Core API Integrations ✅
- Market data (LTP, quotes, OHLC, historical)
- Order management (place, modify, cancel)
- Portfolio queries (positions, holdings)

### Module 3: Technical Indicators ✅
- Moving averages (SMA, EMA, WMA)
- Momentum (RSI, MACD, Stochastic)
- Volatility (Bollinger Bands, ATR)
- Volume (VWAP)
- Trend (ADX, Supertrend)

### Module 4: Price Action ✅
- Candlestick anatomy analysis
- Support & resistance detection
- Trend identification
- Breakout & rejection logic

### Module 5: Candlestick Patterns ✅
- 10 pattern types (Doji, Hammer, Engulfing, etc.)
- Pattern confidence scoring
- Batch and real-time scanning

## 🔑 Common Code Snippets

### Authenticate
```python
from app.services.kite_auth import kite_auth_service

# Check if authenticated
if kite_auth_service.is_authenticated():
    kite = kite_auth_service.get_kite_instance()
else:
    login_url = kite_auth_service.get_login_url()
    print(f"Login: {login_url}")
```

### Get Market Data
```python
from app.services.market_data import market_data_service
from datetime import datetime, timedelta

# Get LTP
ltp = market_data_service.get_ltp(["NSE:RELIANCE"])

# Get historical data
df = market_data_service.get_historical_data_by_symbol(
    symbol="RELIANCE",
    exchange="NSE",
    from_date=datetime.now() - timedelta(days=30),
    to_date=datetime.now(),
    interval="day"
)
```

### Calculate Indicators
```python
from app.services.indicators import TechnicalIndicators

# RSI
df['rsi'] = TechnicalIndicators.rsi_ema(df['close'], 14)

# MACD
macd, signal, hist = TechnicalIndicators.macd(df['close'])

# Bollinger Bands
upper, middle, lower = TechnicalIndicators.bollinger_bands(df['close'])

# Add all indicators at once
df = TechnicalIndicators.add_all_indicators(df)
```

### Place Orders
```python
from app.services.order_service import order_service

# Market order
order_id = order_service.place_market_order(
    tradingsymbol="RELIANCE",
    exchange="NSE",
    transaction_type="BUY",
    quantity=1,
    product="MIS"
)

# Limit order
order_id = order_service.place_limit_order(
    tradingsymbol="RELIANCE",
    exchange="NSE",
    transaction_type="BUY",
    quantity=1,
    price=2500.00,
    product="MIS"
)

# Stop-loss order
order_id = order_service.place_stoploss_order(
    tradingsymbol="RELIANCE",
    exchange="NSE",
    transaction_type="SELL",
    quantity=1,
    trigger_price=2450.00,
    product="MIS"
)
```

### Get Portfolio
```python
# Get positions
positions = order_service.get_positions()

# Get holdings
holdings = order_service.get_holdings()

# Get orders
orders = order_service.get_orders()

# Get trades
trades = order_service.get_trades()
```

### Price Action Analysis
```python
from app.services.price_action import price_action_service

# Find support/resistance
levels = price_action_service.find_support_resistance(df)

# Identify trend
trend = price_action_service.identify_trend(df, method='ma')
trend_strength = price_action_service.calculate_trend_strength(df)

# Detect breakouts
breakouts = price_action_service.detect_breakout(df, level=2500, direction='up')

# Analyze candle anatomy
df = price_action_service.add_candle_anatomy(df)
```

### Pattern Scanner
```python
from app.services.pattern_scanner import pattern_scanner

# Scan all patterns
matches = pattern_scanner.scan_patterns(df, symbol="RELIANCE")

# Scan specific patterns
specific = pattern_scanner.scan_patterns(
    df,
    symbol="RELIANCE",
    patterns=['bullish_engulfing', 'morning_star']
)

# Scan recent candles
recent = pattern_scanner.scan_latest(df, symbol="RELIANCE", lookback=10)

# Display matches
for match in matches:
    print(f"{match.pattern} on {match.timestamp} @ ₹{match.price:.2f}")


## 🧪 Testing

### Run Tests
```bash
# Authentication test
./venv/bin/python backend/test_auth.py

# Market data & indicators test
./venv/bin/python backend/test_modules_2_3.py

# API verification
./venv/bin/python verify_kite.py
```

### API Testing (curl)
```bash
# Authentication status
curl http://localhost:8000/api/auth/status

# Get LTP
curl "http://localhost:8000/api/market/ltp?symbols=NSE:RELIANCE"

# Get historical data
curl "http://localhost:8000/api/market/historical/quick?symbol=RELIANCE&days=30"

# Calculate RSI
curl "http://localhost:8000/api/indicators/rsi?symbol=RELIANCE&days=30"

# Get positions
curl http://localhost:8000/api/orders/positions
```

## 📊 Indicator Reference

| Indicator | Function | Parameters |
|-----------|----------|------------|
| SMA | `TechnicalIndicators.sma(data, period)` | period=20 |
| EMA | `TechnicalIndicators.ema(data, period)` | period=20 |
| RSI | `TechnicalIndicators.rsi_ema(data, period)` | period=14 |
| MACD | `TechnicalIndicators.macd(data, fast, slow, signal)` | 12, 26, 9 |
| Bollinger | `TechnicalIndicators.bollinger_bands(data, period, std)` | 20, 2.0 |
| VWAP | `TechnicalIndicators.vwap(df)` | - |
| ATR | `TechnicalIndicators.atr(df, period)` | period=14 |
| Stochastic | `TechnicalIndicators.stochastic(df, k, d)` | 14, 3 |
| ADX | `TechnicalIndicators.adx(df, period)` | period=14 |
| Supertrend | `TechnicalIndicators.supertrend(df, period, mult)` | 10, 3.0 |

## 🎯 Trading Strategy Template

```python
from app.services.market_data import market_data_service
from app.services.indicators import TechnicalIndicators
from app.services.order_service import order_service
from datetime import datetime, timedelta

def run_strategy(symbol, exchange="NSE"):
    # 1. Fetch data
    df = market_data_service.get_historical_data_by_symbol(
        symbol=symbol,
        exchange=exchange,
        from_date=datetime.now() - timedelta(days=100),
        to_date=datetime.now(),
        interval="day"
    )
    
    # 2. Calculate indicators
    df['rsi'] = TechnicalIndicators.rsi_ema(df['close'], 14)
    df['sma_20'] = TechnicalIndicators.sma(df['close'], 20)
    df['sma_50'] = TechnicalIndicators.sma(df['close'], 50)
    
    # 3. Generate signal
    latest = df.iloc[-1]
    
    # Example: RSI + MA Crossover
    if latest['rsi'] < 30 and latest['sma_20'] > latest['sma_50']:
        # BUY signal
        order_id = order_service.place_market_order(
            tradingsymbol=symbol,
            exchange=exchange,
            transaction_type="BUY",
            quantity=1,
            product="MIS",
            tag="rsi_ma_strategy"
        )
        return f"BUY: {order_id}"
    
    elif latest['rsi'] > 70 and latest['sma_20'] < latest['sma_50']:
        # SELL signal
        order_id = order_service.place_market_order(
            tradingsymbol=symbol,
            exchange=exchange,
            transaction_type="SELL",
            quantity=1,
            product="MIS",
            tag="rsi_ma_strategy"
        )
        return f"SELL: {order_id}"
    
    return "NO SIGNAL"

# Run strategy
result = run_strategy("RELIANCE")
print(result)
```

## 📁 Project Structure

```
smart-algo-trade/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   └── services/     # Business logic
│   ├── data/             # Session & cache
│   ├── main.py           # FastAPI app
│   └── test_*.py         # Test scripts
├── src/                  # Frontend (React)
├── venv/                 # Python virtual env
└── .env                  # Configuration
```

## 🔧 Configuration

### Environment Variables (`backend/.env`)
```bash
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
DATABASE_URL=sqlite:///./algo_trade.db
SECRET_KEY=dev_secret_key_change_in_prod
```

## 📖 Documentation Files

- `MODULE_1_COMPLETE.md` - Authentication module
- `MODULES_2_3_COMPLETE.md` - Market data & indicators
- `backend/MODULE_1_AUTH.md` - Detailed auth docs
- `QUICK_REFERENCE.md` - This file

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Reinstall dependencies
./venv/bin/pip install -r requirements.txt
```

### Authentication fails
```bash
# Clear session and re-login
rm backend/data/kite_session.json
./venv/bin/python backend/test_auth.py
```

### Module import errors
```bash
# Ensure you're in the right directory
cd backend
python -c "from app.services.kite_auth import kite_auth_service"
```

## 🎓 Learning Resources

- [Kite Connect Docs](https://kite.trade/docs/connect/v3/)
- [Technical Indicators Guide](https://www.investopedia.com/technical-analysis-4689657)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pandas Docs](https://pandas.pydata.org/docs/)

---

**Version**: 2.0.0  
**Last Updated**: 2025-12-24  
**Status**: Modules 1, 2, 3 Complete ✅
