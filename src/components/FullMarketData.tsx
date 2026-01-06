import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, BarChart3, DollarSign, Clock, RefreshCw } from 'lucide-react';

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

interface FullMarketDataProps {
    symbols?: string[];
}

export const FullMarketData: React.FC<FullMarketDataProps> = ({ 
    symbols = ['NSE:NIFTY 50', 'NSE:NIFTY BANK', 'NSE:NIFTY IT'] 
}) => {
    const [quotes, setQuotes] = useState<Record<string, FullQuote>>({});
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
    const [autoRefresh, setAutoRefresh] = useState(true);

    const fetchQuotes = async () => {
        try {
            const symbolsParam = symbols.join(',');
            const response = await fetch(`http://localhost:8000/api/market/quote?symbols=${encodeURIComponent(symbolsParam)}`);
            const data = await response.json();

            if (data.status === 'success' && data.data) {
                setQuotes(data.data);
                setLastUpdate(new Date());
            }
        } catch (error) {
            console.error('Failed to fetch quotes:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQuotes();
        
        if (autoRefresh) {
            const interval = setInterval(fetchQuotes, 2000); // Update every 2 seconds (optimized)
            return () => clearInterval(interval);
        }
    }, [autoRefresh, symbols.join(',')]);

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

    return (
        <div className="space-y-6">
            {/* Header Controls */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-zinc-100">Complete Market Data</h2>
                    <p className="text-sm text-zinc-500">Real-time quotes with full market depth</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-zinc-500">Auto-refresh</span>
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
                        className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                    <div className="text-xs text-zinc-500">
                        Updated: {lastUpdate.toLocaleTimeString()}
                    </div>
                </div>
            </div>

            {/* Market Data Cards */}
            {Object.entries(quotes).map(([symbol, quote]) => {
                const changePercent = quote.ohlc?.close > 0 
                    ? ((quote.last_price - quote.ohlc.close) / quote.ohlc.close) * 100 
                    : 0;
                const isPositive = changePercent >= 0;

                return (
                    <div key={symbol} className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                        {/* Header */}
                        <div className="bg-gradient-to-r from-zinc-900 to-zinc-950 p-6 border-b border-zinc-800">
                            <div className="flex items-start justify-between">
                                <div>
                                    <h3 className="text-2xl font-bold text-zinc-100">{quote.tradingsymbol}</h3>
                                    <p className="text-sm text-zinc-500 mt-1">{symbol}</p>
                                </div>
                                <div className="text-right">
                                    <div className="text-3xl font-bold text-zinc-100">
                                        ₹{formatNumber(quote.last_price)}
                                    </div>
                                    <div className={`flex items-center gap-1 justify-end mt-1 ${
                                        isPositive ? 'text-emerald-500' : 'text-red-500'
                                    }`}>
                                        {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                                        <span className="text-lg font-semibold">
                                            {isPositive ? '+' : ''}{formatNumber(quote.net_change)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Main Data Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6">
                            {/* OHLC Data */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-2">
                                    <BarChart3 className="w-4 h-4" />
                                    OHLC Data
                                </h4>
                                <div className="space-y-3">
                                    <DataRow label="Open" value={`₹${formatNumber(quote.ohlc?.open)}`} />
                                    <DataRow label="High" value={`₹${formatNumber(quote.ohlc?.high)}`} valueColor="text-emerald-400" />
                                    <DataRow label="Low" value={`₹${formatNumber(quote.ohlc?.low)}`} valueColor="text-red-400" />
                                    <DataRow label="Close (Prev)" value={`₹${formatNumber(quote.ohlc?.close)}`} />
                                </div>
                            </div>

                            {/* Trading Data */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-2">
                                    <Activity className="w-4 h-4" />
                                    Trading Info
                                </h4>
                                <div className="space-y-3">
                                    <DataRow label="Volume" value={formatNumber(quote.volume)} />
                                    <DataRow label="Last Qty" value={formatNumber(quote.last_quantity)} />
                                    <DataRow label="Avg Price" value={`₹${formatNumber(quote.average_price)}`} />
                                    <DataRow label="Last Trade" value={formatTime(quote.last_trade_time)} />
                                </div>
                            </div>

                            {/* Order Book */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide flex items-center gap-2">
                                    <DollarSign className="w-4 h-4" />
                                    Order Book
                                </h4>
                                <div className="space-y-3">
                                    <DataRow label="Buy Qty" value={formatNumber(quote.buy_quantity)} valueColor="text-emerald-400" />
                                    <DataRow label="Sell Qty" value={formatNumber(quote.sell_quantity)} valueColor="text-red-400" />
                                    {quote.oi !== undefined && (
                                        <>
                                            <DataRow label="Open Interest" value={formatNumber(quote.oi)} />
                                            <DataRow label="OI Day High" value={formatNumber(quote.oi_day_high)} />
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Market Depth */}
                        {quote.depth && (quote.depth.buy?.length > 0 || quote.depth.sell?.length > 0) && (
                            <div className="border-t border-zinc-800 p-6">
                                <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-4">
                                    Market Depth
                                </h4>
                                <div className="grid grid-cols-2 gap-6">
                                    {/* Buy Orders */}
                                    <div>
                                        <div className="text-xs font-semibold text-emerald-400 mb-2 uppercase">Buy Orders</div>
                                        <div className="space-y-1">
                                            {quote.depth.buy?.map((order, idx) => (
                                                <div key={idx} className="flex items-center justify-between text-xs bg-emerald-950/20 p-2 rounded">
                                                    <span className="text-zinc-400">₹{order.price}</span>
                                                    <span className="text-emerald-400 font-medium">{order.quantity}</span>
                                                    <span className="text-zinc-500">({order.orders})</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Sell Orders */}
                                    <div>
                                        <div className="text-xs font-semibold text-red-400 mb-2 uppercase">Sell Orders</div>
                                        <div className="space-y-1">
                                            {quote.depth.sell?.map((order, idx) => (
                                                <div key={idx} className="flex items-center justify-between text-xs bg-red-950/20 p-2 rounded">
                                                    <span className="text-zinc-400">₹{order.price}</span>
                                                    <span className="text-red-400 font-medium">{order.quantity}</span>
                                                    <span className="text-zinc-500">({order.orders})</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Metadata Footer */}
                        <div className="bg-zinc-950/50 px-6 py-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500">
                            <div className="flex items-center gap-4">
                                <span>Token: {quote.instrument_token}</span>
                                <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {formatTime(quote.timestamp)}
                                </span>
                            </div>
                            <div className={`flex items-center gap-1 ${autoRefresh ? 'text-emerald-500' : 'text-zinc-500'}`}>
                                {autoRefresh ? (
                                    <>
                                        <RefreshCw className="w-3 h-3" />
                                        <span>Live</span>
                                    </>
                                ) : (
                                    <>
                                        <Clock className="w-3 h-3" />
                                        <span>Paused</span>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

// Helper component for data rows
const DataRow: React.FC<{ label: string; value: string | number; valueColor?: string }> = ({ 
    label, 
    value, 
    valueColor = 'text-zinc-100' 
}) => (
    <div className="flex items-center justify-between text-sm">
        <span className="text-zinc-500">{label}</span>
        <span className={`font-semibold ${valueColor}`}>{value}</span>
    </div>
);
