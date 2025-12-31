'use client';
import { useState, useEffect } from 'react';
import { API_ENDPOINTS } from '@/lib/api-config';

// Types
interface TradingEvent {
    timestamp: string;
    action: string;
    trigger: string;
}

interface ChartDataPoint {
    time: string;
    holdValue: number; // Value if bought at start and held
    strategyValue: number; // Value from active trading strategy
    events?: TradingEvent[]; // Optional trading events at this time point
}

interface ChartDataParams {
    startDateTime?: string;
    endDateTime?: string;
    cryptoPair?: string;
}

/**
 * Fetches chart data from remote source with optional parameters
 * Supports real API integration
 */
export function useChartData(params?: ChartDataParams) {
    const [data, setData] = useState<ChartDataPoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const [_status, setStatus] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        const sleep = (ms: number) => new Promise((res) => setTimeout(res, ms));

        const fetchWithPolling = async () => {
            // If no params provided, do not fetch (caller must trigger by setting params)
            if (!params || Object.keys(params).length === 0) {
                setLoading(false);
                setStatus(null);
                return;
            }

            setLoading(true);
            setError(null);
            setStatus(null);

            // Build query string from params
            const queryParams = new URLSearchParams();
            // Ensure times are sent as full ISO UTC (with 'Z'). If user inputs a local datetime
            // without timezone, convert it to an ISO string.
            const toIsoUtc = (v?: string) => {
                if (!v) return undefined;
                const d = new Date(v);
                if (isNaN(d.getTime())) return v; // leave as-is if invalid
                return d.toISOString();
            };

            const startIso = toIsoUtc(params?.startDateTime);
            const endIso = toIsoUtc(params?.endDateTime);
            if (startIso) queryParams.append('startDateTime', startIso);
            if (endIso) queryParams.append('endDateTime', endIso);
            if (params?.cryptoPair)
                queryParams.append('cryptoPair', params.cryptoPair);

            const url = `${API_ENDPOINTS.chartData}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
            console.debug('[useChartData] fetching', {
                url,
                params: { startIso, endIso, crypto: params?.cryptoPair },
            });

            const timeoutMs = 120_000; // total polling timeout
            const start = Date.now();
            let delay = 1000; // initial backoff
            const maxDelay = 10_000;
            const multiplier = 1.5;

            try {
                while (!cancelled && Date.now() - start < timeoutMs) {
                    const resp = await fetch(url, { method: 'GET' });
                    console.debug(
                        '[useChartData] response status',
                        resp.status
                    );

                    if (cancelled) return;

                    if (resp.status === 200) {
                        const chartData: ChartDataPoint[] = await resp.json();
                        if (!cancelled) {
                            setData(chartData);
                            setError(null);
                            setStatus('ready');
                        }
                        return;
                    }

                    if (resp.status === 202) {
                        // Accepted: server is processing. Poll again after delay.
                        setStatus('processing');
                        // Optionally read body for progress message
                        try {
                            const body = await resp.json().catch(() => null);
                            if (body && body.message) {
                                setStatus(String(body.message));
                            }
                        } catch (e) {
                            console.error(
                                '[useChartData] Error parsing progress message',
                                e
                            );
                        }

                        // Wait and retry (exponential backoff)
                        await sleep(delay);
                        delay = Math.min(
                            maxDelay,
                            Math.floor(delay * multiplier)
                        );
                        continue;
                    }

                    // Other errors
                    const text = await resp
                        .text()
                        .catch(() => resp.statusText || '');
                    throw new Error(`Fetch failed (${resp.status}): ${text}`);
                }

                if (!cancelled) {
                    throw new Error('Timeout while waiting for chart data');
                }
            } catch (err) {
                if (!cancelled) {
                    setError(
                        err instanceof Error ? err : new Error('Unknown error')
                    );
                    setData([]);
                    setStatus('error');
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        };

        fetchWithPolling();

        return () => {
            cancelled = true;
        };
    }, [params?.startDateTime, params?.endDateTime, params?.cryptoPair]);

    return { data, loading, error };
}
