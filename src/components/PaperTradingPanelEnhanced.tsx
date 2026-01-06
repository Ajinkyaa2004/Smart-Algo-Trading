import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ArrowUpCircle, ArrowDownCircle, Wallet, TrendingUp, TrendingDown, BarChart3, RefreshCcw, Trophy, Clock, Plus, X } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface PaperFunds {
  virtual_capital: number;
  available_funds: number;
  invested_funds: number;
  realized_pnl: number;
  total_value: number;
}

interface PaperHolding {
  symbol: string;
  exchange: string;
  quantity: number;
  average_price: number;
  current_price: number;
  invested_amount: number;
  current_value: number;
  unrealized_pnl: number;
  pnl_percent: number;
}

interface PaperTrade {
  timestamp: string;
  order_id: string;
  symbol: string;
  action: string;
  quantity: number;
  price: number;
  value: number;
  tag: string;
}

interface Statistics {
  total_positions: number;
  total_unrealized_pnl: number;
  total_realized_pnl: number;
  total_pnl: number;
  trades_today: number;
}

interface Portfolio {
  paper_funds: PaperFunds;
  paper_portfolio: PaperHolding[];
  statistics: Statistics;
}

interface PerformanceStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_profit: number;
  avg_loss: number;
  avg_pnl: number;
  best_trade: number;
  worst_trade: number;
  profit_factor: number;
  total_profit: number;
  total_loss: number;
}

interface MarketStatus {
  status: string;
  session: string;
  is_open: boolean;
  current_time: string;
  next_open?: string;
  next_close?: string;
}

