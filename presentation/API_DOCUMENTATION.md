# Chart Data API Documentation

## Overview

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
