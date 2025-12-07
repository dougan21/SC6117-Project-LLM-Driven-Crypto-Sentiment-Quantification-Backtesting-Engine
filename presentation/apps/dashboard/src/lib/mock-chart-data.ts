export interface TradingEvent {
    timestamp: string;
    action: string;
    trigger: string;
}

export interface ChartDataPoint {
    time: string;
    holdValue: number; // Value if bought at start and held
    strategyValue: number; // Value from active trading strategy
    events?: TradingEvent[]; // Optional trading events at this time point
}

export interface ChartDataParams {
    startDateTime?: string; // ISO 8601 format: YYYY-MM-DDTHH:mm
    endDateTime?: string; // ISO 8601 format: YYYY-MM-DDTHH:mm
    cryptoPair?: string; // Cryptocurrency pair (default: BTC/USD)
}

/**
 * Generates mock stock data based on parameters
 * This will be replaced by actual API data
 * Server-side utility - can be called from both client and server
 */
export function generateMockData(params?: ChartDataParams): ChartDataPoint[] {
    const openingPrice = 45000;
    const data: ChartDataPoint[] = [];

    // Parse start and end times
    let startTime: Date;
    let endTime: Date;

    if (params?.startDateTime && params?.endDateTime) {
        startTime = new Date(params.startDateTime);
        endTime = new Date(params.endDateTime);
    } else {
        // Default: last 24 hours
        endTime = new Date();
        startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000);
    }

    // Calculate time range and number of data points
    const timeRangeMs = endTime.getTime() - startTime.getTime();
    const dataPoints = 24; // Fixed to 24 data points
    const intervalMs = timeRangeMs / (dataPoints - 1);

    for (let i = 0; i < dataPoints; i++) {
        const currentTime = new Date(startTime.getTime() + i * intervalMs);

        // Format time based on time range
        let timeLabel: string;
        if (timeRangeMs <= 24 * 60 * 60 * 1000) {
            // Less than or equal to 24 hours: show time
            timeLabel = currentTime.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
            });
        } else if (timeRangeMs <= 30 * 24 * 60 * 60 * 1000) {
            // Less than or equal to 30 days: show date
            timeLabel = currentTime.toISOString().split('T')[0];
        } else {
            // More than 30 days: show date
            timeLabel = currentTime.toISOString().split('T')[0];
        }

        // Simulate real price movement with some randomness
        const priceChange = Math.sin(i / 4) * 2000 + Math.random() * 1000 - 500;
        const realPrice = openingPrice + priceChange;

        // Simulate prediction price (slightly offset from real price)
        const predictionOffset =
            Math.cos(i / 5) * 1500 + Math.random() * 500 - 250;
        const predictionPrice = openingPrice + priceChange + predictionOffset;

        data.push({
            time: timeLabel,
            holdValue: Math.round(realPrice),
            strategyValue: Math.round(predictionPrice),
        });
    }

    return data;
}
