import { generateMockTicker } from '@/lib/mock-ticker';

export async function GET(request: Request) {
    try {
        // Parse query parameters
        const { searchParams } = new URL(request.url);
        const symbolsParam = searchParams.get('symbols');
        const symbols = symbolsParam
            ? symbolsParam.split(',').map((s) => s.trim().toUpperCase())
            : [];

        // Generate mock ticker data
        let tickerData = generateMockTicker();

        // Filter by symbols if provided
        if (symbols.length > 0) {
            tickerData = tickerData.filter((item) =>
                symbols.includes(item.symbol)
            );
        }

        return Response.json(tickerData, {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store', // Disable caching for real-time data
            },
        });
    } catch (error) {
        console.error('Error fetching ticker:', error);
        return Response.json(
            { error: 'Failed to fetch ticker data' },
            { status: 500 }
        );
    }
}
