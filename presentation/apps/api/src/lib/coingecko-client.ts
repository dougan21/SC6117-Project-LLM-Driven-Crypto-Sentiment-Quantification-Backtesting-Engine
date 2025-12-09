import Coingecko from '@coingecko/coingecko-typescript';

/**
 * CoinGecko API Client
 *
 * Singleton instance for interacting with the CoinGecko API.
 * Requires COINGECKO_API_KEY environment variable.
 *
 * Note: The client is initialized lazily to ensure environment variables are loaded.
 */

let _client: Coingecko | null = null;

export function getCoinGeckoClient(): Coingecko {
    if (!_client) {
        const apiKey = process.env.COINGECKO_API_KEY;

        if (!apiKey) {
            throw new Error(
                'COINGECKO_API_KEY not found in environment variables'
            );
        }

        console.log('✅ Initializing CoinGecko client with API key');

        _client = new Coingecko({
            demoAPIKey: apiKey,
            environment: 'demo',
        });
    }

    return _client;
}

// Note: Don't export a pre-initialized client to avoid initialization errors
// Always use getCoinGeckoClient() function instead
