/**
 * Shared Ticker Types
 *
 * These types are shared between the API and dashboard to ensure consistency.
 *
 * @see apps/api/src/lib/ticker-service.ts - API implementation uses the same structure
 */

export interface TickerItem {
    symbol: string;
    pair: string;
    price: string;
    change: number;
    volume24h: number;
    high24h: number;
    low24h: number;
}
