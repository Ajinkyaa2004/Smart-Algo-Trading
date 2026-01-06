import React, { useState, useEffect } from 'react';
import { LayoutDashboard, TrendingUp, Settings, Activity, Menu, LogOut, Wallet, Database, ShoppingCart, Bot, BarChart3 } from 'lucide-react';
import { cn } from '../lib/utils';
import { MarketTicker } from '../components/MarketTicker';

interface SidebarProps {
    activePage: string;
    onNavigate: (page: string) => void;
    isOpen: boolean;
    onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate, isOpen }) => {
    const navItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'portfolio', label: 'Portfolio', icon: Wallet },
        { id: 'strategies', label: 'Strategies', icon: TrendingUp },
        { id: 'trading-bot', label: 'Trading Bot', icon: Bot },
        { id: 'backtesting', label: 'Backtesting', icon: BarChart3 },
        { id: 'live', label: 'Live Trading', icon: Activity },
        { id: 'orders', label: 'Orders', icon: ShoppingCart },
        { id: 'historical', label: 'Historical Data', icon: Database },
        { id: 'settings', label: 'Settings', icon: Settings },
    ];

    return (
        <div className={cn(
            "bg-zinc-950 border-r border-zinc-800 h-screen flex flex-col hidden md:flex transition-all duration-300",
            isOpen ? "w-64" : "w-20"
        )}>
            <div className="p-6 border-b border-zinc-800">
                <div className={cn("flex items-center gap-2", !isOpen && "justify-center")}>
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Activity className="text-white w-5 h-5" />
                    </div>
                    {isOpen && (
                        <h1 className="text-lg font-bold text-zinc-100 tracking-tight whitespace-nowrap">AlgoTrade<span className="text-blue-500">Pro</span></h1>
                    )}
                </div>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onNavigate(item.id)}
                        className={cn(
                            "w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                            activePage === item.id
                                ? "bg-zinc-900 text-blue-400 border border-zinc-800"
                                : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/50",
                            !isOpen && "justify-center"
                        )}
                        title={!isOpen ? item.label : undefined}
                    >
                        <item.icon className="w-5 h-5 flex-shrink-0" />
                        {isOpen && <span>{item.label}</span>}
                    </button>
                ))}
            </nav>

            <div className="p-4 border-t border-zinc-800">
                <button
                    onClick={async () => {
                        if (confirm('Are you sure you want to logout?')) {
                            try {
                                await fetch('http://localhost:8000/api/auth/logout', { method: 'POST' });
                                window.location.href = '/'; // Redirect to root (which will redirect to login if auth check fails)
                            } catch (e) {
                                console.error(e);
                                window.location.href = '/';
                            }
                        }
                    }}
                    className={cn(
                        "w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-950/20 transition-colors",
                        !isOpen && "justify-center"
                    )}
                    title={!isOpen ? "Logout" : undefined}
                >
                    <LogOut className="w-5 h-5 flex-shrink-0" />
                    {isOpen && <span>Logout</span>}
                </button>
            </div>
        </div>
    );
};

