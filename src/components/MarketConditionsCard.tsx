import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { TrendingUp, TrendingDown, Minus, Clock, Calendar } from 'lucide-react';

interface MarketConditions {
    status: string;
    session: string;
    current_time: string;
    trend: string;
    is_tradable: boolean;
    opens_in?: string;
    closes_in?: string;
    next_open?: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MarketConditionsCard: React.FC = () => {
    const [conditions, setConditions] = useState<MarketConditions | null>(null);

    useEffect(() => {
        fetchConditions();
        const interval = setInterval(fetchConditions, 10000); // Update every 10 seconds
        return () => clearInterval(interval);
    }, []);

    const fetchConditions = async () => {
        try {
            const response = await fetch(`${API_URL}/api/bot/market-conditions`);
            const data = await response.json();
            if (data.status === 'success') {
                setConditions(data.market);
            }
        } catch (error) {
            console.error('Error fetching market conditions:', error);
        }
    };

    if (!conditions) {
        return (
            <Card className="bg-zinc-900 border-zinc-800">
                <CardHeader>
                    <CardTitle className="text-white">Market Conditions</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-zinc-500 text-center py-4">Loading...</div>
                </CardContent>
            </Card>
        );
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'OPEN': return 'bg-green-500';
            case 'PRE-OPEN': return 'bg-yellow-500';
            case 'CLOSED': return 'bg-red-500';
            default: return 'bg-gray-500';
        }
    };

    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case 'BULLISH': return <TrendingUp className="h-5 w-5 text-green-500" />;
            case 'BEARISH': return <TrendingDown className="h-5 w-5 text-red-500" />;
            default: return <Minus className="h-5 w-5 text-zinc-500" />;
        }
    };

    const getTrendColor = (trend: string) => {
        switch (trend) {
            case 'BULLISH': return 'text-green-500';
            case 'BEARISH': return 'text-red-500';
            default: return 'text-zinc-500';
        }
    };

    return (
        <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="text-white">Market Conditions</CardTitle>
                    <Badge className={`${getStatusColor(conditions.status)} text-white`}>
                        {conditions.status}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {/* Market Status */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-zinc-800 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <Clock className="h-4 w-4 text-blue-500" />
                                <p className="text-zinc-400 text-sm">Session</p>
                            </div>
                            <p className="text-white font-semibold">{conditions.session}</p>
                        </div>

                        <div className="bg-zinc-800 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <Calendar className="h-4 w-4 text-blue-500" />
                                <p className="text-zinc-400 text-sm">Current Time</p>
                            </div>
                            <p className="text-white font-semibold">{conditions.current_time}</p>
                        </div>
                    </div>

                    {/* Market Trend */}
                    <div className="bg-zinc-800 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-zinc-400 text-sm mb-1">Market Trend</p>
                                <p className={`text-xl font-bold ${getTrendColor(conditions.trend)}`}>
                                    {conditions.trend}
                                </p>
                            </div>
                            {getTrendIcon(conditions.trend)}
                        </div>
                    </div>

                    {/* Timing Info */}
                    {conditions.opens_in && (
                        <div className="bg-blue-600/10 border border-blue-600/30 rounded-lg p-3">
                            <p className="text-blue-400 text-sm">
                                <span className="font-semibold">Opens in:</span> {conditions.opens_in}
                            </p>
                        </div>
                    )}

                    {conditions.closes_in && (
                        <div className="bg-yellow-600/10 border border-yellow-600/30 rounded-lg p-3">
                            <p className="text-yellow-400 text-sm">
                                <span className="font-semibold">Closes in:</span> {conditions.closes_in}
                            </p>
                        </div>
                    )}

                    {conditions.next_open && (
                        <div className="bg-zinc-800 rounded-lg p-3">
                            <p className="text-zinc-400 text-sm">
                                <span className="font-semibold">Next Open:</span> {conditions.next_open}
                            </p>
                        </div>
                    )}

                    {/* Tradable Status */}
                    <div className={`rounded-lg p-3 ${conditions.is_tradable ? 'bg-green-600/10 border border-green-600/30' : 'bg-red-600/10 border border-red-600/30'}`}>
                        <p className={`text-sm font-semibold ${conditions.is_tradable ? 'text-green-400' : 'text-red-400'}`}>
                            {conditions.is_tradable ? '✓ Trading Active' : '✗ Trading Inactive'}
                        </p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default MarketConditionsCard;
