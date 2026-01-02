import { getCoinGeckoClient } from './coingecko-client.js';
import { cryptoIds } from './crypto-ids.js';

/**
 * Ticker Data Types
 *
 * @see apps/dashboard/src/types/ticker.ts - Dashboard uses matching type definition
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

/**
 * Symbol mapping for CoinGecko IDs to trading symbols
 */
const symbolMap: Record<string, string> = {
    bitcoin: 'BTC',
    ethereum: 'ETH',
    tether: 'USDT',
    ripple: 'XRP',
    binancecoin: 'BNB',
    'usd-coin': 'USDC',
    solana: 'SOL',
    tron: 'TRX',
    dogecoin: 'DOGE',
    cardano: 'ADA',
    'bitcoin-cash': 'BCH',
    hyperliquid: 'HYPE',
    chainlink: 'LINK',
    'leo-token': 'LEO',
    stellar: 'XLM',
    monero: 'XMR',
    zcash: 'ZEC',
    litecoin: 'LTC',
    sui: 'SUI',
    'avalanche-2': 'AVAX',
};

/**
 * Fetch ticker data from CoinGecko API
 *
 * @returns Array of ticker items with current prices and 24h changes
 */
export async function fetchTickerData(): Promise<TickerItem[]> {
    try {
        const client = getCoinGeckoClient();
        const response = await client.simple.price.get({
            ids: cryptoIds.join(','),
            vs_currencies: 'usd',
            include_24hr_change: true,
            include_24hr_vol: true,
            precision: '2',
        });

        const tickers: TickerItem[] = [];

        for (const [coinId, data] of Object.entries(response)) {
            const symbol = symbolMap[coinId];

            // Type guard for data structure
            if (!symbol || typeof data !== 'object' || data === null) {
                continue;
            }

            const coinData = data as Record<string, number>;

            if (!coinData.usd) {
                continue;
            }

            // Force 2 decimal places for price
            const price = coinData.usd.toFixed(2);

            tickers.push({
                symbol,
                pair: 'USD',
                price: price,
                change: coinData.usd_24h_change || 0,
                volume24h: coinData.usd_24h_vol || 0,
                high24h: coinData.usd_24h_high ?? 0,
                low24h: coinData.usd_24h_low ?? 0,
            });
        }

        return tickers;
    } catch (error) {
        console.error('Error fetching ticker data from CoinGecko:', error);
        throw new Error('Failed to fetch ticker data from CoinGecko API');
    }
}
