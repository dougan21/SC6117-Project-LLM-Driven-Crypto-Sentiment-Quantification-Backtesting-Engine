#!/bin/bash

set -uoe pipefail

sudo rm -f /etc/nginx/sites-enabled/sc6117_demo.conf
sudo rm -f /etc/nginx/sites-available/sc6117_demo.conf
sudo rm -f /etc/nginx/sites-enabled/sc6117_api_demo.conf
sudo rm -f /etc/nginx/sites-available/sc6117_api_demo.conf

sudo nginx -s reload

pm2 delete ./ecosystem.config.js       
pm2 save --force     

pm2 unstartup systemd

echo "Uninstallation complete."