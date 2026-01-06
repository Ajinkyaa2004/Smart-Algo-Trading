/**
 * Historical Data Panel Component
 * Fetch and display historical OHLC data from the backend
 */

import { useState } from 'react';
import { Calendar, TrendingUp, Download } from 'lucide-react';

interface HistoricalDataPanelProps {
  onDataFetched?: (data: any[]) => void;
}

export default function HistoricalDataPanel({ onDataFetched }: HistoricalDataPanelProps) {
  const [symbol, setSymbol] = useState('RELIANCE');
  const [exchange, setExchange] = useState('NSE');
  const [interval, setInterval] = useState('5minute');
  const [duration, setDuration] = useState(4);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchHistoricalData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/market/fetchOHLC', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: symbol,
          interval: interval,
          duration: duration,
          exchange: exchange
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch historical data');
      }

      const result = await response.json();
      
      if (result.status === 'success' && result.data) {
        setData(result.data);
        onDataFetched?.(result.data);
      } else {
        setError('No data available');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const fetchNFOFutures = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/market/nfo/futures?underlying=NIFTY');
      const result = await response.json();
      console.log('NFO Futures:', result);
      alert(`Found ${result.count} NIFTY futures. Check console for details.`);
    } catch (err) {
      console.error('Failed to fetch NFO futures:', err);
    }
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-zinc-100">Historical Data</h3>
        </div>
        <button
          onClick={fetchNFOFutures}
          className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
        >
          Browse NFO Futures
        </button>
      </div>

      {/* Input Controls */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">
            Symbol
          </label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="RELIANCE"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">
            Exchange
          </label>
          <select
            value={exchange}
            onChange={(e) => setExchange(e.target.value)}
            className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
            <option value="NFO">NFO (Futures)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">
            Interval
          </label>
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="minute">1 Minute</option>
            <option value="3minute">3 Minutes</option>
            <option value="5minute">5 Minutes</option>
            <option value="15minute">15 Minutes</option>
            <option value="30minute">30 Minutes</option>
            <option value="60minute">1 Hour</option>
            <option value="day">Daily</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-300 mb-1">
            Duration (days)
          </label>
          <input
            type="number"
            value={duration}
            onChange={(e) => setDuration(parseInt(e.target.value))}
            min="1"
            max="365"
            className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Fetch Button */}
      <button
        onClick={fetchHistoricalData}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-zinc-800 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            Loading...
          </>
        ) : (
          <>
            <TrendingUp className="w-4 h-4" />
            Fetch Historical Data
          </>
        )}
      </button>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-950/30 border border-red-900/50 rounded-md text-red-400">
          {error}
        </div>
      )}

      {/* Data Summary */}
      {data.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-zinc-400">
                Fetched <span className="font-semibold text-zinc-100">{data.length}</span> candles
              </p>
              <p className="text-xs text-zinc-500">
                {symbol} • {interval} • {duration} days
              </p>
            </div>
            <button
              onClick={() => {
                const csv = convertToCSV(data);
                downloadCSV(csv, `${symbol}_${interval}_${duration}days.csv`);
              }}
              className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>

          {/* Latest Candle Info */}
          {data.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded-md">
              <div>
                <p className="text-xs text-zinc-500">Open</p>
                <p className="text-sm font-semibold text-zinc-100">{data[data.length - 1].open.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500">High</p>
                <p className="text-sm font-semibold text-green-400">{data[data.length - 1].high.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500">Low</p>
                <p className="text-sm font-semibold text-red-400">{data[data.length - 1].low.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500">Close</p>
                <p className="text-sm font-semibold text-zinc-100">{data[data.length - 1].close.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500">Volume</p>
                <p className="text-sm font-semibold text-zinc-300">{data[data.length - 1].volume.toLocaleString()}</p>
              </div>
            </div>
          )}

          {/* Data Table (last 10 candles) */}
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-zinc-800">
              <thead className="bg-zinc-900/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-zinc-400 uppercase">Date</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-zinc-400 uppercase">Open</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-zinc-400 uppercase">High</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-zinc-400 uppercase">Low</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-zinc-400 uppercase">Close</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-zinc-400 uppercase">Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {data.slice(-10).reverse().map((candle, idx) => (
                  <tr key={idx} className="hover:bg-zinc-900/30 transition-colors">
                    <td className="px-4 py-2 text-sm text-zinc-300">
                      {new Date(candle.date).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-sm text-right text-zinc-300">{candle.open.toFixed(2)}</td>
                    <td className="px-4 py-2 text-sm text-right text-green-400">{candle.high.toFixed(2)}</td>
                    <td className="px-4 py-2 text-sm text-right text-red-400">{candle.low.toFixed(2)}</td>
                    <td className="px-4 py-2 text-sm text-right font-medium text-zinc-100">{candle.close.toFixed(2)}</td>
                    <td className="px-4 py-2 text-sm text-right text-zinc-400">{candle.volume.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper function to convert data to CSV
function convertToCSV(data: any[]): string {
  const headers = ['date', 'open', 'high', 'low', 'close', 'volume'];
  const rows = data.map(d => headers.map(h => d[h]).join(','));
  return [headers.join(','), ...rows].join('\n');
}

// Helper function to download CSV
function downloadCSV(csv: string, filename: string): void {
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}
