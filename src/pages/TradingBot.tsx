import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Play, Square, Pause, PlayCircle, TrendingUp, Activity, AlertCircle, CheckCircle, XCircle, Terminal, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import PaperTradingPanelEnhanced from '../components/PaperTradingPanelEnhanced';
import MarketConditionsCard from '../components/MarketConditionsCard';
import PerformanceMetricsCard from '../components/PerformanceMetricsCard';
import StrategyParametersCard from '../components/StrategyParametersCard';

interface BotStatus {
  status: string;
  active_strategies: number;
  active_positions: number;
  signals_generated: number;
  orders_placed: number;
  trades_today: number;
  pnl_today: number;
  strategies: any;
}

interface Strategy {
  type: string;
  name: string;
  description: string;
  parameters: any;
}

interface ActivityLog {
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'trade';
  message: string;
  details?: any;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const TradingBot: React.FC = () => {
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['RELIANCE', 'TCS', 'INFY']);
  const [selectedStrategy, setSelectedStrategy] = useState('supertrend');
  const [capitalPerSymbol, setCapitalPerSymbol] = useState(3000);
  const [enableStorage, setEnableStorage] = useState(false);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [strategyParams, setStrategyParams] = useState<Record<string, any>>({});
  const activityEndRef = useRef<HTMLDivElement>(null);

  const symbols = [
    'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK',
    'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'HINDUNILVR', 'ITC',
    'LT', 'AXISBANK', 'MARUTI', 'BAJFINANCE', 'ASIANPAINT',
    'WIPRO', 'TITAN', 'TECHM', 'ULTRACEMCO', 'SUNPHARMA'
  ];

  // Fetch available strategies on mount
  useEffect(() => {
    fetchStrategies();
  }, []);