interface HeaderProps {
    isSidebarOpen: boolean;
    onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ isSidebarOpen, onToggleSidebar }) => {
    const [marketStatus, setMarketStatus] = useState<{
        market_status: string;
        session?: string;
        current_time?: string;
        is_streaming_recommended?: boolean;
        closes_in?: string;
        opens_in?: string;
        next_open?: string;
    }>({ market_status: 'LOADING' });
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('connecting');
    const [retryCount, setRetryCount] = useState(0);
    const [countdownSeconds, setCountdownSeconds] = useState<number>(0);

    useEffect(() => {
        const fetchMarketStatus = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/market/status', {
                    signal: AbortSignal.timeout(5000) // 5 second timeout
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                if (data.status === 'success') {
                    setMarketStatus(data);
                    setConnectionStatus('connected');
                    setRetryCount(0);

                    // Parse and set initial countdown seconds
                    const timeStr = data.opens_in || data.closes_in;
                    if (timeStr) {
                        const parts = timeStr.split(':').map((p: string) => parseInt(p));
                        let totalSeconds = 0;
                        if (parts.length === 3) {
                            totalSeconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
                        } else if (parts.length === 2) {
                            totalSeconds = parts[0] * 60 + parts[1];
                        }
                        setCountdownSeconds(totalSeconds);
                    }
                }
            } catch (error) {
                console.error('Failed to fetch market status:', error);
                setConnectionStatus('disconnected');
                setRetryCount(prev => prev + 1);

                // After 3 failed attempts, show error in UI
                if (retryCount >= 3) {
                    setMarketStatus(prev => ({ ...prev, market_status: 'ERROR' }));
                }
            }
        };

        // Fetch immediately
        fetchMarketStatus();

        // Refresh every 10 seconds
        const interval = setInterval(fetchMarketStatus, 10000);

        return () => clearInterval(interval);
    }, [retryCount]);

    // Countdown timer that decrements every second
    useEffect(() => {
        if (countdownSeconds <= 0) return;

        const timer = setInterval(() => {
            setCountdownSeconds(prev => {
                if (prev <= 1) return 0;
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [countdownSeconds]);

    const getStatusColor = () => {
        switch (marketStatus.market_status) {
            case 'OPEN':
                return 'text-emerald-500 bg-emerald-500';
            case 'PRE-OPEN':
                return 'text-yellow-500 bg-yellow-500';
            case 'CLOSED':
                return 'text-red-500 bg-red-500';
            case 'LOADING':
                return 'text-blue-500 bg-blue-500';
            case 'ERROR':
                return 'text-orange-500 bg-orange-500';
            default:
                return 'text-zinc-500 bg-zinc-500';
        }
    };

    const getStatusInfo = () => {
        // Format countdown from seconds
        if (countdownSeconds > 0 && (marketStatus.market_status === 'OPEN' || marketStatus.market_status === 'PRE-OPEN')) {
            const hours = Math.floor(countdownSeconds / 3600);
            const minutes = Math.floor((countdownSeconds % 3600) / 60);
            const seconds = countdownSeconds % 60;

            const timeStr = hours > 0
                ? `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
                : `${minutes}:${seconds.toString().padStart(2, '0')}`;

            if (marketStatus.market_status === 'OPEN') {
                return `Closes in ${timeStr}`;
            } else {
                return `Opens in ${timeStr}`;
            }
        }

        if (marketStatus.market_status === 'CLOSED' && marketStatus.next_open) {
            return `Next: ${marketStatus.next_open}`;
        }
        return marketStatus.session || '';
    };

    return (
        <header className="h-16 bg-zinc-950/50 backdrop-blur-md border-b border-zinc-800 flex items-center justify-between px-2 sticky top-0 z-50">
            <div className="flex items-center space-x-4">
                <button
                    onClick={onToggleSidebar}
                    className="hidden md:flex p-2 hover:bg-zinc-800 rounded-lg transition-colors text-zinc-400 hover:text-zinc-100"
                    title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
                >
                    <Menu className="w-5 h-5" />
                </button>

                {/* Mobile Menu */}
                <div className="flex items-center md:hidden">
                    <Menu className="text-zinc-400" />
                </div>

                {/* Market Status - Desktop */}
                <div className="hidden md:flex items-center space-x-6">
                    <div className="flex flex-col">
                        <span className="text-xs text-zinc-500 font-medium uppercase">Market Status</span>
                        <div className="flex items-center gap-2">
                            <span className={`text-sm font-bold flex items-center gap-1 ${getStatusColor().split(' ')[0]}`}>
                                <span className={`w-2 h-2 rounded-full ${getStatusColor().split(' ')[1]} ${marketStatus.market_status === 'OPEN' ? 'animate-pulse' : ''}`}></span>
                                {marketStatus.market_status}
                            </span>
                            <span className="text-xs text-zinc-500">
                                {getStatusInfo()}
                            </span>
                        </div>
                    </div>
                    <div className="h-8 w-px bg-zinc-800"></div>

                    {/* Live Customizable Ticker */}
                    <MarketTicker />
                </div>
            </div>

            <div className="flex items-center space-x-4">
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-emerald-500' :
                        connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                            'bg-red-500'
                        }`}></span>
                    <span className="text-sm text-zinc-400">
                        {connectionStatus === 'connected' ? 'Connected' :
                            connectionStatus === 'connecting' ? 'Connecting...' :
                                'Disconnected'}
                    </span>
                    {marketStatus.is_streaming_recommended && marketStatus.market_status === 'OPEN' && (
                        <span className="text-xs text-emerald-500 font-medium">● LIVE</span>
                    )}
                </div>
            </div>
        </header>
    )
}
