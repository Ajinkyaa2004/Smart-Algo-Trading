import React, { useState, useEffect } from 'react';
import { Eye, TrendingUp, TrendingDown, Plus, X, RefreshCw, Activity } from 'lucide-react';
import { toast } from 'sonner';

interface QuoteData {
  last_price: number;
  volume: number;
  buy_quantity: number;
  sell_quantity: number;
  ohlc: {
    open: number;
    high: number;
    low: number;
    close: number;
  };
  change: number;
}

interface WatchlistItem {
  symbol: string;
  exchange: string;
  fullSymbol: string;
  quote?: QuoteData;
  ltp?: number;
}

const MarketWatch: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([
    { symbol: 'RELIANCE', exchange: 'NSE', fullSymbol: 'NSE:RELIANCE' },
    { symbol: 'INFY', exchange: 'NSE', fullSymbol: 'NSE:INFY' },
    { symbol: 'TCS', exchange: 'NSE', fullSymbol: 'NSE:TCS' }
  ]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<number | null>(null);
  
  // Add symbol state
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newSymbol, setNewSymbol] = useState('');
  const [newExchange, setNewExchange] = useState('NSE');

  useEffect(() => {
    // Initial fetch
    fetchAllData();

    // Setup auto-refresh if enabled
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchAllData(true);
      }, 5000); // Refresh every 5 seconds
      setRefreshInterval(interval);

      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh]);

  const fetchAllData = async (silent = false) => {
    if (!silent) setLoading(true);

    try {
      // Fetch quotes for all symbols
      const symbols = watchlist.map(item => item.fullSymbol).join(',');
      
      const [quoteResponse, ltpResponse] = await Promise.all([
        fetch(`http://localhost:8000/api/market/quote?symbols=${symbols}`),
        fetch(`http://localhost:8000/api/market/ltp?symbols=${symbols}`)
      ]);

      const quoteData = await quoteResponse.json();
      const ltpData = await ltpResponse.json();

      // Update watchlist with new data
      setWatchlist(prevList => 
        prevList.map(item => ({
          ...item,
          quote: quoteData.data?.[item.fullSymbol],
          ltp: ltpData.data?.[item.fullSymbol]?.last_price
        }))
      );

      if (!silent) {
        toast.success('Market data updated');
      }
    } catch (error) {
      console.error('Error fetching market data:', error);
      if (!silent) {
        toast.error('Failed to fetch market data');
      }
    } finally {
      setLoading(false);
    }
  };

  const addSymbol = () => {
    if (!newSymbol.trim()) {
      toast.error('Please enter a symbol');
      return;
    }

    const fullSymbol = `${newExchange}:${newSymbol.toUpperCase()}`;
    
    if (watchlist.some(item => item.fullSymbol === fullSymbol)) {
      toast.error('Symbol already in watchlist');
      return;
    }

    setWatchlist([
      ...watchlist,
      {
        symbol: newSymbol.toUpperCase(),
        exchange: newExchange,
        fullSymbol
      }
    ]);

    setNewSymbol('');
    setShowAddDialog(false);
    toast.success(`Added ${fullSymbol} to watchlist`);
    
    // Fetch data for all symbols including new one
    setTimeout(() => fetchAllData(true), 100);
  };

  const removeSymbol = (fullSymbol: string) => {
    setWatchlist(watchlist.filter(item => item.fullSymbol !== fullSymbol));
    toast.success('Removed from watchlist');
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-400';
    if (change < 0) return 'text-red-400';
    return 'text-zinc-400';
  };

  const getChangeBgColor = (change: number) => {
    if (change > 0) return 'bg-green-500/10 border-green-500/30';
    if (change < 0) return 'bg-red-500/10 border-red-500/30';
    return 'bg-zinc-900 border-zinc-800';
  };

  return (
    <div className="h-full w-full p-4 space-y-4">
      {/* Header */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
              <Eye className="w-7 h-7 text-blue-400" />
              Market Watch
            </h1>
            <p className="text-sm text-zinc-400 mt-1">Real-time quotes and LTP data</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
                autoRefresh
                  ? 'bg-green-500 text-white'
                  : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-800'
              }`}
            >
              <Activity className={`w-4 h-4 ${autoRefresh ? 'animate-pulse' : ''}`} />
              {autoRefresh ? 'Live' : 'Paused'}
            </button>
            <button
              onClick={() => fetchAllData()}
                disabled={loading}
                className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 rounded-lg transition-colors flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button
                onClick={() => setShowAddDialog(true)}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Symbol
              </button>
            </div>
          </div>
        </div>

      <div>
        {/* Add Symbol Dialog */}
        {showAddDialog && (
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-zinc-100">Add Symbol to Watchlist</h3>
              <button
                onClick={() => setShowAddDialog(false)}
                className="text-zinc-400 hover:text-zinc-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Symbol (e.g., RELIANCE, INFY)"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addSymbol()}
                className="flex-1 px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <select
                value={newExchange}
                onChange={(e) => setNewExchange(e.target.value)}
                className="px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="NSE">NSE</option>
                <option value="BSE">BSE</option>
                <option value="NFO">NFO</option>
              </select>
              <button
                onClick={addSymbol}
                className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
              >
                Add
              </button>
            </div>
          </div>
        )}

        {/* Watchlist Grid */}
        {loading && watchlist.length === 0 ? (
          <div className="text-center py-12 text-zinc-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
            Loading market data...
          </div>
        ) : watchlist.length === 0 ? (
          <div className="text-center py-12 text-zinc-400 bg-zinc-950 border border-zinc-800 rounded-lg">
            <Eye className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="mb-4">No symbols in watchlist</p>
            <button
              onClick={() => setShowAddDialog(true)}
              className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors inline-flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Your First Symbol
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {watchlist.map((item) => {
              const quote = item.quote;
              const ltp = item.ltp || quote?.last_price || 0;
              const change = quote?.change || 0;
              const changePercent = quote?.ohlc?.close ? ((ltp - quote.ohlc.close) / quote.ohlc.close * 100) : 0;

              return (
                <div
                  key={item.fullSymbol}
                  className={`bg-zinc-950 border rounded-lg p-6 transition-all hover:border-zinc-700 ${getChangeBgColor(change)}`}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-zinc-100">{item.symbol}</h3>
                      <p className="text-xs text-zinc-500">{item.exchange}</p>
                    </div>
                    <button
                      onClick={() => removeSymbol(item.fullSymbol)}
                      className="text-zinc-500 hover:text-red-400 transition-colors"
                      title="Remove from watchlist"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {/* LTP */}
                  <div className="mb-4">
                    <p className="text-3xl font-bold text-zinc-100">
                      ₹{ltp.toFixed(2)}
                    </p>
                    {quote && (
                      <div className={`flex items-center gap-2 mt-1 ${getChangeColor(change)}`}>
                        {change >= 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        <span className="text-sm font-medium">
                          {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
                        </span>
                      </div>
                    )}
                  </div>

                  {/* OHLC */}
                  {quote?.ohlc && (
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-zinc-500">Open</p>
                        <p className="text-zinc-100 font-medium">₹{quote.ohlc.open.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">High</p>
                        <p className="text-green-400 font-medium">₹{quote.ohlc.high.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">Low</p>
                        <p className="text-red-400 font-medium">₹{quote.ohlc.low.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">Prev Close</p>
                        <p className="text-zinc-100 font-medium">₹{quote.ohlc.close.toFixed(2)}</p>
                      </div>
                    </div>
                  )}

                  {/* Volume */}
                  {quote?.volume && (
                    <div className="mt-4 pt-4 border-t border-zinc-800">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-zinc-500">Volume</span>
                        <span className="text-zinc-100 font-medium">
                          {(quote.volume / 100000).toFixed(2)}L
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Buy/Sell Depth */}
                  {quote?.buy_quantity && quote?.sell_quantity && (
                    <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-zinc-500">Buy Qty</p>
                        <p className="text-green-400 font-medium">{quote.buy_quantity}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">Sell Qty</p>
                        <p className="text-red-400 font-medium">{quote.sell_quantity}</p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 bg-blue-950/20 border border-blue-900/50 rounded-lg p-6">
          <h3 className="text-blue-300 font-medium mb-2 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Market Watch Features
          </h3>
          <ul className="text-sm text-zinc-400 space-y-1">
            <li>• <strong className="text-zinc-300">Real-time LTP:</strong> Last traded price updates</li>
            <li>• <strong className="text-zinc-300">Full Quote Data:</strong> OHLC, volume, buy/sell depth</li>
            <li>• <strong className="text-zinc-300">Live Mode:</strong> Auto-refresh every 5 seconds</li>
            <li>• <strong className="text-zinc-300">Multi-Exchange:</strong> NSE, BSE, NFO support</li>
            <li>• <strong className="text-zinc-300">Watchlist:</strong> Add/remove symbols dynamically</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MarketWatch;
