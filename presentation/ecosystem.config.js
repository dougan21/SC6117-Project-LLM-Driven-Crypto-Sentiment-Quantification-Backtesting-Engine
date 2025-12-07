module.exports = {
    apps: [
        {
            name: 'dashboard',
            script: 'pnpm',
            args: '--filter dashboard start',
            cwd: './',
            interpreter: 'bash',
        },
        {
            name: 'api',
            script: 'pnpm',
            args: '--filter api start',
            cwd: './',
            interpreter: 'bash',
        },
    ],
};
