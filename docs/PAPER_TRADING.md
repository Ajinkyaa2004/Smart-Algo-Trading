# Paper Trading System

The paper trading system has been upgraded to provide a robust, persistent simulation of trading.

## Features
- **Persistence**: All trades, orders, and positions are saved to MongoDB. You can restart the server without losing your paper portfolio.
- **Real-time Updates**: P&L is calculated using real-time market data (LTP).
- **Risk Management**: Enforces daily loss limits, max positions, and fund availability.
- **UI Integration**: Fully integrated with the Dashboard.

## Requirements
- **MongoDB**: You must have MongoDB running locally (`mongodb://localhost:27017`).
  - Check status: `pgrep -x mongod`
  - Start if needed: `brew services start mongodb-community` (on Mac)

## Configuration
To switch between Paper Trading and Live Trading, edit `backend/app/config.py`:

```python
# Set to True for Simulation (Safe)
# Set to False for REAL TRADING (Zerodha)
PAPER_TRADING = True
```

## Testing
You can place a test trade to verify the system:
```bash
curl -X POST http://localhost:8000/api/paper-trading/test-trade
```
This will buy 10 Qty of RELIANCE in your paper portfolio.
