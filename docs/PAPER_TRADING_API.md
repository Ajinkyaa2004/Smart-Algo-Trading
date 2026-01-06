# 🚀 Paper Trading API - Quick Reference

## Base URL
```
http://localhost:8000
```

---

## 📊 Market Data Endpoints

### Get Latest Prices
```bash
GET /api/market/prices?symbols=NSE:RELIANCE,NSE:INFY
```

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "prices": {
    "NSE:RELIANCE": {
      "symbol": "NSE:RELIANCE",
      "last_price": 2550.50,
      "timestamp": "2025-12-30 15:30:00"
    }
  }
}
```

### Get Quote (Full Data)
```bash
GET /api/market/quote?symbols=NSE:RELIANCE
```

---

## 💰 Paper Trading Endpoints

### 1. Buy Stock (Simple)
```bash
POST /api/orders/buy
Content-Type: application/json

{
  "symbol": "RELIANCE",
  "quantity": 10,
  "exchange": "NSE",
  "product": "MIS"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Paper trade: BUY 10 RELIANCE",
  "order_id": "PAPER_ABC123",
  "details": {
    "symbol": "RELIANCE",
    "action": "BUY",
    "quantity": 10,
    "exchange": "NSE"
  }
}
```

### 2. Sell Stock (Simple)
```bash
POST /api/orders/sell
Content-Type: application/json

{
  "symbol": "RELIANCE",
  "quantity": 10,
  "exchange": "NSE"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Paper trade: SELL 10 RELIANCE",
  "order_id": "PAPER_XYZ789",
  "details": {
    "symbol": "RELIANCE",
    "action": "SELL",
    "quantity": 10
  }
}
```

---

## 📂 Portfolio Endpoints

### Get Complete Portfolio
```bash
GET /api/paper-trading/portfolio
```

**Response:**
```json
{
  "status": "success",
  "portfolio": {
    "paper_funds": {
      "virtual_capital": 100000.0,
      "available_funds": 75000.0,
      "invested_funds": 25000.0,
      "realized_pnl": 500.0,
      "total_value": 100500.0
    },
    "paper_portfolio": [
      {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "quantity": 10,
        "average_price": 2500.00,
        "current_price": 2550.50,
        "invested_amount": 25000.0,
        "current_value": 25505.0,
        "unrealized_pnl": 505.0,
        "pnl_percent": 2.02
      }
    ],
    "statistics": {
      "total_positions": 1,
      "total_unrealized_pnl": 505.0,
      "total_realized_pnl": 500.0,
      "total_pnl": 1005.0,
      "trades_today": 5
    }
  }
}
```

### Get Open Positions
```bash
GET /api/paper-trading/positions
```

### Get Virtual Funds
```bash
GET /api/paper-trading/funds
```

---

## 📜 Trade History

### Get All Trades
```bash
GET /api/paper-trading/trades
# OR
GET /api/paper-trading/history
```

**Response:**
```json
{
  "status": "success",
  "trades": [
    {
      "timestamp": "2025-12-30T09:30:00",
      "order_id": "PAPER_ABC123",
      "symbol": "RELIANCE",
      "action": "BUY",
      "quantity": 10,
      "price": 2500.00,
      "value": 25000.0,
      "tag": "paper_trading"
    },
    {
      "timestamp": "2025-12-30T15:30:00",
      "order_id": "PAPER_XYZ789",
      "symbol": "RELIANCE",
      "action": "SELL",
      "quantity": 10,
      "price": 2550.50,
      "value": 25505.0,
      "tag": "paper_trading"
    }
  ],
  "total_trades": 2
}
```

---

## 📈 Performance Statistics

### Get Stats
```bash
GET /api/paper-trading/stats
```

**Response:**
```json
{
  "status": "success",
  "stats": {
    "total_trades": 10,
    "winning_trades": 7,
    "losing_trades": 3,
    "win_rate": 70.0,
    "avg_profit": 300.0,
    "avg_loss": -150.0,
    "avg_pnl": 150.0,
    "best_trade": 800.0,
    "worst_trade": -300.0,
    "profit_factor": 2.33,
    "total_profit": 2100.0,
    "total_loss": 450.0
  }
}
```

---

## 🔄 Portfolio Management

### Reset Portfolio
```bash
POST /api/paper-trading/reset
```

**Response:**
```json
{
  "status": "success",
  "message": "Paper portfolio reset to ₹1,00,000",
  "funds": {
    "virtual_capital": 100000.0,
    "available_funds": 100000.0,
    "invested_funds": 0.0,
    "realized_pnl": 0.0
  }
}
```

---

## 🌐 Market Status

### Check Market Hours
```bash
GET /api/market/status
```

**Response:**
```json
{
  "status": "success",
  "market_status": "OPEN",
  "session": "normal_trading",
  "current_time": "2025-12-30 10:30:00 IST",
  "is_streaming_recommended": true,
  "next_close": "2025-12-30 15:30:00 IST"
}
```

---

## 🎯 Complete Trading Flow Example

### Step 1: Check Market Status
```bash
curl http://localhost:8000/api/market/status
```

### Step 2: Get Current Price
```bash
curl "http://localhost:8000/api/market/prices?symbols=NSE:RELIANCE"
```

### Step 3: Buy Stock
```bash
curl -X POST http://localhost:8000/api/orders/buy \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "quantity": 10,
    "exchange": "NSE"
  }'
```

### Step 4: Check Portfolio
```bash
curl http://localhost:8000/api/paper-trading/portfolio
```

### Step 5: Monitor Live P&L
```bash
# Call this repeatedly or use auto-refresh in UI
curl http://localhost:8000/api/paper-trading/portfolio
```

### Step 6: Sell Stock
```bash
curl -X POST http://localhost:8000/api/orders/sell \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "quantity": 10,
    "exchange": "NSE"
  }'
```

### Step 7: View Trade History
```bash
curl http://localhost:8000/api/paper-trading/history
```

### Step 8: Check Performance
```bash
curl http://localhost:8000/api/paper-trading/stats
```

---

## 💡 Usage Tips

1. **Auto-Refresh**: The frontend automatically refreshes portfolio data every 5 seconds
2. **Real-time P&L**: Unrealized P&L updates with live market prices
3. **Fund Tracking**: All virtual fund changes are tracked automatically
4. **Safety**: All trades are simulated - NO real money involved
5. **Reset**: Use `/reset` endpoint to start fresh anytime

---

## 🔗 API Documentation

Full interactive API docs available at:
```
http://localhost:8000/docs
```

---

## ⚠️ Important Notes

- **Paper Trading Only**: No real orders are placed
- **Market Data**: Uses real live/historical data
- **Virtual Capital**: Starts at ₹1,00,000
- **Safe Testing**: Perfect for strategy testing without risk
- **No Real Money**: Zero financial risk

---

**Happy Paper Trading! 📊💰**
