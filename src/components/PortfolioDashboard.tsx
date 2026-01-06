import React, { useState, useEffect } from 'react';
import { 
    User, Wallet, FileText, DollarSign, Activity, RefreshCw, Package, Target
} from 'lucide-react';

// Helper component for data rows
const DataRow: React.FC<{ label: string; value: string | number; valueColor?: string }> = ({ 
    label, 
    value, 
    valueColor = 'text-zinc-100' 
}) => (
    <div className="flex items-center justify-between text-sm">
        <span className="text-zinc-500">{label}</span>
        <span className={`font-semibold ${valueColor}`}>{value}</span>
    </div>
);

interface UserProfile {
    user_name: string;
    email: string;
    user_type: string;
    broker: string;
    exchanges: string[];
    products: string[];
    order_types: string[];
}

interface Holding {
    tradingsymbol: string;
    exchange: string;
    quantity: number;
    average_price: number;
    last_price: number;
    pnl: number;
    day_change: number;
    day_change_percentage: number;
}

interface Position {
    tradingsymbol: string;
    exchange: string;
    product: string;
    quantity: number;
    average_price: number;
    last_price: number;
    pnl: number;
    buy_quantity: number;
    sell_quantity: number;
}

interface Order {
    order_id: string;
    tradingsymbol: string;
    exchange: string;
    transaction_type: string;
    order_type: string;
    quantity: number;
    filled_quantity: number;
    price: number;
    status: string;
    order_timestamp: string;
}

interface Margins {
    equity: {
        enabled: boolean;
        net: number;
        available: {
            live_balance: number;
            cash: number;
            opening_balance: number;
            adhoc_margin: number;
            collateral: number;
            intraday_payin: number;
        };
        utilised: {
            debits: number;
            exposure: number;
            m2m_realised: number;
            m2m_unrealised: number;
            option_premium: number;
            payout: number;
            span: number;
            holding_sales: number;
            turnover: number;
            liquid_collateral: number;
            stock_collateral: number;
            delivery: number;
        };
    };
    commodity: {
        enabled: boolean;
        net: number;
        available: { live_balance: number; };
        utilised: { debits: number; };
    };
}

interface GTTOrder {
    id: number;
    trigger_type: string;
    tradingsymbol: string;
    exchange: string;
    condition: any;
    orders: any[];
    status: string;
    created_at: string;
}

export const PortfolioDashboard: React.FC = () => {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [holdings, setHoldings] = useState<Holding[]>([]);
    const [positions, setPositions] = useState<{ net: Position[]; day: Position[] }>({ net: [], day: [] });
    const [orders, setOrders] = useState<Order[]>([]);
    const [margins, setMargins] = useState<Margins | null>(null);
    const [gttOrders, setGttOrders] = useState<GTTOrder[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(new Date());

    const fetchAllData = async () => {
        try {
            const [profileRes, holdingsRes, positionsRes, ordersRes, marginsRes, gttRes] = await Promise.all([
                fetch('http://localhost:8000/api/portfolio/profile'),
                fetch('http://localhost:8000/api/portfolio/holdings'),
                fetch('http://localhost:8000/api/portfolio/positions'),
                fetch('http://localhost:8000/api/portfolio/orders'),
                fetch('http://localhost:8000/api/portfolio/margins'),
                fetch('http://localhost:8000/api/portfolio/gtt')
            ]);

            const [profileData, holdingsData, positionsData, ordersData, marginsData, gttData] = await Promise.all([
                profileRes.json(),
                holdingsRes.json(),
                positionsRes.json(),
                ordersRes.json(),
                marginsRes.json(),
                gttRes.json()
            ]);

            if (profileData.status === 'success') setProfile(profileData.data);
            if (holdingsData.status === 'success') setHoldings(holdingsData.data);
            if (positionsData.status === 'success') setPositions(positionsData.data);
            if (ordersData.status === 'success') setOrders(ordersData.data);
            if (marginsData.status === 'success') setMargins(marginsData.data);
            if (gttData.status === 'success') setGttOrders(gttData.data);

            setLastUpdate(new Date());
        } catch (error) {
            console.error('Failed to fetch portfolio data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAllData();
        const interval = setInterval(fetchAllData, 30000); // Refresh every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(amount);
    };

    const totalHoldingsValue = holdings.reduce((sum, h) => sum + (h.last_price * h.quantity), 0);
    const totalHoldingsPnL = holdings.reduce((sum, h) => sum + h.pnl, 0);
    const totalPositionsPnL = [...positions.net, ...positions.day].reduce((sum, p) => sum + p.pnl, 0);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    return (
        <div className="h-full w-full p-4 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-zinc-100">Portfolio & Account</h1>
                    <p className="text-sm text-zinc-500 mt-1">Complete overview of your trading account</p>
                </div>
                <button
                    onClick={fetchAllData}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh All
                </button>
            </div>

            {/* User Profile Card */}
            {profile && (
                <div className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-zinc-800 rounded-xl p-4">
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
                            <User className="w-8 h-8 text-white" />
                        </div>
                        <div className="flex-1">
                            <h2 className="text-2xl font-bold text-zinc-100">{profile.user_name}</h2>
                            <p className="text-sm text-zinc-400">{profile.email}</p>
                            <div className="flex items-center gap-4 mt-2">
                                <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded">
                                    {profile.broker}
                                </span>
                                <span className="text-xs text-zinc-500">
                                    Exchanges: {profile.exchanges.join(', ')}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Margins Overview */}
            {margins && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-semibold text-zinc-400 uppercase">Available Cash</h3>
                                <Wallet className="w-5 h-5 text-emerald-500" />
                            </div>
                            <div className="text-3xl font-bold text-zinc-100">
                                {formatCurrency(margins.equity?.available?.cash || 0)}
                            </div>
                            <p className="text-sm text-zinc-500 mt-2">
                                Opening: {formatCurrency(margins.equity?.available?.opening_balance || 0)}
                            </p>
                        </div>

                        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-semibold text-zinc-400 uppercase">Live Balance</h3>
                                <DollarSign className="w-5 h-5 text-blue-500" />
                            </div>
                            <div className="text-3xl font-bold text-zinc-100">
                                {formatCurrency(margins.equity?.available?.live_balance || 0)}
                            </div>
                            <p className="text-sm text-zinc-500 mt-2">
                                Collateral: {formatCurrency(margins.equity?.available?.collateral || 0)}
                            </p>
                        </div>

                        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-semibold text-zinc-400 uppercase">Holdings Value</h3>
                                <Package className="w-5 h-5 text-purple-500" />
                            </div>
                            <div className="text-3xl font-bold text-zinc-100">
                                {formatCurrency(totalHoldingsValue)}
                            </div>
                            <p className={`text-sm mt-2 ${totalHoldingsPnL >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                P&L: {formatCurrency(totalHoldingsPnL)} ({((totalHoldingsPnL / (totalHoldingsValue - totalHoldingsPnL || 1)) * 100).toFixed(2)}%)
                            </p>
                        </div>

                        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-semibold text-zinc-400 uppercase">Positions P&L</h3>
                                <Activity className="w-5 h-5 text-amber-500" />
                            </div>
                            <div className={`text-3xl font-bold ${totalPositionsPnL >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                {formatCurrency(totalPositionsPnL)}
                            </div>
                            <p className="text-sm text-zinc-500 mt-2">
                                Open: {positions.net.length + positions.day.length}
                            </p>
                        </div>
                    </div>

                    {/* Detailed Margin Breakdown */}
                    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                        <h3 className="text-lg font-semibold text-zinc-100 mb-4">Detailed Margin Breakdown</h3>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Available */}
                            <div>
                                <h4 className="text-sm font-semibold text-emerald-400 mb-3 uppercase">Available Margins</h4>
                                <div className="space-y-2 text-sm">
                                    <DataRow label="Cash" value={formatCurrency(margins.equity?.available?.cash || 0)} />
                                    <DataRow label="Live Balance" value={formatCurrency(margins.equity?.available?.live_balance || 0)} />
                                    <DataRow label="Opening Balance" value={formatCurrency(margins.equity?.available?.opening_balance || 0)} />
                                    <DataRow label="Collateral" value={formatCurrency(margins.equity?.available?.collateral || 0)} />
                                    <DataRow label="Adhoc Margin" value={formatCurrency(margins.equity?.available?.adhoc_margin || 0)} />
                                    <DataRow label="Intraday Payin" value={formatCurrency(margins.equity?.available?.intraday_payin || 0)} />
                                </div>
                            </div>

                            {/* Utilised */}
                            <div>
                                <h4 className="text-sm font-semibold text-red-400 mb-3 uppercase">Utilised Margins</h4>
                                <div className="space-y-2 text-sm">
                                    <DataRow label="Total Debits" value={formatCurrency(margins.equity?.utilised?.debits || 0)} valueColor="text-red-400" />
                                    <DataRow label="Exposure" value={formatCurrency(margins.equity?.utilised?.exposure || 0)} />
                                    <DataRow label="M2M Realised" value={formatCurrency(margins.equity?.utilised?.m2m_realised || 0)} />
                                    <DataRow label="M2M Unrealised" value={formatCurrency(margins.equity?.utilised?.m2m_unrealised || 0)} />
                                    <DataRow label="Option Premium" value={formatCurrency(margins.equity?.utilised?.option_premium || 0)} />
                                    <DataRow label="SPAN" value={formatCurrency(margins.equity?.utilised?.span || 0)} />
                                    <DataRow label="Delivery" value={formatCurrency(margins.equity?.utilised?.delivery || 0)} />
                                    <DataRow label="Turnover" value={formatCurrency(margins.equity?.utilised?.turnover || 0)} />
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {/* Holdings */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                <div className="p-6 border-b border-zinc-800">
                    <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                        <Package className="w-5 h-5" />
                        Holdings ({holdings.length})
                    </h3>
                </div>
                {holdings.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-zinc-950">
                                <tr>
                                    <th className="text-left px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Symbol</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Qty</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Avg Price</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">LTP</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Close Price</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Current Value</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">P&L</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Day Change</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-800">
                                {holdings.map((holding, idx) => (
                                    <tr key={idx} className="hover:bg-zinc-800/50">
                                        <td className="px-6 py-4">
                                            <div>
                                                <div className="font-semibold text-zinc-100">{holding.tradingsymbol}</div>
                                                <div className="text-xs text-zinc-500">{holding.exchange}</div>
                                                {(holding as any).collateral_type && (
                                                    <div className="text-xs text-amber-500 mt-1">
                                                        Collateral: {(holding as any).collateral_quantity || 0}
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-right text-zinc-100">{holding.quantity}</div>
                                            {(holding as any).t1_quantity > 0 && (
                                                <div className="text-xs text-amber-400 text-right">T1: {(holding as any).t1_quantity}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right text-zinc-100">{formatCurrency(holding.average_price)}</td>
                                        <td className="px-6 py-4 text-right text-zinc-100">{formatCurrency(holding.last_price)}</td>
                                        <td className="px-6 py-4 text-right text-zinc-400 text-sm">
                                            {formatCurrency((holding as any).close_price || 0)}
                                        </td>
                                        <td className="px-6 py-4 text-right text-zinc-100 font-semibold">
                                            {formatCurrency(holding.last_price * holding.quantity)}
                                        </td>
                                        <td className={`px-6 py-4 text-right font-semibold ${holding.pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                            {formatCurrency(holding.pnl)}
                                        </td>
                                        <td className={`px-6 py-4 text-right ${holding.day_change >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                            {holding.day_change >= 0 ? '+' : ''}{holding.day_change_percentage?.toFixed(2)}%
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-12 text-center text-zinc-500">
                        <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No holdings found</p>
                    </div>
                )}
            </div>

            {/* Positions */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                <div className="p-6 border-b border-zinc-800">
                    <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                        <Activity className="w-5 h-5" />
                        Positions ({positions.net.length + positions.day.length})
                    </h3>
                </div>
                {(positions.net.length > 0 || positions.day.length > 0) ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-zinc-950">
                                <tr>
                                    <th className="text-left px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Symbol</th>
                                    <th className="text-center px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Product</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Qty</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Avg Price</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">LTP</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">M2M</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Unrealised</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Realised</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Total P&L</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-800">
                                {[...positions.net, ...positions.day].map((position: any, idx) => (
                                    <tr key={idx} className="hover:bg-zinc-800/50">
                                        <td className="px-6 py-4">
                                            <div>
                                                <div className="font-semibold text-zinc-100">{position.tradingsymbol}</div>
                                                <div className="text-xs text-zinc-500">{position.exchange}</div>
                                                <div className="text-xs text-amber-500 mt-1">
                                                    Buy: {position.buy_quantity} @ {formatCurrency(position.buy_price || 0)} | 
                                                    Sell: {position.sell_quantity} @ {formatCurrency(position.sell_price || 0)}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="text-xs px-2 py-1 bg-zinc-800 rounded text-zinc-300">
                                                {position.product}
                                            </span>
                                            {position.overnight_quantity > 0 && (
                                                <div className="text-xs text-blue-400 mt-1">O/N: {position.overnight_quantity}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right text-zinc-100">{position.quantity}</td>
                                        <td className="px-6 py-4 text-right text-zinc-100">{formatCurrency(position.average_price)}</td>
                                        <td className="px-6 py-4 text-right text-zinc-100">{formatCurrency(position.last_price)}</td>
                                        <td className={`px-6 py-4 text-right font-semibold ${(position.m2m || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                            {formatCurrency(position.m2m || 0)}
                                        </td>
                                        <td className={`px-6 py-4 text-right ${(position.unrealised || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                            {formatCurrency(position.unrealised || 0)}
                                        </td>
                                        <td className={`px-6 py-4 text-right ${(position.realised || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                            {formatCurrency(position.realised || 0)}
                                        </td>
                                        <td className={`px-6 py-4 text-right font-bold ${position.pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                            {formatCurrency(position.pnl)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-12 text-center text-zinc-500">
                        <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No open positions</p>
                    </div>
                )}
            </div>

            {/* Orders */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                <div className="p-6 border-b border-zinc-800">
                    <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        Recent Orders ({orders.length})
                    </h3>
                </div>
                {orders.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-zinc-950">
                                <tr>
                                    <th className="text-left px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Symbol</th>
                                    <th className="text-center px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Type</th>
                                    <th className="text-center px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Order Type</th>
                                    <th className="text-center px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Validity</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Qty (Filled/Total)</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Price</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Trigger</th>
                                    <th className="text-center px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Status</th>
                                    <th className="text-right px-6 py-3 text-xs font-semibold text-zinc-400 uppercase">Time</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-800">
                                {orders.slice(0, 10).map((order: any) => (
                                    <tr key={order.order_id} className="hover:bg-zinc-800/50">
                                        <td className="px-6 py-4">
                                            <div>
                                                <div className="font-semibold text-zinc-100">{order.tradingsymbol}</div>
                                                <div className="text-xs text-zinc-500">{order.exchange}</div>
                                                {order.tag && (
                                                    <div className="text-xs text-blue-400 mt-1">#{order.tag}</div>
                                                )}
                                                {order.parent_order_id && (
                                                    <div className="text-xs text-amber-400">Parent: {order.parent_order_id}</div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className={`text-xs px-2 py-1 rounded ${
                                                order.transaction_type === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                                            }`}>
                                                {order.transaction_type}
                                            </span>
                                            {order.variety && (
                                                <div className="text-xs text-zinc-500 mt-1">{order.variety}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-center text-xs text-zinc-400">{order.order_type}</td>
                                        <td className="px-6 py-4 text-center text-xs text-zinc-400">{order.validity || 'DAY'}</td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="text-zinc-100">
                                                {order.filled_quantity}/{order.quantity}
                                            </div>
                                            {order.pending_quantity > 0 && (
                                                <div className="text-xs text-amber-400">Pending: {order.pending_quantity}</div>
                                            )}
                                            {order.cancelled_quantity > 0 && (
                                                <div className="text-xs text-red-400">Cancelled: {order.cancelled_quantity}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="text-zinc-100">{formatCurrency(order.price)}</div>
                                            {order.average_price > 0 && (
                                                <div className="text-xs text-emerald-400">Avg: {formatCurrency(order.average_price)}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right text-zinc-400 text-sm">
                                            {order.trigger_price ? formatCurrency(order.trigger_price) : '-'}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className={`text-xs px-2 py-1 rounded ${
                                                order.status === 'COMPLETE' ? 'bg-emerald-500/20 text-emerald-400' :
                                                order.status === 'REJECTED' ? 'bg-red-500/20 text-red-400' :
                                                order.status === 'CANCELLED' ? 'bg-zinc-600/20 text-zinc-400' :
                                                'bg-amber-500/20 text-amber-400'
                                            }`}>
                                                {order.status}
                                            </span>
                                            {order.status_message && (
                                                <div className="text-xs text-zinc-500 mt-1 max-w-[200px] truncate">
                                                    {order.status_message}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right text-xs text-zinc-500">
                                            {new Date(order.order_timestamp).toLocaleTimeString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="p-12 text-center text-zinc-500">
                        <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No orders placed yet</p>
                    </div>
                )}
            </div>

            {/* GTT Orders */}
            {gttOrders.length > 0 && (
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
                    <div className="p-6 border-b border-zinc-800">
                        <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                            <Target className="w-5 h-5" />
                            GTT Orders ({gttOrders.length})
                        </h3>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                        {gttOrders.map((gtt) => (
                            <div key={gtt.id} className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-semibold text-zinc-100">{gtt.tradingsymbol}</span>
                                    <span className={`text-xs px-2 py-1 rounded ${
                                        gtt.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-700 text-zinc-400'
                                    }`}>
                                        {gtt.status}
                                    </span>
                                </div>
                                <div className="text-xs text-zinc-500">
                                    Type: {gtt.trigger_type}
                                </div>
                                <div className="text-xs text-zinc-500 mt-1">
                                    Created: {new Date(gtt.created_at).toLocaleDateString()}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Last Update */}
            <div className="text-center text-xs text-zinc-500">
                Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
        </div>
    );
};
