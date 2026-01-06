import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Settings, Info } from 'lucide-react';

interface StrategyParameter {
    type: string;
    default: number | string;
    description: string;
}

interface StrategyInfo {
    type: string;
    name: string;
    description: string;
    parameters: Record<string, StrategyParameter>;
}

interface StrategyParametersProps {
    selectedStrategy: string;
    onParametersChange?: (params: Record<string, any>) => void;
    disabled?: boolean;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const StrategyParametersCard: React.FC<StrategyParametersProps> = ({
    selectedStrategy,
    onParametersChange,
    disabled = false
}) => {
    const [strategyInfo, setStrategyInfo] = useState<StrategyInfo | null>(null);
    const [parameters, setParameters] = useState<Record<string, any>>({});

    useEffect(() => {
        if (selectedStrategy) {
            fetchStrategyInfo(selectedStrategy);
        }
    }, [selectedStrategy]);

    const fetchStrategyInfo = async (strategyType: string) => {
        try {
            const response = await fetch(`${API_URL}/api/bot/strategy-parameters/${strategyType}`);
            const data = await response.json();
            if (data.status === 'success') {
                setStrategyInfo(data.strategy);
                // Initialize parameters with defaults
                const defaultParams: Record<string, any> = {};
                Object.entries(data.strategy.parameters).forEach(([key, param]: [string, any]) => {
                    defaultParams[key] = param.default;
                });
                setParameters(defaultParams);
                if (onParametersChange) {
                    onParametersChange(defaultParams);
                }
            }
        } catch (error) {
            console.error('Error fetching strategy info:', error);
        }
    };

    const handleParameterChange = (key: string, value: any, type: string) => {
        const parsedValue = type === 'int' ? parseInt(value) : type === 'float' ? parseFloat(value) : value;
        const newParams = { ...parameters, [key]: parsedValue };
        setParameters(newParams);
        if (onParametersChange) {
            onParametersChange(newParams);
        }
    };

    const resetToDefaults = () => {
        if (strategyInfo) {
            const defaultParams: Record<string, any> = {};
            Object.entries(strategyInfo.parameters).forEach(([key, param]: [string, any]) => {
                defaultParams[key] = param.default;
            });
            setParameters(defaultParams);
            if (onParametersChange) {
                onParametersChange(defaultParams);
            }
        }
    };

    if (!strategyInfo) {
        return (
            <Card className="bg-zinc-900 border-zinc-800">
                <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                        <Settings className="h-5 w-5 text-blue-500" />
                        Strategy Parameters
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-zinc-500 text-center py-4">
                        Select a strategy to customize parameters
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="text-white flex items-center gap-2">
                        <Settings className="h-5 w-5 text-blue-500" />
                        Strategy Parameters
                    </CardTitle>
                    <button
                        onClick={resetToDefaults}
                        disabled={disabled}
                        className="text-xs text-blue-500 hover:text-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Reset to Defaults
                    </button>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {/* Strategy Info */}
                    <div className="bg-blue-600/10 border border-blue-600/30 rounded-lg p-3">
                        <p className="text-blue-400 font-semibold mb-1">{strategyInfo.name}</p>
                        <p className="text-zinc-400 text-sm">{strategyInfo.description}</p>
                    </div>

                    {/* Parameters */}
                    <div className="space-y-3">
                        {Object.entries(strategyInfo.parameters).map(([key, param]: [string, any]) => (
                            <div key={key} className="bg-zinc-800 rounded-lg p-4">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex-1">
                                        <label className="text-white font-medium text-sm block mb-1">
                                            {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                                        </label>
                                        <div className="flex items-center gap-2 text-xs text-zinc-400">
                                            <Info className="h-3 w-3" />
                                            <span>{param.description}</span>
                                        </div>
                                    </div>
                                    <span className="text-xs text-zinc-500 bg-zinc-700 px-2 py-1 rounded">
                                        {param.type}
                                    </span>
                                </div>

                                <div className="flex items-center gap-3 mt-3">
                                    <input
                                        type="number"
                                        value={parameters[key] ?? param.default}
                                        onChange={(e) => handleParameterChange(key, e.target.value, param.type)}
                                        disabled={disabled}
                                        step={param.type === 'float' ? '0.1' : '1'}
                                        className="flex-1 bg-zinc-700 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                                    />
                                    <span className="text-zinc-500 text-sm">
                                        Default: {param.default}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Info Message */}
                    {disabled && (
                        <div className="bg-yellow-600/10 border border-yellow-600/30 rounded-lg p-3">
                            <p className="text-yellow-400 text-xs">
                                ⚠️ Stop the bot to modify parameters
                            </p>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
};

export default StrategyParametersCard;
