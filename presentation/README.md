# SC6117 - LLM-Driven Crypto Sentiment Quantification & Backtesting Engine

A comprehensive dashboard for cryptocurrency analysis powered by LLM technology, featuring real-time price trends, AI-driven price predictions, and sentiment analysis through news integration.

**Live Demo:** [https://sc6117.chencraft.com](https://sc6117.chencraft.com)

## Features

- **Real-time Crypto Price Trends** - Track cryptocurrency price movements with interactive charts
- **AI Price Predictions** - Machine learning models for predicting future price trends
- **News & Sentiment Analysis** - LLM-powered analysis of cryptocurrency-related news for sentiment quantification
- **Dashboard Interface** - Clean, intuitive UI for visualizing market data and insights
- **RESTful API** - Backend API for data retrieval and processing

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
│   └── dashboard/        # Next.js frontend application
├── ecosystem.config.js   # PM2 configuration
├── turbo.json           # Turbo monorepo configuration
└── package.json         # Root package configuration
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

- `pnpm run dev:dashboard` - Development server
- `pnpm run build:dashboard` - Build dashboard
- `pnpm run start:dashboard` - Start production server

## Services

### Dashboard (Next.js)

- URL: [http://localhost:6234](http://localhost:6234)
- Features: UI components, layouts, pages, and middleware

## Development Notes

- This is a monorepo using Turbo for task orchestration and pnpm for package management
- TypeScript is configured across all packages for type safety
- ESLint and Prettier are configured for code quality and formatting
- Next.js middleware is configured for request handling and authentication flows

## Deployment

The application is currently deployed and available at [https://sc6117.chencraft.com](https://sc6117.chencraft.com)

## Contributing

When contributing, ensure:

- All code follows the existing linting rules
- TypeScript compilation passes
- Tests pass (if applicable)
- Code is formatted with Prettier
