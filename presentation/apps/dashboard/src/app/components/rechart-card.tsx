'use client';

import React, { useState } from 'react';
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

export function RechartCard() {
    const [chartParams, setChartParams] = useState<ChartDataParams>({
        startDateTime: '2025-01-01T00:00',
        endDateTime: new Date().toISOString().slice(0, 16),
        dataPoints: 24,
        cryptoPair: 'BTC/USD',
        smoothing: false,
        showVolatility: false,
    });

    const { data: chartData, loading, error } = useChartData(chartParams);

    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-white dark:bg-slate-900 p-3 rounded border border-gray-300 dark:border-slate-600 shadow-md">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {payload[0].payload.time}
                    </p>
                    <p className="text-sm text-emerald-600 dark:text-emerald-400">
                        Real Price: $
                        {payload[0].payload.realPrice.toLocaleString()}
                    </p>
                    <p className="text-sm text-violet-600 dark:text-violet-400">
                        Predicted: $
                        {payload[0].payload.predictionPrice.toLocaleString()}
                    </p>
                    <p className="text-sm text-amber-600 dark:text-amber-400">
                        Difference:{' '}
                        {payload[0].payload.percentDifference > 0 ? '+' : ''}
                        {payload[0].payload.percentDifference.toFixed(2)}%
                    </p>
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
                        <option value="XRP/USD">Ripple (XRP/USD)</option>
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

                <div className="flex flex-col">
                    <label className="text-sm font-medium mb-1">
                        Data Points
                    </label>
                    <select
                        value={chartParams.dataPoints || 24}
                        onChange={(e) =>
                            setChartParams({
                                ...chartParams,
                                dataPoints: parseInt(e.target.value, 10),
                            })
                        }
                        className="px-3 py-2 border rounded-md bg-white dark:bg-slate-800 dark:border-slate-600 text-sm"
                    >
                        <option value="24">24 (Hourly)</option>
                        <option value="30">30 (Daily)</option>
                        <option value="52">52 (Weekly)</option>
                    </select>
                </div>

                <div className="flex flex-col justify-end gap-2">
                    <label className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={chartParams.smoothing || false}
                            onChange={(e) =>
                                setChartParams({
                                    ...chartParams,
                                    smoothing: e.target.checked,
                                })
                            }
                            className="rounded"
                        />
                        <span className="font-medium">Smoothing</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={chartParams.showVolatility || false}
                            onChange={(e) =>
                                setChartParams({
                                    ...chartParams,
                                    showVolatility: e.target.checked,
                                })
                            }
                            className="rounded"
                        />
                        <span className="font-medium">Volatility Bands</span>
                    </label>
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
                            data={chartData}
                            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="time" />
                            <YAxis
                                yAxisId="left"
                                label={{
                                    value: 'Price (USD)',
                                    angle: -90,
                                    position: 'insideLeft',
                                }}
                                tickFormatter={(value) =>
                                    `$${(value / 1000).toFixed(0)}k`
                                }
                            />
                            <YAxis
                                yAxisId="right"
                                orientation="right"
                                label={{
                                    value: 'Difference (%)',
                                    angle: 90,
                                    position: 'insideRight',
                                }}
                            />
                            <Tooltip
                                content={<CustomTooltip />}
                                cursor={{ strokeDasharray: '3 3' }}
                            />
                            <Legend />
                            <Line
                                yAxisId="left"
                                type="monotone"
                                dataKey="realPrice"
                                stroke="#10b981"
                                dot={false}
                                name="Real Price"
                                isAnimationActive={false}
                            />
                            <Line
                                yAxisId="left"
                                type="monotone"
                                dataKey="predictionPrice"
                                stroke="#8b5cf6"
                                dot={false}
                                name="Prediction Price"
                                isAnimationActive={false}
                            />
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="percentDifference"
                                stroke="#f59e0b"
                                dot={false}
                                name="Price Difference %"
                                isAnimationActive={false}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
