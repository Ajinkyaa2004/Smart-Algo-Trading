import { useState, useEffect } from 'react';
import {
    TrendingUp,
    TrendingDown,
    DollarSign,
    Activity,
    Target,
    BarChart3,
    PieChart,
    Filter,
    Download,
    RefreshCw
} from 'lucide-react';
import {
    BarChart,
    Bar,
    PieChart as RechartsPieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Area,
    AreaChart
} from 'recharts';

interface Trade {
    _id: string;
    symbol: string;
    strategy: string;
    action: string;
    quantity: number;
    entry_price: number;
    exit_price?: number;
    pnl: number;
    pnl_percentage: number;
    entry_time: string;
    exit_time?: string;
    status: string;
    duration_minutes?: number;
}

interface Statistics {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    total_pnl: number;
    total_invested: number;
    avg_profit: number;
    avg_loss: number;
    best_trade: {
        symbol: string;
        pnl: number;
        strategy: string;
    };
    worst_trade: {
        symbol: string;
        pnl: number;
        strategy: string;
    };
    profit_factor: number;
    avg_duration_minutes: number;
}

interface StrategyPerformance {
    strategy: string;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    total_pnl: number;
    win_rate: number;
    avg_pnl: number;
    best_trade: number;
    worst_trade: number;
}

interface PnLData {
    date: string;
    pnl: number;
    cumulative_pnl: number;
}

const API_BASE_URL = 'http://localhost:8000';

