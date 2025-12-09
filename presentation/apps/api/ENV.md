# API Server - Environment Variables

## Development Setup

The API server uses environment variables for configuration. Create a `.env` file in this directory (`apps/api/`):

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual API key
nano .env
```

### Required Variables

- `COINGECKO_API_KEY`: Your CoinGecko API key (get from <https://www.coingecko.com/en/api/pricing>)

## Production Deployment

For production, set environment variables directly in your process manager or hosting platform:

### PM2 (ecosystem.config.js)

```javascript
module.exports = {
    apps: [
        {
            name: 'api',
            script: './apps/api/dist/index.js',
            cwd: '/path/to/presentation',
            env: {
                NODE_ENV: 'production',
                COINGECKO_API_KEY: 'your_production_key_here',
            },
        },
    ],
};
```

### systemd service

```ini
[Service]
Environment="COINGECKO_API_KEY=your_production_key_here"
```

### Docker

```dockerfile
ENV COINGECKO_API_KEY=your_production_key_here
```

Or use docker-compose:

```yaml
environment:
    - COINGECKO_API_KEY=${COINGECKO_API_KEY}
```

## Security Notes

- **Never commit `.env` files** to version control (already in `.gitignore`)
- Use different API keys for development and production
- In production, prefer environment variables over `.env` files
- Rotate API keys periodically
- Monitor API usage to detect unauthorized access
