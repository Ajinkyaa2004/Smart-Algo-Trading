import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { TrendingUp, TrendingDown, Target, Award, AlertTriangle } from 'lucide-react';

interface PerformanceMetrics {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    loss_rate: number;
    total_pnl: number;
    total_profit: number;
    total_loss: number;
    avg_win: number;
    avg_loss: number;
    profit_factor: number;
    largest_win: number;
    largest_loss: number;
    current_streak: number;
    max_drawdown: number;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const PerformanceMetricsCard: React.FC = () => {
    const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);

    useEffect(() => {
        fetchMetrics();
        const interval = setInterval(fetchMetrics, 5000); // Update every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchMetrics = async () => {
        try {
            const response = await fetch(`${API_URL}/api/bot/performance-metrics`);
            const data = await response.json();
            if (data.status === 'success') {
                setMetrics(data.metrics);
            }
        } catch (error) {
            console.error('Error fetching performance metrics:', error);
        }
    };

    if (!metrics) {
        return (
            <Card className="bg-zinc-900 border-zinc-800">
                <CardHeader>
                    <CardTitle className="text-white">Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-zinc-500 text-center py-4">Loading...</div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                    <Award className="h-5 w-5 text-yellow-500" />
                    Performance Metrics
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {/* Win Rate Circle */}
                    <div className="bg-zinc-800 rounded-lg p-6 text-center">
                        <div className="relative inline-flex items-center justify-center">
                            <svg className="w-32 h-32">
                                <circle
                                    className="text-zinc-700"
                                    strokeWidth="8"
                                    stroke="currentColor"
                                    fill="transparent"
                                    r="56"
                                    cx="64"
                                    cy="64"
                                />
                                <circle
                                    className={metrics.win_rate >= 50 ? 'text-green-500' : 'text-red-500'}
                                    strokeWidth="8"
                                    strokeDasharray={`${metrics.win_rate * 3.52} 352`}
                                    strokeLinecap="round"
                                    stroke="currentColor"
                                    fill="transparent"
                                    r="56"
                                    cx="64"
                                    cy="64"
                                    transform="rotate(-90 64 64)"
                                />
                            </svg>
                            <div className="absolute">
                                <p className={`text-3xl font-bold ${metrics.win_rate >= 50 ? 'text-green-500' : 'text-red-500'}`}>
                                    {metrics.win_rate.toFixed(1)}%
                                </p>
                                <p className="text-zinc-400 text-xs">Win Rate</p>
                            </div>
                        </div>
                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <p className="text-green-500 font-semibold">{metrics.winning_trades}</p>
                                <p className="text-zinc-400">Wins</p>
                            </div>
                            <div>
                                <p className="text-red-500 font-semibold">{metrics.losing_trades}</p>
                                <p className="text-zinc-400">Losses</p>
                            </div>
                        </div>
                    </div>

                    {/* P&L Stats */}
                    <div className="grid grid-cols-2 gap-3">
                        <div className="bg-zinc-800 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <TrendingUp className="h-4 w-4 text-green-500" />
                                <p className="text-zinc-400 text-xs">Total Profit</p>
                            </div>
                            <p className="text-green-500 font-bold text-lg">₹{metrics.total_profit.toFixed(2)}</p>
                            <p className="text-zinc-500 text-xs mt-1">Avg: ₹{metrics.avg_win.toFixed(2)}</p>
                        </div>

                        <div className="bg-zinc-800 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <TrendingDown className="h-4 w-4 text-red-500" />
                                <p className="text-zinc-400 text-xs">Total Loss</p>
                            </div>
                            <p className="text-red-500 font-bold text-lg">₹{metrics.total_loss.toFixed(2)}</p>
                            <p className="text-zinc-500 text-xs mt-1">Avg: ₹{metrics.avg_loss.toFixed(2)}</p>
                        </div>
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 gap-3">
                        <div className="bg-zinc-800 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <Target className="h-4 w-4 text-blue-500" />
                                <p className="text-zinc-400 text-xs">Profit Factor</p>
                            </div>
                            <p className={`font-bold text-lg ${metrics.profit_factor >= 1.5 ? 'text-green-500' : metrics.profit_factor >= 1 ? 'text-yellow-500' : 'text-red-500'}`}>
                                {metrics.profit_factor.toFixed(2)}x
                            </p>
                        </div>

                        <div className="bg-zinc-800 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle className="h-4 w-4 text-orange-500" />
                                <p className="text-zinc-400 text-xs">Max Drawdown</p>
                            </div>
                            <p className="text-orange-500 font-bold text-lg">₹{metrics.max_drawdown.toFixed(2)}</p>
                        </div>
                    </div>

                    {/* Best/Worst Trades */}
                    <div className="bg-zinc-800 rounded-lg p-4">
                        <p className="text-zinc-400 text-xs mb-3">Trade Extremes</p>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <p className="text-zinc-500 text-xs">Largest Win</p>
                                <p className="text-green-500 font-semibold">₹{metrics.largest_win.toFixed(2)}</p>
                            </div>
                            <div>
                                <p className="text-zinc-500 text-xs">Largest Loss</p>
                                <p className="text-red-500 font-semibold">₹{metrics.largest_loss.toFixed(2)}</p>
                            </div>
                        </div>
                    </div>

                    {/* Current Streak */}
                    {metrics.current_streak !== 0 && (
                        <div className={`rounded-lg p-3 ${metrics.current_streak > 0 ? 'bg-green-600/10 border border-green-600/30' : 'bg-red-600/10 border border-red-600/30'}`}>
                            <p className={`text-sm font-semibold ${metrics.current_streak > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {metrics.current_streak > 0 ? '🔥' : '❄️'} Current Streak: {Math.abs(metrics.current_streak)} {metrics.current_streak > 0 ? 'Wins' : 'Losses'}
                            </p>
                        </div>
                    )}

                    {/* Total Trades */}
                    <div className="text-center pt-2 border-t border-zinc-700">
                        <p className="text-zinc-400 text-xs">Total Trades</p>
                        <p className="text-white font-bold text-2xl">{metrics.total_trades}</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default PerformanceMetricsCard;
