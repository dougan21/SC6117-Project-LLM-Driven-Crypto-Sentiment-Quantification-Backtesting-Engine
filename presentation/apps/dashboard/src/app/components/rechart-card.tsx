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
import { ChartDataParams } from '@/lib/mock-chart-data';

interface RechartCardProps {
    onCryptoPairChange?: (pair: string) => void;
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
    // TODO: Set proper default value here
    const [chartParams, setChartParams] = useState<ChartDataParams>({
        startDateTime: '2025-01-01T00:00',
        endDateTime: new Date().toISOString().slice(0, 16),
        cryptoPair: 'BTC/USD',
    });

    const { data: chartData, loading, error } = useChartData(chartParams);

    // Determine if time range is <= 24 hours for display formatting
    const isShortRange = useMemo(() => {
        if (!chartParams.startDateTime || !chartParams.endDateTime) return true;
        const start = new Date(chartParams.startDateTime).getTime();
        const end = new Date(chartParams.endDateTime).getTime();
        return end - start <= 24 * 60 * 60 * 1000;
    }, [chartParams.startDateTime, chartParams.endDateTime]);

    // Format chart data with display-friendly time labels
    const formattedChartData = useMemo(() => {
        return chartData.map((point) => ({
            ...point,
            displayTime: formatTimeLabel(point.time, isShortRange),
        }));
    }, [chartData, isShortRange]);

    useEffect(() => {
        if (onCryptoPairChange && chartParams.cryptoPair) {
            onCryptoPairChange(chartParams.cryptoPair);
        }
    }, [chartParams.cryptoPair, onCryptoPairChange]);

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
                        value={chartParams.cryptoPair || 'BTC/USD'}
                        onChange={(e) =>
                            setChartParams({
                                ...chartParams,
                                cryptoPair: e.target.value,
                            })
                        }
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
                        value={chartParams.startDateTime || ''}
                        onChange={(e) =>
                            setChartParams({
                                ...chartParams,
                                startDateTime: e.target.value || undefined,
                            })
                        }
                        className="px-3 py-2 border rounded-md bg-white dark:bg-slate-800 dark:border-slate-600 text-sm"
                    />
                </div>

                <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">
                        End Date & Time
                    </label>
                    <input
                        type="datetime-local"
                        value={chartParams.endDateTime || ''}
                        onChange={(e) =>
                            setChartParams({
                                ...chartParams,
                                endDateTime: e.target.value || undefined,
                            })
                        }
                        className="px-3 py-2 border rounded-md bg-white dark:bg-slate-800 dark:border-slate-600 text-sm"
                    />
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
                            <XAxis dataKey="displayTime" />
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
