import React, { useState, useMemo, useEffect, memo } from 'react';
import ReactApexChart from 'react-apexcharts';

interface CandlestickData {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    // Indicators
    atr?: number;
    adx?: number;
    plus_di?: number;
    minus_di?: number;
    bb_upper?: number;
    bb_middle?: number;
    bb_lower?: number;
    macd?: number;
    macd_signal?: number;
    macd_hist?: number;
    rsi?: number;
    supertrend?: number;
    supertrend_direction?: number;
}

interface SignalMarker {
    date: string;
    type: 'BUY' | 'SELL';
    price: number;
}

interface PatternMatch {
    timestamp: string;
    symbol: string;
    pattern: string;
    direction: string;
    confidence: number;
    price: number;
    description: string;
}

interface ApexCandlestickChartProps {
    data: CandlestickData[];
    height?: number;
    signals?: SignalMarker[];
    patterns?: PatternMatch[];
}

// Calculate EMA
const calculateEMA = (data: number[], period: number): number[] => {
    const ema: number[] = [];
    const multiplier = 2 / (period + 1);
    
    // First EMA is SMA
    let sum = 0;
    for (let i = 0; i < period; i++) {
        sum += data[i];
    }
    ema[period - 1] = sum / period;
    
    // Calculate rest of EMA values
    for (let i = period; i < data.length; i++) {
        ema[i] = (data[i] - ema[i - 1]) * multiplier + ema[i - 1];
    }
    
    return ema;
};

// Calculate RSI
const calculateRSI = (data: number[], period: number = 14): number[] => {
    const rsi: number[] = [];
    let gains = 0;
    let losses = 0;
    
    // First RSI calculation
    for (let i = 1; i <= period; i++) {
        const change = data[i] - data[i - 1];
        if (change > 0) gains += change;
        else losses -= change;
    }
    
    let avgGain = gains / period;
    let avgLoss = losses / period;
    rsi[period] = 100 - (100 / (1 + avgGain / avgLoss));
    
    // Calculate rest of RSI values
    for (let i = period + 1; i < data.length; i++) {
        const change = data[i] - data[i - 1];
        const gain = change > 0 ? change : 0;
        const loss = change < 0 ? -change : 0;
        
        avgGain = (avgGain * (period - 1) + gain) / period;
        avgLoss = (avgLoss * (period - 1) + loss) / period;
        
        rsi[i] = 100 - (100 / (1 + avgGain / avgLoss));
    }
    
    return rsi;
};

