/**
 * Historical Data & Backtesting Page
 * Unified page for browsing historical data and running strategy backtests
 */

import { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import HistoricalDataPanel from '../components/HistoricalDataPanel';
import { ApexCandlestickChart } from '../components/ApexCandlestickChart';
import { SymbolSearch } from '../components/SymbolSearch';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  TrendingUp, Database, Search, Play, TrendingDown, BarChart3,
  Target, AlertCircle, CheckCircle2, ArrowDownRight, Loader2,
  Activity, Zap, Calendar
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

interface CandlestickData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

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

export default function HistoricalData() {
  // Tab state
  const [activeTab, setActiveTab] = useState<'historical' | 'backtesting'>('historical');

  // Historical Data state
  const [chartData, setChartData] = useState<CandlestickData[]>([]);
  const [showChart, setShowChart] = useState(true);
  const [instrumentList, setInstrumentList] = useState<any[]>([]);
  const [activeListMode, setActiveListMode] = useState<'FUTURES' | 'OPTIONS' | 'EQUITIES' | null>(null);
  const [listTitle, setListTitle] = useState('');


  // Backtesting state
  const [symbol, setSymbol] = useState('RELIANCE');
  const [backtestExchange] = useState('NSE');
  const [strategyType, setStrategyType] = useState('supertrend');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [interval, setInterval] = useState('15minute');
  const [initialCapital, setInitialCapital] = useState(100000);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [intervals, setIntervals] = useState<any[]>([]);



  useEffect(() => {
    if (activeTab === 'backtesting') {
      fetchStrategies();
      fetchIntervals();
    }
  }, [activeTab]);

  const handleDataFetched = (data: any[]) => {
    setChartData(data);
  };

  const fetchInstrumentList = async (type: 'FUTURES' | 'OPTIONS' | 'EQUITIES') => {
    try {
      setActiveListMode(type);
      setInstrumentList([]); // Clear previous list
      let url = '';
      let title = '';

      if (type === 'FUTURES') {
        url = 'http://localhost:8000/api/market/nfo/futures?underlying=NIFTY';
        title = 'NIFTY Futures';
      } else if (type === 'OPTIONS') {
        url = 'http://localhost:8000/api/market/nfo/options?underlying=NIFTY'; // Assuming this endpoint exists based on backend files
        title = 'NIFTY Options';
      } else {
        url = 'http://localhost:8000/api/market/instruments/NSE'; // Fetch NSE instruments
        title = 'Equity Stocks';
      }

      const response = await fetch(url);
      const result = await response.json();

      if (result.status === 'success') {
        // Limit to 50 for performance if list is huge
        const data = result.data || result.instruments || [];
        setInstrumentList(data.slice(0, 50));
        setListTitle(title);
        toast.success(`Fetched ${data.length} instruments`);
      } else {
        toast.error('Failed to fetch instruments');
      }
    } catch (error) {
      console.error('Error fetching instruments:', error);
      toast.error('Failed to connect to server');
    }
  };






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
      const getFullDateTime = (date: string, time: string) => {
        if (!date) return '';
        if (!time) return date; // Return date only if time is empty. backend will default to 00:00 or similar
        return `${date} ${time}`;
      };

      const requestPayload = {
        symbol,
        exchange: backtestExchange,
        strategy_type: strategyType,
        start_date: getFullDateTime(startDate, startTime),
        end_date: getFullDateTime(endDate, endTime),
        interval,
        initial_capital: initialCapital
      };

      console.log('Sending Backtest Request:', requestPayload);

      const response = await fetch(`${API_URL}/api/backtest/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload)
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
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
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
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(16, 185, 129, 0.5)',
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
    <div className="h-full w-full p-6 space-y-6 bg-black/20">
      {/* Header with Tabs */}
      <div className="bg-gradient-to-br from-zinc-900/90 via-zinc-900/70 to-zinc-950/90 backdrop-blur-xl border border-zinc-800/50 rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-emerald-500/20 to-blue-500/20 rounded-xl border border-emerald-500/30">
              <Database className="w-8 h-8 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
                Historical Data & Backtesting
              </h1>
              <p className="text-zinc-400 mt-1">
                {activeTab === 'historical'
                  ? 'Fetch and analyze historical OHLC data'
                  : 'Test your strategies on real historical data'}
              </p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 bg-zinc-950/50 p-1.5 rounded-xl border border-zinc-800/50">
          <button
            onClick={() => setActiveTab('historical')}
            className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${activeTab === 'historical'
              ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/25'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`}
          >
            <Database className="w-5 h-5" />
            Historical Data
          </button>
          <button
            onClick={() => setActiveTab('backtesting')}
            className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${activeTab === 'backtesting'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`}
          >
            <Activity className="w-5 h-5" />
            Strategy Backtesting
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'historical' ? (
          <motion.div
            key="historical"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="space-y-6"
          >
            {/* Quick Actions Removed as per user request */}

            {/* Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-950/50 to-blue-900/30 border border-blue-900/50 rounded-xl p-6 hover:border-blue-800/70 transition-all backdrop-blur-sm">
                <div className="flex items-center gap-4">
                  <div className="p-4 bg-blue-500/20 rounded-xl border border-blue-500/30">
                    <Database className="w-7 h-7 text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-blue-300/70 mb-1 font-medium">Exchanges</p>
                    <p className="text-2xl font-bold text-blue-100">NSE, BSE, NFO</p>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-emerald-950/50 to-emerald-900/30 border border-emerald-900/50 rounded-xl p-6 hover:border-emerald-800/70 transition-all backdrop-blur-sm">
                <div className="flex items-center gap-4">
                  <div className="p-4 bg-emerald-500/20 rounded-xl border border-emerald-500/30">
                    <TrendingUp className="w-7 h-7 text-emerald-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-emerald-300/70 mb-1 font-medium">Intervals</p>
                    <p className="text-2xl font-bold text-emerald-100">1min to Daily</p>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-950/50 to-purple-900/30 border border-purple-900/50 rounded-xl p-6 hover:border-purple-800/70 transition-all backdrop-blur-sm">
                <div className="flex items-center gap-4">
                  <div className="p-4 bg-purple-500/20 rounded-xl border border-purple-500/30">
                    <Search className="w-7 h-7 text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-purple-300/70 mb-1 font-medium">Instruments</p>
                    <p className="text-2xl font-bold text-purple-100">Stocks + Derivatives</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Historical Data Panel */}
            <div>
              <HistoricalDataPanel onDataFetched={handleDataFetched} />
            </div>

            {/* Chart */}
            {chartData.length > 0 && showChart && (
              <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-6 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-zinc-100">Price Chart</h3>
                  <button
                    onClick={() => setShowChart(false)}
                    className="text-sm text-zinc-400 hover:text-zinc-200 transition-colors px-3 py-1.5 rounded-lg hover:bg-zinc-800/50"
                  >
                    Hide Chart
                  </button>
                </div>
                <ApexCandlestickChart data={chartData} height={500} />
              </div>
            )}

            {!showChart && chartData.length > 0 && (
              <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-6 text-center backdrop-blur-sm">
                <button
                  onClick={() => setShowChart(true)}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-500 hover:to-blue-600 transition-all shadow-lg shadow-blue-500/20 font-medium"
                >
                  Show Chart
                </button>
              </div>
            )}

            {/* Instrument List Table */}
            {instrumentList.length > 0 && activeListMode && (
              <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-6 backdrop-blur-sm animate-in fade-in slide-in-from-bottom-4 duration-300">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-zinc-100">{listTitle} ({instrumentList.length})</h3>
                  <button onClick={() => setActiveListMode(null)} className="text-zinc-500 hover:text-zinc-300">
                    Close
                  </button>
                </div>
                <div className="overflow-x-auto max-h-[400px] scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
                  <table className="min-w-full divide-y divide-zinc-800">
                    <thead className="bg-zinc-900/50 sticky top-0 backdrop-blur-sm z-10">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Symbol</th>
                        {activeListMode !== 'EQUITIES' && <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Expiry</th>}
                        {activeListMode !== 'EQUITIES' && <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Lot Size</th>}
                        <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Exchange</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {instrumentList.map((item, idx) => (
                        <tr key={idx} className="hover:bg-zinc-800/30 transition-colors">
                          <td className="px-4 py-3 text-sm font-medium text-zinc-100">
                            {item.tradingsymbol}
                            <div className="text-xs text-zinc-500">{item.name}</div>
                          </td>
                          {activeListMode !== 'EQUITIES' && (
                            <td className="px-4 py-3 text-sm text-zinc-400">
                              {item.expiry ? new Date(item.expiry).toLocaleDateString() : '-'}
                            </td>
                          )}
                          {activeListMode !== 'EQUITIES' && (
                            <td className="px-4 py-3 text-sm text-zinc-400">
                              {item.lot_size || '-'}
                            </td>
                          )}
                          <td className="px-4 py-3 text-sm text-zinc-400">
                            {item.exchange}
                          </td>
                          <td className="px-4 py-3">
                            <button
                              onClick={() => {
                                toast.info(`Selected ${item.tradingsymbol}`);
                                // Ideally, this would populate the HistoricalDataPanel search box
                                // We can implement a context or callback if needed, but for now just notify
                              }}
                              className="text-xs bg-blue-500/10 text-blue-400 px-3 py-1.5 rounded hover:bg-blue-500/20 transition-colors"
                            >
                              Load
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Instrument Browsing Buttons */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => fetchInstrumentList('FUTURES')}
                className={`p-4 rounded-xl border transition-all flex items-center justify-center gap-3 ${activeListMode === 'FUTURES'
                  ? 'bg-purple-600/20 border-purple-500/50 text-purple-200'
                  : 'bg-zinc-900/50 border-zinc-800/50 text-zinc-400 hover:border-purple-500/30 hover:text-purple-300'
                  }`}
              >
                <TrendingUp className="w-5 h-5" />
                <span className="font-semibold">NFO Futures</span>
              </button>

              <button
                onClick={() => fetchInstrumentList('OPTIONS')}
                className={`p-4 rounded-xl border transition-all flex items-center justify-center gap-3 ${activeListMode === 'OPTIONS'
                  ? 'bg-blue-600/20 border-blue-500/50 text-blue-200'
                  : 'bg-zinc-900/50 border-zinc-800/50 text-zinc-400 hover:border-blue-500/30 hover:text-blue-300'
                  }`}
              >
                <Target className="w-5 h-5" />
                <span className="font-semibold">NFO Options</span>
              </button>
            </div>

            {/* Quick Guide */}
            <div className="bg-gradient-to-br from-blue-950/30 to-blue-900/20 border border-blue-900/50 rounded-xl p-6 backdrop-blur-sm">
              <h3 className="text-lg font-semibold text-blue-400 mb-3 flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Quick Guide
              </h3>
              <ul className="space-y-2 text-sm text-zinc-300">
                <li>• <strong className="text-zinc-100">Fetch Historical Data:</strong> Enter symbol, select interval and duration, click "Fetch Historical Data"</li>
                <li>• <strong className="text-zinc-100">NFO Futures:</strong> Click "NFO Futures" to browse NIFTY futures contracts</li>
                <li>• <strong className="text-zinc-100">Search:</strong> Use search bar to find any NSE/BSE instrument</li>
                <li>• <strong className="text-zinc-100">Export:</strong> After fetching data, click "Export CSV" to download</li>
                <li>• <strong className="text-zinc-100">Chart:</strong> Automatically displays candlestick chart with fetched data</li>
              </ul>
            </div>

          </motion.div>
        ) : (
          <motion.div
            key="backtesting"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="space-y-6"
          >
            {/* Configuration Panel */}
            <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-400" />
                  Backtest Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid grid-cols-12 gap-6">
                  {/* Row 1: Symbol & Strategy */}
                  <div className="col-span-12 md:col-span-8">
                    <label className="text-xs font-semibold text-zinc-400 mb-2 block uppercase tracking-wider">Symbol</label>
                    <SymbolSearch
                      value={symbol}
                      onChange={setSymbol}
                      exchange="NSE"
                      placeholder="Search Stocks (e.g. RELIANCE, TCS...)"
                      className="w-full"
                    />
                  </div>

                  <div className="col-span-12 md:col-span-4">
                    <label className="text-xs font-semibold text-zinc-400 mb-2 block uppercase tracking-wider">Strategy</label>
                    <div className="relative">
                      <select
                        value={strategyType}
                        onChange={(e) => setStrategyType(e.target.value)}
                        disabled={isRunning}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 hover:border-zinc-700 transition-all appearance-none cursor-pointer"
                      >
                        {strategies.map(strategy => (
                          <option key={strategy.type} value={strategy.type}>
                            {strategy.name}
                          </option>
                        ))}
                      </select>
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500">
                        <TrendingUp className="w-4 h-4" />
                      </div>
                    </div>
                  </div>

                  {/* Row 2: Settings */}
                  <div className="col-span-12 md:col-span-4">
                    <label className="text-xs font-semibold text-zinc-400 mb-2 block uppercase tracking-wider">Timeframe</label>
                    <select
                      value={interval}
                      onChange={(e) => setInterval(e.target.value)}
                      disabled={isRunning}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 hover:border-zinc-700 transition-all cursor-pointer"
                    >
                      {intervals.map(int => (
                        <option key={int.value} value={int.value}>
                          {int.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="col-span-12 md:col-span-4">
                    <label className="text-xs font-semibold text-zinc-400 mb-2 block uppercase tracking-wider">Start Date & Time</label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <input
                          type="date"
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          disabled={isRunning}
                          className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-3 pr-2 py-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm"
                        />
                      </div>
                      <input
                        type="time"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        disabled={isRunning}
                        className="w-24 bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm"
                      />
                    </div>
                  </div>

                  <div className="col-span-12 md:col-span-4">
                    <label className="text-xs font-semibold text-zinc-400 mb-2 block uppercase tracking-wider">End Date & Time</label>
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <input
                          type="date"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          disabled={isRunning}
                          className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-3 pr-2 py-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm"
                        />
                      </div>
                      <input
                        type="time"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        disabled={isRunning}
                        className="w-24 bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm"
                      />
                    </div>
                  </div>

                  {/* Row 3: Capital & Run */}
                  <div className="col-span-12 md:col-span-4">
                    <label className="text-xs font-semibold text-zinc-400 mb-2 block uppercase tracking-wider">Initial Capital (₹)</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500">₹</span>
                      <input
                        type="number"
                        value={initialCapital}
                        onChange={(e) => setInitialCapital(Number(e.target.value))}
                        disabled={isRunning}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-8 pr-4 py-2.5 text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono"
                      />
                    </div>
                  </div>

                  <div className="col-span-12 md:col-start-9 md:col-span-4 flex items-end">
                    <Button
                      onClick={runBacktest}
                      disabled={isRunning}
                      className="w-full bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 py-6 text-lg font-semibold rounded-xl transition-all"
                    >
                      {isRunning ? (
                        <>
                          <Loader2 className="h-5 w-5 animate-spin mr-2" />
                          Running...
                        </>
                      ) : (
                        <>
                          <Play className="h-5 w-5 mr-2" />
                          Run Backtest
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Results */}
            {result && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Total P&L */}
                  <Card className="bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 border-zinc-800/50 backdrop-blur-sm">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-zinc-400 font-medium">Total P&L</p>
                          <p className={`text-2xl font-bold mt-1 ${result.metrics.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            ₹{result.metrics.total_pnl.toLocaleString()}
                          </p>
                          <p className={`text-sm mt-1 ${result.metrics.total_pnl_percent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {result.metrics.total_pnl_percent >= 0 ? '+' : ''}{result.metrics.total_pnl_percent}%
                          </p>
                        </div>
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${result.metrics.total_pnl >= 0 ? 'bg-emerald-500/20 border border-emerald-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
                          {result.metrics.total_pnl >= 0 ? (
                            <TrendingUp className="w-6 h-6 text-emerald-400" />
                          ) : (
                            <TrendingDown className="w-6 h-6 text-red-400" />
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Win Rate */}
                  <Card className="bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 border-zinc-800/50 backdrop-blur-sm">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-zinc-400 font-medium">Win Rate</p>
                          <p className="text-2xl font-bold text-white mt-1">{result.metrics.win_rate}%</p>
                          <p className="text-sm text-zinc-400 mt-1">
                            {result.metrics.winning_trades}/{result.metrics.total_trades} trades
                          </p>
                        </div>
                        <div className="w-12 h-12 bg-blue-500/20 border border-blue-500/30 rounded-xl flex items-center justify-center">
                          <Target className="w-6 h-6 text-blue-400" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Profit Factor */}
                  <Card className="bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 border-zinc-800/50 backdrop-blur-sm">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-zinc-400 font-medium">Profit Factor</p>
                          <p className="text-2xl font-bold text-white mt-1">{result.metrics.profit_factor}</p>
                          <p className="text-sm text-zinc-400 mt-1">
                            {result.metrics.profit_factor >= 2 ? 'Excellent' : result.metrics.profit_factor >= 1.5 ? 'Good' : 'Fair'}
                          </p>
                        </div>
                        <div className="w-12 h-12 bg-purple-500/20 border border-purple-500/30 rounded-xl flex items-center justify-center">
                          <BarChart3 className="w-6 h-6 text-purple-400" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Max Drawdown */}
                  <Card className="bg-gradient-to-br from-zinc-900/90 to-zinc-950/90 border-zinc-800/50 backdrop-blur-sm">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-zinc-400 font-medium">Max Drawdown</p>
                          <p className="text-2xl font-bold text-red-400 mt-1">
                            {result.metrics.max_drawdown_percent}%
                          </p>
                          <p className="text-sm text-zinc-400 mt-1">
                            ₹{result.metrics.max_drawdown.toLocaleString()}
                          </p>
                        </div>
                        <div className="w-12 h-12 bg-red-500/20 border border-red-500/30 rounded-xl flex items-center justify-center">
                          <ArrowDownRight className="w-6 h-6 text-red-400" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Equity Curve */}
                <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm">
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Performance Metrics */}
                  <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm">
                    <CardHeader>
                      <CardTitle className="text-white">Performance Metrics</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <MetricRow label="Total Trades" value={result.metrics.total_trades.toString()} />
                        <MetricRow label="Winning Trades" value={result.metrics.winning_trades.toString()} valueColor="text-emerald-400" />
                        <MetricRow label="Losing Trades" value={result.metrics.losing_trades.toString()} valueColor="text-red-400" />
                        <MetricRow label="Average Win" value={`₹${result.metrics.avg_win.toLocaleString()}`} valueColor="text-emerald-400" />
                        <MetricRow label="Average Loss" value={`₹${result.metrics.avg_loss.toLocaleString()}`} valueColor="text-red-400" />
                        <MetricRow label="Largest Win" value={`₹${result.metrics.largest_win.toLocaleString()}`} valueColor="text-emerald-400" />
                        <MetricRow label="Largest Loss" value={`₹${result.metrics.largest_loss.toLocaleString()}`} valueColor="text-red-400" />
                        <MetricRow label="Avg Holding Period" value={result.metrics.avg_holding_period} />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Risk Metrics */}
                  <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm">
                    <CardHeader>
                      <CardTitle className="text-white">Risk Metrics</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <MetricRow label="Sharpe Ratio" value={result.metrics.sharpe_ratio.toString()} />
                        <MetricRow label="Expectancy" value={`₹${result.metrics.expectancy.toFixed(2)}`} />
                        <MetricRow label="Gross Profit" value={`₹${result.metrics.gross_profit.toLocaleString()}`} valueColor="text-emerald-400" />
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
                <Card className="bg-zinc-900/50 border-zinc-800/50 backdrop-blur-sm">
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
                                <Badge className={trade.direction === 'BUY' ? 'bg-emerald-600' : 'bg-red-600'}>
                                  {trade.direction}
                                </Badge>
                              </td>
                              <td className="py-3 px-4 text-right text-zinc-300">₹{trade.entry_price.toFixed(2)}</td>
                              <td className="py-3 px-4 text-right text-zinc-300">₹{trade.exit_price.toFixed(2)}</td>
                              <td className="py-3 px-4 text-right text-zinc-300">{trade.quantity}</td>
                              <td className={`py-3 px-4 text-right font-medium ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                ₹{trade.pnl.toFixed(2)}
                              </td>
                              <td className={`py-3 px-4 text-right ${trade.pnl_percent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
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
                <Card className={`border-2 ${result.metrics.win_rate >= 60 && result.metrics.profit_factor >= 1.5
                  ? 'bg-emerald-900/20 border-emerald-600'
                  : 'bg-yellow-900/20 border-yellow-600'
                  }`}>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      {result.metrics.win_rate >= 60 && result.metrics.profit_factor >= 1.5 ? (
                        <CheckCircle2 className="w-8 h-8 text-emerald-400 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="w-8 h-8 text-yellow-400 flex-shrink-0" />
                      )}
                      <div>
                        <h3 className="text-xl font-bold text-white mb-2">
                          {result.metrics.win_rate >= 60 && result.metrics.profit_factor >= 1.5
                            ? '✅ Strategy Recommended'
                            : '⚠️ Strategy Needs Optimization'}
                        </h3>
                        <p className="text-zinc-300 leading-relaxed">
                          {result.metrics.win_rate >= 60 && result.metrics.profit_factor >= 1.5
                            ? `This strategy shows excellent performance with a ${result.metrics.win_rate}% win rate and ${result.metrics.profit_factor} profit factor. The backtest generated ₹${result.metrics.total_pnl.toLocaleString()} profit (${result.metrics.total_pnl_percent}%) over ${result.metrics.total_trades} trades. Consider using this strategy for live trading.`
                            : `This strategy shows moderate performance. While it may be profitable, consider optimizing parameters or testing different timeframes to improve the win rate (${result.metrics.win_rate}%) and profit factor (${result.metrics.profit_factor}).`}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

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
