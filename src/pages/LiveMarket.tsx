import { useState, useEffect, useCallback } from 'react';
import { TrendingUp, TrendingDown, Plus, X, Search, Activity, Eye, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';
import { ApexCandlestickChart } from '../components/ApexCandlestickChart';

interface QuoteData {
    last_price: number;
    volume: number;
    buy_quantity?: number;
    sell_quantity?: number;
    ohlc: {
        open: number;
        high: number;
        low: number;
        close: number;
    };
    change: number;
}

interface WatchlistStock {
    symbol: string;
    exchange: string;
    fullSymbol: string;
    quote?: QuoteData;
    ltp?: number;
}

interface Candle {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    // Indicators
    atr?: number;
    adx?: number;
    plus_di?: number;
    minus_di?: number;
    bb_upper?: number;
    bb_middle?: number;
    bb_lower?: number;
    macd?: number;
    macd_signal?: number;
    macd_hist?: number;
    rsi?: number;
    supertrend?: number;
    supertrend_direction?: number;
}

interface PatternMatch {
    timestamp: string;
    symbol: string;
    pattern: string;
    direction: string;
    confidence: number;
    price: number;
    description: string;
}

// Popular NSE stocks - OPTIMIZED TO 5 FOR BETTER PERFORMANCE
const POPULAR_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK'
];

