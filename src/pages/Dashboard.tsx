import { useState, useEffect } from 'react';
import { Activity, TrendingUp, BarChart3, Zap, CheckCircle2 } from 'lucide-react';
import { IndexMarketData } from '../components/IndexMarketData';

interface ModuleStatus {
  name: string;
  status: 'active' | 'ready' | 'pending';
  description: string;
  icon: any;
}

interface BackendStatus {
  status: string;
  message: string;
  version: string;
  modules: string[];
}

interface DashboardProps {
  onNavigate: (page: string) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBackendStatus();
  }, []);

  const fetchBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/');
      const data = await response.json();
      setBackendStatus(data);
    } catch (error) {
      console.error('Failed to fetch backend status:', error);
    } finally {
      setLoading(false);
    }
  };

  const modules: ModuleStatus[] = [
    {
      name: 'Authentication',
      status: 'active',
      description: 'Kite Connect OAuth integration with token persistence',
      icon: CheckCircle2
    },
    {
      name: 'Market Data',
      status: 'active',
      description: 'Real-time quotes, historical data, and instrument search',
      icon: BarChart3
    },
    {
      name: 'Technical Indicators',
      status: 'active',
      description: '10+ indicators including RSI, MACD, Bollinger Bands',
      icon: TrendingUp
    },
    {
      name: 'Price Action',
      status: 'active',
      description: 'Support/Resistance detection and trend identification',
      icon: Activity
    },
    {
      name: 'Pattern Scanner',
      status: 'active',
      description: '10 candlestick patterns with confidence scoring',
      icon: Zap
    },
    {
      name: 'Trading Strategies',
      status: 'active',
      description: 'EMA+RSI, Breakout, and Pattern confirmation strategies',
      icon: TrendingUp
    },
    {
      name: 'Live Data (WebSocket)',
      status: 'active',
      description: 'Real-time tick streaming and live candle formation',
      icon: Activity
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'ready': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'pending': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default: return 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30';
    }
  };

  return (
    <div className="h-full w-full p-4 space-y-4">
      {/* Header */}
      <div className="bg-gradient-to-br from-zinc-900 to-zinc-950 border border-zinc-800 rounded-xl p-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-blue-500 bg-clip-text">
              Smart Algo Trade
            </h1>
            <p className="text-zinc-400 mt-2">Production-ready algorithmic trading system</p>
          </div>

          {!loading && backendStatus && (
            <div className="text-right">
              <div className="flex items-center gap-2 justify-end">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-emerald-400 font-medium">Backend Online</span>
              </div>
              <p className="text-xs text-zinc-500 mt-1">Version {backendStatus.version}</p>
            </div>
          )}
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-zinc-100">{modules.filter(m => m.status === 'active').length}</p>
              <p className="text-sm text-zinc-400">Active Modules</p>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-zinc-100">3</p>
              <p className="text-sm text-zinc-400">Trading Strategies</p>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-zinc-100">10+</p>
              <p className="text-sm text-zinc-400">Indicators</p>
            </div>
          </div>
        </div>
      </div>

      {/* Modules Grid */}
      <div>
        <h2 className="text-xl font-semibold text-zinc-100 mb-4">System Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {modules.map((module, index) => {
            const Icon = module.icon;
            return (
              <div
                key={index}
                className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 hover:border-zinc-700 transition-all duration-200"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-emerald-500/20 to-blue-500/20 rounded-lg flex items-center justify-center">
                    <Icon className="w-5 h-5 text-emerald-400" />
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(module.status)}`}>
                    {module.status}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-zinc-100 mb-2">{module.name}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{module.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-zinc-100 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigate('portfolio')}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white font-medium py-4 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-2"
          >
            <Activity className="w-5 h-5" />
            View Portfolio & Account
          </button>
          <button
            onClick={() => onNavigate('live')}
            className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white font-medium py-4 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-2"
          >
            <Activity className="w-5 h-5" />
            View Live Market Data
          </button>
          <button
            onClick={() => onNavigate('strategies')}
            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-medium py-4 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-2"
          >
            <TrendingUp className="w-5 h-5" />
            Explore Strategies
          </button>
        </div>
      </div>

      {/* API Documentation Link */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-zinc-100 mb-2">API Documentation</h3>
        <p className="text-sm text-zinc-400 mb-4">
          Explore the complete API documentation with interactive endpoints
        </p>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-medium py-2 px-4 rounded-lg transition-colors duration-200"
        >
          Open API Docs
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>

      {/* Complete Market Data Section */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <h2 className="text-xl font-semibold text-zinc-100">Complete Real-time Market Data</h2>
        </div>
        <IndexMarketData
          niftySymbols={[
            'NSE:NIFTY 50',
            'NSE:NIFTY NEXT 50',
            'NSE:NIFTY 100',
            'NSE:NIFTY 200',
            'NSE:NIFTY 500',
            'NSE:NIFTY MIDCAP 50',
            'NSE:NIFTY MIDCAP 100',
            'NSE:NIFTY MIDCAP 150',
            'NSE:NIFTY SMALLCAP 50',
            'NSE:NIFTY SMALLCAP 100',
            'NSE:NIFTY SMALLCAP 250',
            'NSE:NIFTY BANK',
            'NSE:NIFTY FIN SERVICE',
            'NSE:NIFTY PSU BANK',
            'NSE:NIFTY PRIVATE BANK',
            'NSE:NIFTY IT',
            'NSE:NIFTY AUTO',
            'NSE:NIFTY FMCG',
            'NSE:NIFTY PHARMA',
            'NSE:NIFTY METAL',
            'NSE:NIFTY REALTY',
            'NSE:NIFTY MEDIA',
            'NSE:NIFTY ENERGY',
            'NSE:NIFTY INFRASTRUCTURE',
            'NSE:NIFTY CONSUMER DURABLES',
            'NSE:NIFTY OIL & GAS',
            'NSE:NIFTY HEALTHCARE INDEX',
            'NSE:INDIA VIX',
          ]}
          bseSymbols={[
            'BSE:SENSEX',
            'BSE:SENSEX 50',
            'BSE:SENSEX NEXT 50',
            'BSE:BSE 100',
            'BSE:BSE 200',
            'BSE:BSE 500',
            'BSE:BSE MIDCAP',
            'BSE:BSE SMALLCAP',
            'BSE:BANKEX',
            'BSE:BSE IT',
            'BSE:BSE FMCG',
            'BSE:BSE AUTO',
            'BSE:BSE METAL',
            'BSE:BSE REALTY',
            'BSE:BSE POWER',
            'BSE:BSE OIL & GAS',
          ]}
        />
      </div>
    </div>
  );
}
