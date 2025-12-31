/**
 * Centralized API Configuration
 *
 * This file contains configuration for data sources.
 * When useActualServer is true, requests will be relayed to remote servers.
 * Otherwise, mock data will be used.
 */

export interface ApiConfig {
    remoteServers: {
        server: string;
    };
}

export const config: ApiConfig = {
    // Remote server addresses (configure these when ready to use actual servers)
    remoteServers: {
        // Use localhost in development, remote server in production
        server:
            process.env.NODE_ENV === 'production'
                ? 'http://kr2.chencraft.com:9452'
                : 'http://localhost:9452'
    },
};
