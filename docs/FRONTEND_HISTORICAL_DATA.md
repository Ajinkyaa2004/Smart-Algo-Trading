# 🎨 Historical Data - Frontend Integration Guide

## ✅ What Was Added to Frontend

I've created a complete frontend interface for your historical data functionality!

---

## 📍 Where to See It

### **Option 1: New "Historical Data" Page** ⭐ RECOMMENDED

**Location:** Navigate to **Historical Data** in the sidebar

**Features:**
- 📊 Fetch historical OHLC data for any symbol
- 📈 Interactive candlestick charts
- 📉 Support for NSE, BSE, and NFO exchanges
- ⏱️ Multiple intervals (1min to daily)
- 💾 Export data to CSV
- 🔍 Search instruments
- 📋 Browse NFO futures

**How to Access:**
1. Start your frontend: `npm run dev`
2. Login to the app
3. Click **"Historical Data"** in the left sidebar (Database icon)

---

## 🚀 Quick Start Guide

### Step 1: Start Backend & Frontend

```bash
# Terminal 1: Start backend
cd backend
source ../venv/bin/activate  # If not already activated
python main.py

# Terminal 2: Start frontend
cd /Users/ajinkya/Desktop/smart-algo-trade
npm run dev
```

### Step 2: Access Historical Data Page

1. Open browser: `http://localhost:5173`
2. Login with Zerodha credentials (if not already logged in)
3. Click **"Historical Data"** in sidebar (look for Database icon 🗄️)

### Step 3: Fetch Data

**Example: Get RELIANCE 5-minute data**
1. Symbol: `RELIANCE`
2. Exchange: `NSE`
3. Interval: `5 Minutes`
4. Duration: `4` days
5. Click **"Fetch Historical Data"**

**Example: Get NIFTY Futures data**
1. Click **"NFO Futures"** button (top right)
2. Browse available NIFTY futures
3. Copy a symbol (e.g., `NIFTY25DECFUT`)
4. Paste in Symbol field
5. Change Exchange to `NFO`
6. Click **"Fetch Historical Data"**

---

## 🎨 Frontend Components Created

### 1. **HistoricalDataPanel.tsx** (Component)
**Location:** `src/components/HistoricalDataPanel.tsx`

**Features:**
- Input form for symbol, exchange, interval, duration
- Fetch button with loading state
- Data table showing last 10 candles
- Export to CSV functionality
- Summary statistics (Open, High, Low, Close, Volume)

**Props:**
```typescript
interface HistoricalDataPanelProps {
  onDataFetched?: (data: any[]) => void;
}
```

---

### 2. **HistoricalData.tsx** (Page)
**Location:** `src/pages/HistoricalData.tsx`

**Features:**
- Full page layout with header
- HistoricalDataPanel integration
- Candlestick chart display
- NFO Futures browser
- Instrument search
- Info cards showing available exchanges/intervals
- Quick guide section

---

## 📊 Features Available

### ✅ Data Fetching
- **Exchanges:** NSE, BSE, NFO
- **Intervals:** 1min, 3min, 5min, 15min, 30min, 60min, daily
- **Duration:** 1-365 days
- **Real-time:** Fetches live data from backend API

### ✅ Visualization
- **Candlestick Chart:** Powered by ApexCharts
- **Volume Chart:** Displays trading volume
- **Technical Indicators:** EMA20, EMA50, RSI (toggle on/off)
- **Interactive:** Zoom, pan, tooltip

### ✅ Data Export
- **CSV Download:** Export fetched data to CSV
- **Formatted Names:** `SYMBOL_INTERVAL_DURATION.csv`
- **Full Data:** All columns included

### ✅ NFO Support
- **Browse Futures:** View all NIFTY futures contracts
- **Expiry Dates:** See contract expiry
- **Lot Sizes:** View lot size information
- **Quick Fetch:** Click to fetch data for any contract

### ✅ Search
- **Instrument Search:** Find any NSE/BSE instrument
- **Real-time:** Searches backend API
- **Results:** Shows matching instruments

---

## 🖼️ Screenshots Guide

### Main Historical Data Page
```
┌─────────────────────────────────────────────────────────────┐
│ 🗄️ Historical Data                         [NFO Futures] [🔍Search] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Info Cards: Exchanges | Intervals | Instruments]         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Historical Data Panel                                 │ │
│  │ Symbol: [RELIANCE]  Exchange: [NSE ▼]                │ │
│  │ Interval: [5minute ▼]  Duration: [4]                 │ │
│  │                    [Fetch Historical Data]            │ │
│  │                                                       │ │
│  │ Fetched 225 candles                                  │ │
│  │ [Export CSV]                                         │ │
│  │                                                       │ │
│  │ Latest: O: 1560.9 H: 1562.0 L: 1556.1 C: 1558.0     │ │
│  │                                                       │ │
│  │ [Data Table - Last 10 Candles]                       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 📈 Price Chart                                        │ │
│  │ [Candlestick Chart with Volume]                      │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints Used

The frontend connects to these backend endpoints:

```typescript
// Fetch historical data (main feature)
POST http://localhost:8000/api/market/fetchOHLC
Body: { ticker, interval, duration, exchange }

