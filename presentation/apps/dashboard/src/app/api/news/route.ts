import { generateMockNews } from '@/lib/mock-news';

export async function GET(request: Request) {
    try {
        // Parse query parameters
        const { searchParams } = new URL(request.url);
        const limit = Math.min(
            parseInt(searchParams.get('limit') || '10', 10),
            10
        ); // Cap at 10

        // Generate mock news
        const newsData = generateMockNews().slice(0, limit);

        return Response.json(newsData, {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-store',
            },
        });
    } catch (error) {
        console.error('Error fetching news:', error);
        return Response.json(
            { error: 'Failed to fetch news' },
            { status: 500 }
        );
    }
}
