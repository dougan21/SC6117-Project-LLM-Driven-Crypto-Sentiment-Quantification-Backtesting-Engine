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
        server3: string;
    };
}

export const config: ApiConfig = {
    // Set to true to relay requests to actual remote servers
    useActualServer: false,

    // Remote server addresses (configure these when ready to use actual servers)
    remoteServers: {
        server1: '', // Primary data source
        server2: '', // Secondary data source
        server3: '', // Tertiary data source
    },
};
