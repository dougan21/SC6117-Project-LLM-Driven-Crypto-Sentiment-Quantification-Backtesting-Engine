import express from 'express';
import cors from 'cors';
import swaggerUi from 'swagger-ui-express';
import YAML from 'yamljs';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';
import { config as apiConfig } from './config.js';
import { fetchTickerData } from './lib/ticker-service.js';

// Load environment variables from .env file in API directory
config();

// Get current file path for other uses
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Utility function to relay requests to remote server
async function relayRequest(
    serverUrl: string,
    path: string,
    method: 'GET' | 'POST' = 'GET',
    body?: any
): Promise<any> {
    if (!serverUrl) {
        throw new Error('Remote server address not configured');
    }

    const url = `${serverUrl}${path}`;
    const options: RequestInit = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (body && method === 'POST') {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
        throw new Error(
            `Remote server error: ${response.status} ${response.statusText}`
        );
    }

    return response.json();
}

// Types
interface TradingEvent {
    timestamp: string;
    action: string;
    trigger: string;
}

interface ChartDataPoint {
    time: string;
    holdValue: number;
    strategyValue: number;
    events?: TradingEvent[];
}

interface ChartDataParams {
    startDateTime?: string;
    endDateTime?: string;
    cryptoPair?: string;
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

        // Always use ISO-8601 format for time
        const timeLabel = currentTime.toISOString();

        const priceChange = Math.sin(i / 4) * 2000 + Math.random() * 1000 - 500;
        const holdValue = openingPrice + priceChange;

        const strategyOffset =
            Math.cos(i / 5) * 1500 + Math.random() * 500 - 250;
        const strategyValue = openingPrice + priceChange + strategyOffset;

        // Generate sample trading events at random intervals
        const events: TradingEvent[] | undefined =
            i % 6 === 0 && i > 0
                ? [
                      {
                          timestamp: currentTime.toISOString(),
                          action: strategyValue > holdValue ? 'BUY' : 'SELL',
                          trigger:
                              strategyValue > holdValue
                                  ? 'Price momentum above MA(20)'
                                  : 'RSI oversold signal',
                      },
                  ]
                : undefined;

        data.push({
            time: timeLabel,
            holdValue: Math.round(holdValue),
            strategyValue: Math.round(strategyValue),
            events,
        });
    }

    return data;
}

const app = express();

// Middleware
app.use(
    cors({
        origin: [
                'http://localhost:5628', // Dev server
                'http://localhost:6234',
                'http://localhost:3024', // microfrontends proxy
                'https://sc6117.chencraft.com',
        ],
        credentials: true,
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    })
);
app.use(express.json());

// Load OpenAPI specification
const swaggerDocument = YAML.load(path.join(__dirname, 'openapi.yaml'));

// Swagger UI endpoint
app.use(
    '/api-docs',
    swaggerUi.serve,
    swaggerUi.setup(swaggerDocument, {
        customCss: '.swagger-ui .topbar { display: none }',
        customSiteTitle: 'SC6117 API Documentation',
    })
);

// Health check
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Chart data endpoint
app.get('/api/chart-data', async (req, res) => {
    try {
        if (apiConfig.useActualServer) {
            // Relay request to remote server
            const queryString = new URLSearchParams(
                req.query as any
            ).toString();
            const path = `/api/chart-data${queryString ? '?' + queryString : ''}`;
            const data = await relayRequest(
                apiConfig.remoteServers.server1,
                path
            );
            // If the remote server returns an envelope with `records`,
            // unwrap it to match the dashboard's expected array shape.
            if (data && typeof data === 'object' && Array.isArray((data as any).records)) {
                return res.status(200).json((data as any).records);
            }
            res.status(200).json(data);
        } else {
            // Use mock data
            const params: ChartDataParams = {
                startDateTime: req.query.startDateTime as string,
                endDateTime: req.query.endDateTime as string,
                cryptoPair: req.query.cryptoPair as string,
            };
            const data = generateMockChartData(params);
            res.status(200).json(data);
        }
    } catch (error) {
        console.error('Chart data error:', error);
        res.status(500).json({ error: 'Failed to fetch chart data' });
    }
});

// News endpoint
app.get('/api/news', async (req, res) => {
    try {
        // Relay request to remote server
        const queryString = new URLSearchParams(req.query as any).toString();
        const path = `/api/news${queryString ? '?' + queryString : ''}`;
        const data = await relayRequest(apiConfig.remoteServers.server1, path);
        res.status(200).json(data);
    } catch (error) {
        console.error('News error:', error);
        res.status(500).json({ error: 'Failed to fetch news' });
    }
});

// Ticker endpoint
app.get('/api/ticker', async (req, res) => {
    // Always try to fetch from CoinGecko first
    try {
        const data = await fetchTickerData();
        res.status(200).json(data);
        return;
    } catch (error) {
        console.error('Ticker error:', error);
        res.status(500).json({ error: 'Failed to fetch ticker data' });
    }
});

// Chatbot endpoint
app.post('/api/chatbot', async (req, res) => {
    try {
        const { message } = req.body as ChatRequest;

        if (!message) {
            res.status(400).json({ error: 'Message is required' });
            return;
        }

        // Relay request to remote server
        const data = await relayRequest(
            apiConfig.remoteServers.server1,
            '/api/chatbot',
            'POST',
            req.body
        );
        res.status(200).json(data);
    } catch (error) {
        console.error('Chatbot error:', error);
        res.status(500).json({ error: 'Failed to process chatbot request' });
    }
});

app.listen(6432, () => {
    console.log(`API app listening on port 6432`);
});
