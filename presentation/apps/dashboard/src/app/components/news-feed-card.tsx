'use client';

import React from 'react';
import { useNews } from '@/hooks/use-news';

function SentimentIndicator({
    sentiment,
}: {
    sentiment: 'positive' | 'negative' | 'neutral';
}) {
    switch (sentiment) {
        case 'positive':
            return (
                <span className="text-2xl" title="Positive">
                    😊
                </span>
            );
        case 'negative':
            return (
                <span className="text-2xl" title="Negative">
                    😟
                </span>
            );
        case 'neutral':
            return (
                <span className="text-2xl" title="Neutral">
                    😐
                </span>
            );
        default:
            return null;
    }
}

function formatTimestamp(iso: string): string {
    const date = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}

export function NewsFeedCard() {
    const { news, loading, error } = useNews({ limit: 10 });

    return (
        <div className="h-full w-full rounded-md border p-4 flex flex-col min-h-0">
            <h3 className="mb-4 text-lg font-medium flex-shrink-0">
                Crypto News Feed
            </h3>
            <div className="flex-1 w-full overflow-y-auto pr-2 min-h-0">
                {loading && (
                    <div className="text-center py-8">
                        <p className="text-gray-500">Loading news...</p>
                    </div>
                )}
                {error && (
                    <div className="text-center py-8">
                        <p className="text-red-500 text-sm">
                            Error loading news
                        </p>
                        <p className="text-gray-400 text-xs mt-1">
                            {error.message}
                        </p>
                    </div>
                )}
                {!loading && !error && news.length === 0 && (
                    <div className="text-center py-8">
                        <p className="text-gray-500">No news available</p>
                    </div>
                )}
                {!loading && !error && news.length > 0 && (
                    <div className="space-y-2">
                        {news.map((item: any) => (
                            <div
                                key={item.id}
                                className="p-2 border rounded-lg bg-white dark:bg-slate-800 dark:border-slate-700 hover:shadow-md transition-shadow"
                            >
                                <div className="flex justify-between items-start gap-2">
                                    <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-xs line-clamp-1 text-gray-900 dark:text-gray-100">
                                            {item.title}
                                        </h4>
                                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5 line-clamp-1">
                                            {item.abstract}
                                        </p>
                                        <p
                                            className="text-xs text-gray-500 dark:text-gray-500 mt-1 cursor-help"
                                            title={new Date(
                                                item.timestamp
                                            ).toLocaleString()}
                                        >
                                            {formatTimestamp(item.timestamp)}
                                        </p>
                                    </div>
                                    <div className="flex-shrink-0">
                                        <SentimentIndicator
                                            sentiment={item.sentiment}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
