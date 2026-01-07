# Trading History Feature Documentation

## Overview
The Trading History feature provides comprehensive analytics and visualization of all trading activity, including profit/loss tracking, strategy performance analysis, and detailed trade records.

## Features

### 1. **Overview Statistics**
- **Total P&L**: Cumulative profit/loss across all trades
- **Win Rate**: Percentage of profitable trades
- **Total Trades**: Number of completed trades
- **Profit Factor**: Ratio of total profit to total loss

### 2. **Best & Worst Trades**
- Highlights the most profitable and least profitable trades
- Shows symbol, P&L, and strategy used

### 3. **Visualizations**

#### P&L Over Time (Area Chart)
- Shows cumulative P&L progression over time
- Helps identify profitable periods and trends
- Configurable time range (7, 30, 90, 365 days)

#### Strategy Usage Distribution (Pie Chart)
- Visual breakdown of which strategies are used most frequently
- Helps identify strategy preferences

#### Strategy Performance Comparison (Bar Chart)
- Compares total P&L and win rate across different strategies
- Identifies which strategies are most profitable

### 4. **Strategy Analytics Table**
Detailed breakdown for each strategy:
- Total Trades
- Win Rate (%)
- Total P&L
- Average P&L per trade
- Best Trade
- Worst Trade

### 5. **Detailed Trade History Table**
Complete trade log with:
- Date/Time
- Symbol
- Strategy used
- Action (BUY/SELL)
- Quantity
- Entry Price
- Exit Price
- P&L (amount and percentage)
- Status (OPEN/CLOSED)

### 6. **Filters**
- **Time Range**: Last 7/30/90/365 days
- **Status**: All, Open, Closed
- **Strategy**: Filter by specific strategy

## API Endpoints

### Base URL: `http://localhost:8000/api/history`

#### 1. Get Trade History
```
GET /trades
Query Parameters:
  - limit: Maximum number of trades to return
  - skip: Number of trades to skip (pagination)
  - strategy: Filter by strategy name
  - symbol: Filter by trading symbol
  - status: Filter by status (OPEN/CLOSED)
  - days: Filter by last N days
```

#### 2. Get Statistics
```
GET /statistics
Query Parameters:
  - days: Calculate stats for last N days (optional)
```

#### 3. Get Strategy Performance
```
GET /strategy-performance
```

#### 4. Get P&L Over Time
```
GET /pnl-over-time
Query Parameters:
  - days: Number of days to look back (default: 30)
  - interval: daily, weekly, or monthly (default: daily)
```

#### 5. Get Complete Summary
```
GET /summary
Returns all data in one call:
  - Statistics
  - Strategy Performance
  - P&L Over Time
  - Recent Trades
```

## MongoDB Schema

### Trade History Collection: `trade_history`
```javascript
{
  _id: ObjectId,
  user_id: String,
  symbol: String,
  strategy: String,
  action: String,  // "BUY" or "SELL"
  quantity: Number,
  entry_price: Number,
  exit_price: Number,
  pnl: Number,
  pnl_percentage: Number,
  entry_time: Date,
  exit_time: Date,
  status: String,  // "OPEN" or "CLOSED"
  order_id: String,
  duration_minutes: Number,
  created_at: Date,
  updated_at: Date,
  metadata: Object
}
```

### Strategy Performance Collection: `strategy_performance`
```javascript
{
  _id: ObjectId,
  user_id: String,
  strategy: String,
  total_trades: Number,
  winning_trades: Number,
  losing_trades: Number,
  total_pnl: Number,
  win_rate: Number,
  avg_pnl: Number,
  best_trade: Number,
  worst_trade: Number,
  created_at: Date,
  last_updated: Date
}
```

## Integration with Paper Trading

The Trading History feature is automatically integrated with the paper trading system. Trades are logged to MongoDB when:

1. **Position is opened**: Creates a trade record with status "OPEN"
2. **Position is closed**: Updates the trade record with exit price, P&L, and status "CLOSED"
3. **Strategy performance is updated**: Automatically calculates and stores strategy metrics

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend
source ~/smart-algo-venv/bin/activate
pip install pymongo==4.9.2
```

### 2. Configure MongoDB
Add to `backend/.env`:
```
MONGO_URI=mongodb://localhost:27017
# Or for MongoDB Atlas:
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### 3. Start MongoDB (Local)
```bash
# macOS with Homebrew
brew services start mongodb-community

# Or manually
mongod --config /usr/local/etc/mongod.conf
```

### 4. MongoDB Atlas Setup (Cloud)
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster (free tier available)
3. Create database user
4. Whitelist your IP address
5. Get connection string and add to `.env`

### 5. Access the Feature
1. Start backend: `cd backend && ./start_dev.sh`
2. Start frontend: `npm run dev`
3. Navigate to "Trading History" in the sidebar

## Usage Tips

### Viewing Historical Performance
1. Use the time range filter to focus on specific periods
2. Compare strategy performance to identify which strategies work best
3. Analyze P&L trends to understand your trading patterns

### Strategy Optimization
1. Check win rate by strategy
2. Identify strategies with highest profit factor
3. Review best and worst trades to learn from successes and failures

### Export Data
Click "Export CSV" to download trade history for external analysis

## Troubleshooting

### MongoDB Connection Issues
- **Local**: Ensure MongoDB is running (`brew services list`)
- **Atlas**: Check IP whitelist and connection string
- **Error logs**: Check backend console for connection errors

### No Data Showing
- Ensure you have executed trades in paper trading mode
- Check that trades are being logged (backend console shows "✓ Trade logged")
- Verify MongoDB connection is successful

### Performance Issues
- Large datasets may slow down queries
- Use filters to limit data range
- Consider adding indexes (automatically created on startup)

## Future Enhancements

Potential improvements:
- Real-time updates via WebSocket
- Advanced filtering (by P&L range, duration, etc.)
- Comparison with market benchmarks
- Risk metrics (Sharpe ratio, max drawdown)
- Trade journal with notes
- Performance reports (PDF export)
- Backtesting comparison overlay

## Technical Details

### Database Indexes
Automatically created for optimal performance:
- `user_id + timestamp` (descending)
- `user_id + strategy`
- `user_id + symbol`
- `timestamp` (descending)

### Data Retention
- All trade data is persisted indefinitely
- Can be manually cleared via database
- Consider implementing data archival for very old trades

### Multi-User Support
- All data is user-specific (filtered by `user_id`)
- Each user sees only their own trades
- Isolated performance metrics per user
