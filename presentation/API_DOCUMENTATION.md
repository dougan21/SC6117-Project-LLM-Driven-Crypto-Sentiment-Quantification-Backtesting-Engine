# API Documentation

This document describes all API endpoints available in the SC6117 Crypto Dashboard application.

## Table of Contents

1. [Chart Data API](#chart-data-api)
2. [News Feed API](#news-feed-api)
3. [Ticker API](#ticker-api)
4. [Chatbot API](#chatbot-api)

---

## Chart Data API

### Overview

The Chart Data API provides cryptocurrency price data with real-time prices, predicted prices, and the percentage difference between them. This endpoint is designed to power the BTC/USD dashboard chart visualization.

## Endpoint

### GET `/api/chart-data`

Returns cryptocurrency price data with real and predicted prices based on query parameters.

#### Request

```bash
GET /api/chart-data?startDateTime=2025-01-01T00:00&endDateTime=2025-01-02T00:00&interval=hourly&smoothing=false HTTP/1.1
Host: localhost:3000
```

#### Query Parameters

| Parameter        | Type      | Required | Default   | Description                                                      |
| ---------------- | --------- | -------- | --------- | ---------------------------------------------------------------- |
| `startDateTime`  | `string`  | No       | -         | Start date and time in ISO 8601 format (YYYY-MM-DDTHH:mm)        |
| `endDateTime`    | `string`  | No       | -         | End date and time in ISO 8601 format (YYYY-MM-DDTHH:mm)          |
| `dataPoints`     | `number`  | No       | `24`      | Number of data points to return (24 hourly, 30 daily, 52 weekly) |
| `cryptoPair`     | `string`  | No       | `BTC/USD` | Cryptocurrency pair (BTC/USD, ETH/USD, XRP/USD)                  |
| `smoothing`      | `boolean` | No       | `false`   | Apply data smoothing filter                                      |
| `showVolatility` | `boolean` | No       | `false`   | Include volatility band calculations                             |

#### Response Body

An array of chart data points based on selected parameters:

```json
[
    {
        "time": "00:00",
        "realPrice": 45234,
        "predictionPrice": 45612,
        "percentDifference": 0.84
    },
    {
        "time": "01:00",
        "realPrice": 45891,
        "predictionPrice": 45234,
        "percentDifference": -1.43
    }
]
```

#### Response Schema

| Field               | Type     | Description                                                                                                                 |
| ------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------- |
| `time`              | `string` | Hour in `HH:00` format (24-hour)                                                                                            |
| `realPrice`         | `number` | Actual cryptocurrency price in USD (integer)                                                                                |
| `predictionPrice`   | `number` | Predicted price by the ML model in USD (integer)                                                                            |
| `percentDifference` | `number` | Percentage difference between prediction and real price, calculated as: `((predictionPrice - realPrice) / realPrice) * 100` |

#### Example Request

```bash
# Get 24 hourly data points for Bitcoin
curl "http://localhost:3000/api/chart-data?dataPoints=24&cryptoPair=BTC%2FUSD"

# Get daily data with custom date range
curl "http://localhost:3000/api/chart-data?startDateTime=2024-12-01T00:00&endDateTime=2024-12-31T23:59&dataPoints=30"

# Get weekly data with smoothing enabled
curl "http://localhost:3000/api/chart-data?dataPoints=52&smoothing=true&showVolatility=true"
```

#### Example Response

```json
[
    {
        "time": "00:00",
        "realPrice": 45000,
        "predictionPrice": 45523,
        "percentDifference": 1.17
    },
    {
        "time": "01:00",
        "realPrice": 46245,
        "predictionPrice": 45812,
        "percentDifference": -0.94
    },
    {
        "time": "02:00",
        "realPrice": 45678,
        "predictionPrice": 46234,
        "percentDifference": 1.22
    }
]
```

#### Error Response

**Status:** `500 Internal Server Error`

```json
{
    "error": "Failed to fetch chart data"
}
```

## Implementation Notes

### Current Implementation

- **Status:** Mock data generation
- **Location:** `src/app/api/chart-data/route.ts`
- **Data Generation:** Uses `generateMockData()` from `src/lib/mock-chart-data.ts`
- **Caching:** Disabled (`Cache-Control: no-store`)

### Integration Points

**Frontend Hook:**

- File: `src/hooks/use-chart-data.ts`
- Function: `useChartData(params?: ChartDataParams)`
- Manages: Loading state, error handling, parameter serialization

**Chart Component:**

- File: `src/app/components/rechart-card.tsx`
- Displays three lines:
    - Real Price (Emerald #10b981)
    - Prediction Price (Violet #8b5cf6)
    - Price Difference % (Amber #f59e0b)

## Future Integration

To replace mock data with actual API:

1. Update the `GET` handler in `src/app/api/chart-data/route.ts` to call your real data source
2. Modify `generateMockData()` in `src/lib/mock-chart-data.ts` or replace the entire function
3. Maintain the response schema structure to avoid client-side changes

Example:

```typescript
// src/app/api/chart-data/route.ts
export async function GET() {
    try {
        const chartData = await fetchFromRealAPI(); // Replace with your API call

        return Response.json(chartData, {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
        });
    } catch (error) {
        return Response.json(
            { error: 'Failed to fetch chart data' },
            { status: 500 }
        );
    }
}
```

## Testing

### Using cURL

```bash
# Basic request
curl http://localhost:3000/api/chart-data

# With parameters
curl "http://localhost:3000/api/chart-data?dataPoints=30&cryptoPair=ETH%2FUSD&smoothing=true"
```

### Using Fetch API

```javascript
// Basic request
const response = await fetch('/api/chart-data');
const data = await response.json();
console.log(data);

// With parameters
const params = new URLSearchParams({
    dataPoints: '30',
    cryptoPair: 'ETH/USD',
    startDateTime: '2024-12-01T00:00',
    endDateTime: '2024-12-31T23:59',
    smoothing: 'true',
});

const response = await fetch(`/api/chart-data?${params}`);
const data = await response.json();
console.log(data);
```

### Using React Hook

```typescript
import { useChartData } from '@/hooks/use-chart-data';

function MyComponent() {
    const { data, loading, error } = useChartData({
        dataPoints: 30,
        cryptoPair: 'BTC/USD',
        startDateTime: '2024-12-01T00:00',
        endDateTime: '2024-12-31T23:59',
        smoothing: true,
        showVolatility: false,
    });

    if (loading) return <p>Loading...</p>;
    if (error) return <p>Error: {error.message}</p>;

    return <div>{/* Use data */}</div>;
}
```

---

## News Feed API

### Overview

The News Feed API provides cryptocurrency news articles with sentiment analysis. Articles include titles, abstracts, timestamps, and AI-generated sentiment indicators (positive, negative, neutral).

### Endpoint

#### GET `/api/news`

Returns a list of cryptocurrency news articles with sentiment analysis.

##### Request

```bash
GET /api/news?limit=10 HTTP/1.1
Host: localhost:3000
```

##### Query Parameters

| Parameter | Type     | Required | Default | Description                                 |
| --------- | -------- | -------- | ------- | ------------------------------------------- |
| `limit`   | `number` | No       | `10`    | Maximum number of news items (capped at 10) |

##### Response Body

An array of news items:

```json
[
    {
        "id": "news-1-1234567890",
        "title": "Bitcoin Reaches New All-Time High",
        "abstract": "Lorem ipsum dolor sit amet, consectetur adipiscing elit...",
        "timestamp": "2025-12-04T10:30:00.000Z",
        "sentiment": "positive"
    },
    {
        "id": "news-2-1234567891",
        "title": "Regulatory Clarity Expected in Q1 2025",
        "abstract": "Duis aute irure dolor in reprehenderit...",
        "timestamp": "2025-12-04T09:15:00.000Z",
        "sentiment": "neutral"
    }
]
```

##### Response Schema

| Field       | Type                                    | Description                                                    |
| ----------- | --------------------------------------- | -------------------------------------------------------------- |
| `id`        | `string`                                | Unique identifier for the news item                            |
| `title`     | `string`                                | News article headline                                          |
| `abstract`  | `string`                                | Brief summary or excerpt from the article                      |
| `timestamp` | `string`                                | Publication time in ISO 8601 format                            |
| `sentiment` | `"positive" \| "negative" \| "neutral"` | AI-analyzed sentiment of the article's impact on crypto market |

##### Example Request

```bash
# Get latest 10 news items
curl "http://localhost:3000/api/news?limit=10"

# Get latest 5 news items
curl "http://localhost:3000/api/news?limit=5"
```

##### Error Response

**Status:** `500 Internal Server Error`

```json
{
    "error": "Failed to fetch news"
}
```

### Implementation Notes

**Current Implementation:**

- **Status:** Mock data generation
- **Location:** `src/app/api/news/route.ts`
- **Data Generation:** Uses `generateMockNews()` from `src/lib/mock-news.ts`
- **Polling:** Frontend polls every 15 seconds via `use-news.ts` hook

**Frontend Hook:**

- File: `src/hooks/use-news.ts`
- Function: `useNews(options?: UseNewsOptions)`
- Features: Auto-refresh every 15 seconds, error handling with fallback to mock data

**Component:**

- File: `src/app/components/news-feed-card.tsx`
- Displays: Scrollable news feed with sentiment emoji indicators

---

## Ticker API

### Overview

The Ticker API provides real-time cryptocurrency price data including current price, 24h change, volume, and high/low values. This endpoint powers the scrolling ticker in the dashboard header.

### Endpoint

#### GET `/api/ticker`

Returns real-time cryptocurrency ticker data.

##### Request

```bash
GET /api/ticker?symbols=BTC,ETH,SOL HTTP/1.1
Host: localhost:3000
```

##### Query Parameters

| Parameter | Type     | Required | Default     | Description                                                          |
| --------- | -------- | -------- | ----------- | -------------------------------------------------------------------- |
| `symbols` | `string` | No       | All symbols | Comma-separated list of cryptocurrency symbols (e.g., "BTC,ETH,SOL") |

##### Response Body

An array of ticker items:

```json
[
    {
        "symbol": "BTC",
        "pair": "USD",
        "price": 42150.75,
        "change": 2.34,
        "volume24h": 28500000000,
        "high24h": 42800.0,
        "low24h": 41200.0
    },
    {
        "symbol": "ETH",
        "pair": "USD",
        "price": 2245.5,
        "change": -0.82,
        "volume24h": 15200000000,
        "high24h": 2280.0,
        "low24h": 2210.0
    }
]
```

##### Response Schema

| Field       | Type     | Description                            |
| ----------- | -------- | -------------------------------------- |
| `symbol`    | `string` | Cryptocurrency symbol (e.g., BTC, ETH) |
| `pair`      | `string` | Trading pair (e.g., USD)               |
| `price`     | `number` | Current price in USD                   |
| `change`    | `number` | 24-hour percentage change              |
| `volume24h` | `number` | 24-hour trading volume in USD          |
| `high24h`   | `number` | Highest price in the last 24 hours     |
| `low24h`    | `number` | Lowest price in the last 24 hours      |

##### Example Request

```bash
# Get all available tickers
curl "http://localhost:3000/api/ticker"

# Get specific symbols
curl "http://localhost:3000/api/ticker?symbols=BTC,ETH,BNB"
```

##### Error Response

**Status:** `500 Internal Server Error`

```json
{
    "error": "Failed to fetch ticker data"
}
```

### Implementation Notes

**Current Implementation:**

- **Status:** Mock data generation with random walk algorithm
- **Location:** `src/app/api/ticker/route.ts`
- **Data Generation:** Uses `generateMockTicker()` from `src/lib/mock-ticker.ts`
- **Simulation:** Realistic price movements using random walk with drift

**Frontend Hook:**

- File: `src/hooks/use-ticker.ts`
- Function: `useTicker(options?: UseTickerOptions)`
- Features: Auto-refresh every 3 seconds for real-time updates

**Component:**

- File: `src/app/components/dashboard-header.tsx`
- Displays: Animated scrolling ticker with price changes and indicators

**Supported Symbols:**

- BTC (Bitcoin)
- ETH (Ethereum)
- BNB (Binance Coin)
- SOL (Solana)
- XRP (Ripple)
- ADA (Cardano)
- DOGE (Dogecoin)

---

## Chatbot API

### Overview

The Chatbot API provides AI-powered conversational assistance for cryptocurrency analysis and market insights. This endpoint handles user messages and returns intelligent responses using pattern matching (to be replaced with full LLM integration).

### Endpoint

#### POST `/api/chatbot`

Sends a message to the chatbot and receives a response.

##### Request

```bash
POST /api/chatbot HTTP/1.1
Host: localhost:3000
Content-Type: application/json

{
    "message": "What's the current Bitcoin trend?",
    "history": [
        {
            "role": "assistant",
            "content": "Hello! How can I help you?",
            "timestamp": "2025-12-04T10:00:00.000Z"
        }
    ]
}
```

##### Request Body Schema

| Field     | Type            | Required | Description                               |
| --------- | --------------- | -------- | ----------------------------------------- |
| `message` | `string`        | Yes      | User's message to the chatbot             |
| `history` | `ChatMessage[]` | No       | Previous conversation history for context |

**ChatMessage Schema:**

| Field       | Type                    | Description          |
| ----------- | ----------------------- | -------------------- |
| `role`      | `"user" \| "assistant"` | Who sent the message |
| `content`   | `string`                | Message content      |
| `timestamp` | `string`                | ISO 8601 timestamp   |

##### Response Body

```json
{
    "message": "Bitcoin is currently showing strong momentum. Based on recent data, the price has been fluctuating between $40,000 and $45,000. Would you like me to analyze specific trends?",
    "timestamp": "2025-12-04T10:00:05.000Z"
}
```

##### Response Schema

| Field       | Type     | Description                           |
| ----------- | -------- | ------------------------------------- |
| `message`   | `string` | Chatbot's response message            |
| `timestamp` | `string` | Response timestamp in ISO 8601 format |

##### Example Request

```bash
curl -X POST "http://localhost:3000/api/chatbot" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about Ethereum",
    "history": []
  }'
```

##### Error Responses

**Status:** `400 Bad Request`

```json
{
    "error": "Message is required"
}
```

**Status:** `500 Internal Server Error`

```json
{
    "error": "Failed to process message"
}
```

### Implementation Notes

**Current Implementation:**

- **Status:** Mock responses using pattern matching
- **Location:** `src/app/api/chatbot/route.ts`
- **Response Generation:** `generateMockChatResponse()` function
- **Patterns:** Recognizes queries about Bitcoin, Ethereum, predictions, sentiment, and general help

**Frontend Hook:**

- File: `src/hooks/use-chatbot.ts`
- Function: `useChatbot()`
- Features: Message history management, loading states, error handling

**Component:**

- File: `src/app/components/chatbot-card.tsx`
- Displays: Interactive chat interface with auto-scroll and form submission

**Supported Query Types:**

- Bitcoin/BTC price and trends
- Ethereum/ETH analysis
- Price predictions and forecasts
- Sentiment analysis and news interpretation
- General help and capabilities

**Future Integration:**

To integrate with a real LLM API (OpenAI, Anthropic, etc.):

1. Replace `generateMockChatResponse()` in `src/app/api/chatbot/route.ts`
2. Add API key configuration
3. Implement proper context management with conversation history
4. Add streaming support for real-time responses
5. Implement rate limiting and error handling

Example integration:

```typescript
// src/app/api/chatbot/route.ts
import OpenAI from 'openai';

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: Request) {
    const { message, history } = await request.json();

    const messages = [
        {
            role: 'system',
            content: 'You are a helpful cryptocurrency analysis assistant...',
        },
        ...history.map((h) => ({ role: h.role, content: h.content })),
        { role: 'user', content: message },
    ];

    const completion = await openai.chat.completions.create({
        model: 'gpt-4',
        messages,
    });

    return Response.json({
        message: completion.choices[0].message.content,
        timestamp: new Date().toISOString(),
    });
}
```

---

## Common Response Headers

All API endpoints include the following headers:

```
Content-Type: application/json
Cache-Control: no-store
```

## Error Handling

All endpoints follow a consistent error response format:

```json
{
    "error": "Error message description"
}
```

Common HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `500` - Internal Server Error

## Rate Limiting

Currently, there is no rate limiting implemented. In production, consider implementing rate limiting to prevent abuse, especially for the Chatbot API which may incur LLM API costs.

## Testing

All endpoints can be tested using the provided `curl` examples or through the frontend React hooks. The frontend automatically handles polling, error states, and fallback to mock data when needed.
