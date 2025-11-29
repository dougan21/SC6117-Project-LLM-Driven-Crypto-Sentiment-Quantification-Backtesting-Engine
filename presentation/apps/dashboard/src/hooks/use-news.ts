'use client';

import { useState, useEffect } from 'react';
import { NewsItem, generateMockNews } from '@/lib/mock-news';

const NEWS_API = '/api/news';
const POLL_INTERVAL = 15000; // 15 seconds

export interface UseNewsOptions {
    limit?: number;
    autoFetch?: boolean;
}

/**
 * Hook for fetching and polling news from remote source
 * Automatically refetches every 15 seconds
 */
export function useNews(options?: UseNewsOptions) {
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const limit = options?.limit || 10;
    const autoFetch = options?.autoFetch !== false; // Default true

    // TODO: News should be sorted by timestamp descending
    // TODO: Display full title and abstract upon hover
    const fetchNews = async () => {
        try {
            setLoading(true);
            const queryParams = new URLSearchParams();
            queryParams.append('limit', String(limit));

            const url = `${NEWS_API}?${queryParams}`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Failed to fetch news: ${response.statusText}`);
            }

            const newsData: NewsItem[] = await response.json();
            setNews(newsData);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Unknown error'));
            // Fallback to mock data on error
            setNews(generateMockNews().slice(0, limit));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!autoFetch) return;

        // Fetch immediately
        fetchNews();

        // Set up polling interval
        const interval = setInterval(fetchNews, POLL_INTERVAL);

        return () => clearInterval(interval);
    }, [limit, autoFetch]);

    return { news, loading, error, refetch: fetchNews };
}