  useEffect(() => {
    fetchBotStatus();
    const interval = setInterval(fetchBotStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (autoScroll && activityEndRef.current) {
      activityEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activityLogs, autoScroll]);

  const fetchStrategies = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bot/strategies`);
      const data = await response.json();
      if (data.status === 'success') {
        setStrategies(data.strategies);
      }
    } catch (error) {
      console.error('Error fetching strategies:', error);
      // Fallback to default strategies if API fails
      setStrategies([
        { type: 'supertrend', name: 'Supertrend Strategy', description: 'Multi-timeframe supertrend with trailing SL', parameters: {} },
        { type: 'ema_rsi', name: 'EMA + RSI Strategy', description: 'EMA crossover with RSI confirmation', parameters: {} },
        { type: 'renko_macd', name: 'Renko + MACD Strategy', description: 'Renko bricks with MACD signals', parameters: {} }
      ]);
    }
  };

  const fetchBotStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bot/status`);
      const data = await response.json();
      if (data.status === 'success') {
        setBotStatus(data.bot);
      }
    } catch (error) {
      console.error('Error fetching bot status:', error);
    }
  };

  const addLog = (type: ActivityLog['type'], message: string, details?: any) => {
    const newLog: ActivityLog = {
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      type,
      message,
      details
    };
    setActivityLogs(prev => [...prev, newLog]);
  };

  const clearLogs = () => {
    setActivityLogs([]);
  };

  const startBot = async () => {
    setIsLoading(true);
    clearLogs();
    addLog('info', '🚀 Initializing trading bot...');
    addLog('info', `📊 Strategy: ${selectedStrategy.toUpperCase()}`);
    addLog('info', `💰 Capital per symbol: ₹${capitalPerSymbol}`);
    addLog('info', `📈 Symbols: ${selectedSymbols.join(', ')}`);
    addLog('warning', '🛡️ PAPER TRADING MODE - No real orders');

    try {
      const response = await fetch(`${API_URL}/api/bot/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbols: selectedSymbols,
          strategy_type: selectedStrategy,
          capital_per_symbol: capitalPerSymbol,
          enable_tick_storage: enableStorage,
          strategy_params: strategyParams
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        addLog('success', '✅ Trading bot started successfully');
        addLog('success', `✓ ${selectedSymbols.length} strategies initialized`);
        addLog('info', '⏰ Checking for signals every 60 seconds');
        addLog('info', '🔔 Will auto square-off at 3:15 PM');

        toast.success('Trading Bot Started', {
          description: `Bot is now running with ${selectedSymbols.length} symbols`
        });
        fetchBotStatus();
        startActivityPolling();
      } else {
        addLog('error', `❌ Failed to start: ${data.message || 'Unknown error'}`);
        toast.error('Failed to Start Bot', {
          description: data.message || 'Unknown error'
        });
      }
    } catch (error) {
      addLog('error', `❌ Connection error: ${error}`);
      toast.error('Connection Error', {
        description: 'Unable to connect to backend'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const startActivityPolling = () => {
    // Poll for activity updates every 2 seconds when bot is running
    const interval = setInterval(async () => {
      if (botStatus?.status !== 'running') {
        clearInterval(interval);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/bot/activity`);
        const data = await response.json();

        if (data.status === 'success' && data.activities) {
          data.activities.forEach((activity: any) => {
            addLog(
              activity.type || 'info',
              activity.message,
              activity.details
            );
          });
        }
      } catch (error) {
        // Silently fail - don't spam errors
      }
    }, 2000);
  };

  const stopBot = async () => {
    setIsLoading(true);
    addLog('warning', '⏸️ Stopping trading bot...');

    try {
      const response = await fetch(`${API_URL}/api/bot/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ square_off_positions: true })
      });

      const data = await response.json();
      if (data.status === 'success') {
        addLog('success', '✅ Bot stopped successfully');
        addLog('info', '📊 Squaring off all positions...');
        addLog('success', '✓ All positions closed');

        toast.success('Trading Bot Stopped', {
          description: 'All positions have been squared off'
        });
        fetchBotStatus();
      }
    } catch (error) {
      addLog('error', '❌ Error stopping bot');
      toast.error('Error', { description: 'Failed to stop bot' });
    } finally {
      setIsLoading(false);
    }
  };

  const pauseBot = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bot/pause`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'success') {
        toast.info('Bot Paused', { description: 'No new signals will be generated' });
        fetchBotStatus();
      }
    } catch (error) {
      toast.error('Error', { description: 'Failed to pause bot' });
    }
  };

  const resumeBot = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bot/resume`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'success') {
        toast.success('Bot Resumed', { description: 'Signal generation resumed' });
        fetchBotStatus();
      }
    } catch (error) {
      toast.error('Error', { description: 'Failed to resume bot' });
    }
  };

  const toggleSymbol = (symbol: string) => {
    setSelectedSymbols(prev =>
      prev.includes(symbol)
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'paused': return 'bg-yellow-500';
      case 'stopped': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <CheckCircle className="h-5 w-5" />;
      case 'paused': return <Pause className="h-5 w-5" />;
      case 'stopped': return <Square className="h-5 w-5" />;
      case 'error': return <XCircle className="h-5 w-5" />;
      default: return <AlertCircle className="h-5 w-5" />;
    }
  };

  const isRunning = botStatus?.status === 'running';
  const isPaused = botStatus?.status === 'paused';
  const isStopped = !botStatus || botStatus?.status === 'stopped' || botStatus?.status === 'error';

  return (
    <div className="h-full w-full p-4 space-y-4">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">Trading Bot</h2>
        <p className="text-zinc-400 mt-2">Automated trading with real-time signal generation</p>
      </div>

      {/* Bot Status Card */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white">Bot Status</CardTitle>
            {botStatus ? (
              <Badge className={`${getStatusColor(botStatus.status)} text-white flex items-center gap-2`}>
                {getStatusIcon(botStatus.status)}
                {botStatus.status.toUpperCase()}
              </Badge>
            ) : (
              <Badge className="bg-gray-500 text-white flex items-center gap-2">
                <Square className="h-5 w-5" />
                STOPPED
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {botStatus ? (
            <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-4">
              <div className="bg-zinc-800 rounded-lg p-4">
                <p className="text-zinc-400 text-sm">Active Strategies</p>
                <p className="text-2xl font-bold text-white mt-1">{botStatus.active_strategies}</p>
              </div>
              <div className="bg-zinc-800 rounded-lg p-4">
                <p className="text-zinc-400 text-sm">Positions</p>
                <p className="text-2xl font-bold text-white mt-1">{botStatus.active_positions}</p>
              </div>
              <div className="bg-zinc-800 rounded-lg p-4">
                <p className="text-zinc-400 text-sm">Signals Today</p>
                <p className="text-2xl font-bold text-white mt-1">{botStatus.signals_generated}</p>
              </div>
              <div className="bg-zinc-800 rounded-lg p-4">
                <p className="text-zinc-400 text-sm">P&L Today</p>
                <p className={`text-2xl font-bold mt-1 ${botStatus.pnl_today >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  ₹{botStatus.pnl_today.toFixed(2)}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              <Square className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>Bot is stopped. Configure settings and click Start Bot.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Control Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Configuration */}
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white">Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Strategy Selection */}
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">Trading Strategy</label>
              <div className="space-y-2">
                {strategies.map(strategy => (
                  <div
                    key={strategy.type}
                    onClick={() => !isRunning && setSelectedStrategy(strategy.type)}
                    className={`cursor-pointer p-3 rounded-lg border transition-all ${selectedStrategy === strategy.type
                      ? 'bg-blue-600/20 border-blue-600'
                      : 'bg-zinc-800 border-zinc-700 hover:bg-zinc-750'
                      } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <TrendingUp className="h-5 w-5 text-blue-500" />
                      <div className="flex-1">
                        <p className="text-white font-medium">{strategy.name}</p>
                        <p className="text-zinc-400 text-xs">{strategy.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Capital */}
            <div>
              <label className="text-sm text-zinc-400 mb-2 block">Capital per Symbol</label>
              <input
                type="number"
                value={capitalPerSymbol}
                onChange={(e) => setCapitalPerSymbol(Number(e.target.value))}
                disabled={isRunning}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-600"
                placeholder="3000"
              />
            </div>

            {/* Enable Storage */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="enableStorage"
                checked={enableStorage}
                onChange={(e) => setEnableStorage(e.target.checked)}
                disabled={isRunning}
                className="rounded"
              />
              <label htmlFor="enableStorage" className="text-sm text-zinc-400">
                Enable tick data storage (SQLite)
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Symbol Selection - Takes full width */}
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white">
              Symbols ({selectedSymbols.length} selected)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3 max-h-96 overflow-y-auto pr-2">
              {symbols.map(symbol => (
                <button
                  key={symbol}
                  onClick={() => !isRunning && toggleSymbol(symbol)}
                  disabled={isRunning}
                  className={`px-6 py-4 rounded-lg text-base font-semibold transition-all ${selectedSymbols.includes(symbol)
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30 border border-blue-400'
                    : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white border border-zinc-700 hover:border-zinc-600'
                    } ${isRunning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:scale-105'}`}
                  title={symbol}
                >
                  {symbol}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* New Features Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Market Conditions */}
        <MarketConditionsCard />

        {/* Performance Metrics */}
        <PerformanceMetricsCard />

        {/* Strategy Parameters */}
        <StrategyParametersCard
          selectedStrategy={selectedStrategy}
          onParametersChange={setStrategyParams}
          disabled={isRunning}
        />
      </div>

      {/* Control Buttons */}
      <div className="flex gap-4">
        {isStopped && (
          <Button
            onClick={startBot}
            disabled={isLoading || selectedSymbols.length === 0}
            className="bg-green-600 hover:bg-green-700 text-white flex items-center gap-2"
          >
            <Play className="h-4 w-4" />
            Start Bot
          </Button>
        )}

        {isRunning && (
          <>
            <Button
              onClick={pauseBot}
              className="bg-yellow-600 hover:bg-yellow-700 text-white flex items-center gap-2"
            >
              <Pause className="h-4 w-4" />
              Pause
            </Button>
            <Button
              onClick={stopBot}
              disabled={isLoading}
              className="bg-red-600 hover:bg-red-700 text-white flex items-center gap-2"
            >
              <Square className="h-4 w-4" />
              Stop & Square Off
            </Button>
          </>
        )}

        {isPaused && (
          <>
            <Button
              onClick={resumeBot}
              className="bg-green-600 hover:bg-green-700 text-white flex items-center gap-2"
            >
              <PlayCircle className="h-4 w-4" />
              Resume
            </Button>
            <Button
              onClick={stopBot}
              disabled={isLoading}
              className="bg-red-600 hover:bg-red-700 text-white flex items-center gap-2"
            >
              <Square className="h-4 w-4" />
              Stop & Square Off
            </Button>
          </>
        )}
      </div>

      {/* Activity Log */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="h-5 w-5 text-blue-500" />
              <CardTitle className="text-white">Bot Activity Log</CardTitle>
              <Badge variant="outline" className="text-zinc-400">
                {activityLogs.length} events
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 text-sm text-zinc-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="rounded"
                />
                Auto-scroll
              </label>
              <Button
                onClick={clearLogs}
                variant="outline"
                size="sm"
                className="text-zinc-400 hover:text-white"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-black rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
            {activityLogs.length === 0 ? (
              <div className="text-zinc-500 text-center py-8">
                <Terminal className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No activity yet. Start the bot to see live updates.</p>
              </div>
            ) : (
              <div className="space-y-1">
                {activityLogs.map((log, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 py-1 ${log.type === 'error' ? 'text-red-400' :
                      log.type === 'success' ? 'text-green-400' :
                        log.type === 'warning' ? 'text-yellow-400' :
                          log.type === 'trade' ? 'text-blue-400' :
                            'text-zinc-300'
                      }`}
                  >
                    <span className="text-zinc-500 min-w-[80px]">{log.timestamp}</span>
                    <span className="flex-1">{log.message}</span>
                  </div>
                ))}
                <div ref={activityEndRef} />
              </div>
            )}
          </div>

          {/* Real-time indicators */}
          {isRunning && (
            <div className="mt-4 flex items-center gap-4 text-xs text-zinc-500">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live monitoring active</span>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="h-3 w-3" />
                <span>Checking signals every 60s</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Strategy Details (when running) */}
      {isRunning && botStatus?.strategies && (
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white">Active Strategies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(botStatus.strategies).map(([symbol, strategy]: [string, any]) => (
                <div key={symbol} className="bg-zinc-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-white text-lg">{symbol}</h3>
                    <Badge className={strategy.has_position ? 'bg-green-600' : 'bg-zinc-700'}>
                      {strategy.has_position ? 'IN POSITION' : 'MONITORING'}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 text-sm">
                    <div>
                      <p className="text-zinc-500">Strategy</p>
                      <p className="text-white font-medium">{strategy.strategy}</p>
                    </div>
                    <div>
                      <p className="text-zinc-500">Status</p>
                      <p className="text-white">{strategy.active ? 'Active' : 'Inactive'}</p>
                    </div>
                    <div>
                      <p className="text-zinc-500">Trades Today</p>
                      <p className="text-white">{strategy.trades_today}</p>
                    </div>
                    <div>
                      <p className="text-zinc-500">P&L Today</p>
                      <p className={strategy.pnl_today >= 0 ? 'text-green-500' : 'text-red-500'}>
                        ₹{strategy.pnl_today.toFixed(2)}
                      </p>
                    </div>
                  </div>

                  {strategy.position && (
                    <div className="mt-3 pt-3 border-t border-zinc-700">
                      <p className="text-zinc-400 text-xs mb-2">CURRENT POSITION</p>
                      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 text-sm">
                        <div>
                          <p className="text-zinc-500">Type</p>
                          <p className="text-white font-medium">{strategy.position.type}</p>
                        </div>
                        <div>
                          <p className="text-zinc-500">Quantity</p>
                          <p className="text-white">{strategy.position.quantity}</p>
                        </div>
                        <div>
                          <p className="text-zinc-500">Entry Price</p>
                          <p className="text-white">₹{strategy.position.entry_price.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-zinc-500">Unrealized P&L</p>
                          <p className={strategy.position.pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                            ₹{strategy.position.pnl.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Paper Trading Panel */}
      <div className="mt-8">
        <PaperTradingPanelEnhanced />
      </div>
    </div>
  );
};

export default TradingBot;
