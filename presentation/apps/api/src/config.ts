/**
 * Centralized API Configuration
 *
 * This file contains configuration for data sources.
 * When useActualServer is true, requests will be relayed to remote servers.
 * Otherwise, mock data will be used.
 */

export interface ApiConfig {
    useActualServer: boolean;
    remoteServers: {
        server1: string;
        server2: string;
    };
}

export const config: ApiConfig = {
    // Set to true to relay requests to actual remote servers
    useActualServer: true,

    // Remote server addresses (configure these when ready to use actual servers)
    remoteServers: {
        server1: 'http://localhost:6432',
        server2: '',
    },
};
