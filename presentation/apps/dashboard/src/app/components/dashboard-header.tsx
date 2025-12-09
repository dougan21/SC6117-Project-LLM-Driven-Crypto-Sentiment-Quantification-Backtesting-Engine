'use client';
import React from 'react';
import { Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/theme-toggle';
import { useTicker } from '@/hooks/use-ticker';

export function DashboardHeader() {
    // Fetch real-time ticker data from API
    const { data: items, loading, error } = useTicker();

    // Duplicate to create a seamless loop (scrolls by 50%)
    const tickerItems = React.useMemo(() => [...items, ...items], [items]);

    return (
        <header className="flex h-14 items-center justify-between border-b bg-background px-6">
            <div className="relative flex-1 overflow-hidden">
                {loading && items.length === 0 && (
                    <span className="text-sm text-muted-foreground">
                        Loading prices...
                    </span>
                )}
                {error && items.length === 0 && (
                    <span className="text-sm text-red-500">
                        Unable to load live prices
                    </span>
                )}
                {items.length > 0 && (
                    <div
                        aria-live="polite"
                        className="pointer-events-none select-none"
                    >
                        <div className="ticker-track flex items-center gap-6 whitespace-nowrap">
                            {tickerItems.map((it, idx) => {
                                const up = it.change >= 0;
                                const color = up
                                    ? 'text-emerald-500'
                                    : 'text-rose-500';
                                const sign = up ? '+' : '';
                                return (
                                    <div
                                        key={`${it.symbol}-${idx}`}
                                        className="flex items-center gap-2"
                                    >
                                        <span className="font-medium">
                                            {it.symbol}/{it.pair}
                                        </span>
                                        <span className="tabular-nums">
                                            {it.price}
                                        </span>
                                        <span
                                            className={`tabular-nums ${color}`}
                                        >
                                            {up ? '▲' : '▼'} {sign}
                                            {Math.abs(it.change).toFixed(2)}%
                                        </span>
                                        <span className="opacity-40">•</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
                <style>{`
                    .ticker-track {
                        animation: ticker-scroll 25s linear infinite;
                        will-change: transform;
                    }
                    @keyframes ticker-scroll {
                        0% {
                            transform: translateX(0);
                        }
                        100% {
                            transform: translateX(-50%);
                        }
                    }
                `}</style>
            </div>
            <div className="flex items-center gap-2 pl-6 text-xs text-muted-foreground">
                <span className="opacity-40">|</span>
                <span>
                    Powered by{' '}
                    <a
                        href="https://www.coingecko.com/en/api"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline"
                    >
                        CoinGecko API
                    </a>
                </span>
            </div>
            <div className="flex items-center gap-2 pl-4">
                <ThemeToggle />
                <Button variant="ghost" size="icon" className="relative">
                    <Bell className="h-4 w-4" />
                    {/* <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-primary" /> */}
                    <span className="sr-only">Notifications</span>
                </Button>
            </div>
        </header>
    );
}
