module.exports = {
    apps: [
        {
            name: 'dashboard',
            script: 'pnpm',
            args: '--filter dashboard start',
            cwd: './',
            interpreter: 'bash',
            env: {
                NODE_ENV: 'production',
            },
        },
        {
            name: 'api',
            script: 'pnpm',
            args: '--filter api start',
            cwd: './',
            interpreter: 'bash',
            env: {
                NODE_ENV: 'production',
                // COINGECKO_API_KEY will be read from apps/api/.env file
                // or you can set it here directly for production:
                // COINGECKO_API_KEY: 'your_production_key_here',
            },
        },
    ],
};
