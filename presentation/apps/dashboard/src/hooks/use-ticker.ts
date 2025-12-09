'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { API_ENDPOINTS } from '@/lib/api-config';
import { TickerItem } from '@/types/ticker';

interface UseTickerOptions {
    symbols?: string[];
    autoFetch?: boolean;
}

const POLL_INTERVAL = 30000; // 30 seconds for real-time updates

/**
 * Hook for fetching and polling cryptocurrency ticker data
 * Automatically refetches every 30 seconds for real-time updates
 */
export function useTicker(options?: UseTickerOptions) {
    const [data, setData] = useState<TickerItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const [isInitialLoad, setIsInitialLoad] = useState(true);
    const symbols = options?.symbols || [];
    const autoFetch = options?.autoFetch !== false; // Default true

    // Create a stable dependency key for symbols
    const symbolsKey = useMemo(() => symbols.join(','), [symbols]);

    // Stable refetch function for manual calls
    const refetch = useCallback(async () => {
        const queryParams = new URLSearchParams();
        if (symbolsKey) {
            queryParams.append('symbols', symbolsKey);
        }
        const url = `${API_ENDPOINTS.ticker}${queryParams.toString() ? `?${queryParams}` : ''}`;
        try {
            setLoading(true);
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(
                    `Failed to fetch ticker: ${response.statusText}`
                );
            }
            const tickerData: TickerItem[] = await response.json();
            setData(tickerData);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Unknown error'));
            setData([]);
        } finally {
            setLoading(false);
        }
    }, [symbolsKey]);

    useEffect(() => {
        if (!autoFetch) return;

        let mounted = true;

        const fetchTicker = async () => {
            try {
                if (mounted && isInitialLoad) setLoading(true);
                const queryParams = new URLSearchParams();
                if (symbolsKey) {
                    queryParams.append('symbols', symbolsKey);
                }

                const url = `${API_ENDPOINTS.ticker}${queryParams.toString() ? `?${queryParams}` : ''}`;
                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(
                        `Failed to fetch ticker: ${response.statusText}`
                    );
                }

                const tickerData: TickerItem[] = await response.json();
                if (mounted) {
                    setData(tickerData);
                    setError(null);
                }
            } catch (err) {
                if (mounted) {
                    setError(
                        err instanceof Error ? err : new Error('Unknown error')
                    );
                    // Fallback: gracefully handle error without mock data
                    setData([]);
                }
            } finally {
                if (mounted) {
                    setLoading(false);
                    setIsInitialLoad(false);
                }
            }
        };

        // Fetch immediately
        fetchTicker();

        // Set up polling interval
        const interval = setInterval(fetchTicker, POLL_INTERVAL);

        return () => {
            mounted = false;
            clearInterval(interval);
        };
    }, [symbolsKey, autoFetch, isInitialLoad]);

    return { data, loading, error, refetch };
}
