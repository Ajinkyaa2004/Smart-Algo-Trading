# 🤖 Trading Bot Complete Guide

## Overview
Your trading bot is now fully implemented and ready to trade! It integrates all the components you've built:
- ✅ Price action patterns (Doji, Hammer, Shooting Star, Marubozu, Pivot Points, Slope)
- ✅ Technical indicators (ATR, MACD, Supertrend, RSI, EMA)
- ✅ Strategy deployment (Supertrend, EMA+RSI, Renko+MACD)
- ✅ Tick data streaming and storage
- ✅ Real-time signal generation
- ✅ Automated order execution
- ✅ Position management
- ✅ Auto square-off at 3:15 PM

---

## Quick Start

### 1️⃣ Authentication
```bash
cd backend
python test_auth.py
```
This will:
- Open Kite login page in browser
- Store your session
- Verify authentication

### 2️⃣ Test Trading Bot
```bash
python test_trading_bot.py
```
This verifies:
- All modules load correctly
- Authentication is active
- Market hours detection works
- Bot can start/stop properly

### 3️⃣ Start Backend
```bash
python main.py
```
Backend runs on: `http://localhost:8000`

### 4️⃣ Start Frontend
```bash
cd ..  # Back to project root
npm run dev
```
Frontend runs on: `http://localhost:5173`

### 5️⃣ Open Browser
Navigate to: `http://localhost:5173`
- Login if needed
- Go to **Trading Bot** page (sidebar)

---

## Trading Bot UI

### Configuration Panel
1. **Select Strategy**:
   - 🎯 **Supertrend**: Multi-timeframe with trailing SL
   - 📊 **EMA + RSI**: Crossover with momentum confirmation
   - 🧱 **Renko + MACD**: Noise-filtered trend following

2. **Set Capital**: Amount per symbol (default: ₹3000)

3. **Enable Storage** (optional): Store tick data in SQLite

4. **Select Symbols**: Choose from 20 NSE stocks
   - RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK
   - SBIN, BHARTIARTL, KOTAKBANK, HINDUNILVR, ITC
   - LT, AXISBANK, MARUTI, BAJFINANCE, ASIANPAINT
   - WIPRO, TITAN, TECHM, ULTRACEMCO, SUNPHARMA

### Bot Controls
- 🟢 **Start Bot**: Begin automated trading
- 🟡 **Pause**: Stop generating new signals (keep positions)
- ▶️ **Resume**: Continue signal generation
- 🔴 **Stop & Square Off**: Close all positions and stop

### Status Dashboard
Real-time display of:
- **Bot Status**: Running / Paused / Stopped
- **Active Strategies**: Number of symbols being traded
- **Positions**: Current open positions
- **Signals Today**: Total signals generated
- **P&L Today**: Today's profit/loss

---

## How It Works

### 1. Strategy Initialization
When you start the bot:
```python
bot.start(
    symbols=["RELIANCE", "TCS", "INFY"],
    strategy_type="supertrend",
    capital_per_symbol=3000.0
)
```

For each symbol, the bot:
- Creates a strategy instance
- Fetches historical data (last 200 candles)
- Initializes indicators
- Starts monitoring

### 2. Real-Time Processing
The bot runs a monitoring loop every 60 seconds:

```python
def _bot_loop():
    while not stop_flag:
        # Check market hours
        if not is_market_open():
            continue
            
        # Process each strategy
        for strategy in strategies:
            signal = strategy.generate_signal()
            if signal:
                execute_signal(signal)
                
        # Auto square-off at 3:15 PM
        if time == "15:15":
            square_off_all_positions()
```

### 3. Signal Generation

#### Supertrend Strategy
```python
if price > st1 and price > st2 and price > st3:
    signal = "BUY"
    stop_loss = weighted_average(st1, st2, st3)
```

#### EMA + RSI Strategy
```python
if ema_short > ema_long and rsi < oversold:
    signal = "BUY"
    stop_loss = recent_low
```

#### Renko + MACD Strategy
```python
if brick_count >= 2 and macd_crossover == "bullish":
    signal = "BUY"
    stop_loss = brick_lower_limit - (2 * brick_size)
```

### 4. Order Execution
When a signal is generated:
```python
def _execute_signal(signal):
    # Place market order
    order = place_market_order_with_sl(
        symbol=signal.symbol,
        transaction_type=signal.action,
        quantity=signal.quantity,
        stop_loss=signal.stop_loss
    )
    
    # Track position
    active_positions[symbol] = {
        "entry_price": order.price,
        "quantity": order.quantity,
        "stop_loss": signal.stop_loss
    }
```

### 5. Position Management
The bot monitors:
- **Stop Loss Hits**: Automatically exits if SL triggered
- **Target Hits**: Books profit at target
- **Trailing Stop Loss**: Adjusts SL as price moves favorably
- **Time-Based Exit**: Squares off all at 3:15 PM

---

## Strategy Details

### 🎯 Supertrend Strategy
**Best for**: Trending markets

**Indicators**:
- Supertrend 1 (10, 3)
- Supertrend 2 (11, 2)
- Supertrend 3 (12, 1)

**Entry Rules**:
- BUY: Price above all 3 supertrends
- SELL: Price below all 3 supertrends