const PaperTradingPanelEnhanced: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastTradeCount, setLastTradeCount] = useState(0);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [showManualTrade, setShowManualTrade] = useState(false);
  const [manualOrder, setManualOrder] = useState({ symbol: 'RELIANCE', action: 'BUY', quantity: 1, strategy: 'MANUAL' });

  useEffect(() => {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        setNotificationsEnabled(permission === 'granted');
      });
    } else if ('Notification' in window && Notification.permission === 'granted') {
      setNotificationsEnabled(true);
    }

    fetchAll();

    // Auto-refresh every 5 seconds
    let interval: ReturnType<typeof setInterval>;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchAll();
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchAll = async () => {
    await Promise.all([
      fetchPortfolio(),
      fetchTrades(),
      fetchStats(),
      fetchMarketStatus()
    ]);
  };

  const fetchPortfolio = async () => {
    try {
      const response = await fetch(`${API_URL}/api/paper-trading/portfolio`);
      const data = await response.json();
      if (data.status === 'success') {
        setPortfolio(data.portfolio);
      }
    } catch (error) {
      console.error('Error fetching portfolio:', error);
    }
  };

  const fetchTrades = async () => {
    try {
      const response = await fetch(`${API_URL}/api/paper-trading/trades`);
      const data = await response.json();
      if (data.status === 'success') {
        // Check for new trades and show notification
        if (data.trades.length > lastTradeCount && lastTradeCount > 0) {
          const newTrade = data.trades[data.trades.length - 1];
          showTradeNotification(newTrade);
        }
        setTrades(data.trades);
        setLastTradeCount(data.trades.length);
      }
    } catch (error) {
      console.error('Error fetching trades:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/paper-trading/stats`);
      const data = await response.json();
      if (data.status === 'success') {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchMarketStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/market/status`);
      const data = await response.json();
      if (data.status === 'success') {
        setMarketStatus(data);
      }
    } catch (error) {
      console.error('Error fetching market status:', error);
    }
  };

  const showTradeNotification = (trade: PaperTrade) => {
    // Play sound
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = trade.action === 'BUY' ? 800 : 600;
      oscillator.type = 'sine';
      gainNode.gain.value = 0.1;

      oscillator.start();
      setTimeout(() => oscillator.stop(), 100);
    } catch (error) {
      // Silent fail if audio doesn't work
    }

    // Browser notification
    if (notificationsEnabled) {
      new Notification('📊 Paper Trade Executed', {
        body: `${trade.action} ${trade.quantity} ${trade.symbol} @ ₹${trade.price.toFixed(2)}`,
        icon: '/favicon.ico'
      });
    }

    // Toast notification with color
    const isBuy = trade.action === 'BUY';
    toast.success(
      `${isBuy ? '📈 BUY' : '📉 SELL'} ${trade.quantity} ${trade.symbol} @ ₹${trade.price.toFixed(2)}`,
      {
        description: `Total Value: ₹${trade.value.toFixed(2)} • ${trade.tag || 'Paper Trade'}`,
        duration: 5000
      }
    );
  };

  const resetPortfolio = async () => {
    if (!confirm('Reset paper portfolio to ₹1,00,000? This will clear all positions and trades.')) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/paper-trading/reset`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.status === 'success') {
        toast.success('Portfolio reset to ₹1,00,000');
        setLastTradeCount(0);
        fetchAll();
      }
    } catch (error) {
      toast.error('Failed to reset portfolio');
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualTrade = async () => {
    if (!manualOrder.symbol || manualOrder.quantity <= 0) {
      toast.error("Invalid order details");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/paper-trading/manual-trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(manualOrder)
      });
      const data = await response.json();

      if (data.status === 'success') {
        toast.success(`Trade Executed: ${manualOrder.action} ${manualOrder.quantity} ${manualOrder.symbol}`);
        setShowManualTrade(false);
        fetchAll();
      } else {
        toast.error(data.detail || "Trade failed");
      }
    } catch (error) {
      toast.error('Failed to place trade');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (!portfolio) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading paper portfolio...</div>
      </div>
    );
  }

  const { paper_funds, paper_portfolio, statistics } = portfolio;
  const totalPnlPercent = (statistics.total_pnl / paper_funds.virtual_capital) * 100;

  return (
    <div className="space-y-6">
      {/* Market Status Banner */}
      {marketStatus && (
        <Card className={`border-2 ${marketStatus.is_open ? 'border-green-500/50 bg-zinc-900' : 'border-zinc-700 bg-zinc-900'}`}>
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Clock className={`h-5 w-5 ${marketStatus.is_open ? 'text-green-400' : 'text-zinc-400'}`} />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-lg">
                      {marketStatus.is_open ? '🟢 Market Open' : '🔴 Market Closed'}
                    </span>
                    <Badge variant={marketStatus.is_open ? 'default' : 'secondary'}>
                      {marketStatus.session}
                    </Badge>
                  </div>
                  <div className="text-xs text-zinc-400 mt-1">
                    {marketStatus.is_open
                      ? `Closes at ${marketStatus.next_close}`
                      : `Opens at ${marketStatus.next_open}`}
                  </div>
                </div>
              </div>
              <div className="text-sm text-zinc-400">
                Current Time: {new Date(marketStatus.current_time).toLocaleTimeString('en-IN')}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance Stats Widget */}
      {stats && (
        <Card className="border-purple-500/30 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Trophy className="h-5 w-5 text-purple-400" />
              Performance Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-xs text-zinc-400 mb-1">Win Rate</div>
                <div className={`text-2xl font-bold ${stats.win_rate >= 50 ? 'text-green-400' : 'text-orange-400'}`}>
                  {stats.win_rate.toFixed(1)}%
                </div>
                <div className="text-xs text-zinc-500 mt-1">
                  {stats.winning_trades}W / {stats.losing_trades}L
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-zinc-400 mb-1">Avg Profit</div>
                <div className="text-2xl font-bold text-green-400">
                  {formatCurrency(stats.avg_profit)}
                </div>
                <div className="text-xs text-zinc-500 mt-1">
                  per winning trade
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-zinc-400 mb-1">Avg Loss</div>
                <div className="text-2xl font-bold text-red-400">
                  {formatCurrency(stats.avg_loss)}
                </div>
                <div className="text-xs text-zinc-500 mt-1">
                  per losing trade
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-zinc-400 mb-1">Profit Factor</div>
                <div className={`text-2xl font-bold ${stats.profit_factor >= 1.5 ? 'text-green-400' : stats.profit_factor >= 1 ? 'text-blue-400' : 'text-red-400'}`}>
                  {stats.profit_factor.toFixed(2)}
                </div>
                <div className="text-xs text-zinc-500 mt-1">
                  {stats.profit_factor >= 1.5 ? 'Excellent' : stats.profit_factor >= 1 ? 'Good' : 'Poor'}
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-zinc-800 grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-xs text-zinc-400 mb-1">Best Trade</div>
                <div className="text-lg font-bold text-green-400">
                  {formatCurrency(stats.best_trade)}
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-zinc-400 mb-1">Worst Trade</div>
                <div className="text-lg font-bold text-red-400">
                  {formatCurrency(stats.worst_trade)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Paper Funds Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-blue-500/30 bg-zinc-900">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-400 flex items-center gap-2">
              <Wallet className="h-4 w-4" />
              Paper Funds
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zinc-100">
              {formatCurrency(paper_funds.available_funds)}
            </div>
            <div className="text-xs text-zinc-400 mt-1">
              of {formatCurrency(paper_funds.virtual_capital)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-zinc-900 border-blue-500/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-400 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 " />
              Invested
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-zinc-100">
              {formatCurrency(paper_funds.invested_funds)}
            </div>
            <div className="text-xs text-zinc-400 mt-1">
              {statistics.total_positions} positions
            </div>
          </CardContent>
        </Card>

        <Card className={statistics.total_unrealized_pnl >= 0 ? 'border-green-500/30 bg-zinc-900' : 'border-red-500/30 bg-zinc-900'}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium flex items-center gap-2 ${statistics.total_unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {statistics.total_unrealized_pnl >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
              Unrealized P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${statistics.total_unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(statistics.total_unrealized_pnl)}
            </div>
            <div className={`text-xs mt-1 ${statistics.total_unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              Live P&L {autoRefresh && <span className="animate-pulse">●</span>}
            </div>
          </CardContent>
        </Card>

        <Card className={statistics.total_realized_pnl >= 0 ? 'border-green-500/30 bg-zinc-900' : 'border-red-500/30 bg-zinc-900'}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium flex items-center gap-2 ${statistics.total_realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {statistics.total_realized_pnl >= 0 ? <ArrowUpCircle className="h-4 w-4" /> : <ArrowDownCircle className="h-4 w-4" />}
              Realized P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${statistics.total_realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(statistics.total_realized_pnl)}
            </div>
            <div className={`text-xs mt-1 ${statistics.total_realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {statistics.trades_today} trades today
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Paper Portfolio Holdings with Color Coding */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Paper Portfolio</CardTitle>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={autoRefresh ? 'bg-green-900/20 text-green-400 border-green-900/50' : 'bg-zinc-800 text-zinc-400 border-zinc-700'}
              >
                <RefreshCcw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
                {autoRefresh ? 'Auto' : 'Paused'}
              </Button>
              <Button
                variant="default"
                size="sm"
                className="bg-blue-600 hover:bg-blue-700 text-white"
                onClick={() => setShowManualTrade(!showManualTrade)}
              >
                <Plus className="h-4 w-4 mr-2" />
                New Trade
              </Button>
              <Button variant="destructive" size="sm" onClick={resetPortfolio} disabled={isLoading}>
                Reset Portfolio
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {showManualTrade && (
            <div className="mb-6 p-4 bg-zinc-800/50 border border-zinc-700 rounded-lg animate-in slide-in-from-top-2">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-sm font-medium text-zinc-200">Manual Trade Execution</h4>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => setShowManualTrade(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div>
                  <label className="text-xs text-zinc-400 block mb-1">Symbol</label>
                  <input
                    type="text"
                    value={manualOrder.symbol}
                    onChange={(e) => setManualOrder({ ...manualOrder, symbol: e.target.value.toUpperCase() })}
                    className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-blue-500"
                    placeholder="e.g. RELIANCE"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-400 block mb-1">Action</label>
                  <select
                    value={manualOrder.action}
                    onChange={(e) => setManualOrder({ ...manualOrder, action: e.target.value })}
                    className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="BUY">BUY</option>
                    <option value="SELL">SELL</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-zinc-400 block mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={manualOrder.quantity}
                    onChange={(e) => setManualOrder({ ...manualOrder, quantity: parseInt(e.target.value) || 0 })}
                    className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <Button
                  onClick={handleManualTrade}
                  disabled={isLoading}
                  className={manualOrder.action === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
                >
                  Place {manualOrder.action} Order
                </Button>
              </div>
            </div>
          )}

          {paper_portfolio.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No holdings yet. Start trading to see positions here.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b">
                  <tr className="text-left text-zinc-400">
                    <th className="pb-2 pl-2">Symbol</th>
                    <th className="pb-2 text-right">Qty</th>
                    <th className="pb-2 text-right">Avg Price</th>
                    <th className="pb-2 text-right">Current</th>
                    <th className="pb-2 text-right">Invested</th>
                    <th className="pb-2 text-right">Current Value</th>
                    <th className="pb-2 text-right">P&L</th>
                    <th className="pb-2 text-right pr-2">%</th>
                  </tr>
                </thead>
                <tbody>
                  {paper_portfolio.map((holding, index) => {
                    const isWinning = holding.unrealized_pnl > 0;
                    const rowClass = isWinning
                      ? 'bg-green-900/10 border-l-4 border-green-500 hover:bg-green-900/20'
                      : holding.unrealized_pnl < 0
                        ? 'bg-red-900/10 border-l-4 border-red-500 hover:bg-red-900/20'
                        : 'hover:bg-zinc-800/50';

                    return (
                      <tr key={index} className={`border-b border-zinc-800 ${rowClass} transition-colors`}>
                        <td className="py-3 pl-2 font-medium text-zinc-200">{holding.symbol}</td>
                        <td className="py-3 text-right text-zinc-300">{holding.quantity}</td>
                        <td className="py-3 text-right text-zinc-400">{formatCurrency(holding.average_price)}</td>
                        <td className="py-3 text-right font-medium text-zinc-200">{formatCurrency(holding.current_price)}</td>
                        <td className="py-3 text-right text-zinc-400">{formatCurrency(holding.invested_amount)}</td>
                        <td className="py-3 text-right font-medium text-zinc-200">{formatCurrency(holding.current_value)}</td>
                        <td className={`py-3 text-right font-bold ${holding.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {formatCurrency(holding.unrealized_pnl)}
                        </td>
                        <td className={`py-3 text-right pr-2 font-semibold ${holding.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {holding.pnl_percent > 0 ? '+' : ''}{holding.pnl_percent.toFixed(2)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Paper Trade History */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Paper Trade History</CardTitle>
        </CardHeader>
        <CardContent>
          {trades.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No trades yet. All paper trades will be recorded here.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-zinc-800">
                  <tr className="text-left text-zinc-400">
                    <th className="pb-2 pl-2">Time</th>
                    <th className="pb-2">Symbol</th>
                    <th className="pb-2">Action</th>
                    <th className="pb-2 text-right">Qty</th>
                    <th className="pb-2 text-right">Price</th>
                    <th className="pb-2 text-right">Value</th>
                    <th className="pb-2 pr-2">Strategy</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.slice().reverse().map((trade, index) => (
                    <tr key={index} className="border-b border-zinc-800 hover:bg-zinc-800/50 transition-colors">
                      <td className="py-2 pl-2 text-zinc-400">{formatTime(trade.timestamp)}</td>
                      <td className="py-2 font-medium text-zinc-200">{trade.symbol}</td>
                      <td className="py-2">
                        <Badge variant={trade.action === 'BUY' ? 'default' : 'destructive'}>
                          {trade.action}
                        </Badge>
                      </td>
                      <td className="py-2 text-right text-zinc-300">{trade.quantity}</td>
                      <td className="py-2 text-right text-zinc-300">{formatCurrency(trade.price)}</td>
                      <td className="py-2 text-right font-medium text-zinc-200">{formatCurrency(trade.value)}</td>
                      <td className="py-2 pr-2 text-zinc-500">{trade.tag || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Overall Summary */}
      <Card className="border-2 border-blue-200">
        <CardHeader>
          <CardTitle className="text-lg text-blue-900">Overall Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-gray-600">Total Capital</div>
              <div className="text-lg font-bold">{formatCurrency(paper_funds.total_value)}</div>
            </div>
            <div>
              <div className="text-xs text-gray-600">Total P&L</div>
              <div className={`text-lg font-bold ${statistics.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(statistics.total_pnl)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-600">P&L %</div>
              <div className={`text-lg font-bold ${totalPnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {totalPnlPercent > 0 ? '+' : ''}{totalPnlPercent.toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-600">Total Trades</div>
              <div className="text-lg font-bold">{trades.length}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaperTradingPanelEnhanced;
