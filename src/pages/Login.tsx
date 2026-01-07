import { useState, useEffect } from 'react';
import { Activity, ArrowRight, ShieldCheck, Zap, TrendingUp, X } from 'lucide-react';

export default function Login() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showBrokerSelection, setShowBrokerSelection] = useState(false);
    const [selectedBroker, setSelectedBroker] = useState<'kite' | 'fyers' | null>(null);

    useEffect(() => {
        // Check for error in URL
        const params = new URLSearchParams(window.location.search);
        if (params.get('error')) {
            setError('Authentication failed. Please try again.');
        }

        // Check for request_token (Redirect from Zerodha)
        const requestToken = params.get('request_token');
        if (requestToken) {
            setLoading(true);
            // Bounce to backend for processing
            window.location.href = `http://localhost:8000/api/auth/callback?request_token=${requestToken}`;
        }
    }, []);

    const handleLoginClick = () => {
        setShowBrokerSelection(true);
        setError(null);
    };

    const handleBrokerLogin = async (broker: 'kite' | 'fyers') => {
        setSelectedBroker(broker);
        setLoading(true);
        setError(null);

        if (broker === 'kite') {
            try {
                // Get login URL from backend
                const response = await fetch('http://localhost:8000/api/auth/login');
                const data = await response.json();

                if (data.status === 'success' && data.login_url) {
                    // Redirect to Zerodha login
                    window.location.href = data.login_url;
                } else {
                    setError('Failed to get login URL');
                    setLoading(false);
                }
            } catch (err) {
                console.error(err);
                setError('Connection refused. Is the backend running?');
                setLoading(false);
            }
        } else if (broker === 'fyers') {
            // Future implementation for Fyers
            setError('Fyers integration coming soon!');
            setLoading(false);
            setSelectedBroker(null);
        }
    };

    return (
        <div className="fixed inset-0 w-screen h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 flex items-center justify-center p-4 overflow-hidden">
            {/* Animated Background Effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-pulse"></div>
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-500/5 rounded-full blur-3xl"></div>
            </div>

            {/* Grid Pattern Overlay */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>

            <div className="relative w-full max-w-lg mx-auto z-10">
                {/* Logo Section */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-500/20 via-blue-500/20 to-purple-500/20 border border-emerald-500/30 mb-6 backdrop-blur-xl shadow-2xl shadow-emerald-500/20">
                        <Activity className="w-10 h-10 text-emerald-400" strokeWidth={2.5} />
                    </div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 via-blue-400 to-purple-400 bg-clip-text text-transparent mb-3">
                        Smart Algo Trade
                    </h1>
                    <p className="text-zinc-400 text-lg font-medium">
                        Professional Algorithmic Trading Platform
                    </p>
                </div>

                {/* Main Login Card */}
                <div className="bg-zinc-900/60 backdrop-blur-2xl border border-zinc-800/50 rounded-3xl p-10 shadow-2xl relative overflow-hidden">
                    {/* Gradient Border Effect */}
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-emerald-500/20 via-blue-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-blue-500 to-purple-500"></div>

                    <div className="relative space-y-8">
                        <div className="text-center">
                            <h2 className="text-2xl font-bold text-zinc-100 mb-2">Welcome Back</h2>
                            <p className="text-zinc-400">
                                Connect with your broker to start trading
                            </p>
                        </div>

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-400 flex items-center gap-2 backdrop-blur-sm">
                                <div className="w-1.5 h-1.5 bg-red-400 rounded-full animate-pulse"></div>
                                {error}
                            </div>
                        )}

                        {!showBrokerSelection ? (
                            <button
                                onClick={handleLoginClick}
                                className="w-full group relative bg-gradient-to-r from-emerald-500 to-blue-500 hover:from-emerald-400 hover:to-blue-400 text-white font-bold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center gap-3 shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/40 hover:scale-[1.02]"
                            >
                                <TrendingUp className="w-5 h-5" />
                                <span className="text-lg">Login</span>
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </button>
                        ) : (
                            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-lg font-semibold text-zinc-200">Select Your Broker</h3>
                                    <button
                                        onClick={() => setShowBrokerSelection(false)}
                                        className="text-zinc-400 hover:text-zinc-200 transition-colors"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Zerodha Kite Option */}
                                <button
                                    onClick={() => handleBrokerLogin('kite')}
                                    disabled={loading && selectedBroker === 'kite'}
                                    className="w-full group bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700/50 hover:border-emerald-500/50 text-zinc-100 font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-between shadow-lg hover:shadow-emerald-500/20 hover:scale-[1.02]"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 backdrop-blur-sm flex items-center justify-center border border-zinc-700/50">
                                            <TrendingUp className="w-6 h-6 text-emerald-400" />
                                        </div>
                                        <div className="text-left">
                                            <div className="text-base font-bold">Zerodha Kite</div>
                                            <div className="text-xs text-zinc-400">India's largest broker</div>
                                        </div>
                                    </div>
                                    {loading && selectedBroker === 'kite' ? (
                                        <div className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
                                    ) : (
                                        <ArrowRight className="w-5 h-5 text-zinc-400 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
                                    )}
                                </button>

                                {/* Fyers Option */}
                                <button
                                    onClick={() => handleBrokerLogin('fyers')}
                                    disabled={loading && selectedBroker === 'fyers'}
                                    className="w-full group bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700/50 hover:border-blue-500/50 text-zinc-100 font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-between shadow-lg hover:shadow-blue-500/20 hover:scale-[1.02] relative"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 backdrop-blur-sm flex items-center justify-center border border-zinc-700/50">
                                            <TrendingUp className="w-6 h-6 text-blue-400" />
                                        </div>
                                        <div className="text-left">
                                            <div className="text-base font-bold">Fyers</div>
                                            <div className="text-xs text-zinc-400">Advanced trading platform</div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-md border border-blue-500/30">Coming Soon</span>
                                        {loading && selectedBroker === 'fyers' ? (
                                            <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                                        ) : (
                                            <ArrowRight className="w-5 h-5 text-zinc-400 group-hover:text-blue-400 group-hover:translate-x-1 transition-all" />
                                        )}
                                    </div>
                                </button>
                            </div>
                        )}

                        {/* Features */}
                        <div className="pt-6 mt-6 border-t border-zinc-800/50 grid grid-cols-2 gap-6">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                                </div>
                                <div>
                                    <div className="text-xs font-semibold text-zinc-300">Secure OAuth2</div>
                                    <div className="text-xs text-zinc-500">Bank-grade security</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                                    <Zap className="w-4 h-4 text-blue-400" />
                                </div>
                                <div>
                                    <div className="text-xs font-semibold text-zinc-300">Real-time Data</div>
                                    <div className="text-xs text-zinc-500">Live market feeds</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <p className="text-center text-xs text-zinc-500 mt-8">
                    Powered by leading broker APIs • Secure & Reliable
                </p>
            </div>
        </div>
    );
}
