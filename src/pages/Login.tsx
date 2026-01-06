import { useState, useEffect } from 'react';
import { Activity, ArrowRight, ShieldCheck, Zap } from 'lucide-react';

export default function Login() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

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

    const handleLogin = async () => {
        setLoading(true);
        setError(null);
        try {
            // Get login URL from backend
            const response = await fetch('http://localhost:8000/api/auth/login');
            const data = await response.json();

            if (data.status === 'success' && data.login_url) {
                // Redirect to Zerodha login
                window.location.href = data.login_url;
            } else {
                setError('Failed to get login URL');
            }
        } catch (err) {
            console.error(err);
            setError('Connection refused. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full bg-zinc-950 flex flex-col items-center justify-center p-4 relative">
            {/* Background Effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
            </div>

            <div className="relative w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-blue-500/20 border border-emerald-500/20 mb-6">
                        <Activity className="w-8 h-8 text-emerald-400" />
                    </div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
                        Smart Algo Trade
                    </h1>
                    <p className="text-zinc-400 mt-2 text-lg">
                        Professional Algorithmic Trading System
                    </p>
                </div>

                {/* Login Card */}
                <div className="bg-zinc-900/50 backdrop-blur-xl border border-zinc-800 rounded-2xl p-8 shadow-xl relative overflow-hidden">
                    {/* Top Highlight */}
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-blue-500 to-emerald-500"></div>

                    <div className="space-y-6">
                        <div>
                            <h2 className="text-xl font-semibold text-zinc-100">Welcome Back</h2>
                            <p className="text-sm text-zinc-400 mt-1">
                                Connect with your broker to start trading
                            </p>
                        </div>

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-400">
                                {error}
                            </div>
                        )}

                        <button
                            onClick={handleLogin}
                            disabled={loading}
                            className="w-full group bg-zinc-100 hover:bg-white text-zinc-900 font-semibold py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin"></div>
                            ) : (
                                <>
                                    <img
                                        src="https://kite.trade/static/images/kite-logo.svg"
                                        alt="Kite"
                                        className="w-5 h-5"
                                        onError={(e) => {
                                            // Fallback if image fails
                                            e.currentTarget.style.display = 'none';
                                        }}
                                    />
                                    <span>Login with Kite</span>
                                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>

                        {/* Features */}
                        <div className="pt-6 mt-6 border-t border-zinc-800 grid grid-cols-2 gap-4">
                            <div className="flex items-center gap-2">
                                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                                <span className="text-xs text-zinc-400">Secure OAuth2</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Zap className="w-4 h-4 text-blue-400" />
                                <span className="text-xs text-zinc-400">Real-time Data</span>
                            </div>
                        </div>
                    </div>
                </div>

                <p className="text-center text-xs text-zinc-500 mt-8">
                    Powered by Zerodha Kite Connect API
                </p>
            </div>
        </div>
    );
}
