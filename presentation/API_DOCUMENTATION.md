# API Documentation

This document describes all API endpoints available in the SC6117 Crypto Dashboard application.

## Base URLs

- **Development:** `http://localhost:6432`
- **Production:** `https://sc6117-api.chencraft.com`

## CORS Configuration

The API accepts requests from the following origins:

- `http://localhost:5628`
- `http://localhost:6234`
- `https://sc6117.chencraft.com`

## Table of Contents

1. [Health Check API](#health-check-api)
2. [Chart Data API](#chart-data-api)
3. [News Feed API](#news-feed-api)
4. [Ticker API](#ticker-api)
5. [Chatbot API](#chatbot-api)

---

## Health Check API

### GET `/health`

Health check endpoint to verify the API server is running.

#### Request

```bash
GET /health HTTP/1.1
Host: localhost:6432
```

#### Response

**Status:** `200 OK`

```json
{
    "status": "ok",
    "timestamp": "2025-12-04T12:00:00.000Z"
}
```

#### Example

```bash
curl http://localhost:6432/health
```

---

## Chart Data API

### GET `/api/chart-data`

Returns cryptocurrency price data with real and predicted prices based on query parameters.

#### Request

```bash
GET /api/chart-data?startDateTime=2025-12-03T00:00&endDateTime=2025-12-04T00:00&cryptoPair=BTC/USD HTTP/1.1
Host: localhost:6432
```

#### Query Parameters

| Parameter       | Type     | Required | Description                                               |
| --------------- | -------- | -------- | --------------------------------------------------------- |
| `startDateTime` | `string` | Yes      | Start date and time in ISO 8601 format (YYYY-MM-DDTHH:mm) |
| `endDateTime`   | `string` | Yes      | End date and time in ISO 8601 format (YYYY-MM-DDTHH:mm)   |
| `cryptoPair`    | `string` | Yes      | Cryptocurrency pair (BTC/USD, ETH/USD, XRP/USD)           |

#### Response Body

An array of 24 chart data points:

```json
[
    {
        "time": "00:00",
        "realPrice": 45234,
        "predictionPrice": 45612
    },
    {
        "time": "01:02",
        "realPrice": 45891,
        "predictionPrice": 45234
    }
]
```

#### Response Schema

| Field             | Type     | Description                                                                               |
| ----------------- | -------- | ----------------------------------------------------------------------------------------- |
| `time`            | `string` | Time/date label - format adapts based on time range (HH:MM for ≤24h, YYYY-MM-DD for >24h) |
| `realPrice`       | `number` | Actual cryptocurrency price in USD (integer)                                              |
| `predictionPrice` | `number` | Predicted price by the ML model in USD (integer)                                          |

#### Example Request

```bash
# Get data for Bitcoin (default: last 24 hours)
curl "http://localhost:6432/api/chart-data?cryptoPair=BTC/USD"

# Get data with custom date range for Ethereum
curl "http://localhost:6432/api/chart-data?startDateTime=2025-11-01T00:00&endDateTime=2025-12-01T00:00&cryptoPair=ETH/USD"
```

#### Example Response

```json
[
    {
        "time": "00:00",
        "realPrice": 45000,
        "predictionPrice": 45523
    },
    {
        "time": "01:02",
        "realPrice": 46245,
        "predictionPrice": 45812
    },
    {
        "time": "02:05",
        "realPrice": 45678,
        "predictionPrice": 46234
    }
]
```

#### Implementation Notes

**Current Status:** Mock data generation using `generateMockChartData()` function

**Data Generation Logic:**

- Always returns exactly 24 data points
- Data points are evenly distributed across the selected time range
- **Time formatting:**
    - Time ranges ≤24 hours: HH:MM format (24-hour, e.g., "10:00", "14:30")
    - Time ranges >24 hours: YYYY-MM-DD format (e.g., "2025-11-27", "2025-12-03")
- Uses mathematical functions (sin/cos) for realistic price simulation
- Base opening price: $45,000
- Default range (if not specified): Last 24 hours

**Integration:** Replace `generateMockChartData()` in `apps/api/src/index.ts` with real data source

---

## News Feed API

### GET `/api/news`

Returns a list of cryptocurrency news articles with sentiment analysis.

#### Request

```bash
GET /api/news?limit=10 HTTP/1.1
Host: localhost:6432
```

#### Query Parameters

| Parameter | Type     | Required | Description                  |
| --------- | -------- | -------- | ---------------------------- |
| `limit`   | `number` | Yes      | Maximum number of news items |

#### Response Body

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

#### Response Schema

| Field       | Type                                    | Description                                                    |
| ----------- | --------------------------------------- | -------------------------------------------------------------- |
| `id`        | `string`                                | Unique identifier for the news item                            |
| `title`     | `string`                                | News article headline                                          |
| `abstract`  | `string`                                | Brief summary or excerpt from the article                      |
| `timestamp` | `string`                                | Publication time in ISO 8601 format                            |
| `sentiment` | `"positive" \| "negative" \| "neutral"` | AI-analyzed sentiment of the article's impact on crypto market |

#### Example Request

```bash
# Get latest 10 news items
curl "http://localhost:6432/api/news?limit=10"

# Get latest 5 news items
curl "http://localhost:6432/api/news?limit=5"
```

#### Implementation Notes

**Current Status:** Mock data generation using `generateMockNews()` function

**Data Generation:**

- Generates 10 mock news items with predefined titles and abstracts
- Random timestamps within the last 24 hours
- Predefined sentiment distribution
- **Sorting:** News items are sorted chronologically with newest items first (descending timestamp order)

**Integration:** Replace `generateMockNews()` in `apps/api/src/index.ts` with real news API

---

## Ticker API

### GET `/api/ticker`

Returns real-time cryptocurrency ticker data for all supported symbols.

#### Request

```bash
GET /api/ticker HTTP/1.1
Host: localhost:6432
```

#### Query Parameters

None. The endpoint returns data for all supported symbols.

#### Response Body

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

#### Response Schema

| Field       | Type     | Description                            |
| ----------- | -------- | -------------------------------------- |
| `symbol`    | `string` | Cryptocurrency symbol (e.g., BTC, ETH) |
| `pair`      | `string` | Trading pair (always "USD")            |
| `price`     | `number` | Current price in USD                   |
| `change`    | `number` | 24-hour percentage change              |
| `volume24h` | `number` | 24-hour trading volume in USD          |
| `high24h`   | `number` | Highest price in the last 24 hours     |
| `low24h`    | `number` | Lowest price in the last 24 hours      |

#### Example Request

```bash
curl "http://localhost:6432/api/ticker"
```

#### Implementation Notes

**Current Status:** Mock data generation using `generateMockTicker()` function with stateful random walk algorithm

**Supported Symbols:**

- BTC (Bitcoin) - Base: $42,000
- ETH (Ethereum) - Base: $2,200
- BNB (Binance Coin) - Base: $310
- SOL (Solana) - Base: $95
- XRP (Ripple) - Base: $0.62
- ADA (Cardano) - Base: $0.48
- DOGE (Dogecoin) - Base: $0.087

**Price Simulation:**

- Uses random walk algorithm with drift
- Maintains state between calls for realistic continuous price movement
- Price changes capped between -10% and +10%
- Volume ranges from 500M to 1.5B USD

**Integration:** Replace `generateMockTicker()` in `apps/api/src/index.ts` with real exchange API (e.g., Binance, Coinbase)

---

## Chatbot API

### POST `/api/chatbot`

Sends a message to the chatbot and receives a response.

#### Request

```bash
POST /api/chatbot HTTP/1.1
Host: localhost:6432
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

#### Request Body Schema

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

#### Response Body

```json
{
    "message": "You said: \"What's the current Bitcoin trend?\". This is a mock response. The chatbot feature is under development.",
    "timestamp": "2025-12-04T10:00:05.000Z"
}
```

#### Response Schema

| Field       | Type     | Description                           |
| ----------- | -------- | ------------------------------------- |
| `message`   | `string` | Chatbot's response message            |
| `timestamp` | `string` | Response timestamp in ISO 8601 format |

#### Example Request

```bash
curl -X POST "http://localhost:6432/api/chatbot" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about Ethereum",
    "history": []
  }'
```

#### Error Responses

**Status:** `400 Bad Request`

```json
{
    "error": "Message is required"
}
```

#### Implementation Notes

**Current Status:** Simple mock response that echoes the user's message

**Response Format:** The chatbot currently returns a simple echo response: `You said: "{message}". This is a mock response. The chatbot feature is under development.`

**Integration:** Replace the mock response logic in `apps/api/src/index.ts` with real LLM integration (OpenAI, Anthropic, etc.)

---

## Common Response Headers

All API endpoints return:

```
Content-Type: application/json
```

## Error Handling

Error responses follow this format:

```json
{
    "error": "Error message description"
}
```

HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid parameters)

## Server Configuration

**Port:** 6432

**CORS:** Enabled for the following origins:

- `http://localhost:5628`
- `http://localhost:6234`
- `https://sc6117.chencraft.com`

**Middleware:**

- `express.json()` - Parse JSON request bodies
- `cors()` - Enable CORS with configured origins

## Running the API

**Development:**

```bash
cd apps/api
pnpm dev
```

The server will start on `http://localhost:6432`

**Production:**
Deploy to your hosting service and ensure it's accessible at `https://sc6117-api.chencraft.com`

## Testing

Test all endpoints using curl:

```bash
# Health check
curl http://localhost:6432/health

# Chart data (default: last 24 hours)
curl "http://localhost:6432/api/chart-data?cryptoPair=BTC/USD"

# Chart data with time range
curl "http://localhost:6432/api/chart-data?startDateTime=2025-12-03T00:00&endDateTime=2025-12-04T00:00&cryptoPair=BTC/USD"

# News
curl "http://localhost:6432/api/news?limit=5"

# Ticker
curl http://localhost:6432/api/ticker

# Chatbot
curl -X POST http://localhost:6432/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","history":[]}'
```
