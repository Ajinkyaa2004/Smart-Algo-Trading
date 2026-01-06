import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { TrendingUp, TrendingDown, Activity, BarChart3, DollarSign, Clock, RefreshCw, ChevronRight, X, TrendingUpIcon } from 'lucide-react';
import { ApexCandlestickChart } from './ApexCandlestickChart';

interface OHLC {
    open: number;
    high: number;
    low: number;
    close: number;
}

interface MarketDepth {
    quantity: number;
    price: number;
    orders: number;
}

interface FullQuote {
    instrument_token: number;
    tradingsymbol: string;
    timestamp: string;
    last_price: number;
    net_change: number;
    ohlc: OHLC;
    volume?: number;
    buy_quantity?: number;
    sell_quantity?: number;
    average_price?: number;
    oi?: number;
    oi_day_high?: number;
    oi_day_low?: number;
    last_quantity?: number;
    last_trade_time?: string;
    depth?: {
        buy: MarketDepth[];
        sell: MarketDepth[];
    };
}

interface IndexMarketDataProps {
    niftySymbols: string[];
    bseSymbols: string[];
}

interface HistoricalCandle {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export const IndexMarketData: React.FC<IndexMarketDataProps> = React.memo(({ niftySymbols, bseSymbols }) => {
    const [quotes, setQuotes] = useState<Record<string, FullQuote>>({});
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [selectedIndex, setSelectedIndex] = useState<string | null>(null);
    const [historicalData, setHistoricalData] = useState<HistoricalCandle[]>([]);
    const [loadingChart, setLoadingChart] = useState(false);
    const [connectionError, setConnectionError] = useState(false);
    const [retryCount, setRetryCount] = useState(0);

    const allSymbols = useMemo(() => [...niftySymbols, ...bseSymbols], [niftySymbols, bseSymbols]);

    const fetchQuotes = useCallback(async () => {
        try {
            const symbolsParam = allSymbols.join(',');
            const response = await fetch(`http://localhost:8000/api/market/quote?symbols=${encodeURIComponent(symbolsParam)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            if (data.status === 'success' && data.data) {
                setQuotes(data.data);
                setLastUpdate(new Date());
                setConnectionError(false);
                setRetryCount(0);
            } else {
                console.warn('No data received from API');
            }
        } catch (error) {
            console.error('Failed to fetch quotes:', error);
            setConnectionError(true);
            setRetryCount(prev => prev + 1);
            
            // Exponential backoff: if too many failures, reduce frequency
            if (retryCount > 5) {
                setAutoRefresh(false);
                console.error('Too many failed attempts. Auto-refresh disabled. Please check backend connection.');
            }
        } finally {
            setLoading(false);
        }
    }, [allSymbols, retryCount]);

    useEffect(() => {
        fetchQuotes();
        
        if (autoRefresh) {
            // Update every 2 seconds for real-time data (optimized for performance)
            const interval = setInterval(fetchQuotes, 2000);
            return () => clearInterval(interval);
        }
    }, [autoRefresh, allSymbols.join(',')]);

    // Reset retry count when auto-refresh is manually re-enabled
    useEffect(() => {
        if (autoRefresh && retryCount > 0) {
            setRetryCount(0);
            setConnectionError(false);
        }
    }, [autoRefresh]);

    const formatNumber = (num: number | undefined) => {
        if (num === undefined || num === null) return 'N/A';
        return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };

    const formatTime = (timestamp: string | undefined) => {
        if (!timestamp) return 'N/A';
        try {
            return new Date(timestamp).toLocaleTimeString('en-IN');
        } catch {
            return timestamp;
        }
    };

    const getChangePercent = (quote: FullQuote) => {
        if (!quote.ohlc?.close || quote.ohlc.close === 0) return 0;
        return ((quote.last_price - quote.ohlc.close) / quote.ohlc.close) * 100;
    };

    const fetchHistoricalData = async (symbol: string, exchange: string) => {
        setLoadingChart(true);
        try {
            const response = await fetch(
                `http://localhost:8000/api/market/historical/quick?symbol=${encodeURIComponent(symbol)}&exchange=${exchange}&days=90&interval=day`
            );
            const data = await response.json();
            
            if (data.status === 'success' && data.data) {
                setHistoricalData(data.data);
            } else {
                setHistoricalData([]);
            }
        } catch (error) {
            console.error('Failed to fetch historical data:', error);
            setHistoricalData([]);
        } finally {
            setLoadingChart(false);
        }
    };

    useEffect(() => {
        if (selectedIndex) {
            const [exchange, ...symbolParts] = selectedIndex.split(':');
            const symbol = symbolParts.join(':');
            
            // Only fetch historical data for NSE indices (BSE not supported by Kite Connect)
            if (exchange === 'NSE') {
                fetchHistoricalData(symbol, exchange);
            } else {
                setHistoricalData([]);
                setLoadingChart(false);
            }
        }
    }, [selectedIndex]);

    const IndexCard: React.FC<{ symbol: string; quote: FullQuote }> = ({ symbol, quote }) => {
        const changePercent = getChangePercent(quote);
        const isPositive = changePercent >= 0;

        return (
            <button
                onClick={() => setSelectedIndex(symbol)}
                className="w-full bg-zinc-900/50 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-lg p-4 transition-all duration-200 text-left group"
            >
                <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                        <h4 className="font-semibold text-zinc-100 text-sm mb-1 group-hover:text-emerald-400 transition-colors">
                            {quote.tradingsymbol}
                        </h4>
                        <p className="text-xs text-zinc-500">{symbol.split(':')[0]}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-emerald-400 transition-colors" />
                </div>
                <div className="flex items-end justify-between">
                    <div className="text-xl font-bold text-zinc-100">
                        ₹{formatNumber(quote.last_price)}
                    </div>
                    <div className={`flex items-center gap-1 text-xs font-semibold ${
                        isPositive ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                        {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        <span>{isPositive ? '+' : ''}{changePercent.toFixed(2)}%</span>
                    </div>
                </div>
            </button>
        );
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-zinc-400 flex items-center gap-2">
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Loading market data...
                </div>
            </div>
        );
    }

    const selectedQuote = selectedIndex ? quotes[selectedIndex] : null;

    return (
        <div className="space-y-4">
            {/* Header Controls */}
            <div className="flex items-center justify-between bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-zinc-400">Auto-refresh</span>
                        <button
                            onClick={() => setAutoRefresh(!autoRefresh)}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                                autoRefresh ? 'bg-emerald-600' : 'bg-zinc-700'
                            }`}
                        >
                            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                autoRefresh ? 'translate-x-6' : 'translate-x-1'
                            }`} />
                        </button>
                    </div>
                    <button
                        onClick={fetchQuotes}
                        className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors text-sm"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                </div>
                <div className="flex items-center gap-3">
                    {connectionError && (
                        <div className="flex items-center gap-2 text-xs text-red-400 bg-red-950/30 px-3 py-1.5 rounded-lg border border-red-900/50">
                            <Activity className="w-3 h-3" />
                            Connection Error (Retry: {retryCount})
                        </div>
                    )}
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <Clock className="w-3 h-3" />
                        Updated: {lastUpdate.toLocaleTimeString()}
                    </div>
                </div>
            </div>

            {/* Main Layout Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Side - Index Boxes (Vertically Stacked) */}
                <div className="lg:col-span-1 space-y-6">
                    {/* NIFTY Indexes */}
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                        <div className="bg-gradient-to-r from-emerald-900/30 to-emerald-950/30 border-b border-zinc-800 p-4">
                            <h3 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                                <BarChart3 className="w-5 h-5 text-emerald-400" />
                                NIFTY Indexes
                            </h3>
                            <p className="text-xs text-zinc-400 mt-1">{niftySymbols.length} indices</p>
                        </div>
                        <div className="p-4 space-y-3 max-h-[500px] overflow-y-scroll custom-scrollbar">
                            {niftySymbols.map(symbol => {
                                const quote = quotes[symbol];
                                return quote ? (
                                    <IndexCard key={symbol} symbol={symbol} quote={quote} />
                                ) : null;
                            })}
                        </div>
                    </div>

                    {/* BSE Indexes */}
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                        <div className="bg-gradient-to-r from-blue-900/30 to-blue-950/30 border-b border-zinc-800 p-4">
                            <h3 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                                <BarChart3 className="w-5 h-5 text-blue-400" />
                                BSE Indexes
                            </h3>
                            <p className="text-xs text-zinc-400 mt-1">{bseSymbols.length} indices</p>
                        </div>
                        <div className="p-4 space-y-3 max-h-[500px] overflow-y-scroll custom-scrollbar">
                            {bseSymbols.map(symbol => {
                                const quote = quotes[symbol];
                                return quote ? (
                                    <IndexCard key={symbol} symbol={symbol} quote={quote} />
                                ) : null;
                            })}
                        </div>
                    </div>
                </div>

                {/* Right Side - Detailed View */}
                <div className="lg:col-span-2">
                    {selectedQuote && selectedIndex ? (
                        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden sticky top-4">
                            {/* Header */}
                            <div className="bg-gradient-to-r from-zinc-900 to-zinc-950 border-b border-zinc-800 p-6">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <h3 className="text-2xl font-bold text-zinc-100">{selectedQuote.tradingsymbol}</h3>
                                        <p className="text-sm text-zinc-500 mt-1">{selectedIndex}</p>
                                    </div>
                                    <div className="flex items-start gap-4">
                                        <div className="text-right">
                                            <div className="text-3xl font-bold text-zinc-100">
                                                ₹{formatNumber(selectedQuote.last_price)}
                                            </div>
                                            <div className={`flex items-center gap-1 justify-end mt-1 ${
                                                getChangePercent(selectedQuote) >= 0 ? 'text-emerald-500' : 'text-red-500'
                                            }`}>
                                                {getChangePercent(selectedQuote) >= 0 ? (
                                                    <TrendingUp className="w-5 h-5" />
                                                ) : (
                                                    <TrendingDown className="w-5 h-5" />
                                                )}
                                                <span className="text-lg font-semibold">
                                                    {getChangePercent(selectedQuote) >= 0 ? '+' : ''}
                                                    {formatNumber(selectedQuote.net_change)} (
                                                    {getChangePercent(selectedQuote) >= 0 ? '+' : ''}
                                                    {getChangePercent(selectedQuote).toFixed(2)}%)
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setSelectedIndex(null)}
                                            className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
                                        >
                                            <X className="w-5 h-5 text-zinc-400" />
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Content */}
                            <div className="p-6 space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto custom-scrollbar">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {/* OHLC Data */}
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5">
                                        <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-2 mb-4">
                                            <BarChart3 className="w-4 h-4" />
                                            OHLC Data
                                        </h4>
                                        <div className="space-y-3">
                                            <DataRow label="Open" value={`₹${formatNumber(selectedQuote.ohlc?.open)}`} />
                                            <DataRow 
                                                label="High" 
                                                value={`₹${formatNumber(selectedQuote.ohlc?.high)}`} 
                                                valueColor="text-emerald-400" 
                                            />
                                            <DataRow 
                                                label="Low" 
                                                value={`₹${formatNumber(selectedQuote.ohlc?.low)}`} 
                                                valueColor="text-red-400" 
                                            />
                                            <DataRow label="Close (Prev)" value={`₹${formatNumber(selectedQuote.ohlc?.close)}`} />
                                        </div>
                                    </div>

                                    {/* Trading Info */}
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5">
                                        <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-2 mb-4">
                                            <Activity className="w-4 h-4" />
                                            Trading Info
                                        </h4>
                                        <div className="space-y-3">
                                            <DataRow label="Volume" value={formatNumber(selectedQuote.volume)} />
                                            <DataRow label="Last Qty" value={formatNumber(selectedQuote.last_quantity)} />
                                            <DataRow label="Avg Price" value={`₹${formatNumber(selectedQuote.average_price)}`} />
                                            <DataRow label="Last Trade" value={formatTime(selectedQuote.last_trade_time)} />
                                        </div>
                                    </div>

                                    {/* Order Book */}
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5">
                                        <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-2 mb-4">
                                            <DollarSign className="w-4 h-4" />
                                            Order Book
                                        </h4>
                                        <div className="space-y-3">
                                            <DataRow 
                                                label="Buy Qty" 
                                                value={formatNumber(selectedQuote.buy_quantity)} 
                                                valueColor="text-emerald-400" 
                                            />
                                            <DataRow 
                                                label="Sell Qty" 
                                                value={formatNumber(selectedQuote.sell_quantity)} 
                                                valueColor="text-red-400" 
                                            />
                                            {selectedQuote.oi !== undefined && (
                                                <>
                                                    <DataRow label="Open Interest" value={formatNumber(selectedQuote.oi)} />
                                                    <DataRow label="OI Day High" value={formatNumber(selectedQuote.oi_day_high)} />
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Candlestick Chart */}
                                <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5">
                                    <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-4 flex items-center gap-2">
                                        <TrendingUpIcon className="w-4 h-4" />
                                        Price Chart (90 Days)
                                    </h4>
                                    {loadingChart ? (
                                        <div className="flex items-center justify-center h-[400px] bg-zinc-950/50 rounded-lg">
                                            <div className="text-zinc-500 flex items-center gap-2">
                                                <RefreshCw className="w-5 h-5 animate-spin" />
                                                Loading chart data...
                                            </div>
                                        </div>
                                    ) : historicalData.length > 0 ? (
                                        <div className="bg-zinc-950/30 rounded-lg p-3">
                                            <ApexCandlestickChart data={historicalData} height={400} />
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center h-[400px] bg-zinc-950/50 rounded-lg text-zinc-500">
                                            {selectedIndex?.startsWith('BSE:') ? (
                                                <>
                                                    <BarChart3 className="w-12 h-12 mb-3 opacity-50" />
                                                    <p className="font-medium">Historical data not available for BSE indices</p>
                                                    <p className="text-sm mt-2 text-zinc-600">Kite Connect API only supports NSE index historical data</p>
                                                </>
                                            ) : (
                                                <p>No historical data available for this index</p>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Market Depth */}
                                {selectedQuote.depth && (selectedQuote.depth.buy?.length > 0 || selectedQuote.depth.sell?.length > 0) && (
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5">
                                        <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-4">
                                            Market Depth
                                        </h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* Buy Orders */}
                                            <div>
                                                <div className="text-xs font-semibold text-emerald-400 mb-3 uppercase flex items-center gap-2">
                                                    <TrendingUp className="w-3 h-3" />
                                                    Buy Orders
                                                </div>
                                                <div className="space-y-2">
                                                    {selectedQuote.depth.buy?.map((order, idx) => (
                                                        <div key={idx} className="flex items-center justify-between text-xs bg-emerald-950/20 border border-emerald-900/30 p-3 rounded-lg">
                                                            <span className="text-zinc-400">₹{order.price.toFixed(2)}</span>
                                                            <span className="text-emerald-400 font-semibold">{order.quantity.toLocaleString()}</span>
                                                            <span className="text-zinc-500">({order.orders} orders)</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Sell Orders */}
                                            <div>
                                                <div className="text-xs font-semibold text-red-400 mb-3 uppercase flex items-center gap-2">
                                                    <TrendingDown className="w-3 h-3" />
                                                    Sell Orders
                                                </div>
                                                <div className="space-y-2">
                                                    {selectedQuote.depth.sell?.map((order, idx) => (
                                                        <div key={idx} className="flex items-center justify-between text-xs bg-red-950/20 border border-red-900/30 p-3 rounded-lg">
                                                            <span className="text-zinc-400">₹{order.price.toFixed(2)}</span>
                                                            <span className="text-red-400 font-semibold">{order.quantity.toLocaleString()}</span>
                                                            <span className="text-zinc-500">({order.orders} orders)</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Metadata Footer */}
                                <div className="mt-6 bg-zinc-950/50 rounded-lg px-5 py-3 flex items-center justify-between text-xs text-zinc-500">
                                    <div className="flex items-center gap-4">
                                        <span>Token: {selectedQuote.instrument_token}</span>
                                        <span className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {formatTime(selectedQuote.timestamp)}
                                        </span>
                                    </div>
                                    <div className={`flex items-center gap-1 ${autoRefresh ? 'text-emerald-500' : 'text-zinc-500'}`}>
                                        <div className={`w-2 h-2 rounded-full ${autoRefresh ? 'bg-emerald-500 animate-pulse' : 'bg-zinc-500'}`}></div>
                                        <span>{autoRefresh ? 'Live' : 'Paused'}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-zinc-900/50 border border-zinc-800 border-dashed rounded-xl h-full min-h-[600px] flex items-center justify-center">
                            <div className="text-center text-zinc-500">
                                <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                <p className="text-lg font-medium">Select an index to view details</p>
                                <p className="text-sm mt-2">Click on any NIFTY or BSE index card to see OHLC data</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
});

// Helper component for data rows - memoized to prevent re-renders
const DataRow: React.FC<{ label: string; value: string | number; valueColor?: string }> = React.memo(({ 
    label, 
    value, 
    valueColor = 'text-zinc-100' 
}) => (
    <div className="flex items-center justify-between text-sm">
        <span className="text-zinc-500">{label}</span>
        <span className={`font-semibold ${valueColor}`}>{value}</span>
    </div>
));
