import React, { useState, useEffect } from 'react';
import { Search, X, Plus, TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { toast } from 'sonner';

interface TickerSymbol {
    symbol: string;
    exchange: string;
    price: number;
    change: number; // Percentage change
    prevClose?: number; // Previous close for calculating change
}

interface SearchResult {
    instrument_token: number;
    exchange_token: string;
    tradingsymbol: string;
    name: string;
    last_price: number;
    expiry: string;
    strike: number;
    tick_size: number;
    lot_size: number;
    instrument_type: string;
    segment: string;
    exchange: string;
}

export const MarketTicker: React.FC = () => {
    const [watchlist, setWatchlist] = useState<TickerSymbol[]>(() => {
        const saved = localStorage.getItem('marketTickerWatchlist');
        return saved ? JSON.parse(saved) : [
            { symbol: 'NIFTY 50', exchange: 'NSE', price: 0, change: 0, prevClose: 0 },
            { symbol: 'NIFTY BANK', exchange: 'NSE', price: 0, change: 0, prevClose: 0 },
            { symbol: 'NIFTY IT', exchange: 'NSE', price: 0, change: 0, prevClose: 0 }
        ];
    });

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    // Auto-updating price fetcher using HTTP polling (more reliable than WebSockets)
    useEffect(() => {
        const fetchPrices = async () => {
            try {
                const symbolsParam = watchlist.map(w => `${w.exchange}:${w.symbol}`).join(',');
                if (!symbolsParam) return;

                const response = await fetch(`http://localhost:8000/api/market/quote?symbols=${encodeURIComponent(symbolsParam)}`);
                const data = await response.json();

                if (data.status === 'success' && data.data) {
                    setWatchlist(prev => prev.map(item => {
                        const key = `${item.exchange}:${item.symbol}`;
                        const quote = data.data[key];
                        if (quote) {
                            const price = quote.last_price || 0;
                            
                            // Calculate % change more accurately
                            // Priority: 1. Use net_change if available, 2. Calculate from ohlc.close (prev day), 3. From ohlc.open (today)
                            let change = 0;
                            let basePrice = 0;
                            
                            if (quote.net_change !== undefined && quote.net_change !== null) {
                                // If API provides net_change, use it directly
                                change = quote.net_change;
                            } else if (quote.ohlc?.close && quote.ohlc.close > 0) {
                                // Use previous day's close (most accurate for day change)
                                basePrice = quote.ohlc.close;
                                change = ((price - basePrice) / basePrice) * 100;
                            } else if (quote.ohlc?.open && quote.ohlc.open > 0 && quote.ohlc.open !== price) {
                                // Fallback to today's open
                                basePrice = quote.ohlc.open;
                                change = ((price - basePrice) / basePrice) * 100;
                            }
                            
                            return { ...item, price, change, prevClose: basePrice || price };
                        }
                        return item;
                    }));
                }
            } catch (e) {
                console.error("Failed to fetch prices:", e);
            }
        };

        // Fetch immediately on mount
        fetchPrices();

        // Then fetch every 2 seconds for real-time updates (optimized for performance)
        const interval = setInterval(fetchPrices, 2000);

        // Cleanup interval on unmount or watchlist change
        return () => clearInterval(interval);
    }, [watchlist.map(w => w.symbol).join(',')]); // Re-run when watchlist symbols change

    // Persist Watchlist
    useEffect(() => {
        localStorage.setItem('marketTickerWatchlist', JSON.stringify(watchlist));
    }, [watchlist]);

    // Search Handler
    useEffect(() => {
        const delayDebounceFn = setTimeout(async () => {
            if (searchQuery.length > 2) {
                setIsSearching(true);
                try {
                    const response = await fetch(`http://localhost:8000/api/market/instruments/search/${searchQuery}`);
                    const data = await response.json();
                    if (data.status === 'success') {
                        setSearchResults(data.results.slice(0, 10)); // Limit to 10
                    }
                } catch (error) {
                    console.error("Search failed", error);
                } finally {
                    setIsSearching(false);
                }
            } else {
                setSearchResults([]);
            }
        }, 500);

        return () => clearTimeout(delayDebounceFn);
    }, [searchQuery]);

    const addToWatchlist = (result: SearchResult) => {
        if (watchlist.length >= 3) {
            toast.warning('Watchlist Limit Reached', {
                description: 'You can only pin 3 instruments. Remove one first.'
            });
            return;
        }
        const newItem = { symbol: result.tradingsymbol, exchange: result.exchange, price: 0, change: 0, prevClose: 0 };
        setWatchlist([...watchlist, newItem]);
        setSearchQuery('');
        setSearchResults([]);
        setIsModalOpen(false);
    };

    const removeFromWatchlist = (symbol: string) => {
        setWatchlist(watchlist.filter(w => w.symbol !== symbol));
    };

    return (
        <div className="flex items-center gap-4">
            {/* Ticker Items */}
            {watchlist.map((item) => (
                <div key={item.symbol} className="flex flex-col w-[180px] relative group">
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-zinc-500 font-medium uppercase truncate max-w-[90px]">{item.symbol}</span>
                        <button
                            onClick={() => removeFromWatchlist(item.symbol)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity text-zinc-600 hover:text-red-400"
                        >
                            <X className="w-3 h-3" />
                        </button>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-zinc-100">
                            {item.price > 0 ? `₹${item.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'Loading...'}
                        </span>
                        {item.price > 0 && (
                            <span className={`text-xs font-medium flex items-center gap-0.5 ${
                                item.change > 0 ? 'text-emerald-500' : item.change < 0 ? 'text-red-500' : 'text-zinc-500'
                            }`}>
                                {item.change > 0 ? <TrendingUp className="w-3 h-3" /> : item.change < 0 ? <TrendingDown className="w-3 h-3" /> : null}
                                {item.change > 0 ? '+' : ''}{item.change.toFixed(2)}%
                            </span>
                        )}
                    </div>
                </div>
            ))}

            {/* Add Button (if slots available) */}
            {watchlist.length < 3 && (
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-zinc-700 hover:border-zinc-500 text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    <span className="text-xs font-medium">Add</span>
                </button>
            )}

            {/* Search Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/50 backdrop-blur-sm" onClick={() => setIsModalOpen(false)}>
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-md shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
                        <div className="p-4 border-b border-zinc-800 flex items-center gap-3">
                            <Search className="w-5 h-5 text-zinc-500" />
                            <input
                                type="text"
                                placeholder="Search symbol (e.g. INF, BANKNIFTY, GOLD)..."
                                className="bg-transparent border-none focus:outline-none text-zinc-100 w-full placeholder-zinc-600"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                autoFocus
                            />
                            <button onClick={() => setIsModalOpen(false)} className="text-zinc-500 hover:text-zinc-300">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="max-h-[300px] overflow-y-auto">
                            {isSearching ? (
                                <div className="p-4 text-center text-zinc-500 flex items-center justify-center gap-2">
                                    <Clock className="w-4 h-4 animate-spin" /> Searching...
                                </div>
                            ) : searchResults.length > 0 ? (
                                <div className="divide-y divide-zinc-800">
                                    {searchResults.map((result) => (
                                        <button
                                            key={result.instrument_token}
                                            onClick={() => addToWatchlist(result)}
                                            className="w-full p-3 flex items-center justify-between hover:bg-zinc-800 transition-colors text-left"
                                        >
                                            <div>
                                                <div className="font-medium text-zinc-100">{result.tradingsymbol}</div>
                                                <div className="text-xs text-zinc-500">{result.name || result.exchange} {result.segment}</div>
                                            </div>
                                            <div className="text-xs font-medium bg-zinc-800 px-2 py-1 rounded text-zinc-300 border border-zinc-700">
                                                {result.exchange}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            ) : searchQuery.length > 2 ? (
                                <div className="p-4 text-center text-zinc-500">No results found</div>
                            ) : (
                                <div className="p-4 text-center text-zinc-600 text-sm">
                                    Type at least 3 characters to search for Indices, Stocks, F&O, Commodities, or Currrency.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
