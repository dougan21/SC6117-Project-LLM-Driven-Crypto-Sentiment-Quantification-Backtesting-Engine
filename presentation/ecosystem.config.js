module.exports = {
    apps: [
        {
            name: 'dashboard',
            script: 'pnpm',
            args: '--filter dashboard start',
            cwd: './',
            interpreter: 'bash',
        },
    ],
};