export default function TradingHistory() {
    const [trades, setTrades] = useState<Trade[]>([]);
    const [statistics, setStatistics] = useState<Statistics | null>(null);
    const [strategyPerformance, setStrategyPerformance] = useState<StrategyPerformance[]>([]);
    const [pnlData, setPnlData] = useState<PnLData[]>([]);
    const [loading, setLoading] = useState(true);
    const [filterStrategy, setFilterStrategy] = useState<string>('');
    const [filterStatus, setFilterStatus] = useState<string>('CLOSED');
    const [filterDays, setFilterDays] = useState<number>(30);

    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchHistoryData();
    }, [filterStrategy, filterStatus, filterDays]);

    const fetchHistoryData = async () => {
        setLoading(true);
        setError(null);
        try {
            const sessionToken = localStorage.getItem('authToken');
            const headers = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${sessionToken}`
            };

            // Fetch all data in parallel
            const [summaryRes, tradesRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/history/summary`, { headers }),
                fetch(
                    `${API_BASE_URL}/api/history/trades?status=${filterStatus}&days=${filterDays}${filterStrategy ? `&strategy=${filterStrategy}` : ''}`,
                    { headers }
                )
            ]);

            if (summaryRes.ok) {
                const summaryData = await summaryRes.json();
                setStatistics(summaryData.summary.statistics);
                setStrategyPerformance(summaryData.summary.strategy_performance);
                setPnlData(summaryData.summary.pnl_over_time);
            } else {
                throw new Error("Failed to fetch summary");
            }

            if (tradesRes.ok) {
                const tradesData = await tradesRes.json();
                setTrades(tradesData.trades);
            }
        } catch (error) {
            console.error('Error fetching history data:', error);
            setError("Could not load trading history. The backend might be unreachable or the session expired.");
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(value);
    };

    // ... existing helpers ...

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];

    // Prepare data for strategy usage pie chart
    const strategyUsageData = strategyPerformance.map((sp, index) => ({
        name: sp.strategy,
        value: sp.total_trades,
        color: COLORS[index % COLORS.length]
    }));

    // Prepare data for strategy P&L bar chart
    const strategyPnLData = strategyPerformance.map(sp => ({
        strategy: sp.strategy,
        pnl: sp.total_pnl,
        winRate: sp.win_rate
    }));

    const handleSeedData = async () => {
        setLoading(true);
        try {
            const sessionToken = localStorage.getItem('authToken');
            const res = await fetch(`${API_BASE_URL}/api/history/seed`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${sessionToken}`
                }
            });
            if (res.ok) {
                await fetchHistoryData();
            } else {
                setError("Failed to generate demo data. Check server logs.");
            }
        } catch (error) {
            console.error(error);
            setError("Failed to connect to server during seeding.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="h-full w-full flex items-center justify-center">
                <div className="text-center">
                    <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
                    <p className="text-zinc-400">Loading trading history...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full w-full p-6 flex flex-col items-center justify-center text-center">
                <div className="bg-red-500/10 p-6 rounded-full mb-4">
                    <TrendingDown className="w-12 h-12 text-red-500" />
                </div>
                <h3 className="text-xl font-bold text-red-400 mb-2">Connection Error</h3>
                <p className="text-zinc-400 max-w-md mb-6">{error}</p>
                <button
                    onClick={fetchHistoryData}
                    className="flex items-center gap-2 px-6 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg transition-colors"
                >
                    <RefreshCw className="w-4 h-4" />
                    Retry Connection
                </button>
            </div>
        );
    }

    if (!statistics || statistics.total_trades === 0) {
        return (
            <div className="h-full w-full p-6 space-y-6 overflow-y-auto">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-zinc-100 flex items-center gap-3">
                            <BarChart3 className="w-8 h-8 text-blue-500" />
                            Trading History
                        </h1>
                        <p className="text-zinc-400 mt-1">Comprehensive analysis of your trading performance</p>
                    </div>
                </div>

                <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-6 bg-zinc-900/50 border border-zinc-800 rounded-xl p-12">
                    <div className="bg-zinc-800/50 p-6 rounded-full">
                        <Activity className="w-16 h-16 text-blue-500" />
                    </div>
                    <div>
                        <h3 className="text-2xl font-bold text-zinc-100 mb-2">No Trading History Found</h3>
                        <p className="text-zinc-400 max-w-md mx-auto">
                            You haven't executed any trades yet. The history will populate automatically as you trade.
                        </p>
                    </div>
                    <button
                        onClick={handleSeedData}
                        className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                    >
                        <RefreshCw className="w-5 h-5" />
                        Generate Demo Data
                    </button>
                    <p className="text-xs text-zinc-500">
                        Use this for testing visualization features (Adds 50 mock trades)
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full w-full p-6 space-y-6 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-zinc-100 flex items-center gap-3">
                        <BarChart3 className="w-8 h-8 text-blue-500" />
                        Trading History
                    </h1>
                    <p className="text-zinc-400 mt-1">Comprehensive analysis of your trading performance</p>
                </div>
                <button
                    onClick={fetchHistoryData}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            {/* Filters */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                <div className="flex items-center gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-zinc-400" />
                        <span className="text-sm text-zinc-400">Filters:</span>
                    </div>

                    <select
                        value={filterDays}
                        onChange={(e) => setFilterDays(Number(e.target.value))}
                        className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value={7}>Last 7 Days</option>
                        <option value={30}>Last 30 Days</option>
                        <option value={90}>Last 90 Days</option>
                        <option value={365}>Last Year</option>
                    </select>

                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Status</option>
                        <option value="OPEN">Open</option>
                        <option value="CLOSED">Closed</option>
                    </select>

                    <select
                        value={filterStrategy}
                        onChange={(e) => setFilterStrategy(e.target.value)}
                        className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Strategies</option>
                        {strategyPerformance.map(sp => (
                            <option key={sp.strategy} value={sp.strategy}>{sp.strategy}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Overview Statistics */}
            {statistics && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-blue-900/20 to-blue-950/20 border border-blue-800/30 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-blue-400">Total P&L</span>
                            <DollarSign className="w-5 h-5 text-blue-400" />
                        </div>
                        <p className={`text-2xl font-bold ${statistics.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {formatCurrency(statistics.total_pnl)}
                        </p>
                        <p className="text-xs text-zinc-500 mt-1">
                            From {statistics.total_invested > 0 ? formatCurrency(statistics.total_invested) : '₹0'} invested
                        </p>
                    </div>

                    <div className="bg-gradient-to-br from-emerald-900/20 to-emerald-950/20 border border-emerald-800/30 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-emerald-400">Win Rate</span>
                            <Target className="w-5 h-5 text-emerald-400" />
                        </div>
                        <p className="text-2xl font-bold text-emerald-400">{statistics.win_rate.toFixed(1)}%</p>
                        <p className="text-xs text-zinc-500 mt-1">
                            {statistics.winning_trades} wins / {statistics.losing_trades} losses
                        </p>
                    </div>

                    <div className="bg-gradient-to-br from-purple-900/20 to-purple-950/20 border border-purple-800/30 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-purple-400">Total Trades</span>
                            <Activity className="w-5 h-5 text-purple-400" />
                        </div>
                        <p className="text-2xl font-bold text-purple-400">{statistics.total_trades}</p>
                        <p className="text-xs text-zinc-500 mt-1">
                            Avg duration: {statistics.avg_duration_minutes.toFixed(0)} min
                        </p>
                    </div>

                    <div className="bg-gradient-to-br from-amber-900/20 to-amber-950/20 border border-amber-800/30 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-amber-400">Profit Factor</span>
                            <TrendingUp className="w-5 h-5 text-amber-400" />
                        </div>
                        <p className="text-2xl font-bold text-amber-400">{statistics.profit_factor.toFixed(2)}</p>
                        <p className="text-xs text-zinc-500 mt-1">
                            Avg Profit: {formatCurrency(statistics.avg_profit)}
                        </p>
                    </div>
                </div>
            )}

            {/* Best & Worst Trades */}
            {statistics && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-900/10 border border-emerald-800/30 rounded-xl p-6">
                        <div className="flex items-center gap-2 mb-4">
                            <TrendingUp className="w-5 h-5 text-emerald-400" />
                            <h3 className="text-lg font-semibold text-emerald-400">Best Trade</h3>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Symbol:</span>
                                <span className="text-zinc-100 font-medium">{statistics.best_trade.symbol || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-400">P&L:</span>
                                <span className="text-emerald-400 font-bold">{formatCurrency(statistics.best_trade.pnl)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Strategy:</span>
                                <span className="text-zinc-100">{statistics.best_trade.strategy || 'N/A'}</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-red-900/10 border border-red-800/30 rounded-xl p-6">
                        <div className="flex items-center gap-2 mb-4">
                            <TrendingDown className="w-5 h-5 text-red-400" />
                            <h3 className="text-lg font-semibold text-red-400">Worst Trade</h3>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Symbol:</span>
                                <span className="text-zinc-100 font-medium">{statistics.worst_trade.symbol || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-400">P&L:</span>
                                <span className="text-red-400 font-bold">{formatCurrency(statistics.worst_trade.pnl)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-zinc-400">Strategy:</span>
                                <span className="text-zinc-100">{statistics.worst_trade.strategy || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* P&L Over Time */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-zinc-100 mb-4 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-blue-400" />
                        P&L Over Time
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={pnlData}>
                            <defs>
                                <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                            <XAxis dataKey="date" stroke="#71717a" style={{ fontSize: '12px' }} />
                            <YAxis stroke="#71717a" style={{ fontSize: '12px' }} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                                labelStyle={{ color: '#a1a1aa' }}
                            />
                            <Area
                                type="monotone"
                                dataKey="cumulative_pnl"
                                stroke="#3b82f6"
                                fillOpacity={1}
                                fill="url(#colorPnl)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Strategy Usage Distribution */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-zinc-100 mb-4 flex items-center gap-2">
                        <PieChart className="w-5 h-5 text-purple-400" />
                        Strategy Usage
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <RechartsPieChart>
                            <Pie
                                data={strategyUsageData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {strategyUsageData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                            />
                        </RechartsPieChart>
                    </ResponsiveContainer>
                </div>

                {/* Strategy Performance Comparison */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 lg:col-span-2">
                    <h3 className="text-lg font-semibold text-zinc-100 mb-4 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-emerald-400" />
                        Strategy Performance Comparison
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={strategyPnLData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                            <XAxis dataKey="strategy" stroke="#71717a" style={{ fontSize: '12px' }} />
                            <YAxis stroke="#71717a" style={{ fontSize: '12px' }} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                                labelStyle={{ color: '#a1a1aa' }}
                            />
                            <Legend />
                            <Bar dataKey="pnl" fill="#10b981" name="Total P&L (₹)" />
                            <Bar dataKey="winRate" fill="#3b82f6" name="Win Rate (%)" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Strategy Performance Table */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-zinc-100 mb-4">Strategy Analytics</h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-zinc-800">
                                <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Strategy</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Total Trades</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Win Rate</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Total P&L</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Avg P&L</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Best Trade</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Worst Trade</th>
                            </tr>
                        </thead>
                        <tbody>
                            {strategyPerformance.map((sp, index) => (
                                <tr key={index} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                                    <td className="py-3 px-4 text-zinc-100 font-medium">{sp.strategy}</td>
                                    <td className="py-3 px-4 text-right text-zinc-300">{sp.total_trades}</td>
                                    <td className="py-3 px-4 text-right">
                                        <span className={`${sp.win_rate >= 50 ? 'text-emerald-400' : 'text-red-400'} font-medium`}>
                                            {sp.win_rate.toFixed(1)}%
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-right">
                                        <span className={`${sp.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'} font-medium`}>
                                            {formatCurrency(sp.total_pnl)}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-right text-zinc-300">{formatCurrency(sp.avg_pnl)}</td>
                                    <td className="py-3 px-4 text-right text-emerald-400">{formatCurrency(sp.best_trade)}</td>
                                    <td className="py-3 px-4 text-right text-red-400">{formatCurrency(sp.worst_trade)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Trade History Table */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-zinc-100">Recent Trades</h3>
                    <button className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm rounded-lg transition-colors">
                        <Download className="w-4 h-4" />
                        Export CSV
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-zinc-800">
                                <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Date/Time</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Symbol</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Strategy</th>
                                <th className="text-center py-3 px-4 text-sm font-medium text-zinc-400">Action</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Qty</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Entry Price</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">Exit Price</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">P&L</th>
                                <th className="text-right py-3 px-4 text-sm font-medium text-zinc-400">P&L %</th>
                                <th className="text-center py-3 px-4 text-sm font-medium text-zinc-400">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.map((trade) => (
                                <tr key={trade._id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                                    <td className="py-3 px-4 text-sm text-zinc-300">{formatDate(trade.entry_time)}</td>
                                    <td className="py-3 px-4 text-sm text-zinc-100 font-medium">{trade.symbol}</td>
                                    <td className="py-3 px-4 text-sm text-zinc-300">{trade.strategy}</td>
                                    <td className="py-3 px-4 text-center">
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${trade.action === 'BUY' ? 'bg-blue-500/20 text-blue-400' : 'bg-orange-500/20 text-orange-400'
                                            }`}>
                                            {trade.action}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-right text-sm text-zinc-300">{trade.quantity}</td>
                                    <td className="py-3 px-4 text-right text-sm text-zinc-300">{formatCurrency(trade.entry_price)}</td>
                                    <td className="py-3 px-4 text-right text-sm text-zinc-300">
                                        {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
                                    </td>
                                    <td className="py-3 px-4 text-right text-sm">
                                        <span className={`font-medium ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {formatCurrency(trade.pnl)}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-right text-sm">
                                        <span className={`font-medium ${trade.pnl_percentage >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {trade.pnl_percentage.toFixed(2)}%
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-center">
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${trade.status === 'CLOSED' ? 'bg-zinc-700 text-zinc-300' : 'bg-emerald-500/20 text-emerald-400'
                                            }`}>
                                            {trade.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
