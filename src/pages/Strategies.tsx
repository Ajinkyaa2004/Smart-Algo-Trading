import React, { useState } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Zap, TrendingUp, Activity, CheckCircle2, Settings } from 'lucide-react';
import { cn } from '../lib/utils';
import { toast } from 'sonner';

interface RiskProfile {
    id: string;
    label: string;
    description: string;
    color: string;
    stopLoss: string;
    target: string;
}

const riskProfiles: RiskProfile[] = [
    { id: 'low', label: 'Conservative', description: 'Capital preservation first. Tight stops, smaller targets.', color: 'bg-emerald-500', stopLoss: '0.5%', target: '1-2%' },
    { id: 'medium', label: 'Balanced', description: 'Growth with managed risk. Standard swing trading parameters.', color: 'bg-blue-500', stopLoss: '1.0%', target: '2-4%' },
    { id: 'high', label: 'Aggressive', description: 'Maximum growth potential. Wider stops for volatile moves.', color: 'bg-purple-500', stopLoss: '2.0%', target: '5%+' },
    { id: 'custom', label: 'Custom Parameters', description: 'Set your own Stop-Loss and Target goals manually.', color: 'bg-zinc-500', stopLoss: '?', target: '?' },
];

const strategies = [
    { id: 'trend', name: 'Trend Follower', icon: TrendingUp, description: 'Buys when price is going up, sells when going down.' },
    { id: 'reversion', name: 'Mean Reversion', icon: Activity, description: 'Bets that price will return to the average after a spike.' },
    { id: 'scalp', name: 'Quick Scalper', icon: Zap, description: 'Takes many small profits throughout the day.' },
    { id: 'manual', name: 'Manual Setup', icon: Settings, description: 'You define exact parameters for execution.' },
];

