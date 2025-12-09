'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { API_ENDPOINTS } from '@/lib/api-config';

// Types
interface NewsItem {
    id: string;
    title: string;
    abstract: string;
    timestamp: string;
    sentiment: 'positive' | 'negative' | 'neutral';
}

interface UseNewsOptions {
    limit?: number;
    autoFetch?: boolean;
}

const POLL_INTERVAL = 15000; // 15 seconds

/**
 * Hook for fetching and polling news from remote source
 * Automatically refetches every 15 seconds
 */
export function useNews(options?: UseNewsOptions) {
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    // useRef aboids double fetch on mount in StrictMode
    const isFirstLoad = useRef(true);

    const limit = options?.limit || 10;
    const autoFetch = options?.autoFetch !== false; // Default true

    // TODO: Display full title and abstract upon hover
    /**
     * Fetch News 核心逻辑
     * @param isBackground - is background fetch (true-->do not show loading, false=show loading)
     */
    const fetchNews = useCallback(async (isBackground = false) => {
        try {
            if (!isBackground) {
                setLoading(true);
            }
            const queryParams = new URLSearchParams();
            queryParams.append('limit', String(limit));

            const url = `${API_ENDPOINTS.news}?${queryParams}`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Failed to fetch news: ${response.statusText}`);
            }

            let newsData: NewsItem[] = await response.json();
            // according to timestamp desc
            newsData = newsData.sort((a, b) => 
                new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
            );

            setNews(newsData);
            setError(null);
        } catch (err) {
            console.error("News fetch error:", err);
            setError(err instanceof Error ? err : new Error('Unknown error'));

            // background fetch do not clear existing news
            if (!isBackground) {
                setNews([]);
            }
        } finally {
            // whatever background or not, set loading false
            if (!isBackground) {
                setLoading(false);
            }
        }
    }, [limit]);

    useEffect(() => {
        if (!autoFetch) return;

        // Fetch immediately
        fetchNews();

        // Set up polling interval
        const interval = setInterval(() => {
            fetchNews(true); // <--- background fetch
        }, POLL_INTERVAL);

        return () => clearInterval(interval);
    }, [fetchNews, autoFetch]);

    return { 
        news, 
        loading, 
        error, 
        // Expose manual refresh for buttons, usually want to show loading state, so pass false
        refetch: () => fetchNews(false) 
    };
}
