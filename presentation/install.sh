#!/bin/bash

set -uoe pipefail

sudo cp ./configs/sc6117_demo.conf /etc/nginx/sites-available/sc6117_demo.conf
sudo ln -sf /etc/nginx/sites-available/sc6117_demo.conf /etc/nginx/sites-enabled/sc6117_demo.conf
sudo nginx -s reload

echo "Installation complete."