const Strategies: React.FC = () => {
    const [selectedAsset, setSelectedAsset] = useState<string>('NIFTY 50');
    const [selectedRisk, setSelectedRisk] = useState<string>('medium');
    const [selectedStrategy, setSelectedStrategy] = useState<string>('trend');
    const [customSL, setCustomSL] = useState<string>('1.0');
    const [customTP, setCustomTP] = useState<string>('2.0');
    const [capital, setCapital] = useState<number>(50000);
    const [isDeploying, setIsDeploying] = useState(false);

    const handleDeploy = async () => {
        setIsDeploying(true);
        try {
            const response = await fetch('http://localhost:8000/api/strategies/deploy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    strategy: selectedStrategy,
                    riskProfile: selectedRisk,
                    capital: capital,
                    asset: selectedAsset,
                    customSL: selectedRisk === 'custom' ? customSL : null,
                    customTP: selectedRisk === 'custom' ? customTP : null
                }),
            });

            const data = await response.json();

            if (response.ok) {
                toast.success('Strategy Deployed', {
                    description: `Bot ID ${data.bot_id} is now running`
                });
            } else {
                toast.error('Deployment Failed', {
                    description: 'Unable to deploy strategy'
                });
            }
        } catch (error) {
            console.error("Deploy error:", error);
            toast.error('Connection Error', {
                description: 'Unable to connect to backend'
            });
        } finally {
            setIsDeploying(false);
        }
    };

    return (
        <div className="h-full w-full p-4 space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight text-white">Auto-Trading Setup</h2>
                <p className="text-zinc-400 mt-2">Configure your automated trading bot in 3 simple steps. No coding required.</p>
            </div>

            {/* Step 1: Select Asset */}
            <section className="space-y-4">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white">1</div>
                    <h3 className="text-xl font-semibold text-zinc-100">Select Asset</h3>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
                    {['NIFTY 50', 'BANKNIFTY', 'RELIANCE', 'HDFCBANK'].map((asset) => (
                        <div
                            key={asset}
                            onClick={() => setSelectedAsset(asset)}
                            className={cn(
                                "cursor-pointer rounded-xl border p-4 text-center transition-all hover:bg-zinc-900",
                                selectedAsset === asset
                                    ? "border-blue-500 bg-blue-500/10 ring-1 ring-blue-500"
                                    : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                            )}
                        >
                            <span className="font-bold text-zinc-200">{asset}</span>
                        </div>
                    ))}
                </div>
            </section>

            {/* Step 2: Strategy Selection */}
            <section className="space-y-4">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white">2</div>
                    <h3 className="text-xl font-semibold text-zinc-100">Choose a Strategy</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {strategies.map((strat) => (
                        <div
                            key={strat.id}
                            onClick={() => setSelectedStrategy(strat.id)}
                            className={cn(
                                "cursor-pointer rounded-xl border p-6 transition-all hover:bg-zinc-900",
                                selectedStrategy === strat.id
                                    ? "border-blue-500 bg-blue-500/10 ring-1 ring-blue-500"
                                    : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                            )}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <strat.icon className={cn("w-8 h-8", selectedStrategy === strat.id ? "text-blue-400" : "text-zinc-500")} />
                                {selectedStrategy === strat.id && <CheckCircle2 className="w-5 h-5 text-blue-500" />}
                            </div>
                            <h4 className="font-semibold text-zinc-100">{strat.name}</h4>
                            <p className="text-sm text-zinc-400 mt-2 leading-relaxed">{strat.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Step 3: Risk Profile */}
            <section className="space-y-4">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white">3</div>
                    <h3 className="text-xl font-semibold text-zinc-100">Select Risk Profile</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {riskProfiles.map((risk) => (
                        <div
                            key={risk.id}
                            onClick={() => setSelectedRisk(risk.id)}
                            className={cn(
                                "cursor-pointer rounded-xl border p-6 transition-all relative overflow-hidden",
                                selectedRisk === risk.id
                                    ? "border-zinc-700 bg-zinc-800"
                                    : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                            )}
                        >
                            {selectedRisk === risk.id && (
                                <div className={cn("absolute top-0 left-0 w-1 h-full", risk.color)}></div>
                            )}
                            <div className="mb-2">
                                <Badge variant="outline" className={cn("mb-2 border-0 bg-opacity-20", risk.color.replace('bg-', 'text-').replace('500', '400'), risk.color.replace('bg-', 'bg-').replace('500', '500/10'))}>
                                    {risk.label}
                                </Badge>
                            </div>
                            <p className="text-sm text-zinc-400 mb-4 h-10">{risk.description}</p>
                            <div className="flex items-center justify-between text-xs font-mono text-zinc-500 border-t border-zinc-700/50 pt-3">
                                <span>SL: <span className="text-zinc-300">{risk.stopLoss}</span></span>
                                <span>TP: <span className="text-zinc-300">{risk.target}</span></span>
                            </div>
                        </div>
                    ))}
                </div>

                {selectedRisk === 'custom' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 p-6 rounded-xl bg-zinc-900 border border-blue-500/30 animate-in fade-in slide-in-from-top-4 shadow-lg shadow-blue-500/5">
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Manual Stop-Loss (%)</label>
                            <div className="relative">
                                <input
                                    type="number"
                                    step="0.1"
                                    value={customSL}
                                    onChange={(e) => setCustomSL(e.target.value)}
                                    className="w-full bg-black/40 border border-zinc-700 rounded-lg p-3 text-xl font-bold text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                                />
                                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500 font-bold">%</span>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Manual Profit Target (%)</label>
                            <div className="relative">
                                <input
                                    type="number"
                                    step="0.1"
                                    value={customTP}
                                    onChange={(e) => setCustomTP(e.target.value)}
                                    className="w-full bg-black/40 border border-zinc-700 rounded-lg p-3 text-xl font-bold text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                                />
                                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500 font-bold">%</span>
                            </div>
                        </div>
                    </div>
                )}
            </section>

            {/* Step 4: Deployment */}
            <section className="space-y-4">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-white">4</div>
                    <h3 className="text-xl font-semibold text-zinc-100">Deploy & Run</h3>
                </div>

                <Card className="bg-zinc-900 border-zinc-800">
                    <CardContent className="p-8">
                        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                            <div className="space-y-4 w-full md:w-auto text-center md:text-left">
                                <div className="text-sm text-zinc-400 uppercase tracking-wider font-semibold">How much to invest?</div>

                                <div className="flex flex-wrap gap-2 mb-6 justify-center md:justify-start">
                                    {[10000, 25000, 50000, 100000].map((amt) => (
                                        <button
                                            key={amt}
                                            onClick={() => setCapital(amt)}
                                            className={cn(
                                                "px-4 py-2 rounded-lg text-sm font-semibold transition-all border",
                                                capital === amt
                                                    ? "bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-500/20"
                                                    : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
                                            )}
                                        >
                                            ₹{(amt / 1000).toFixed(0)}k
                                        </button>
                                    ))}
                                    <button
                                        onClick={() => { }} // Just visual helper, typing in input works
                                        className={cn(
                                            "px-4 py-2 rounded-lg text-sm font-semibold transition-all border",
                                            ![10000, 25000, 50000, 100000].includes(capital)
                                                ? "bg-amber-500/10 border-amber-500/50 text-amber-500 shadow-lg shadow-amber-500/10"
                                                : "bg-zinc-800 border-zinc-700 text-zinc-400"
                                        )}
                                    >
                                        Custom / Manual
                                    </button>
                                </div>

                                <div className="relative group max-w-[280px] mx-auto md:mx-0">
                                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl blur opacity-20 group-focus-within:opacity-40 transition duration-1000 group-hover:duration-200"></div>
                                    <div className="relative flex items-center bg-black rounded-xl p-4 border border-zinc-800 group-focus-within:border-blue-500 transition-colors">
                                        <span className="text-2xl font-bold text-zinc-600 mr-2">₹</span>
                                        <input
                                            type="number"
                                            value={capital}
                                            onChange={(e) => setCapital(Number(e.target.value))}
                                            className="bg-transparent border-none focus:ring-0 w-full text-3xl font-bold text-white placeholder-zinc-800"
                                            placeholder="0.00"
                                        />
                                    </div>
                                </div>
                                <p className="text-xs text-zinc-500 mt-2">Maximum exposure: <span className="text-zinc-300 font-mono">₹{(capital * 0.02).toLocaleString()}</span> per trade</p>
                            </div>

                            <div className="w-full md:w-auto">
                                <Button
                                    size="lg"
                                    onClick={handleDeploy}
                                    disabled={isDeploying}
                                    className={cn(
                                        "w-full md:w-64 h-16 text-lg font-bold shadow-xl shadow-blue-500/20 transition-all",
                                        isDeploying ? "bg-zinc-800 text-zinc-500" : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 hover:scale-105"
                                    )}
                                >
                                    {isDeploying ? (
                                        <span className="flex items-center gap-2">
                                            <Activity className="w-5 h-5 animate-spin" />
                                            Allocating...
                                        </span>
                                    ) : (
                                        <span className="flex items-center gap-2">
                                            <Zap className="w-5 h-5 fill-current" />
                                            Start Trading Bot
                                        </span>
                                    )}
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </section>
        </div>
    );
};

export default Strategies;