**Stop Loss**: Weighted average (60% closest, 40% second)

**Exit**: SL hit or auto square-off

---

### 📊 EMA + RSI Strategy
**Best for**: Momentum + mean reversion

**Indicators**:
- EMA Short (12)
- EMA Long (26)
- RSI (14)

**Entry Rules**:
- BUY: EMA short > EMA long AND RSI < 30
- SELL: EMA short < EMA long AND RSI > 70

**Stop Loss**: Recent swing low/high

**Exit**: SL hit or auto square-off

---

### 🧱 Renko + MACD Strategy
**Best for**: Noise-filtered trends

**Indicators**:
- Renko Bricks (0.5% size)
- MACD (12, 26, 9)

**Entry Rules**:
- BUY: 2+ green bricks AND MACD bullish crossover
- SELL: 2+ red bricks AND MACD bearish crossover

**Stop Loss**: 2 bricks below/above entry

**Exit**: SL hit or auto square-off

---

## API Endpoints

### Start Bot
```bash
POST http://localhost:8000/api/bot/start
Content-Type: application/json

{
  "symbols": ["RELIANCE", "TCS"],
  "strategy_type": "supertrend",
  "capital_per_symbol": 3000,
  "enable_tick_storage": false
}
```

### Stop Bot
```bash
POST http://localhost:8000/api/bot/stop
Content-Type: application/json

{
  "square_off_positions": true
}
```

### Get Status
```bash
GET http://localhost:8000/api/bot/status
```

Response:
```json
{
  "status": "success",
  "bot": {
    "status": "running",
    "active_strategies": 2,
    "active_positions": 1,
    "signals_generated": 5,
    "orders_placed": 3,
    "trades_today": 3,
    "pnl_today": 450.50
  }
}
```

### Pause Bot
```bash
POST http://localhost:8000/api/bot/pause
```

### Resume Bot
```bash
POST http://localhost:8000/api/bot/resume
```

### Get Positions
```bash
GET http://localhost:8000/api/bot/positions
```

---

## Safety Features

### 1. Market Hours Check
Bot only trades during market hours (9:15 AM - 3:30 PM)

### 2. Auto Square-Off
All positions closed at 3:15 PM automatically

### 3. Stop Loss Protection
Every trade has a calculated stop loss

### 4. Position Limits
Capital per symbol prevents over-exposure

### 5. Authentication Check
Bot won't start without valid Kite session

---

## Monitoring

### Real-Time Metrics
The bot tracks:
- Active strategies count
- Open positions
- Signals generated today
- Orders placed today
- Total trades
- P&L today

### Logs
Check console for:
- Strategy initialization
- Signal generation
- Order execution
- Position updates
- Errors

---

## Troubleshooting

### Bot Won't Start
**Issue**: "Not authenticated"
**Solution**: Run `python test_auth.py`

**Issue**: "Market is closed"
**Solution**: Wait for market hours (9:15 AM - 3:30 PM)

### No Signals Generated
**Issue**: Strategy not triggering
**Solutions**:
- Check if market is moving
- Verify historical data loaded
- Try different strategy
- Reduce capital per symbol

### Orders Not Placing
**Issue**: Insufficient margin
**Solution**: Reduce capital_per_symbol

**Issue**: Invalid symbol
**Solution**: Use NSE symbols (RELIANCE, not RELIANCE.NS)

### Frontend Not Connecting
**Issue**: Connection refused
**Solution**: Ensure backend is running on port 8000

---

## Testing Recommendations

### Paper Trading
Before live trading:
1. Start bot with small capital (₹500-1000)
2. Monitor for 1 day
3. Review signals and orders
4. Check P&L accuracy
5. Verify auto square-off works

### Strategy Testing
Test each strategy separately:
1. Start with 1 symbol
2. Run for full day
3. Review trades
4. Calculate win rate
5. Adjust parameters if needed

---

## Next Steps

### 1. Monitor Performance
Track metrics daily:
- Win rate
- Average profit/loss
- Maximum drawdown
- Sharpe ratio

### 2. Optimize Parameters
Adjust based on performance:
- Stop loss percentage
- Target profit
- Capital allocation
- Symbol selection

### 3. Add More Strategies
Expand strategy library:
- Breakout patterns
- Support/resistance
- Volume analysis
- Multi-timeframe confirmation

### 4. Enhance Risk Management
Implement:
- Position sizing based on volatility
- Maximum daily loss limit
- Correlation-based diversification
- Time-based position limits

---

## Important Notes

⚠️ **Risk Disclaimer**
- Trading involves risk
- Past performance ≠ future results
- Test thoroughly before live trading
- Start with small capital
- Never invest more than you can afford to lose

🔒 **Security**
- Keep API credentials secure
- Don't share access token
- Use environment variables for secrets
- Log out after trading

📊 **Market Data**
- Ensure stable internet connection
- WebSocket interruptions handled automatically
- Historical data refreshed every 60 seconds

---

## Support

If you encounter issues:
1. Check `test_trading_bot.py` output
2. Review backend logs
3. Verify authentication
4. Check market hours
5. Test with 1 symbol first

---

**Your trading bot is ready! Happy Trading! 🚀**
