import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ArrowUpCircle, ArrowDownCircle, Wallet, TrendingUp, TrendingDown, BarChart3, RefreshCcw } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';

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

const PaperTradingPanel: React.FC = () => {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [trades, setTrades] = useState<PaperTrade[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchPortfolio();
    fetchTrades();

    // Auto-refresh every 5 seconds
    let interval: ReturnType<typeof setInterval>;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchPortfolio();
        fetchTrades();
      }, 5000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchPortfolio = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/paper-trading/portfolio');
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
      const response = await fetch('http://localhost:8000/api/paper-trading/trades');
      const data = await response.json();
      if (data.status === 'success') {
        setTrades(data.trades);
      }
    } catch (error) {
      console.error('Error fetching trades:', error);
    }
  };

  const resetPortfolio = async () => {
    if (!confirm('Reset paper portfolio to ₹1,00,000? This will clear all positions and trades.')) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/paper-trading/reset', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.status === 'success') {
        toast.success('Portfolio reset to ₹1,00,000');
        fetchPortfolio();
        fetchTrades();
      }
    } catch (error) {
      toast.error('Failed to reset portfolio');
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
      {/* Paper Funds Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-700 flex items-center gap-2">
              <Wallet className="h-4 w-4" />
              Paper Funds
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">
              {formatCurrency(paper_funds.available_funds)}
            </div>
            <div className="text-xs text-blue-600 mt-1">
              of {formatCurrency(paper_funds.virtual_capital)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Invested
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(paper_funds.invested_funds)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {statistics.total_positions} positions
            </div>
          </CardContent>
        </Card>

        <Card className={statistics.total_unrealized_pnl >= 0 ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium flex items-center gap-2 ${statistics.total_unrealized_pnl >= 0 ? 'text-green-700' : 'text-red-700'}`}>
              {statistics.total_unrealized_pnl >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
              Unrealized P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${statistics.total_unrealized_pnl >= 0 ? 'text-green-900' : 'text-red-900'}`}>
              {formatCurrency(statistics.total_unrealized_pnl)}
            </div>
            <div className={`text-xs mt-1 ${statistics.total_unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              Live P&L
            </div>
          </CardContent>
        </Card>

        <Card className={statistics.total_realized_pnl >= 0 ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
          <CardHeader className="pb-2">
            <CardTitle className={`text-sm font-medium flex items-center gap-2 ${statistics.total_realized_pnl >= 0 ? 'text-green-700' : 'text-red-700'}`}>
              {statistics.total_realized_pnl >= 0 ? <ArrowUpCircle className="h-4 w-4" /> : <ArrowDownCircle className="h-4 w-4" />}
              Realized P&L
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${statistics.total_realized_pnl >= 0 ? 'text-green-900' : 'text-red-900'}`}>
              {formatCurrency(statistics.total_realized_pnl)}
            </div>
            <div className={`text-xs mt-1 ${statistics.total_realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {statistics.trades_today} trades today
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Paper Portfolio Holdings */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Paper Portfolio</CardTitle>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                <RefreshCcw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
                {autoRefresh ? 'Auto' : 'Manual'}
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={resetPortfolio}
                disabled={isLoading}
              >
                Reset Portfolio
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {paper_portfolio.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No holdings yet. Start trading to see positions here.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b">
                  <tr className="text-left text-gray-600">
                    <th className="pb-2">Symbol</th>
                    <th className="pb-2 text-right">Qty</th>
                    <th className="pb-2 text-right">Avg Price</th>
                    <th className="pb-2 text-right">Current</th>
                    <th className="pb-2 text-right">Invested</th>
                    <th className="pb-2 text-right">Current Value</th>
                    <th className="pb-2 text-right">P&L</th>
                    <th className="pb-2 text-right">%</th>
                  </tr>
                </thead>
                <tbody>
                  {paper_portfolio.map((holding, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="py-3 font-medium">{holding.symbol}</td>
                      <td className="py-3 text-right">{holding.quantity}</td>
                      <td className="py-3 text-right">{formatCurrency(holding.average_price)}</td>
                      <td className="py-3 text-right">{formatCurrency(holding.current_price)}</td>
                      <td className="py-3 text-right text-gray-600">{formatCurrency(holding.invested_amount)}</td>
                      <td className="py-3 text-right font-medium">{formatCurrency(holding.current_value)}</td>
                      <td className={`py-3 text-right font-semibold ${holding.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(holding.unrealized_pnl)}
                      </td>
                      <td className={`py-3 text-right ${holding.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {holding.pnl_percent.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
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
                <thead className="border-b">
                  <tr className="text-left text-gray-600">
                    <th className="pb-2">Time</th>
                    <th className="pb-2">Symbol</th>
                    <th className="pb-2">Action</th>
                    <th className="pb-2 text-right">Qty</th>
                    <th className="pb-2 text-right">Price</th>
                    <th className="pb-2 text-right">Value</th>
                    <th className="pb-2">Strategy</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.slice().reverse().map((trade, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="py-2 text-gray-600">{formatTime(trade.timestamp)}</td>
                      <td className="py-2 font-medium">{trade.symbol}</td>
                      <td className="py-2">
                        <Badge variant={trade.action === 'BUY' ? 'default' : 'destructive'}>
                          {trade.action}
                        </Badge>
                      </td>
                      <td className="py-2 text-right">{trade.quantity}</td>
                      <td className="py-2 text-right">{formatCurrency(trade.price)}</td>
                      <td className="py-2 text-right font-medium">{formatCurrency(trade.value)}</td>
                      <td className="py-2 text-gray-600">{trade.tag || '-'}</td>
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
                {totalPnlPercent.toFixed(2)}%
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

export default PaperTradingPanel;
