import React, { useState, useEffect } from 'react';
import { ShoppingCart, TrendingUp, TrendingDown, Clock, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface Order {
  order_id: string;
  tradingsymbol: string;
  exchange: string;
  transaction_type: string;
  quantity: number;
  order_type: string;
  price?: number;
  status: string;
  placed_by?: string;
  order_timestamp?: string;
}

const Orders: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'bracket' | 'market' | 'history'>('bracket');
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);

  // Bracket Order Form State
  const [bracketForm, setBracketForm] = useState({
    tradingsymbol: '',
    exchange: 'NSE',
    transaction_type: 'BUY',
    quantity: 1,
    price: '',
    squareoff: '',
    stoploss: '',
    trailing_stoploss: '',
    tag: ''
  });

  // Market Order Form State
  const [marketForm, setMarketForm] = useState({
    tradingsymbol: '',
    exchange: 'NSE',
    transaction_type: 'BUY',
    quantity: 1,
    product: 'MIS',
    tag: ''
  });

  // Fetch orders on mount
  useEffect(() => {
    if (activeTab === 'history') {
      fetchOrders();
    }
  }, [activeTab]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/orders/orders');
      const data = await response.json();
      setOrders(data.orders || []);
    } catch (error) {
      toast.error('Failed to fetch orders');
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const placeBracketOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/orders/place/bracket', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tradingsymbol: bracketForm.tradingsymbol.toUpperCase(),
          exchange: bracketForm.exchange,
          transaction_type: bracketForm.transaction_type,
          quantity: parseInt(bracketForm.quantity.toString()),
          price: parseFloat(bracketForm.price),
          squareoff: parseInt(bracketForm.squareoff),
          stoploss: parseInt(bracketForm.stoploss),
          trailing_stoploss: bracketForm.trailing_stoploss ? parseInt(bracketForm.trailing_stoploss) : undefined,
          product: 'MIS',
          tag: bracketForm.tag || undefined
        })
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(`Bracket order placed: ${data.order_id}`);
        // Reset form
        setBracketForm({
          tradingsymbol: '',
          exchange: 'NSE',
          transaction_type: 'BUY',
          quantity: 1,
          price: '',
          squareoff: '',
          stoploss: '',
          trailing_stoploss: '',
          tag: ''
        });
      } else {
        toast.error(data.detail || 'Failed to place order');
      }
    } catch (error) {
      toast.error('Failed to place bracket order');
      console.error('Error placing bracket order:', error);
    } finally {
      setLoading(false);
    }
  };

  const placeMarketOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/orders/place/market', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tradingsymbol: marketForm.tradingsymbol.toUpperCase(),
          exchange: marketForm.exchange,
          transaction_type: marketForm.transaction_type,
          quantity: parseInt(marketForm.quantity.toString()),
          product: marketForm.product,
          tag: marketForm.tag || undefined
        })
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(`Market order placed: ${data.order_id}`);
        // Reset form
        setMarketForm({
          tradingsymbol: '',
          exchange: 'NSE',
          transaction_type: 'BUY',
          quantity: 1,
          product: 'MIS',
          tag: ''
        });
      } else {
        toast.error(data.detail || 'Failed to place order');
      }
    } catch (error) {
      toast.error('Failed to place market order');
      console.error('Error placing market order:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case 'COMPLETE':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'REJECTED':
      case 'CANCELLED':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'OPEN':
      case 'TRIGGER PENDING':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-zinc-400" />;
    }
  };

  return (
    <div className="h-full w-full p-4 space-y-4">
      {/* Header */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
              <ShoppingCart className="w-7 h-7 text-blue-400" />
              Order Management
            </h1>
            <p className="text-sm text-zinc-400 mt-1">Place and manage your orders</p>
          </div>
        </div>
      </div>

      <div>
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('bracket')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'bracket'
                ? 'bg-blue-500 text-white'
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-800'
            }`}
          >
            Bracket Order
          </button>
          <button
            onClick={() => setActiveTab('market')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'market'
                ? 'bg-blue-500 text-white'
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-800'
            }`}
          >
            Market Order
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'history'
                ? 'bg-blue-500 text-white'
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-800'
            }`}
          >
            Order History
          </button>
        </div>

        {/* Bracket Order Form */}
        {activeTab === 'bracket' && (
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-zinc-100 mb-4">Place Bracket Order</h2>
            <p className="text-sm text-zinc-400 mb-6">
              Bracket orders include automatic stop-loss and target orders
            </p>

            <form onSubmit={placeBracketOrder} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {/* Symbol */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Trading Symbol
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., RELIANCE, INFY"
                    value={bracketForm.tradingsymbol}
                    onChange={(e) => setBracketForm({ ...bracketForm, tradingsymbol: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Exchange */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Exchange
                  </label>
                  <select
                    value={bracketForm.exchange}
                    onChange={(e) => setBracketForm({ ...bracketForm, exchange: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="NSE">NSE</option>
                    <option value="BSE">BSE</option>
                    <option value="NFO">NFO</option>
                  </select>
                </div>

                {/* Transaction Type */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Transaction Type
                  </label>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setBracketForm({ ...bracketForm, transaction_type: 'BUY' })}
                      className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
                        bracketForm.transaction_type === 'BUY'
                          ? 'bg-green-500 text-white'
                          : 'bg-zinc-900 text-zinc-400 border border-zinc-800 hover:bg-zinc-800'
                      }`}
                    >
                      <TrendingUp className="w-4 h-4 inline mr-2" />
                      BUY
                    </button>
                    <button
                      type="button"
                      onClick={() => setBracketForm({ ...bracketForm, transaction_type: 'SELL' })}
                      className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
                        bracketForm.transaction_type === 'SELL'
                          ? 'bg-red-500 text-white'
                          : 'bg-zinc-900 text-zinc-400 border border-zinc-800 hover:bg-zinc-800'
                      }`}
                    >
                      <TrendingDown className="w-4 h-4 inline mr-2" />
                      SELL
                    </button>
                  </div>
                </div>

                {/* Quantity */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Quantity
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={bracketForm.quantity}
                    onChange={(e) => setBracketForm({ ...bracketForm, quantity: parseInt(e.target.value) || 1 })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Entry Price */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Entry Price (Limit)
                  </label>
                  <input
                    type="number"
                    required
                    step="0.05"
                    placeholder="e.g., 2550.00"
                    value={bracketForm.price}
                    onChange={(e) => setBracketForm({ ...bracketForm, price: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Target (Squareoff) */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Target (Points)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    placeholder="e.g., 10"
                    value={bracketForm.squareoff}
                    onChange={(e) => setBracketForm({ ...bracketForm, squareoff: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Absolute points for profit booking</p>
                </div>

                {/* Stop Loss */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Stop Loss (Points)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    placeholder="e.g., 5"
                    value={bracketForm.stoploss}
                    onChange={(e) => setBracketForm({ ...bracketForm, stoploss: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Absolute points for risk management</p>
                </div>

                {/* Trailing Stop Loss */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Trailing SL (Ticks) - Optional
                  </label>
                  <input
                    type="number"
                    min="1"
                    placeholder="e.g., 2"
                    value={bracketForm.trailing_stoploss}
                    onChange={(e) => setBracketForm({ ...bracketForm, trailing_stoploss: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-zinc-500 mt-1">SL trails as price moves favorably</p>
                </div>

                {/* Tag */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Tag (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., strategy_name"
                    value={bracketForm.tag}
                    onChange={(e) => setBracketForm({ ...bracketForm, tag: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Summary */}
              {bracketForm.price && bracketForm.squareoff && bracketForm.stoploss && (
                <div className="bg-blue-950/20 border border-blue-900/50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-blue-300 mb-2">Order Summary</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 text-sm">
                    <div>
                      <p className="text-zinc-400">Entry</p>
                      <p className="text-zinc-100 font-medium">₹{bracketForm.price}</p>
                    </div>
                    <div>
                      <p className="text-zinc-400">Target</p>
                      <p className="text-green-400 font-medium">
                        ₹{(parseFloat(bracketForm.price) + (bracketForm.transaction_type === 'BUY' ? 1 : -1) * parseFloat(bracketForm.squareoff)).toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-zinc-400">Stop Loss</p>
                      <p className="text-red-400 font-medium">
                        ₹{(parseFloat(bracketForm.price) - (bracketForm.transaction_type === 'BUY' ? 1 : -1) * parseFloat(bracketForm.stoploss)).toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-zinc-400">Risk:Reward</p>
                      <p className="text-zinc-100 font-medium">
                        1:{(parseFloat(bracketForm.squareoff) / parseFloat(bracketForm.stoploss)).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-zinc-800 text-white font-medium rounded-lg transition-colors"
              >
                {loading ? 'Placing Order...' : 'Place Bracket Order'}
              </button>
            </form>
          </div>
        )}

        {/* Market Order Form */}
        {activeTab === 'market' && (
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6">
            <h2 className="text-xl font-bold text-zinc-100 mb-4">Place Market Order</h2>
            <p className="text-sm text-zinc-400 mb-6">
              Execute orders immediately at current market price
            </p>

            <form onSubmit={placeMarketOrder} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {/* Symbol */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Trading Symbol
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., RELIANCE, INFY"
                    value={marketForm.tradingsymbol}
                    onChange={(e) => setMarketForm({ ...marketForm, tradingsymbol: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Exchange */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Exchange
                  </label>
                  <select
                    value={marketForm.exchange}
                    onChange={(e) => setMarketForm({ ...marketForm, exchange: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="NSE">NSE</option>
                    <option value="BSE">BSE</option>
                    <option value="NFO">NFO</option>
                  </select>
                </div>

                {/* Transaction Type */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Transaction Type
                  </label>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setMarketForm({ ...marketForm, transaction_type: 'BUY' })}
                      className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
                        marketForm.transaction_type === 'BUY'
                          ? 'bg-green-500 text-white'
                          : 'bg-zinc-900 text-zinc-400 border border-zinc-800 hover:bg-zinc-800'
                      }`}
                    >
                      <TrendingUp className="w-4 h-4 inline mr-2" />
                      BUY
                    </button>
                    <button
                      type="button"
                      onClick={() => setMarketForm({ ...marketForm, transaction_type: 'SELL' })}
                      className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
                        marketForm.transaction_type === 'SELL'
                          ? 'bg-red-500 text-white'
                          : 'bg-zinc-900 text-zinc-400 border border-zinc-800 hover:bg-zinc-800'
                      }`}
                    >
                      <TrendingDown className="w-4 h-4 inline mr-2" />
                      SELL
                    </button>
                  </div>
                </div>

                {/* Quantity */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Quantity
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={marketForm.quantity}
                    onChange={(e) => setMarketForm({ ...marketForm, quantity: parseInt(e.target.value) || 1 })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Product Type */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Product Type
                  </label>
                  <select
                    value={marketForm.product}
                    onChange={(e) => setMarketForm({ ...marketForm, product: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="MIS">MIS (Intraday)</option>
                    <option value="CNC">CNC (Delivery)</option>
                    <option value="NRML">NRML (Normal)</option>
                  </select>
                </div>

                {/* Tag */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Tag (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., strategy_name"
                    value={marketForm.tag}
                    onChange={(e) => setMarketForm({ ...marketForm, tag: e.target.value })}
                    className="w-full px-4 py-2 bg-zinc-900 border border-zinc-800 text-zinc-100 placeholder-zinc-500 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-zinc-800 text-white font-medium rounded-lg transition-colors"
              >
                {loading ? 'Placing Order...' : 'Place Market Order'}
              </button>
            </form>
          </div>
        )}

        {/* Order History */}
        {activeTab === 'history' && (
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-zinc-100">Order History</h2>
              <button
                onClick={fetchOrders}
                disabled={loading}
                className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 rounded-lg transition-colors flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>

            {loading ? (
              <div className="text-center py-12 text-zinc-400">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
                Loading orders...
              </div>
            ) : orders.length === 0 ? (
              <div className="text-center py-12 text-zinc-400">
                <ShoppingCart className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No orders found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-zinc-800">
                      <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Symbol</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Type</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Qty</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Price</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Order Type</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Status</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Order ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order, index) => (
                      <tr key={order.order_id || index} className="border-b border-zinc-800/50 hover:bg-zinc-900/50">
                        <td className="py-3 px-4">
                          <div>
                            <p className="text-zinc-100 font-medium">{order.tradingsymbol}</p>
                            <p className="text-xs text-zinc-500">{order.exchange}</p>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                            order.transaction_type === 'BUY'
                              ? 'bg-green-500/10 text-green-400'
                              : 'bg-red-500/10 text-red-400'
                          }`}>
                            {order.transaction_type === 'BUY' ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {order.transaction_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-zinc-100">{order.quantity}</td>
                        <td className="py-3 px-4 text-zinc-100">{order.price ? `₹${order.price}` : '-'}</td>
                        <td className="py-3 px-4 text-zinc-400 text-sm">{order.order_type}</td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center gap-1">
                            {getStatusIcon(order.status)}
                            <span className="text-sm text-zinc-300">{order.status}</span>
                          </span>
                        </td>
                        <td className="py-3 px-4 text-zinc-400 text-xs font-mono">{order.order_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Orders;
