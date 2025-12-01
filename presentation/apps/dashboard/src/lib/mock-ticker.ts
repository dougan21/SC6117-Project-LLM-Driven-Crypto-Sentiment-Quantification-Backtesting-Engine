export interface TickerItem {
    symbol: string; // e.g. BTC
    pair: string; // e.g. USD
    price: number; // latest price
    change: number; // percent change
    volume24h: number; // 24h trading volume
    high24h: number; // 24h high
    low24h: number; // 24h low
}

// Base prices for consistent simulation
const BASE_PRICES: Record<string, number> = {
    BTC: 42000,
    ETH: 2200,
    BNB: 310,
    SOL: 95,
    XRP: 0.62,
    ADA: 0.48,
    DOGE: 0.087,
};

let lastPrices: Record<string, number> = { ...BASE_PRICES };
let lastChanges: Record<string, number> = {
    BTC: 0.8,
    ETH: -0.3,
    BNB: 1.2,
    SOL: 2.1,
    XRP: -0.9,
    ADA: 0.4,
    DOGE: 3.5,
};

/**
 * Generates mock ticker data with simulated price movements
 * Uses a random walk algorithm for realistic price changes
 * This will be replaced by actual WebSocket/API data
 */
export function generateMockTicker(): TickerItem[] {
    const symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE'];

    return symbols.map((symbol) => {
        // Random walk with drift influenced by previous change
        const baseDrift = (Math.random() - 0.5) * 0.006; // +/-0.6%
        const prevChange = lastChanges[symbol] || 0;
        const pct = (prevChange / 100) * 0.2 + baseDrift;

        // Update price
        const prevPrice = lastPrices[symbol] || BASE_PRICES[symbol];
        const nextPrice = Math.max(0.00000001, prevPrice * (1 + pct));
        lastPrices[symbol] = nextPrice;

        // Update change with some randomness
        const changeAdjustment = (Math.random() - 0.5) * 0.6;
        const nextChange = Math.max(
            -10,
            Math.min(10, prevChange + changeAdjustment)
        );
        lastChanges[symbol] = nextChange;

        // Generate realistic 24h data
        const high24h = nextPrice * (1 + Math.random() * 0.05);
        const low24h = nextPrice * (1 - Math.random() * 0.05);
        const volume24h = Math.random() * 1000000000 + 500000000; // 500M-1.5B

        return {
            symbol,
            pair: 'USD',
            price: nextPrice,
            change: nextChange,
            volume24h,
            high24h,
            low24h,
        };
    });
}

/**
 * Resets the price simulation to base values
 * Useful for testing or resetting the state
 */
export function resetTickerSimulation() {
    lastPrices = { ...BASE_PRICES };
    lastChanges = {
        BTC: 0.8,
        ETH: -0.3,
        BNB: 1.2,
        SOL: 2.1,
        XRP: -0.9,
        ADA: 0.4,
        DOGE: 3.5,
    };
}
