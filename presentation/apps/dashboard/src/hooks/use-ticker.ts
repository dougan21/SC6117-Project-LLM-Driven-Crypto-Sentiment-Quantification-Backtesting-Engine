'use client';

import { useState, useEffect } from 'react';
import { TickerItem, generateMockTicker } from '@/lib/mock-ticker';

const TICKER_API = '/api/ticker';
const POLL_INTERVAL = 3000; // 3 seconds for real-time updates

export interface UseTickerOptions {
    symbols?: string[];
    autoFetch?: boolean;
}

/**
 * Hook for fetching and polling cryptocurrency ticker data
 * Automatically refetches every 3 seconds for real-time updates
 */
export function useTicker(options?: UseTickerOptions) {
    const [data, setData] = useState<TickerItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const symbols = options?.symbols || [];
    const autoFetch = options?.autoFetch !== false; // Default true

    const fetchTicker = async () => {
        try {
            setLoading(true);
            const queryParams = new URLSearchParams();
            if (symbols.length > 0) {
                queryParams.append('symbols', symbols.join(','));
            }

            const url = `${TICKER_API}${queryParams.toString() ? `?${queryParams}` : ''}`;
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
            // Fallback to mock data on error
            setData(generateMockTicker());
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!autoFetch) return;

        // Fetch immediately
        fetchTicker();

        // Set up polling interval
        const interval = setInterval(fetchTicker, POLL_INTERVAL);

        return () => clearInterval(interval);
    }, [symbols.join(','), autoFetch]);

    return { data, loading, error, refetch: fetchTicker };
}
