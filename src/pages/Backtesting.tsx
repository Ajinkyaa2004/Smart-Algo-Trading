import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
    Play, TrendingUp, TrendingDown, BarChart3,
    Target, AlertCircle, CheckCircle2,
    ArrowDownRight, Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface BacktestMetrics {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    loss_rate: number;
    total_pnl: number;
    total_pnl_percent: number;
    gross_profit: number;
    gross_loss: number;
    profit_factor: number;
    avg_win: number;
    avg_loss: number;
    largest_win: number;
    largest_loss: number;
    avg_holding_period: string;
    max_drawdown: number;
    max_drawdown_percent: number;
    sharpe_ratio: number;
    expectancy: number;
    consecutive_wins: number;
    consecutive_losses: number;
    avg_trades_per_day: number;
}

interface BacktestResult {
    backtest_id: string;
    strategy_type: string;
    symbol: string;
    start_date: string;
    end_date: string;
    interval: string;
    initial_capital: number;
    final_capital: number;
    metrics: BacktestMetrics;
    trades: any[];
    equity_curve: any[];
    strategy_params: any;
    total_candles: number;
    execution_time: number;
    created_at: string;
}

const Backtesting: React.FC = () => {
    const [symbol, setSymbol] = useState('RELIANCE');
    const [exchange] = useState('NSE');
    const [strategyType, setStrategyType] = useState('supertrend');
    const [startDate, setStartDate] = useState('2024-01-01');
    const [endDate, setEndDate] = useState('2024-12-31');
    const [interval, setInterval] = useState('15minute');
    const [initialCapital, setInitialCapital] = useState(100000);

    const [isRunning, setIsRunning] = useState(false);
    const [result, setResult] = useState<BacktestResult | null>(null);
    const [strategies, setStrategies] = useState<any[]>([]);
    const [intervals, setIntervals] = useState<any[]>([]);

    const symbols = [
        'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
        'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'HINDUNILVR', 'ITC',
        'LT', 'AXISBANK', 'MARUTI', 'BAJFINANCE', 'ASIANPAINT'
    ];

    useEffect(() => {
        fetchStrategies();
        fetchIntervals();
    }, []);

    const fetchStrategies = async () => {
        try {
            const response = await fetch(`${API_URL}/api/backtest/strategies`);
            const data = await response.json();
            if (data.status === 'success') {
                setStrategies(data.strategies);
            }
        } catch (error) {
            console.error('Error fetching strategies:', error);
        }
    };

    const fetchIntervals = async () => {
        try {
            const response = await fetch(`${API_URL}/api/backtest/intervals`);
            const data = await response.json();
            if (data.status === 'success') {
                setIntervals(data.intervals);
            }
        } catch (error) {
            console.error('Error fetching intervals:', error);
        }
    };

    const runBacktest = async () => {
        setIsRunning(true);
        toast.info('Starting backtest...', {
            description: 'Fetching historical data and running strategy simulation'
        });

        try {
            const response = await fetch(`${API_URL}/api/backtest/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol,
                    exchange,
                    strategy_type: strategyType,
                    start_date: startDate,
                    end_date: endDate,
                    interval,
                    initial_capital: initialCapital
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                setResult(data.result);
                toast.success('Backtest Completed!', {
                    description: `${data.result.metrics.total_trades} trades executed in ${data.result.execution_time.toFixed(2)}s`
                });
            } else {
                toast.error('Backtest Failed', {
                    description: data.message || 'Unknown error'
                });
            }
        } catch (error) {
            toast.error('Connection Error', {
                description: 'Unable to connect to backend'
            });
        } finally {
            setIsRunning(false);
        }
    };

    const getEquityChartData = () => {
        if (!result || !result.equity_curve.length) return null;

        return {
            labels: result.equity_curve.map(point => {
                const date = new Date(point.date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [
                {
                    label: 'Portfolio Value',
                    data: result.equity_curve.map(point => point.equity),
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        };
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                mode: 'index' as const,
                intersect: false,
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(59, 130, 246, 0.5)',
                borderWidth: 1
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)'
                },
                ticks: {
                    color: '#9ca3af'
                }
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)'
                },
                ticks: {
                    color: '#9ca3af',
                    callback: function (value: any) {
                        return '₹' + value.toLocaleString();
                    }
                }
            }
        }
    };

    return (
        <div className="h-full w-full p-4 space-y-4 flex flex-col">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-bold tracking-tight text-white">Strategy Backtesting</h2>
                <p className="text-zinc-400 mt-2">Test your strategies on real historical data before going live</p>
            </div>

            {/* Configuration Panel */}
            <Card className="w-full bg-zinc-900 border-zinc-800">
                <CardHeader>
                    <CardTitle className="text-white">Backtest Configuration</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {/* Symbol Selection */}
                        <div>
                            <label className="text-sm text-zinc-400 mb-2 block">Symbol</label>
                            <select
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value)}
                                disabled={isRunning}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-600"
                            >
                                {symbols.map(sym => (
                                    <option key={sym} value={sym}>{sym}</option>
                                ))}
                            </select>
                        </div>

                        {/* Strategy Selection */}
                        <div>
                            <label className="text-sm text-zinc-400 mb-2 block">Strategy</label>
                            <select
                                value={strategyType}
                                onChange={(e) => setStrategyType(e.target.value)}
                                disabled={isRunning}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-600"
                            >
                                {strategies.map(strategy => (
                                    <option key={strategy.type} value={strategy.type}>
                                        {strategy.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Interval Selection */}
                        <div>
                            <label className="text-sm text-zinc-400 mb-2 block">Timeframe</label>
                            <select
                                value={interval}
                                onChange={(e) => setInterval(e.target.value)}
                                disabled={isRunning}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-600"
                            >
                                {intervals.map(int => (
                                    <option key={int.value} value={int.value}>
                                        {int.label} ({int.recommended_for})
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Start Date */}
                        <div>
                            <label className="text-sm text-zinc-400 mb-2 block">Start Date</label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                disabled={isRunning}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-600"
                            />
                        </div>

                        {/* End Date */}
                        <div>
                            <label className="text-sm text-zinc-400 mb-2 block">End Date</label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                disabled={isRunning}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-600"
                            />
                        </div>

                        {/* Initial Capital */}
                        <div>
                            <label className="text-sm text-zinc-400 mb-2 block">Initial Capital (₹)</label>
                            <input
                                type="number"
                                value={initialCapital}
                                onChange={(e) => setInitialCapital(Number(e.target.value))}
                                disabled={isRunning}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-600"
                            />
                        </div>
                    </div>

                    {/* Run Button */}
                    <div className="mt-6">
                        <Button
                            onClick={runBacktest}
                            disabled={isRunning}
                            className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
                        >
                            {isRunning ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Running Backtest...
                                </>
                            ) : (
                                <>
                                    <Play className="h-4 w-4" />
                                    Run Backtest
                                </>
                            )}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Results */}
            {result && (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
                        {/* Total P&L */}
                        <Card className="bg-zinc-900 border-zinc-800 w-full">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-zinc-400">Total P&L</p>
                                        <p className={`text-2xl font-bold mt-1 ${result.metrics.total_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                            ₹{result.metrics.total_pnl.toLocaleString()}
                                        </p>
                                        <p className={`text-sm mt-1 ${result.metrics.total_pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {result.metrics.total_pnl_percent >= 0 ? '+' : ''}{result.metrics.total_pnl_percent}%
                                        </p>
                                    </div>
                                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${result.metrics.total_pnl >= 0 ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                                        {result.metrics.total_pnl >= 0 ? (
                                            <TrendingUp className="w-6 h-6 text-green-500" />
                                        ) : (
                                            <TrendingDown className="w-6 h-6 text-red-500" />
                                        )}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Win Rate */}
                        <Card className="bg-zinc-900 border-zinc-800 w-full">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-zinc-400">Win Rate</p>
                                        <p className="text-2xl font-bold text-white mt-1">{result.metrics.win_rate}%</p>
                                        <p className="text-sm text-zinc-400 mt-1">
                                            {result.metrics.winning_trades}/{result.metrics.total_trades} trades
                                        </p>
                                    </div>
                                    <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
                                        <Target className="w-6 h-6 text-blue-500" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Profit Factor */}
                        <Card className="bg-zinc-900 border-zinc-800 w-full">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-zinc-400">Profit Factor</p>
                                        <p className="text-2xl font-bold text-white mt-1">{result.metrics.profit_factor}</p>
                                        <p className="text-sm text-zinc-400 mt-1">
                                            {result.metrics.profit_factor >= 2 ? 'Excellent' : result.metrics.profit_factor >= 1.5 ? 'Good' : 'Fair'}
                                        </p>
                                    </div>
                                    <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
                                        <BarChart3 className="w-6 h-6 text-purple-500" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Max Drawdown */}
                        <Card className="bg-zinc-900 border-zinc-800 w-full">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-zinc-400">Max Drawdown</p>
                                        <p className="text-2xl font-bold text-red-400 mt-1">
                                            {result.metrics.max_drawdown_percent}%
                                        </p>
                                        <p className="text-sm text-zinc-400 mt-1">
                                            ₹{result.metrics.max_drawdown.toLocaleString()}
                                        </p>
                                    </div>
                                    <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                                        <ArrowDownRight className="w-6 h-6 text-red-500" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Equity Curve */}
                    <Card className="bg-zinc-900 border-zinc-800 w-full">
                        <CardHeader>
                            <CardTitle className="text-white">Equity Curve</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="h-80">
                                {getEquityChartData() && (
                                    <Line data={getEquityChartData()!} options={chartOptions} />
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Detailed Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                        {/* Performance Metrics */}
                        <Card className="bg-zinc-900 border-zinc-800 w-full">
                            <CardHeader>
                                <CardTitle className="text-white">Performance Metrics</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    <MetricRow label="Total Trades" value={result.metrics.total_trades.toString()} />
                                    <MetricRow label="Winning Trades" value={result.metrics.winning_trades.toString()} valueColor="text-green-400" />
                                    <MetricRow label="Losing Trades" value={result.metrics.losing_trades.toString()} valueColor="text-red-400" />
                                    <MetricRow label="Average Win" value={`₹${result.metrics.avg_win.toLocaleString()}`} valueColor="text-green-400" />
                                    <MetricRow label="Average Loss" value={`₹${result.metrics.avg_loss.toLocaleString()}`} valueColor="text-red-400" />
                                    <MetricRow label="Largest Win" value={`₹${result.metrics.largest_win.toLocaleString()}`} valueColor="text-green-400" />
                                    <MetricRow label="Largest Loss" value={`₹${result.metrics.largest_loss.toLocaleString()}`} valueColor="text-red-400" />
                                    <MetricRow label="Avg Holding Period" value={result.metrics.avg_holding_period} />
                                </div>
                            </CardContent>
                        </Card>

                        {/* Risk Metrics */}
                        <Card className="bg-zinc-900 border-zinc-800 w-full">
                            <CardHeader>
                                <CardTitle className="text-white">Risk Metrics</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    <MetricRow label="Sharpe Ratio" value={result.metrics.sharpe_ratio.toString()} />
                                    <MetricRow label="Expectancy" value={`₹${result.metrics.expectancy.toFixed(2)}`} />
                                    <MetricRow label="Gross Profit" value={`₹${result.metrics.gross_profit.toLocaleString()}`} valueColor="text-green-400" />
                                    <MetricRow label="Gross Loss" value={`₹${result.metrics.gross_loss.toLocaleString()}`} valueColor="text-red-400" />
                                    <MetricRow label="Consecutive Wins" value={result.metrics.consecutive_wins.toString()} />
                                    <MetricRow label="Consecutive Losses" value={result.metrics.consecutive_losses.toString()} />
                                    <MetricRow label="Avg Trades/Day" value={result.metrics.avg_trades_per_day.toFixed(2)} />
                                    <MetricRow label="Total Candles" value={result.total_candles.toLocaleString()} />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Trade History */}
                    <Card className="bg-zinc-900 border-zinc-800 w-full">
                        <CardHeader>
                            <CardTitle className="text-white">Trade History ({result.trades.length} trades)</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-zinc-800">
                                            <th className="text-left py-3 px-4 text-zinc-400 font-medium">Entry Time</th>
                                            <th className="text-left py-3 px-4 text-zinc-400 font-medium">Exit Time</th>
                                            <th className="text-left py-3 px-4 text-zinc-400 font-medium">Direction</th>
                                            <th className="text-right py-3 px-4 text-zinc-400 font-medium">Entry Price</th>
                                            <th className="text-right py-3 px-4 text-zinc-400 font-medium">Exit Price</th>
                                            <th className="text-right py-3 px-4 text-zinc-400 font-medium">Qty</th>
                                            <th className="text-right py-3 px-4 text-zinc-400 font-medium">P&L</th>
                                            <th className="text-right py-3 px-4 text-zinc-400 font-medium">P&L %</th>
                                            <th className="text-right py-3 px-4 text-zinc-400 font-medium">Duration</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.trades.slice(0, 50).map((trade, index) => (
                                            <tr key={index} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                                                <td className="py-3 px-4 text-zinc-300">{new Date(trade.entry_time).toLocaleString()}</td>
                                                <td className="py-3 px-4 text-zinc-300">{new Date(trade.exit_time).toLocaleString()}</td>
                                                <td className="py-3 px-4">
                                                    <Badge className={trade.direction === 'BUY' ? 'bg-green-600' : 'bg-red-600'}>
                                                        {trade.direction}
                                                    </Badge>
                                                </td>
                                                <td className="py-3 px-4 text-right text-zinc-300">₹{trade.entry_price.toFixed(2)}</td>
                                                <td className="py-3 px-4 text-right text-zinc-300">₹{trade.exit_price.toFixed(2)}</td>
                                                <td className="py-3 px-4 text-right text-zinc-300">{trade.quantity}</td>
                                                <td className={`py-3 px-4 text-right font-medium ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    ₹{trade.pnl.toFixed(2)}
                                                </td>
                                                <td className={`py-3 px-4 text-right ${trade.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
                                                </td>
                                                <td className="py-3 px-4 text-right text-zinc-300">{trade.holding_period}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                                {result.trades.length > 50 && (
                                    <p className="text-center text-zinc-500 text-sm mt-4">
                                        Showing first 50 of {result.trades.length} trades
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Decision Helper */}
                    <Card className={`border-2 w-full ${result.metrics.win_rate >= 60 && result.metrics.profit_factor >= 1.5
                        ? 'bg-green-900/20 border-green-600'
                        : result.metrics.win_rate >= 50 && result.metrics.profit_factor >= 1.2
                            ? 'bg-yellow-900/20 border-yellow-600'
                            : 'bg-red-900/20 border-red-600'
                        }`}>
                        <CardContent className="p-6">
                            <div className="flex items-start gap-4">
                                {result.metrics.win_rate >= 60 && result.metrics.profit_factor >= 1.5 ? (
                                    <CheckCircle2 className="w-8 h-8 text-green-500 flex-shrink-0" />
                                ) : (
                                    <AlertCircle className="w-8 h-8 text-yellow-500 flex-shrink-0" />
                                )}
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-2">
                                        {result.metrics.win_rate >= 60 && result.metrics.profit_factor >= 1.5
                                            ? '✅ Strategy Recommended'
                                            : result.metrics.win_rate >= 50 && result.metrics.profit_factor >= 1.2
                                                ? '⚠️ Strategy Needs Optimization'
                                                : '❌ Strategy Not Recommended'}
                                    </h3>
                                    <p className="text-zinc-300 leading-relaxed">
                                        {result.metrics.win_rate >= 60 && result.metrics.profit_factor >= 1.5
                                            ? `This strategy shows excellent performance with a ${result.metrics.win_rate}% win rate and ${result.metrics.profit_factor} profit factor. The backtest generated ₹${result.metrics.total_pnl.toLocaleString()} profit (${result.metrics.total_pnl_percent}%) over ${result.metrics.total_trades} trades. Consider using this strategy for live trading.`
                                            : result.metrics.win_rate >= 50 && result.metrics.profit_factor >= 1.2
                                                ? `This strategy shows moderate performance. While it's profitable, consider optimizing parameters or testing different timeframes to improve the win rate (${result.metrics.win_rate}%) and profit factor (${result.metrics.profit_factor}).`
                                                : `This strategy underperformed in backtesting with a ${result.metrics.win_rate}% win rate and ${result.metrics.profit_factor} profit factor. We recommend testing different parameters, timeframes, or trying a different strategy before going live.`}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
};

const MetricRow: React.FC<{ label: string; value: string; valueColor?: string }> = ({
    label,
    value,
    valueColor = 'text-white'
}) => (
    <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
        <span className="text-zinc-400">{label}</span>
        <span className={`font-medium ${valueColor}`}>{value}</span>
    </div>
);

export default Backtesting;
