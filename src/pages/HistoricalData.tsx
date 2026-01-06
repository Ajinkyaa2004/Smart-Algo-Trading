/**
 * Historical Data Page
 * Complete page for browsing and analyzing historical market data
 */

import { useState } from 'react';
import HistoricalDataPanel from '../components/HistoricalDataPanel';
import { ApexCandlestickChart } from '../components/ApexCandlestickChart';
import { TrendingUp, Database, Search } from 'lucide-react';

interface CandlestickData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export default function HistoricalData() {
  const [chartData, setChartData] = useState<CandlestickData[]>([]);
  const [showChart, setShowChart] = useState(true);
  const [nfoFutures, setNfoFutures] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const handleDataFetched = (data: any[]) => {
    setChartData(data);
  };

  const fetchNFOFutures = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/market/nfo/futures?underlying=NIFTY');
      const result = await response.json();
      if (result.status === 'success') {
        setNfoFutures(result.data);
      }
    } catch (err) {
      console.error('Failed to fetch NFO futures:', err);
    }
  };

  const searchInstruments = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/market/instruments/search/${searchQuery}`);
      const result = await response.json();
      console.log('Search results:', result);
      alert(`Found ${result.count} instruments. Check console for details.`);
    } catch (err) {
      console.error('Failed to search instruments:', err);
    }
  };

  return (
    <div className="h-full w-full p-4 space-y-4">
      {/* Header */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-blue-500" />
              <div>
                <h1 className="text-2xl font-bold text-zinc-100">Historical Data</h1>
                <p className="text-sm text-zinc-400">Fetch and analyze historical OHLC data</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={fetchNFOFutures}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 flex items-center gap-2 transition-colors"
            >
              <TrendingUp className="w-4 h-4" />
              NFO Futures
            </button>
            
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchInstruments()}
                placeholder="Search instruments..."
                className="px-3 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                onClick={searchInstruments}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <Search className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div>
        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all">
            <div className="flex items-center gap-4">
              <div className="p-4 bg-blue-950/50 rounded-xl border border-blue-900/30">
                <Database className="w-7 h-7 text-blue-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-zinc-400 mb-1">Exchanges</p>
                <p className="text-2xl font-bold text-zinc-100">NSE, BSE, NFO</p>
              </div>
            </div>
          </div>

          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all">
            <div className="flex items-center gap-4">
              <div className="p-4 bg-green-950/50 rounded-xl border border-green-900/30">
                <TrendingUp className="w-7 h-7 text-green-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-zinc-400 mb-1">Intervals</p>
                <p className="text-2xl font-bold text-zinc-100">1min to Daily</p>
              </div>
            </div>
          </div>

          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all">
            <div className="flex items-center gap-4">
              <div className="p-4 bg-purple-950/50 rounded-xl border border-purple-900/30">
                <Search className="w-7 h-7 text-purple-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-zinc-400 mb-1">Instruments</p>
                <p className="text-2xl font-bold text-zinc-100">Stocks + Derivatives</p>
              </div>
            </div>
          </div>
        </div>

        {/* Historical Data Panel */}
        <div className="mb-8">
          <HistoricalDataPanel onDataFetched={handleDataFetched} />
        </div>

        {/* Chart */}
        {chartData.length > 0 && showChart && (
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-zinc-100">Price Chart</h3>
              <button
                onClick={() => setShowChart(false)}
                className="text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                Hide Chart
              </button>
            </div>
            <ApexCandlestickChart data={chartData} height={500} />
          </div>
        )}

        {!showChart && chartData.length > 0 && (
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6 text-center">
            <button
              onClick={() => setShowChart(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Show Chart
            </button>
          </div>
        )}

        {/* NFO Futures Table */}
        {nfoFutures.length > 0 && (
          <div className="mt-8 bg-zinc-950 border border-zinc-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-zinc-100 mb-4">NIFTY Futures ({nfoFutures.length})</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-zinc-800">
                <thead className="bg-zinc-900/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Symbol</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Expiry</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Lot Size</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Exchange</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-400 uppercase">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {nfoFutures.slice(0, 20).map((future, idx) => (
                    <tr key={idx} className="hover:bg-zinc-900/50 transition-colors">
                      <td className="px-4 py-3 text-sm font-medium text-zinc-100">
                        {future.tradingsymbol}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-400">
                        {new Date(future.expiry).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-400">
                        {future.lot_size}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-400">
                        {future.exchange}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => alert(`Fetch data for ${future.tradingsymbol}`)}
                          className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          Fetch Data
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Quick Guide */}
        <div className="mt-8 bg-blue-950/20 border border-blue-900/50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-400 mb-3">📚 Quick Guide</h3>
          <ul className="space-y-2 text-sm text-zinc-300">
            <li>• <strong className="text-zinc-100">Fetch Historical Data:</strong> Enter symbol, select interval and duration, click "Fetch Historical Data"</li>
            <li>• <strong className="text-zinc-100">NFO Futures:</strong> Click "NFO Futures" to browse NIFTY futures contracts</li>
            <li>• <strong className="text-zinc-100">Search:</strong> Use search bar to find any NSE/BSE instrument</li>
            <li>• <strong className="text-zinc-100">Export:</strong> After fetching data, click "Export CSV" to download</li>
            <li>• <strong className="text-zinc-100">Chart:</strong> Automatically displays candlestick chart with fetched data</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