export default function LiveMarket() {
    const [watchlist, setWatchlist] = useState<WatchlistStock[]>([]);
    const [selectedStock, setSelectedStock] = useState<WatchlistStock | null>(null);
    const [showAddDialog, setShowAddDialog] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [newSymbol, setNewSymbol] = useState('');
    const [newExchange, setNewExchange] = useState('NSE');
    
    // Chart data
    const [candles, setCandles] = useState<Candle[]>([]);
    const [interval, setInterval] = useState('5min');
    const [isLoadingChart, setIsLoadingChart] = useState(false);
    
    // Indicators
    const [showADX, setShowADX] = useState(false);
    const [showATR, setShowATR] = useState(false);
    const [showBollinger, setShowBollinger] = useState(false);
    const [showMACD, setShowMACD] = useState(false);
    const [showRSI, setShowRSI] = useState(false);
    const [showSupertrend, setShowSupertrend] = useState(false);
    
    // Patterns
    const [patterns, setPatterns] = useState<PatternMatch[]>([]);
    const [showPatterns, setShowPatterns] = useState(false);
    const [isLoadingPatterns, setIsLoadingPatterns] = useState(false);

    // Initialize watchlist with stocks
    useEffect(() => {
        const initialWatchlist = POPULAR_STOCKS.map(symbol => ({
            symbol,
            exchange: 'NSE',
            fullSymbol: `NSE:${symbol}`
        }));
        setWatchlist(initialWatchlist);
        fetchAllQuotes(initialWatchlist);
    }, []);

    // Auto-refresh quotes every 2 seconds (optimized for performance)
    useEffect(() => {
        if (watchlist.length === 0) return;
        
        const intervalId = window.setInterval(() => {
            fetchAllQuotes(watchlist);
        }, 2000);
        
        return () => window.clearInterval(intervalId);
    }, [watchlist.length]);

    // Fetch candles when stock or interval changes (but only use symbol, not the whole object)
    useEffect(() => {
        if (selectedStock) {
            fetchHistoricalData(selectedStock.symbol);
        }
    }, [selectedStock?.symbol, interval]);
    
    // Auto-refresh chart every 5 minutes
    useEffect(() => {
        if (!selectedStock) return;
        
        const chartRefreshInterval = window.setInterval(() => {
            console.log('Auto-refreshing chart data (5 min interval)');
            fetchHistoricalData(selectedStock.symbol);
        }, 5 * 60 * 1000); // 5 minutes in milliseconds
        
        return () => window.clearInterval(chartRefreshInterval);
    }, [selectedStock?.symbol, interval]);
    
    // Refetch indicators when toggled (but don't refetch candles)
    useEffect(() => {
        if (selectedStock && candles.length > 0) {
            if (showADX || showATR || showBollinger || showMACD || showRSI || showSupertrend) {
                fetchIndicators(selectedStock.symbol, candles).then(candlesWithIndicators => {
                    setCandles(candlesWithIndicators);
                });
            }
        }
    }, [showADX, showATR, showBollinger, showMACD, showRSI, showSupertrend]);
    
    // Refetch patterns when toggled
    useEffect(() => {
        if (selectedStock && candles.length > 0 && showPatterns) {
            fetchPatterns(selectedStock.symbol, candles);
        } else if (!showPatterns) {
            setPatterns([]);
        }
    }, [showPatterns]);

    const fetchAllQuotes = useCallback(async (stocks: WatchlistStock[]) => {
        if (stocks.length === 0) return;

        try {
            const symbols = stocks.map(s => s.fullSymbol).join(',');
            const [quoteRes, ltpRes] = await Promise.all([
                fetch(`http://localhost:8000/api/market/quote?symbols=${symbols}`),
                fetch(`http://localhost:8000/api/market/ltp?symbols=${symbols}`)
            ]);

            const quoteData = await quoteRes.json();
            const ltpData = await ltpRes.json();

            setWatchlist(prevList =>
                prevList.map(item => ({
                    ...item,
                    quote: quoteData.data?.[item.fullSymbol],
                    ltp: ltpData.data?.[item.fullSymbol]?.last_price
                }))
            );
            
            // Update selectedStock quote data without changing reference (to avoid chart refresh)
            setSelectedStock(prevSelected => {
                if (!prevSelected) return null;
                const updatedQuote = quoteData.data?.[prevSelected.fullSymbol];
                const updatedLtp = ltpData.data?.[prevSelected.fullSymbol]?.last_price;
                
                // Only update if quote or ltp actually changed
                if (prevSelected.quote !== updatedQuote || prevSelected.ltp !== updatedLtp) {
                    return {
                        ...prevSelected,
                        quote: updatedQuote,
                        ltp: updatedLtp
                    };
                }
                return prevSelected;
            });
        } catch (error) {
            console.error('Error fetching quotes:', error);
        }
    }, []);

    const fetchHistoricalData = useCallback(async (symbol: string) => {
        if (isLoadingChart) return;
        
        setIsLoadingChart(true);
        setCandles([]);
        
        try {
            // Map frontend interval format to backend format
            const intervalMap: Record<string, string> = {
                '1min': 'minute',
                '3min': '3minute',
                '5min': '5minute',
                '15min': '15minute',
                '30min': '30minute',
                '60min': '60minute'
            };
            
            const backendInterval = intervalMap[interval] || '5minute';
            
            const response = await fetch('http://localhost:8000/api/market/fetchOHLC', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: symbol,
                    interval: backendInterval,
                    duration: 10,
                    exchange: 'NSE'
                })
            });

            const data = await response.json();
            console.log('Fetched OHLC data:', { 
                symbol, 
                interval: backendInterval, 
                dataPoints: data.data?.length,
                success: data.status === 'success' 
            });
            
            if (data.status === 'success' && data.data) {
                let formattedCandles = data.data.map((item: any) => ({
                    date: item.date,
                    open: item.open,
                    high: item.high,
                    low: item.low,
                    close: item.close,
                    volume: item.volume
                }));
                
                console.log('Setting candles:', formattedCandles.length, 'candles');
                setCandles(formattedCandles);
                
                if (showADX || showATR || showBollinger || showMACD || showRSI || showSupertrend) {
                    fetchIndicators(symbol, formattedCandles).then(candlesWithIndicators => {
                        if (candlesWithIndicators) {
                            setCandles(candlesWithIndicators);
                        }
                    });
                }
                
                if (showPatterns) {
                    fetchPatterns(symbol, formattedCandles);
                }
            }
        } catch (error) {
            console.error('Error fetching historical data:', error);
            toast.error('Failed to load chart data');
        } finally {
            setIsLoadingChart(false);
        }
    }, [interval, showADX, showATR, showBollinger, showMACD, showRSI, showSupertrend, showPatterns]);
    
    const fetchIndicators = async (symbol: string, candlesData: Candle[]) => {
        try {
            const indicators = [];
            if (showADX) indicators.push('adx');
            if (showATR) indicators.push('atr');
            if (showBollinger) indicators.push('bollinger');
            if (showMACD) indicators.push('macd');
            if (showRSI) indicators.push('rsi');
            if (showSupertrend) indicators.push('supertrend');
            
            if (indicators.length === 0) return candlesData;
            
            // Get date range from candles
            const fromDate = candlesData[0]?.date.split('T')[0];
            const toDate = candlesData[candlesData.length - 1]?.date.split('T')[0];
            
            // Map frontend interval format to backend format
            const intervalMap: Record<string, string> = {
                '1min': 'minute',
                '3min': '3minute',
                '5min': '5minute',
                '15min': '15minute',
                '30min': '30minute',
                '60min': '60minute'
            };
            
            const backendInterval = intervalMap[interval] || '5minute';
            
            const response = await fetch('http://localhost:8000/api/indicators/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    exchange: 'NSE',
                    from_date: fromDate,
                    to_date: toDate,
                    interval: backendInterval,
                    indicators: indicators
                })
            });
            
            const result = await response.json();
            if (result.status === 'success' && result.data) {
                // Merge indicator data with candles
                const indicatorMap = new Map();
                result.data.forEach((item: any) => {
                    indicatorMap.set(item.date, item);
                });
                
                return candlesData.map(candle => {
                    const indicatorData = indicatorMap.get(candle.date);
                    if (indicatorData) {
                        return {
                            ...candle,
                            atr: indicatorData.atr,
                            adx: indicatorData.adx,
                            plus_di: indicatorData.plus_di,
                            minus_di: indicatorData.minus_di,
                            bb_upper: indicatorData.bb_upper,
                            bb_middle: indicatorData.bb_middle,
                            bb_lower: indicatorData.bb_lower,
                            macd: indicatorData.macd,
                            macd_signal: indicatorData.macd_signal,
                            macd_hist: indicatorData.macd_hist,
                            rsi: indicatorData.rsi,
                            supertrend: indicatorData.supertrend,
                            supertrend_direction: indicatorData.supertrend_direction
                        };
                    }
                    return candle;
                });
            }
        } catch (error) {
            console.error('Error fetching indicators:', error);
        }
        return candlesData;
    };
    
    const fetchPatterns = async (symbol: string, candlesData: Candle[]) => {
        if (!showPatterns || candlesData.length === 0 || isLoadingPatterns) {
            setPatterns([]);
            return;
        }
        
        setIsLoadingPatterns(true);
        try {
            const fromDate = candlesData[0]?.date.split('T')[0];
            const toDate = candlesData[candlesData.length - 1]?.date.split('T')[0];
            
            // Map frontend interval format to backend format
            const intervalMap: Record<string, string> = {
                '1min': 'minute',
                '3min': '3minute',
                '5min': '5minute',
                '15min': '15minute',
                '30min': '30minute',
                '60min': '60minute'
            };
            
            const backendInterval = intervalMap[interval] || '5minute';
            
            const response = await fetch('http://localhost:8000/api/price-action/scan-patterns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    exchange: 'NSE',
                    from_date: fromDate,
                    to_date: toDate,
                    interval: backendInterval
                })
            });
            
            const result = await response.json();
            if (result.status === 'success' && result.patterns) {
                setPatterns(result.patterns);
                if (result.patterns.length > 0) {
                    toast.success(`Found ${result.patterns.length} patterns`);
                }
            } else {
                setPatterns([]);
            }
        } catch (error) {
            console.error('Error fetching patterns:', error);
            setPatterns([]);
            toast.error('Failed to scan patterns');
        } finally {
            setIsLoadingPatterns(false);
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

        const newStock = {
            symbol: newSymbol.toUpperCase(),
            exchange: newExchange,
            fullSymbol
        };

        setWatchlist([...watchlist, newStock]);
        setNewSymbol('');
        setShowAddDialog(false);
        toast.success(`Added ${fullSymbol} to watchlist`);
        
        setTimeout(() => fetchAllQuotes([...watchlist, newStock]), 100);
    };

    const removeSymbol = (fullSymbol: string) => {
        setWatchlist(watchlist.filter(item => item.fullSymbol !== fullSymbol));
        if (selectedStock?.fullSymbol === fullSymbol) {
            setSelectedStock(null);
        }
        toast.success('Removed from watchlist');
    };

    const getChangeColor = (change: number) => {
        if (change > 0) return 'text-green-400';
        if (change < 0) return 'text-red-400';
        return 'text-zinc-400';
    };

    const filteredWatchlist = watchlist.filter(stock =>
        stock.symbol.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="h-full w-full flex gap-4 p-4">
            {/* Watchlist Panel - Left Side */}
            <div className="w-80 flex-shrink-0 flex flex-col bg-zinc-950 border border-zinc-800 rounded-xl">
                {/* Header */}
                <div className="p-4 border-b border-zinc-800">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                            <Activity className="w-5 h-5 text-blue-400" />
                            Live Market
                        </h2>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setShowAddDialog(true)}
                                className="p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                                title="Add symbol"
                            >
                                <Plus className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    {/* Search */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <input
                            type="text"
                            placeholder="Search stocks..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>
                </div>

                {/* Watchlist */}
                <div className="flex-1 overflow-y-auto">
                    {filteredWatchlist.length === 0 ? (
                        <div className="p-8 text-center text-zinc-500">
                            <Eye className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>No stocks in watchlist</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-zinc-800">
                            {filteredWatchlist.map((stock) => {
                                const quote = stock.quote;
                                const ltp = stock.ltp || quote?.last_price || 0;
                                const change = quote?.ohlc?.close ? ((ltp - quote.ohlc.close) / quote.ohlc.close * 100) : 0;
                                const isSelected = selectedStock?.fullSymbol === stock.fullSymbol;

                                return (
                                    <div
                                        key={stock.fullSymbol}
                                        onClick={() => setSelectedStock(stock)}
                                        className={`p-3 cursor-pointer hover:bg-zinc-900/50 transition-colors ${
                                            isSelected ? 'bg-zinc-900 border-l-2 border-blue-500' : ''
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="font-medium text-zinc-100">{stock.symbol}</span>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            removeSymbol(stock.fullSymbol);
                                                        }}
                                                        className="text-zinc-500 hover:text-red-400 transition-colors"
                                                    >
                                                        <X className="w-3 h-3" />
                                                    </button>
                                                </div>
                                                <div className="flex items-center justify-between">
                                                    <span className="text-lg font-bold text-zinc-100">
                                                        ₹{ltp.toFixed(2)}
                                                    </span>
                                                    <div className={`flex items-center gap-1 text-sm ${getChangeColor(change)}`}>
                                                        {change >= 0 ? (
                                                            <TrendingUp className="w-3 h-3" />
                                                        ) : (
                                                            <TrendingDown className="w-3 h-3" />
                                                        )}
                                                        <span className="font-medium">
                                                            {change >= 0 ? '+' : ''}{change.toFixed(2)}%
                                                        </span>
                                                    </div>
                                                </div>
                                                {quote?.volume && (
                                                    <div className="text-xs text-zinc-500 mt-1">
                                                        Vol: {(quote.volume / 100000).toFixed(2)}L
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* Details Panel - Right Side */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {selectedStock ? (
                    <>
                        {/* Stock Header */}
                        <div className="p-6 bg-zinc-950 border-b border-zinc-800">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h1 className="text-3xl font-bold text-zinc-100">{selectedStock.symbol}</h1>
                                    <p className="text-sm text-zinc-500 mt-1">{selectedStock.exchange} • NSE Stock</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-3xl font-bold text-zinc-100">
                                        ₹{(selectedStock.ltp || selectedStock.quote?.last_price || 0).toFixed(2)}
                                    </p>
                                    {selectedStock.quote && (
                                        <div className={`flex items-center gap-2 justify-end mt-1 ${
                                            getChangeColor(
                                                ((selectedStock.ltp || selectedStock.quote.last_price) - selectedStock.quote.ohlc.close) / 
                                                selectedStock.quote.ohlc.close * 100
                                            )
                                        }`}>
                                            {((selectedStock.ltp || selectedStock.quote.last_price) - selectedStock.quote.ohlc.close) >= 0 ? (
                                                <TrendingUp className="w-5 h-5" />
                                            ) : (
                                                <TrendingDown className="w-5 h-5" />
                                            )}
                                            <span className="text-lg font-medium">
                                                {((selectedStock.ltp || selectedStock.quote.last_price) - selectedStock.quote.ohlc.close) >= 0 ? '+' : ''}
                                                {(((selectedStock.ltp || selectedStock.quote.last_price) - selectedStock.quote.ohlc.close) / selectedStock.quote.ohlc.close * 100).toFixed(2)}%
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* OHLC Grid */}
                            {selectedStock.quote?.ohlc && (
                                <div className="grid grid-cols-5 gap-3 mb-4">
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3">
                                        <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wide">Open</p>
                                        <p className="text-base font-semibold text-zinc-100">
                                            ₹{selectedStock.quote.ohlc.open.toFixed(2)}
                                        </p>
                                    </div>
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3">
                                        <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wide">High</p>
                                        <p className="text-base font-semibold text-green-400">
                                            ₹{selectedStock.quote.ohlc.high.toFixed(2)}
                                        </p>
                                    </div>
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3">
                                        <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wide">Low</p>
                                        <p className="text-base font-semibold text-red-400">
                                            ₹{selectedStock.quote.ohlc.low.toFixed(2)}
                                        </p>
                                    </div>
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3">
                                        <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wide">Prev Close</p>
                                        <p className="text-base font-semibold text-zinc-100">
                                            ₹{selectedStock.quote.ohlc.close.toFixed(2)}
                                        </p>
                                    </div>
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3">
                                        <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wide">Volume</p>
                                        <p className="text-base font-semibold text-blue-400">
                                            {selectedStock.quote.volume ? (selectedStock.quote.volume / 100000).toFixed(2) + 'L' : '-'}
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Interval Selector */}
                            <div className="flex items-center gap-2 mt-4">
                                <BarChart3 className="w-4 h-4 text-zinc-400" />
                                <span className="text-sm text-zinc-400">Interval:</span>
                                <div className="flex gap-2">
                                    {['1min', '3min', '5min', '15min', '30min', '60min'].map((int) => (
                                        <button
                                            key={int}
                                            onClick={() => setInterval(int)}
                                            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                                                interval === int
                                                    ? 'bg-blue-500 text-white'
                                                    : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
                                            }`}
                                        >
                                            {int}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            
                            {/* Indicator Toggles */}
                            <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-4 mt-4">
                                <div className="flex items-center gap-2 mb-3">
                                    <Activity className="w-4 h-4 text-zinc-400" />
                                    <span className="text-sm font-semibold text-zinc-400 uppercase tracking-wide">Technical Indicators</span>
                                </div>
                                <div className="flex gap-2 flex-wrap">
                                    <button
                                        onClick={() => setShowSupertrend(!showSupertrend)}
                                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                            showSupertrend
                                                ? 'bg-yellow-500 text-white'
                                                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
                                        }`}
                                    >
                                        Supertrend
                                    </button>
                                    <button
                                        onClick={() => setShowBollinger(!showBollinger)}
                                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                            showBollinger
                                                ? 'bg-purple-500 text-white'
                                                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
                                        }`}
                                    >
                                        Bollinger
                                    </button>
                                    <button
                                        onClick={() => setShowATR(!showATR)}
                                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                            showATR
                                                ? 'bg-orange-500 text-white'
                                                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
                                        }`}
                                    >
                                        ATR
                                    </button>
                                    <button
                                        onClick={() => setShowADX(!showADX)}
                                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                            showADX
                                                ? 'bg-cyan-500 text-white'
                                                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
                                        }`}
                                    >
                                        ADX
                                    </button>
                                    <button
                                        onClick={() => setShowMACD(!showMACD)}
                                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                            showMACD
                                                ? 'bg-blue-500 text-white'
                                                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
                                        }`}
                                    >
                                        MACD
                                    </button>
                                    <button
                                        onClick={() => setShowRSI(!showRSI)}
                                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                            showRSI
                                                ? 'bg-green-500 text-white'
                                                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
                                        }`}
                                    >
                                        RSI
                                    </button>
                                    <button
                                        onClick={() => setShowPatterns(!showPatterns)}
                                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                            showPatterns
                                                ? 'bg-pink-500 text-white'
                                                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800'
                                        }`}
                                    >
                                        Patterns
                                    </button>
                                </div>
                            </div>
                            
                            {/* Pattern List */}
                            {showPatterns && (
                                <div className="mt-3 p-3 bg-zinc-900 rounded border border-zinc-800">
                                    <div className="flex justify-between items-center mb-2">
                                        <h4 className="text-sm font-medium text-zinc-300">Candlestick Patterns</h4>
                                        {patterns.length > 0 && (
                                            <span className="text-xs text-zinc-500">{patterns.length} detected</span>
                                        )}
                                    </div>
                                    {patterns.length > 0 ? (
                                        <div className="space-y-2 max-h-40 overflow-y-auto">
                                            {patterns.slice(-10).reverse().map((pattern, idx) => (
                                                <div
                                                    key={idx}
                                                    className={`p-2 rounded text-xs ${
                                                        pattern.direction === 'bullish'
                                                            ? 'bg-green-900/30 border border-green-700/50'
                                                            : pattern.direction === 'bearish'
                                                            ? 'bg-red-900/30 border border-red-700/50'
                                                            : 'bg-zinc-800 border border-zinc-700'
                                                    }`}
                                                >
                                                    <div className="flex justify-between items-start">
                                                        <span className={`font-medium ${
                                                            pattern.direction === 'bullish' ? 'text-green-400' :
                                                            pattern.direction === 'bearish' ? 'text-red-400' :
                                                            'text-zinc-400'
                                                        }`}>
                                                            {pattern.pattern}
                                                        </span>
                                                        <span className="text-zinc-500">
                                                            {new Date(pattern.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                        </span>
                                                    </div>
                                                    <div className="mt-1 text-zinc-400">
                                                        ₹{pattern.price.toFixed(2)} • {(pattern.confidence * 100).toFixed(0)}% confidence
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="text-center py-4 text-zinc-500 text-xs">
                                            <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                            <p>Scanning for patterns...</p>
                                            <p className="text-zinc-600 mt-1">No patterns detected yet</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Chart */}
                        <div className="flex-1 overflow-auto p-6">
                            {isLoadingChart ? (
                                <div className="flex items-center justify-center h-full min-h-[500px] bg-zinc-950 border border-zinc-800 rounded-lg">
                                    <div className="text-zinc-500 flex items-center gap-2">
                                        <BarChart3 className="w-5 h-5 animate-spin" />
                                        Loading chart data...
                                    </div>
                                </div>
                            ) : candles.length > 0 ? (
                                <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                                            <BarChart3 className="w-5 h-5 text-blue-400" />
                                            {selectedStock.symbol} - {interval}
                                        </h3>
                                        {selectedStock.ltp && (
                                            <div className="flex items-center gap-2">
                                                <span className="text-2xl font-bold text-zinc-100">
                                                    ₹{selectedStock.ltp.toFixed(2)}
                                                </span>
                                                {selectedStock.quote && selectedStock.quote.ohlc && (
                                                    <span className={`text-sm font-medium ${
                                                        (selectedStock.ltp - selectedStock.quote.ohlc.close) >= 0 ? 'text-green-400' : 'text-red-400'
                                                    }`}>
                                                        {(selectedStock.ltp - selectedStock.quote.ohlc.close) >= 0 ? '+' : ''}{(selectedStock.ltp - selectedStock.quote.ohlc.close).toFixed(2)} 
                                                        ({(((selectedStock.ltp - selectedStock.quote.ohlc.close) / selectedStock.quote.ohlc.close) * 100).toFixed(2)}%)
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                    <div className="bg-zinc-950/30 rounded-lg p-3">
                                        <ApexCandlestickChart
                                            data={candles}
                                            patterns={patterns}
                                            height={500}
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div className="flex items-center justify-center h-full min-h-[500px] bg-zinc-950 border border-zinc-800 rounded-lg">
                                    <div className="text-center text-zinc-500">
                                        <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                        <p className="text-lg mb-2">No chart data available</p>
                                        <p className="text-sm text-zinc-600">Select a stock to view candlestick chart</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-zinc-500">
                        <div className="text-center">
                            <Eye className="w-20 h-20 mx-auto mb-4 opacity-30" />
                            <p className="text-xl mb-2">Select a stock from the watchlist</p>
                            <p className="text-sm">Click on any stock to view OHLC data and charts</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Add Symbol Dialog */}
            {showAddDialog && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6 w-96">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-zinc-100">Add Stock</h3>
                            <button
                                onClick={() => setShowAddDialog(false)}
                                className="text-zinc-400 hover:text-zinc-100"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="space-y-4">
                            <input
                                type="text"
                                placeholder="Symbol (e.g., RELIANCE)"
                                value={newSymbol}
                                onChange={(e) => setNewSymbol(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && addSymbol()}
                                className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            />
                            <select
                                value={newExchange}
                                onChange={(e) => setNewExchange(e.target.value)}
                                className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="NSE">NSE</option>
                                <option value="BSE">BSE</option>
                                <option value="NFO">NFO</option>
                            </select>
                            <button
                                onClick={addSymbol}
                                className="w-full px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                            >
                                Add to Watchlist
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
