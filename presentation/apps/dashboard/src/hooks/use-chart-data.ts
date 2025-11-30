'use client';
import { useState, useEffect } from 'react';
import {
    ChartDataPoint,
    ChartDataParams,
    generateMockData,
} from '@/lib/mock-chart-data';

// Mock API endpoint - replace with actual API URL
const CHART_DATA_API = '/api/chart-data';

/**
 * Fetches chart data from remote source with optional parameters
 * Currently uses mock data, but structure supports real API integration
 */
export function useChartData(params?: ChartDataParams) {
    const [data, setData] = useState<ChartDataPoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);

                // Build query string from params
                const queryParams = new URLSearchParams();
                if (params?.startDateTime)
                    queryParams.append('startDateTime', params.startDateTime);
                if (params?.endDateTime)
                    queryParams.append('endDateTime', params.endDateTime);
                if (params?.smoothing)
                    queryParams.append('smoothing', String(params.smoothing));
                if (params?.showVolatility)
                    queryParams.append(
                        'showVolatility',
                        String(params.showVolatility)
                    );
                if (params?.dataPoints)
                    queryParams.append('dataPoints', String(params.dataPoints));
                if (params?.cryptoPair)
                    queryParams.append('cryptoPair', params.cryptoPair);

                const url = `${CHART_DATA_API}${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(
                        `Failed to fetch chart data: ${response.statusText}`
                    );
                }

                const chartData: ChartDataPoint[] = await response.json();
                setData(chartData);
                setError(null);
            } catch (err) {
                setError(
                    err instanceof Error ? err : new Error('Unknown error')
                );
                // Fallback to mock data on error
                setData(generateMockData(params));
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [
        params?.startDateTime,
        params?.endDateTime,
        params?.smoothing,
        params?.showVolatility,
        params?.dataPoints,
        params?.cryptoPair,
    ]);

    return { data, loading, error };
}
