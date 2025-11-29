#!/bin/bash

set -uoe pipefail

sudo rm -f /etc/nginx/sites-enabled/sc6117_demo.conf
sudo rm -f /etc/nginx/sites-available/sc6117_demo.conf
sudo nginx -s reload

pm2 delete all       
pm2 save --force     

pm2 unstartup systemd

echo "Uninstallation complete."