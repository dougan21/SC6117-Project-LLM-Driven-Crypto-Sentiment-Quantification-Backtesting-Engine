import express from 'express';
import cors from 'cors';

// Types
interface ChartDataPoint {
    time: string;
    realPrice: number;
    predictionPrice: number;
}

interface ChartDataParams {
    startDateTime?: string;
    endDateTime?: string;
    cryptoPair?: string;
}

interface NewsItem {
    id: string;
    title: string;
    abstract: string;
    timestamp: string;
    sentiment: 'positive' | 'negative' | 'neutral';
}

interface TickerItem {
    symbol: string;
    pair: string;
    price: number;
    change: number;
    volume24h: number;
    high24h: number;
    low24h: number;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

interface ChatRequest {
    message: string;
    history: ChatMessage[];
}

// Mock data generators
function generateMockChartData(params?: ChartDataParams): ChartDataPoint[] {
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

        const priceChange = Math.sin(i / 4) * 2000 + Math.random() * 1000 - 500;
        const realPrice = openingPrice + priceChange;

        const predictionOffset =
            Math.cos(i / 5) * 1500 + Math.random() * 500 - 250;
        const predictionPrice = openingPrice + priceChange + predictionOffset;

        data.push({
            time: timeLabel,
            realPrice: Math.round(realPrice),
            predictionPrice: Math.round(predictionPrice),
        });
    }

    return data;
}

function generateMockNews(): NewsItem[] {
    const titles = [
        'Bitcoin Reaches New All-Time High',
        'Ethereum Developers Announce Major Upgrade',
        'Regulatory Clarity Expected in Q1 2025',
        'Top Crypto Exchange Reports Record Trading Volume',
        'New DeFi Protocol Launches with $50M TVL',
        'Central Banks Study CBDC Implementation',
        'Cryptocurrency Adoption Grows in Developing Nations',
        'Mining Difficulty Reaches New Peak',
        'Major Institution Adds Bitcoin to Treasury',
        'Blockchain Technology Disrupts Supply Chain',
    ];

    const abstracts = [
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
        'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.',
        'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.',
        'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
        'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.',
        'Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores.',
        'Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit.',
        'Sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem.',
        'Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam.',
        'At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti.',
    ];

    const sentiments: ('positive' | 'negative' | 'neutral')[] = [
        'negative',
        'positive',
        'neutral',
        'negative',
        'positive',
        'neutral',
        'positive',
        'neutral',
        'positive',
        'positive',
    ];

    const news: NewsItem[] = [];

    for (let i = 0; i < 10; i++) {
        const now = new Date();
        const minutesAgo = Math.floor(Math.random() * 1440);
        const timestamp = new Date(
            now.getTime() - minutesAgo * 60000
        ).toISOString();

        news.push({
            id: `news-${i}-${Date.now()}`,
            title: titles[i],
            abstract: abstracts[i],
            timestamp,
            sentiment: sentiments[i],
        });
    }

    // Sort by timestamp descending (newest first)
    news.sort(
        (a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    return news;
}

// Ticker state for consistent simulation
const BASE_PRICES: Record<string, number> = {
    BTC: 42000,
    ETH: 2200,
    BNB: 310,
    SOL: 95,
    XRP: 0.62,
    ADA: 0.48,
    DOGE: 0.087,
};

const INITIAL_CHANGES: Record<string, number> = {
    BTC: 0.8,
    ETH: -0.3,
    BNB: 1.2,
    SOL: 2.1,
    XRP: -0.9,
    ADA: 0.4,
    DOGE: 3.5,
};

let lastPrices: Record<string, number> = { ...BASE_PRICES };
let lastChanges: Record<string, number> = { ...INITIAL_CHANGES };

function generateMockTicker(): TickerItem[] {
    const symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE'];

    return symbols.map((symbol) => {
        const baseDrift = (Math.random() - 0.5) * 0.006;
        const prevChange = lastChanges[symbol] || 0;
        const pct = (prevChange / 100) * 0.2 + baseDrift;

        const prevPrice = lastPrices[symbol] || BASE_PRICES[symbol];
        const minPrice = BASE_PRICES[symbol] * 0.01;
        const nextPrice = Math.max(minPrice, prevPrice * (1 + pct));
        lastPrices[symbol] = nextPrice;

        const changeAdjustment = (Math.random() - 0.5) * 0.6;
        const nextChange = Math.max(
            -10,
            Math.min(10, prevChange + changeAdjustment)
        );
        lastChanges[symbol] = nextChange;

        const range = nextPrice * 0.05;
        const priceA = nextPrice + (Math.random() - 0.5) * 2 * range;
        const priceB = nextPrice + (Math.random() - 0.5) * 2 * range;
        const high24h = Math.max(nextPrice, priceA, priceB);
        const low24h = Math.min(nextPrice, priceA, priceB);
        const volume24h = Math.random() * 1000000000 + 500000000;

        return {
            symbol,
            pair: 'USD',
            price: nextPrice,
            change: nextChange,
            volume24h,
            high24h,
            low24h,
        };
    });
}

const app = express();

// Middleware
app.use(
    cors({
        origin: [
            'http://localhost:5628', // Dev server
            'http://localhost:6234',
            'https://sc6117.chencraft.com',
        ],
        credentials: true,
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    })
);
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Chart data endpoint
app.get('/api/chart-data', (req, res) => {
    const params: ChartDataParams = {
        startDateTime: req.query.startDateTime as string,
        endDateTime: req.query.endDateTime as string,
        cryptoPair: req.query.cryptoPair as string,
    };

    const data = generateMockChartData(params);
    res.status(200).json(data);
});

// News endpoint
app.get('/api/news', (req, res) => {
    const limit = req.query.limit
        ? parseInt(req.query.limit as string, 10)
        : 10;
    const news = generateMockNews().slice(0, limit);
    res.status(200).json(news);
});

// Ticker endpoint
app.get('/api/ticker', (req, res) => {
    const data = generateMockTicker();
    res.status(200).json(data);
});

// Chatbot endpoint
app.post('/api/chatbot', (req, res) => {
    const { message } = req.body as ChatRequest;

    if (!message) {
        res.status(400).json({ error: 'Message is required' });
        return;
    }

    // Simple mock response
    const response = {
        message: `You said: "${message}". This is a mock response. The chatbot feature is under development.`,
        timestamp: new Date().toISOString(),
    };

    res.status(200).json(response);
});

app.listen(6432, '0.0.0.0', () => {
    console.log(`API app listening on port 6432`);
});
