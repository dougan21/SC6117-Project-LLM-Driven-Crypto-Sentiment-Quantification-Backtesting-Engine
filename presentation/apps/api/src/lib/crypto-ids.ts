/**
 * CoinGecko Cryptocurrency IDs
 *
 * This file contains the canonical CoinGecko IDs for supported cryptocurrencies.
 * These IDs are used to query the CoinGecko API for price data and market information.
 */

export const cryptoIds = [
    'bitcoin', // BTC
    'ethereum', // ETH
    'tether', // USDT
    'ripple', // XRP
    'binancecoin', // BNB
    'usd-coin', // USDC
    'solana', // SOL
    'tron', // TRX
    'dogecoin', // DOGE
    'cardano', // ADA
    'bitcoin-cash', // BCH
    'hyperliquid', // HYPE
    'chainlink', // LINK
    'leo-token', // LEO
    'stellar', // XLM
    'monero', // XMR
    'zcash', // ZEC
    'litecoin', // LTC
    'sui', // SUI
    'avalanche-2', // AVAX
] as const;

export type CryptoId = (typeof cryptoIds)[number];
