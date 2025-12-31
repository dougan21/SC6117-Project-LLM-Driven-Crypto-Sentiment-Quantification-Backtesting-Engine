'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
    ComposedChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';
import { useChartData } from '@/hooks/use-chart-data';

interface RechartCardProps {
    onCryptoPairChange?: (pair: string) => void;
}

interface ChartDataParams {
    startDateTime?: string; // ISO 8601 format: YYYY-MM-DDTHH:mm
    endDateTime?: string; // ISO 8601 format: YYYY-MM-DDTHH:mm
    cryptoPair?: string; // Cryptocurrency pair (default: BTC/USD)
}

/**
 * Format ISO-8601 time string for display based on time range
 * - Less than or equal to 24 hours: show time only (HH:mm)
 * - More than 24 hours: show date only (MM/DD)
 */
function formatTimeLabel(isoString: string, isShortRange: boolean): string {
    const date = new Date(isoString);
    if (isShortRange) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
        });
    } else {
        return date.toLocaleDateString('en-US', {
            month: '2-digit',
            day: '2-digit',
        });
    }
}

export function RechartCard({ onCryptoPairChange }: RechartCardProps) {
    // Form state (user-editable). chartParams controls when we actually fetch.
    const [startInput, setStartInput] = useState<string>('2025-07-01T00:00');
    const [endInput, setEndInput] = useState<string>('2025-08-01T00:00');
    const [cryptoInput, setCryptoInput] = useState<string>('BTC/USD');

    // Actual params passed to hook; undefined => no auto-fetch
    const [chartParams, setChartParams] = useState<ChartDataParams | undefined>(undefined);
    const { data: chartData, loading, error } = useChartData(chartParams as any);

    // Compute local min/max strings derived from UTC boundaries
    const utcMin = new Date('2025-07-01T00:00:00Z');
    const utcMax = new Date('2025-08-01T00:00:00Z');

    const toLocalInputValue = (d: Date) => {
        const pad = (n: number) => String(n).padStart(2, '0');
        const year = d.getFullYear();
        const month = pad(d.getMonth() + 1);
        const day = pad(d.getDate());
        const hours = pad(d.getHours());
        const minutes = pad(d.getMinutes());
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    };

    const localMin = toLocalInputValue(new Date(utcMin));
    const localMax = toLocalInputValue(new Date(utcMax));

    // Initialize time inputs to a system-time based window on mount (clamped to UTC allowed range)
    useEffect(() => {
        const now = new Date();
        // clamp end instant to UTC max
        const endInstant = now > utcMax ? utcMax : now;
        // default window: 1 hour
        let startInstant = new Date(endInstant.getTime() - 60 * 60 * 1000);
        if (startInstant < utcMin) startInstant = utcMin;

        setStartInput(toLocalInputValue(new Date(startInstant)));
        setEndInput(toLocalInputValue(new Date(endInstant)));
    }, []);

    // Determine if time range is <= 24 hours for display formatting
    const isShortRange = useMemo(() => {
        const s = chartParams?.startDateTime;
        const e = chartParams?.endDateTime;
        if (!s || !e) return true;
        const start = new Date(s).getTime();
        const end = new Date(e).getTime();
        return end - start <= 24 * 60 * 60 * 1000;
    }, [chartParams?.startDateTime, chartParams?.endDateTime]);

    // Format chart data with display-friendly time labels and numeric timestamps
    const formattedChartData = useMemo(() => {
        return chartData.map((point) => ({
            ...point,
            displayTime: formatTimeLabel(point.time, isShortRange),
            timestamp: new Date(point.time).getTime(), // Convert to numeric timestamp for proper spacing
        }));
    }, [chartData, isShortRange]);

    useEffect(() => {
        if (onCryptoPairChange && chartParams?.cryptoPair) {
            onCryptoPairChange(chartParams.cryptoPair as string);
        }
    }, [chartParams?.cryptoPair, onCryptoPairChange]);

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            const events = data.events;

            return (
                <div className="bg-white dark:bg-slate-900 p-3 rounded border border-gray-300 dark:border-slate-600 shadow-md">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                        {data.displayTime}
                    </p>
                    <p className="text-sm text-emerald-600 dark:text-emerald-400">
                        Hold Value: ${data.holdValue.toLocaleString()}
                    </p>
                    <p className="text-sm text-violet-600 dark:text-violet-400">
                        Strategy Value: ${data.strategyValue.toLocaleString()}
                    </p>
                    {events && events.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-slate-700">
                            {events.map((event: any, idx: number) => (
                                <div key={idx} className="text-xs">
                                    <p className="font-semibold text-blue-600 dark:text-blue-400">
                                        {event.action}
                                    </p>
                                    <p className="text-gray-600 dark:text-gray-400">
                                        {event.trigger}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="h-full w-full rounded-md border p-4 flex flex-col">
            <div className="mb-4 flex flex-wrap gap-4">
                <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">
                        Cryptocurrency
                    </label>
                    <select
                        value={cryptoInput}
                        onChange={(e) => setCryptoInput(e.target.value)}
                        className="px-3 py-2 border rounded-md bg-white dark:bg-slate-800 dark:border-slate-600 text-sm"
                    >
                        <option value="BTC/USD">Bitcoin (BTC/USD)</option>
                        <option value="ETH/USD">Ethereum (ETH/USD)</option>
                    </select>
                </div>

                <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">
                        Start Date & Time
                    </label>
                    <input
                        type="datetime-local"
                        value={startInput}
                        min="2025-07-01T00:00"
                        max="2025-08-01T00:00"
                        onChange={(e) => setStartInput(e.target.value)}
                        className="px-3 py-2 border rounded-md bg-white dark:bg-slate-800 dark:border-slate-600 text-sm"
                    />
                </div>

                <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">
                        End Date & Time
                    </label>
                    <input
                        type="datetime-local"
                        value={endInput}
                        min="2025-07-01T00:00"
                        max="2025-08-01T00:00"
                        onChange={(e) => setEndInput(e.target.value)}
                        className="px-3 py-2 border rounded-md bg-white dark:bg-slate-800 dark:border-slate-600 text-sm"
                    />
                </div>
                <div className="flex items-end">
                    <button
                        onClick={() => {
                            console.debug('[RechartCard] Enquiry clicked', { startInput, endInput, cryptoInput });
                            // Prevent duplicate or invalid requests
                            try {
                                const startIso = new Date(startInput);
                                const endIso = new Date(endInput);
                                if (isNaN(startIso.getTime()) || isNaN(endIso.getTime())) return;
                                // Ensure within allowed UTC bounds
                                const min = new Date('2025-07-01T00:00:00Z');
                                const max = new Date('2025-08-01T00:00:00Z');
                                if (startIso < min || endIso > max) return;

                                const params = {
                                    startDateTime: startIso.toISOString(),
                                    endDateTime: endIso.toISOString(),
                                    cryptoPair: cryptoInput,
                                } as ChartDataParams;

                                // Avoid re-requesting identical params
                                if (JSON.stringify(params) === JSON.stringify(chartParams)) return;
                                setChartParams(params);
                            } catch (e) {
                                // swallow invalid date errors
                            }
                        }}
                        disabled={loading}
                        className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-md disabled:opacity-50"
                    >
                        Enquiry
                    </button>
                </div>
            </div>
            <div className="flex-1 w-full flex items-center justify-center">
                {loading && (
                    <div className="text-center">
                        <p className="text-gray-500">Loading chart data...</p>
                    </div>
                )}
                {error && (
                    <div className="text-center">
                        <p className="text-red-500 text-sm">
                            Error loading data
                        </p>
                        <p className="text-gray-400 text-xs mt-1">
                            {error.message}
                        </p>
                    </div>
                )}
                {!loading && !error && (
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart
                            data={formattedChartData}
                            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey="timestamp"
                                type="number"
                                domain={['dataMin', 'dataMax']}
                                tickFormatter={(timestamp) => {
                                    const date = new Date(timestamp);
                                    return formatTimeLabel(
                                        date.toISOString(),
                                        isShortRange
                                    );
                                }}
                                scale="time"
                            />
                            <YAxis
                                domain={[10000, 'auto']}
                                label={{
                                    value: 'Price (USD)',
                                    angle: -90,
                                    position: 'insideLeft',
                                }}
                                tickFormatter={(value) =>
                                    `$${(value / 1000).toFixed(0)}k`
                                }
                            />
                            <Tooltip
                                content={<CustomTooltip />}
                                cursor={{ strokeDasharray: '3 3' }}
                            />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey="holdValue"
                                stroke="#10b981"
                                dot={false}
                                name="Buy & Hold"
                                isAnimationActive={false}
                            />
                            <Line
                                type="monotone"
                                dataKey="strategyValue"
                                stroke="#8b5cf6"
                                dot={false}
                                name="Active Strategy"
                                isAnimationActive={false}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
