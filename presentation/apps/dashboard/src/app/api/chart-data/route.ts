import { generateMockData } from '@/lib/mock-chart-data';

export async function GET(request: Request) {
    try {
        // Parse query parameters
        const { searchParams } = new URL(request.url);
        const startDateTime = searchParams.get('startDateTime') || undefined;
        const endDateTime = searchParams.get('endDateTime') || undefined;
        const cryptoPair = searchParams.get('cryptoPair') || 'BTC/USD';

        // Generate data with parameters
        const chartData = generateMockData({
            startDateTime,
            endDateTime,
            cryptoPair,
        });

        return Response.json(chartData, {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store',
            },
        });
    } catch (error) {
        console.error('Error fetching chart data:', error);
        return Response.json(
            { error: 'Failed to fetch chart data' },
            { status: 500 }
        );
    }
}
