/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

const isDevelopment = process.env.NODE_ENV === 'development';

/**
 * Base API URL - switches between development and production
 * Development: http://localhost:6432
 * Production: https://sc6117-api.chencraft.com
 */
export const API_BASE_URL = isDevelopment
    ? 'http://localhost:6432'
    : 'https://sc6117-api.chencraft.com';

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
    health: `${API_BASE_URL}/health`,
    chartData: `${API_BASE_URL}/api/chart-data`,
    news: `${API_BASE_URL}/api/news`,
    ticker: `${API_BASE_URL}/api/ticker`,
    chatbot: `${API_BASE_URL}/api/chatbot`,
} as const;

/**
 * Helper function to get the API URL for a specific endpoint
 */
export function getApiUrl(endpoint: keyof typeof API_ENDPOINTS): string {
    return API_ENDPOINTS[endpoint];
}
