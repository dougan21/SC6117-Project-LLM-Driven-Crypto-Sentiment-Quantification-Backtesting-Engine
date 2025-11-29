export interface ChartDataPoint {
    time: string;
    realPrice: number;
    predictionPrice: number;
    percentDifference: number;
}

export interface ChartDataParams {
    startDateTime?: string; // ISO 8601 format: YYYY-MM-DDTHH:mm
    endDateTime?: string; // ISO 8601 format: YYYY-MM-DDTHH:mm
    smoothing?: boolean; // Apply data smoothing
    showVolatility?: boolean; // Show volatility bands
    dataPoints?: number; // Number of data points to return (default: 24)
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

    // Determine number of data points
    const dataPoints = params?.dataPoints || 24;

    for (let i = 0; i < dataPoints; i++) {
        // Format time based on data points
        let timeLabel = '';
        if (dataPoints <= 24) {
            // Hourly format
            timeLabel = `${i.toString().padStart(2, '0')}:00`;
        } else if (dataPoints <= 30) {
            // Daily format
            const date = new Date();
            date.setDate(date.getDate() - (dataPoints - i));
            timeLabel = date.toISOString().split('T')[0];
        } else {
            // Weekly format
            const date = new Date();
            date.setDate(date.getDate() - (dataPoints - i) * 7);
            timeLabel = `Week of ${date.toISOString().split('T')[0]}`;
        }

        // Simulate real price movement with some randomness
        const priceChange = Math.sin(i / 4) * 2000 + Math.random() * 1000 - 500;
        const realPrice = openingPrice + priceChange;

        // Simulate prediction price (slightly offset from real price)
        const predictionOffset =
            Math.cos(i / 5) * 1500 + Math.random() * 500 - 250;
        const predictionPrice = openingPrice + priceChange + predictionOffset;

        // Calculate percentage difference between prediction and real price
        const percentDifference =
            ((predictionPrice - realPrice) / realPrice) * 100;

        data.push({
            time: timeLabel,
            realPrice: Math.round(realPrice),
            predictionPrice: Math.round(predictionPrice),
            percentDifference: Math.round(percentDifference * 100) / 100,
        });
    }

    return data;
}