export const ApexCandlestickChart: React.FC<ApexCandlestickChartProps> = memo(({ 
    data, 
    height = 400,
    signals = [],
    patterns = []
}) => {
    const [showEMA20, setShowEMA20] = useState(false);
    const [showEMA50, setShowEMA50] = useState(false);
    const [showRSI, setShowRSI] = useState(false);
    const [showSignals, setShowSignals] = useState(true);
    const [showBollinger, setShowBollinger] = useState(false);
    const [showATR, setShowATR] = useState(false);
    const [showADX, setShowADX] = useState(false);
    const [showMACD, setShowMACD] = useState(false);
    const [showSupertrend, setShowSupertrend] = useState(false);

    // Auto-enable indicators if data is present
    useEffect(() => {
        if (data.length > 0) {
            if (data[0].bb_upper !== undefined) setShowBollinger(true);
            if (data[0].atr !== undefined) setShowATR(true);
            if (data[0].adx !== undefined) setShowADX(true);
            if (data[0].macd !== undefined) setShowMACD(true);
            if (data[0].rsi !== undefined) setShowRSI(true);
            if (data[0].supertrend !== undefined) setShowSupertrend(true);
        }
    }, [data]);

    // Calculate indicators
    const { candleData, volumeData, ema20Data, ema50Data, rsiData, annotations, bollingerData, atrData, adxData, macdData, supertrendData } = useMemo(() => {
        const candleData = data.map(d => ({
            x: new Date(d.date).getTime(),
            y: [d.open, d.high, d.low, d.close]
        }));

        const volumeData = data.map(d => ({
            x: new Date(d.date).getTime(),
            y: d.volume
        }));

        const closePrices = data.map(d => d.close);
        
        // Calculate EMAs
        const ema20 = calculateEMA(closePrices, 20);
        const ema50 = calculateEMA(closePrices, 50);
        
        const ema20Data = data.map((d, i) => ({
            x: new Date(d.date).getTime(),
            y: ema20[i] || null
        })).filter(d => d.y !== null);

        const ema50Data = data.map((d, i) => ({
            x: new Date(d.date).getTime(),
            y: ema50[i] || null
        })).filter(d => d.y !== null);

        // Calculate RSI
        const rsi = calculateRSI(closePrices);
        const rsiData = data.map((d, i) => ({
            x: new Date(d.date).getTime(),
            y: rsi[i] || null
        })).filter(d => d.y !== null);

        // Create annotations for buy/sell signals and patterns
        const annotations: any = {
            points: [
                ...signals.map(signal => ({
                    x: new Date(signal.date).getTime(),
                    y: signal.price,
                    marker: {
                        size: 8,
                        fillColor: signal.type === 'BUY' ? '#10b981' : '#ef4444',
                        strokeColor: '#ffffff',
                        strokeWidth: 2,
                        shape: signal.type === 'BUY' ? 'circle' : 'circle',
                    },
                    label: {
                        borderColor: signal.type === 'BUY' ? '#10b981' : '#ef4444',
                        offsetY: signal.type === 'BUY' ? 10 : -10,
                        style: {
                            color: '#fff',
                            background: signal.type === 'BUY' ? '#10b981' : '#ef4444',
                            fontSize: '11px',
                            fontWeight: 600,
                            padding: {
                                left: 6,
                                right: 6,
                                top: 2,
                                bottom: 2
                            }
                        },
                        text: signal.type === 'BUY' ? '▲ BUY' : '▼ SELL'
                    }
                })),
                ...patterns.map(pattern => ({
                    x: new Date(pattern.timestamp).getTime(),
                    y: pattern.price,
                    marker: {
                        size: 6,
                        fillColor: pattern.direction === 'bullish' ? '#ec4899' : 
                                   pattern.direction === 'bearish' ? '#f97316' : '#a855f7',
                        strokeColor: '#ffffff',
                        strokeWidth: 1,
                        shape: 'square',
                    },
                    label: {
                        borderColor: pattern.direction === 'bullish' ? '#ec4899' : 
                                     pattern.direction === 'bearish' ? '#f97316' : '#a855f7',
                        offsetY: pattern.direction === 'bearish' ? -10 : 10,
                        style: {
                            color: '#fff',
                            background: pattern.direction === 'bullish' ? '#ec4899' : 
                                       pattern.direction === 'bearish' ? '#f97316' : '#a855f7',
                            fontSize: '9px',
                            fontWeight: 500,
                            padding: {
                                left: 4,
                                right: 4,
                                top: 1,
                                bottom: 1
                            }
                        },
                        text: pattern.pattern
                    }
                }))
            ]
        };

        // Extract Bollinger Bands if present
        const bollingerData = {
            upper: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.bb_upper || null
            })).filter(d => d.y !== null),
            middle: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.bb_middle || null
            })).filter(d => d.y !== null),
            lower: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.bb_lower || null
            })).filter(d => d.y !== null)
        };

        // Extract ATR if present
        const atrData = data.map(d => ({
            x: new Date(d.date).getTime(),
            y: d.atr || null
        })).filter(d => d.y !== null);

        // Extract ADX and DI if present
        const adxData = {
            adx: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.adx || null
            })).filter(d => d.y !== null),
            plusDI: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.plus_di || null
            })).filter(d => d.y !== null),
            minusDI: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.minus_di || null
            })).filter(d => d.y !== null)
        };

        // Extract MACD if present
        const macdData = {
            macd: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.macd || null
            })).filter(d => d.y !== null),
            signal: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.macd_signal || null
            })).filter(d => d.y !== null),
            histogram: data.map(d => ({
                x: new Date(d.date).getTime(),
                y: d.macd_hist || null
            })).filter(d => d.y !== null)
        };

        // Extract RSI if present (use backend data if available, otherwise calculate)
        const rsiDataBackend = data.map(d => ({
            x: new Date(d.date).getTime(),
            y: d.rsi || null
        })).filter(d => d.y !== null);

        // Extract Supertrend if present
        const supertrendData = data.map(d => ({
            x: new Date(d.date).getTime(),
            y: d.supertrend || null,
            direction: d.supertrend_direction || 0
        })).filter(d => d.y !== null);

        return { candleData, volumeData, ema20Data, ema50Data, rsiData: rsiDataBackend.length > 0 ? rsiDataBackend : rsiData, annotations, bollingerData, atrData, adxData, macdData, supertrendData };
    }, [data, signals, patterns]);


    // Build series array
    const series: any[] = [
        {
            name: 'Price',
            type: 'candlestick',
            data: candleData
        }
    ];

    if (showEMA20) {
        series.push({
            name: 'EMA 20',
            type: 'line',
            data: ema20Data
        });
    }

    if (showEMA50) {
        series.push({
            name: 'EMA 50',
            type: 'line',
            data: ema50Data
        });
    }

    if (showBollinger && bollingerData.upper.length > 0) {
        series.push({
            name: 'BB Upper',
            type: 'line',
            data: bollingerData.upper
        });
        series.push({
            name: 'BB Middle',
            type: 'line',
            data: bollingerData.middle
        });
        series.push({
            name: 'BB Lower',
            type: 'line',
            data: bollingerData.lower
        });
    }

    if (showSupertrend && supertrendData.length > 0) {
        series.push({
            name: 'Supertrend',
            type: 'line',
            data: supertrendData
        });
    }

    const options: any = {
        chart: {
            type: 'candlestick',
            height: height,
            background: 'transparent',
            foreColor: '#a1a1aa',
            toolbar: {
                show: true,
                tools: {
                    download: true,
                    selection: true,
                    zoom: true,
                    zoomin: true,
                    zoomout: true,
                    pan: true,
                    reset: true,
                }
            },
            animations: {
                enabled: true,
                speed: 800
            }
        },
        theme: {
            mode: 'dark'
        },
        plotOptions: {
            candlestick: {
                colors: {
                    upward: '#10b981',
                    downward: '#ef4444'
                },
                wick: {
                    useFillColor: true
                }
            }
        },
        stroke: {
            width: [1, 2, 2, 2, 2, 2, 3], // Different widths for candlestick, EMA20, EMA50, BB lines, Supertrend
            curve: 'smooth'
        },
        colors: ['#3b82f6', '#f59e0b', '#8b5cf6', '#a855f7', '#8b5cf6', '#a855f7', '#eab308'], // Price, EMA20, EMA50, BB Upper, BB Middle, BB Lower, Supertrend
        annotations: showSignals ? annotations : { points: [] },
        xaxis: {
            type: 'datetime',
            labels: {
                style: {
                    colors: '#a1a1aa'
                },
                datetimeFormatter: {
                    year: 'yyyy',
                    month: "MMM 'yy",
                    day: 'dd MMM',
                    hour: 'HH:mm'
                }
            },
            axisBorder: {
                color: '#27272a'
            },
            axisTicks: {
                color: '#27272a'
            }
        },
        yaxis: {
            tooltip: {
                enabled: true
            },
            labels: {
                style: {
                    colors: '#a1a1aa'
                },
                formatter: (value: number) => `₹${value.toFixed(2)}`
            }
        },
        grid: {
            borderColor: '#27272a',
            strokeDashArray: 3,
            xaxis: {
                lines: {
                    show: true
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        },
        tooltip: {
            theme: 'dark',
            x: {
                format: 'dd MMM yyyy'
            },
            y: {
                formatter: (value: number) => `₹${value.toFixed(2)}`
            }
        },
        legend: {
            show: showEMA20 || showEMA50,
            position: 'top',
            horizontalAlign: 'left',
            labels: {
                colors: '#a1a1aa'
            },
            markers: {
                width: 10,
                height: 10,
                radius: 2
            }
        }
    };

    const rsiOptions: any = {
        chart: {
            type: 'line',
            height: 150,
            background: 'transparent',
            toolbar: { show: false },
            foreColor: '#a1a1aa'
        },
        theme: { mode: 'dark' },
        stroke: {
            width: 2,
            curve: 'smooth'
        },
        colors: ['#8b5cf6'],
        xaxis: {
            type: 'datetime',
            labels: { show: false }
        },
        yaxis: {
            min: 0,
            max: 100,
            tickAmount: 4,
            labels: {
                style: { colors: '#a1a1aa' }
            }
        },
        annotations: {
            yaxis: [
                {
                    y: 70,
                    borderColor: '#ef4444',
                    strokeDashArray: 4,
                    label: {
                        borderColor: '#ef4444',
                        style: {
                            color: '#fff',
                            background: '#ef4444',
                            fontSize: '10px'
                        },
                        text: 'Overbought (70)'
                    }
                },
                {
                    y: 30,
                    borderColor: '#10b981',
                    strokeDashArray: 4,
                    label: {
                        borderColor: '#10b981',
                        style: {
                            color: '#fff',
                            background: '#10b981',
                            fontSize: '10px'
                        },
                        text: 'Oversold (30)'
                    }
                }
            ]
        },
        grid: {
            borderColor: '#27272a',
            strokeDashArray: 3
        },
        dataLabels: { enabled: false },
        tooltip: {
            theme: 'dark',
            x: { format: 'dd MMM yyyy' },
            y: {
                formatter: (value: number) => `${value.toFixed(2)}`
            }
        }
    };

    return (
        <div className="w-full">
            {/* Indicator Controls */}
            <div className="mb-4 p-3 bg-zinc-900 rounded-lg border border-zinc-800">
                <div className="flex flex-wrap gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showEMA20}
                            onChange={(e) => setShowEMA20(e.target.checked)}
                            className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 text-blue-500 focus:ring-2 focus:ring-blue-500"
                        />
                        <span className="text-sm text-zinc-300">EMA 20</span>
                        <div className="w-3 h-3 rounded-full bg-[#f59e0b]"></div>
                    </label>
                    
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showEMA50}
                            onChange={(e) => setShowEMA50(e.target.checked)}
                            className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 text-purple-500 focus:ring-2 focus:ring-purple-500"
                        />
                        <span className="text-sm text-zinc-300">EMA 50</span>
                        <div className="w-3 h-3 rounded-full bg-[#8b5cf6]"></div>
                    </label>
                    
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showRSI}
                            onChange={(e) => setShowRSI(e.target.checked)}
                            className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 text-purple-500 focus:ring-2 focus:ring-purple-500"
                        />
                        <span className="text-sm text-zinc-300">RSI (14)</span>
                    </label>
                    
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showSignals}
                            onChange={(e) => setShowSignals(e.target.checked)}
                            className="w-4 h-4 rounded border-zinc-700 bg-zinc-800 text-green-500 focus:ring-2 focus:ring-green-500"
                        />
                        <span className="text-sm text-zinc-300">Buy/Sell Signals</span>
                    </label>
                </div>
            </div>

            {/* Main Chart */}
            <ReactApexChart
                options={options}
                series={series}
                type="candlestick"
                height={height}
            />
            
            {/* RSI Chart */}
            {showRSI && (
                <div className="mt-4">
                    <p className="text-xs text-zinc-400 font-medium mb-2 px-1">RSI (14)</p>
                    <ReactApexChart
                        options={rsiOptions}
                        series={[{ name: 'RSI', data: rsiData }]}
                        type="line"
                        height={150}
                    />
                </div>
            )}
            
            {/* ATR Chart */}
            {showATR && atrData.length > 0 && (
                <div className="mt-4">
                    <p className="text-xs text-zinc-400 font-medium mb-2 px-1">ATR (14)</p>
                    <ReactApexChart
                        options={{
                            chart: {
                                type: 'line',
                                height: 120,
                                background: 'transparent',
                                toolbar: { show: false }
                            },
                            theme: { mode: 'dark' },
                            stroke: {
                                curve: 'smooth',
                                width: 2
                            },
                            colors: ['#f97316'],
                            xaxis: {
                                type: 'datetime',
                                labels: { show: false }
                            },
                            yaxis: {
                                labels: {
                                    style: { colors: '#a1a1aa' },
                                    formatter: (value: number) => value.toFixed(2)
                                }
                            },
                            grid: {
                                borderColor: '#27272a',
                                strokeDashArray: 3
                            },
                            dataLabels: { enabled: false },
                            tooltip: {
                                theme: 'dark',
                                x: { format: 'dd MMM yyyy' },
                                y: {
                                    formatter: (value: number) => `ATR: ${value.toFixed(2)}`
                                }
                            }
                        }}
                        series={[{ name: 'ATR', data: atrData }]}
                        type="line"
                        height={120}
                    />
                </div>
            )}
            
            {/* ADX Chart */}
            {showADX && adxData.adx.length > 0 && (
                <div className="mt-4">
                    <p className="text-xs text-zinc-400 font-medium mb-2 px-1">ADX (14) with +DI / -DI</p>
                    <ReactApexChart
                        options={{
                            chart: {
                                type: 'line',
                                height: 140,
                                background: 'transparent',
                                toolbar: { show: false }
                            },
                            theme: { mode: 'dark' },
                            stroke: {
                                curve: 'smooth',
                                width: 2
                            },
                            colors: ['#06b6d4', '#10b981', '#ef4444'],
                            xaxis: {
                                type: 'datetime',
                                labels: { show: false }
                            },
                            yaxis: {
                                min: 0,
                                max: 100,
                                labels: {
                                    style: { colors: '#a1a1aa' },
                                    formatter: (value: number) => value.toFixed(0)
                                }
                            },
                            annotations: {
                                yaxis: [
                                    {
                                        y: 25,
                                        borderColor: '#fbbf24',
                                        strokeDashArray: 4,
                                        label: {
                                            borderColor: '#fbbf24',
                                            style: {
                                                color: '#000',
                                                background: '#fbbf24',
                                                fontSize: '10px'
                                            },
                                            text: 'Strong Trend (25)'
                                        }
                                    }
                                ]
                            },
                            grid: {
                                borderColor: '#27272a',
                                strokeDashArray: 3
                            },
                            dataLabels: { enabled: false },
                            legend: {
                                show: true,
                                position: 'top',
                                horizontalAlign: 'right',
                                labels: {
                                    colors: '#a1a1aa'
                                }
                            },
                            tooltip: {
                                theme: 'dark',
                                x: { format: 'dd MMM yyyy' },
                                y: {
                                    formatter: (value: number) => value.toFixed(2)
                                }
                            }
                        }}
                        series={[
                            { name: 'ADX', data: adxData.adx },
                            { name: '+DI', data: adxData.plusDI },
                            { name: '-DI', data: adxData.minusDI }
                        ]}
                        type="line"
                        height={140}
                    />
                </div>
            )}
            
            {/* MACD Chart */}
            {showMACD && macdData.macd.length > 0 && (
                <div className="mt-4">
                    <p className="text-xs text-zinc-400 font-medium mb-2 px-1">MACD (12, 26, 9)</p>
                    <ReactApexChart
                        options={{
                            chart: {
                                type: 'line',
                                height: 150,
                                background: 'transparent',
                                toolbar: { show: false }
                            },
                            theme: { mode: 'dark' },
                            stroke: {
                                curve: 'smooth',
                                width: [2, 2, 0]
                            },
                            colors: ['#3b82f6', '#f59e0b', '#10b981'],
                            xaxis: {
                                type: 'datetime',
                                labels: { show: false }
                            },
                            yaxis: {
                                labels: {
                                    style: { colors: '#a1a1aa' },
                                    formatter: (value: number) => value.toFixed(2)
                                }
                            },
                            annotations: {
                                yaxis: [
                                    {
                                        y: 0,
                                        borderColor: '#52525b',
                                        strokeDashArray: 4
                                    }
                                ]
                            },
                            grid: {
                                borderColor: '#27272a',
                                strokeDashArray: 3
                            },
                            dataLabels: { enabled: false },
                            legend: {
                                show: true,
                                position: 'top',
                                horizontalAlign: 'right',
                                labels: {
                                    colors: '#a1a1aa'
                                }
                            },
                            tooltip: {
                                theme: 'dark',
                                x: { format: 'dd MMM yyyy' },
                                y: {
                                    formatter: (value: number) => value.toFixed(4)
                                }
                            },
                            plotOptions: {
                                bar: {
                                    columnWidth: '80%',
                                    colors: {
                                        ranges: [{
                                            from: -1000,
                                            to: 0,
                                            color: '#ef4444'
                                        }, {
                                            from: 0,
                                            to: 1000,
                                            color: '#10b981'
                                        }]
                                    }
                                }
                            }
                        }}
                        series={[
                            { name: 'MACD', type: 'line', data: macdData.macd },
                            { name: 'Signal', type: 'line', data: macdData.signal },
                            { name: 'Histogram', type: 'bar', data: macdData.histogram }
                        ]}
                        type="line"
                        height={150}
                    />
                </div>
            )}
            
            {/* Volume Chart */}
            {data.some(d => d.volume > 0) && (
                <div className="mt-4">
                    <p className="text-xs text-zinc-400 font-medium mb-2 px-1">Volume</p>
                    <ReactApexChart
                        options={{
                            chart: {
                                type: 'bar',
                                height: 100,
                                background: 'transparent',
                                toolbar: { show: false }
                            },
                            theme: { mode: 'dark' },
                            plotOptions: {
                                bar: {
                                    colors: {
                                        ranges: [{
                                            from: 0,
                                            to: Number.MAX_VALUE,
                                            color: '#3f3f46'
                                        }]
                                    }
                                }
                            },
                            xaxis: {
                                type: 'datetime',
                                labels: { show: false }
                            },
                            yaxis: {
                                labels: {
                                    style: { colors: '#a1a1aa' },
                                    formatter: (value: number) => value.toFixed(0)
                                }
                            },
                            grid: {
                                borderColor: '#27272a',
                                strokeDashArray: 3
                            },
                            dataLabels: { enabled: false },
                            tooltip: {
                                theme: 'dark',
                                x: { format: 'dd MMM yyyy' }
                            }
                        }}
                        series={[{ name: 'Volume', data: volumeData }]}
                        type="bar"
                        height={100}
                    />
                </div>
            )}
        </div>
    );
});
