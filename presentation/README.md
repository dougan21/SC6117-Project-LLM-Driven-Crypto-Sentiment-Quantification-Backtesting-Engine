# SC6117 - LLM-Driven Crypto Sentiment Quantification & Backtesting Engine

A comprehensive dashboard for cryptocurrency analysis powered by LLM technology, featuring real-time price trends, AI-driven price predictions, and sentiment analysis through news integration.

**Live Demo:** [https://sc6117.chencraft.com](https://sc6117.chencraft.com)

## Features

### Trading Strategy Analysis

- **Buy & Hold vs Active Strategy Comparison** - Interactive chart comparing passive holding strategy against active trading
- **Trading Events Visualization** - Hover over chart data points to view buy/sell actions and technical triggers
- **Real-time Data Updates** - Chart data refreshes with configurable time ranges and cryptocurrency pairs
- **Technical Indicators** - Events triggered by MA (Moving Average), RSI, and momentum indicators

### Market Intelligence

- **Real-time Cryptocurrency Ticker** - Live price updates for BTC, ETH, BNB, SOL, XRP, ADA, DOGE
- **News Feed with Sentiment Analysis** - AI-powered sentiment classification (positive/negative/neutral)
- **AI Chatbot** - Interactive assistant for cryptocurrency queries and market insights
- **Multi-timeframe Analysis** - Support for hourly, daily, and monthly data views

### Dashboard Interface

- **Modern UI Design** - Built with Next.js 15, React 19, and Tailwind CSS
- **Responsive Layout** - Optimized for desktop and mobile viewing
- **Dark Mode Support** - Theme toggle for comfortable viewing
- **Interactive Components** - Hover tooltips, real-time updates, and smooth animations

### RESTful API

- **Mock Data Mode** - Development-friendly simulated data for rapid prototyping
- **Relay Mode** - Production-ready request forwarding to actual data sources
- **OpenAPI/Swagger Documentation** - Interactive API documentation at `/api-docs`
- **Flexible Configuration** - Centralized config for switching between mock and real data
- **Error Handling** - Comprehensive error responses and logging

## Tech Stack

- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS, Radix UI
- **Backend:** Express.js, TypeScript, Node.js 22
- **Monorepo:** Turbo, pnpm
- **Process Management:** PM2
- **Build Tools:** ESLint, Prettier, TypeScript Compiler

## Project Structure

```sh
presentation/
├── apps/
│   ├── dashboard/              # Next.js frontend application
│   └── api/                    # Express.js backend API
├── ecosystem.config.js         # PM2 configuration
├── turbo.json                  # Turbo monorepo configuration
└── package.json                # Root package configuration
```

## Getting Started

### Prerequisites

- Node.js 22.x
- pnpm 10.x

### Installation

```bash
# Install dependencies
pnpm install

# Build all packages
pnpm run build

# Or build specific packages
pnpm run build:dashboard
```

### Development

Start development servers for all packages:

```bash
pnpm run dev
```

Or start specific services:

```bash
pnpm run dev:dashboard # Start Dashboard on port 3000
```

### Production

Build and start all services:

```bash
pnpm run build:dashboard
pnpm run start:all
```

Or use PM2 for process management:

```bash
pm2 start ecosystem.config.js
pm2 logs          # View logs
pm2 status        # Check status
pm2 stop all      # Stop all processes
pm2 delete all    # Remove all processes
```

## Available Scripts

### Root Level

- `pnpm run dev` - Start development servers
- `pnpm run build` - Build all packages
- `pnpm run start:all` - Start all services in production
- `pnpm run typecheck` - Type check all packages
- `pnpm run lint` - Lint all files
- `pnpm run lint:fix` - Fix linting issues
- `pnpm run format` - Format code with Prettier

### Dashboard Specific

- `pnpm run dev:dashboard` - Development server (port 5628)
- `pnpm run build:dashboard` - Build dashboard for production
- `pnpm run start:dashboard` - Start production server (port 6234)

### API Specific

- `pnpm run dev:api` - Development server with hot reload (port 6432)
- `pnpm run build:api` - Build API and copy OpenAPI spec to dist
- `pnpm run start:api` - Start production server (port 6432)

## Services

### Dashboard (Next.js)

- **Development URL:** [http://localhost:5628](http://localhost:5628)
- **Production URL:** [http://localhost:6234](http://localhost:6234)
- **Live URL:** [https://sc6117.chencraft.com](https://sc6117.chencraft.com)
- **Features:**
    - Interactive trading strategy comparison chart (Buy & Hold vs Active Strategy)
    - Real-time cryptocurrency ticker (BTC, ETH, BNB, SOL, XRP, ADA, DOGE)
    - News feed with sentiment analysis (positive/negative/neutral)
    - AI chatbot for crypto queries
    - Dark mode support
    - Responsive design

### API (Express.js)

- **Development URL:** [http://localhost:6432](http://localhost:6432)
- **Production URL:** [https://sc6117-api.chencraft.com](https://sc6117-api.chencraft.com)
- **Swagger UI:** [https://sc6117-api.chencraft.com](https://sc6117-api.chencraft.com/api-docs)
- **Endpoints:**
    - `GET /health` - Health check endpoint
    - `GET /api/chart-data` - Trading strategy comparison data (24 data points)
    - `GET /api/news` - Cryptocurrency news with sentiment analysis
    - `GET /api/ticker` - Real-time ticker data for 7 cryptocurrencies
    - `POST /api/chatbot` - AI chatbot message processing
- **Features:**
    - Mock data mode for development
    - Relay mode for production (configurable in `config.ts`)
    - OpenAPI/Swagger documentation
    - CORS enabled for dashboard origins
    - Error handling and logging

### API Configuration

The API supports two operational modes controlled by `apps/api/src/config.ts`:

1. **Mock Data Mode (Default)**

    ```typescript
    useActualServer: false; // Uses simulated data
    ```

2. **Relay Mode**

    ```typescript
    useActualServer: true   // Relays to remote servers
    remoteServers: {
        server1: 'https://api.example.com',  // Configure actual server
        server2: '',  // Optional fallback
        server3: '',  // Optional fallback
    }
    ```

## Development Notes

### Architecture

- **Monorepo Structure** - Using Turbo for task orchestration and pnpm for package management
- **TypeScript** - Configured across all packages for type safety
- **Code Quality** - ESLint and Prettier configured for consistent formatting
- **Process Management** - PM2 with ecosystem.config.js for production deployment

### Recent Updates

#### Chart Data Improvements

- Renamed `realPrice` → `holdValue` (buy-and-hold strategy value)
- Renamed `predictionPrice` → `strategyValue` (active trading strategy value)
- Added `events` array to track trading actions (BUY/SELL) with technical triggers
- Enhanced tooltips to display trading events on hover
- Updated all API endpoints, hooks, and components to reflect new naming

#### API Infrastructure

- **Swagger UI Integration** - Interactive API documentation at `/api-docs`
- **Centralized Configuration** - `config.ts` with `useActualServer` flag and remote server settings
- **Relay Mode** - Ability to forward requests to actual data sources
- **Mock Data Generators** - Realistic simulation for development
    - Chart data with random walk algorithm
    - News with sentiment analysis
    - Ticker with continuous price updates
    - Chatbot with pattern-matched responses

#### Data Models

```typescript
// Chart Data Point
{
    time: string;              // HH:MM or YYYY-MM-DD
    holdValue: number;         // Buy-and-hold portfolio value
    strategyValue: number;     // Active trading portfolio value
    events?: TradingEvent[];   // Optional trading actions
}

// Trading Event
{
    timestamp: string;         // ISO 8601 format
    action: string;            // "BUY" or "SELL"
    trigger: string;           // Technical indicator reason
}
```

### API Development

To switch between mock and real data:

1. Edit `apps/api/src/config.ts`
2. Set `useActualServer: true` for relay mode
3. Configure `server1` with your actual API URL
4. Rebuild: `pnpm run build:api`
5. Restart: `pm2 restart api`

### Documentation

- **API Documentation** - See `API_DOCUMENTATION.md` for detailed endpoint specifications
- **OpenAPI Spec** - `openapi.yaml` contains the full API specification
- **Swagger UI** - Interactive testing available at `/api-docs` endpoint

## Deployment

The application is currently deployed and available at [https://sc6117.chencraft.com](https://sc6117.chencraft.com)

## Contributing

When contributing, ensure:

- All code follows the existing linting rules
- TypeScript compilation passes
- Tests pass (if applicable)
- Code is formatted with Prettier
