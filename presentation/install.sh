#!/bin/bash

set -uoe pipefail

git pull

pnpm install

sudo cp ./configs/sc6117_demo.conf /etc/nginx/sites-available/sc6117_demo.conf
sudo cp ./configs/sc6117_api_demo.conf /etc/nginx/sites-available/sc6117_api_demo.conf

sudo ln -sf /etc/nginx/sites-available/sc6117_demo.conf /etc/nginx/sites-enabled/sc6117_demo.conf
sudo ln -sf /etc/nginx/sites-available/sc6117_api_demo.conf /etc/nginx/sites-enabled/sc6117_api_demo.conf

sudo nginx -s reload

pnpm build

pm2 start ./ecosystem.config.js
pm2 save --force

echo "Installation complete."