// Get NFO futures
GET http://localhost:8000/api/market/nfo/futures?underlying=NIFTY

// Search instruments
GET http://localhost:8000/api/market/instruments/search/{query}

// Look up instrument token
GET http://localhost:8000/api/market/instrument-lookup/{symbol}?exchange=NSE
```

---

## 🎯 Usage Examples

### Example 1: Intraday Analysis
```
Symbol: RELIANCE
Exchange: NSE
Interval: 5 Minutes
Duration: 1 day

Result: Get today's 5-minute candles for RELIANCE
```

### Example 2: Historical Trends
```
Symbol: INFY
Exchange: NSE
Interval: Daily
Duration: 365 days

Result: Get 1 year of daily data for INFY
```

### Example 3: Futures Analysis
```
1. Click "NFO Futures" button
2. Find "NIFTY25DECFUT" in table
3. Use symbol in form
Symbol: NIFTY25DECFUT
Exchange: NFO
Interval: 5 Minutes
Duration: 4 days

Result: Get recent futures data with chart
```

---

## 🎨 Customization

### Change Chart Colors
Edit `ApexCandlestickChart.tsx`:
```typescript
// Find the colors section in options
colors: {
  up: '#10b981',    // Green for bullish
  down: '#ef4444'   // Red for bearish
}
```

### Add More Intervals
Edit `HistoricalDataPanel.tsx`:
```tsx
<select value={interval} onChange={...}>
  <option value="minute">1 Minute</option>
  <option value="2minute">2 Minutes</option>  // Add this
  <option value="3minute">3 Minutes</option>
  ...
</select>
```

### Change Default Values
Edit `HistoricalDataPanel.tsx`:
```tsx
const [symbol, setSymbol] = useState('TCS');        // Change default symbol
const [interval, setInterval] = useState('15minute'); // Change default interval
const [duration, setDuration] = useState(7);         // Change default duration
```

---

## 🔧 Troubleshooting

### Issue: "Failed to fetch historical data"
**Solution:**
1. Check backend is running: `http://localhost:8000/`
2. Verify you're logged in (check auth status)
3. Try a different symbol (some may not have data)

### Issue: No chart showing
**Solution:**
1. Ensure data was fetched successfully (check table)
2. Click "Show Chart" if hidden
3. Check browser console for errors

### Issue: NFO Futures button does nothing
**Solution:**
1. Check browser console for results
2. Results are logged, not displayed inline
3. Use the symbol in the main form

### Issue: Search not working
**Solution:**
1. Enter full or partial symbol name
2. Press Enter or click Search button
3. Check console for results

---

## 📱 Mobile Responsive

The interface is fully responsive:
- **Desktop:** Full layout with sidebar
- **Tablet:** Collapsible sidebar
- **Mobile:** Hidden sidebar, hamburger menu

---

## 🚀 Next Steps

### Integration Ideas

1. **Add to Live Market Page**
   - Show historical data alongside live data
   - Compare live vs historical performance

2. **Strategy Backtesting**
   - Use historical data to test strategies
   - Display results on Strategies page

3. **Pattern Detection**
   - Automatically detect patterns in historical data
   - Highlight patterns on chart

4. **Alerts**
   - Set price alerts based on historical levels
   - Support/resistance detection

---

## 📖 Developer Notes

### File Structure
```
src/
├── pages/
│   └── HistoricalData.tsx          # Main page
├── components/
│   ├── HistoricalDataPanel.tsx     # Data fetching panel
│   └── ApexCandlestickChart.tsx    # Chart component (existing)
├── layout/
│   └── Layout.tsx                  # Updated with nav item
└── App.tsx                         # Updated with route
```

### State Management
```typescript
// Main page state
const [chartData, setChartData] = useState<CandlestickData[]>([]);
const [showChart, setShowChart] = useState(true);
const [nfoFutures, setNfoFutures] = useState<any[]>([]);

// Panel state
const [symbol, setSymbol] = useState('RELIANCE');
const [exchange, setExchange] = useState('NSE');
const [interval, setInterval] = useState('5minute');
const [duration, setDuration] = useState(4);
const [loading, setLoading] = useState(false);
const [data, setData] = useState<any[]>([]);
```

### Adding More Features

To add new features, modify:
1. `HistoricalDataPanel.tsx` - For form controls
2. `HistoricalData.tsx` - For page-level features
3. Backend API - For new data sources

---

## ✅ Summary

**What You Can Do Now:**

✅ Fetch historical data for any stock/index/future  
✅ View interactive candlestick charts  
✅ Export data to CSV  
✅ Browse NFO futures contracts  
✅ Search for instruments  
✅ Analyze with technical indicators  
✅ Use multiple timeframes and intervals  

**How to Access:**

1. Start backend: `python main.py`
2. Start frontend: `npm run dev`
3. Navigate to **"Historical Data"** in sidebar
4. Start analyzing! 📊

---

**Need Help?** Check the backend documentation:
- `HISTORICAL_DATA_SUMMARY.md` - Overview
- `HISTORICAL_DATA_QUICK_REF.md` - Quick reference
- `HISTORICAL_DATA_DOCS.md` - Complete API docs
