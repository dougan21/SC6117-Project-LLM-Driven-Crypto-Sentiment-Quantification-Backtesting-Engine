#!/bin/bash

# SC6117 API Server Service Setup Script
# This script installs and configures the systemd service for the API server

SERVICE_NAME="sc6117-api"
SERVICE_FILE="$SERVICE_NAME.service"
SYSTEMD_DIR="/etc/systemd/system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Install the service
install_service() {
    print_info "Installing $SERVICE_NAME service..."
    
    if [ ! -f "$SCRIPT_DIR/$SERVICE_FILE" ]; then
        print_error "Service file $SERVICE_FILE not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Copy service file
    cp "$SCRIPT_DIR/$SERVICE_FILE" "$SYSTEMD_DIR/"
    print_info "Service file copied to $SYSTEMD_DIR/"
    
    # Reload systemd
    systemctl daemon-reload
    print_info "Systemd daemon reloaded"
    
    # Enable service to start on boot
    systemctl enable $SERVICE_NAME
    print_info "Service enabled to start on boot"
    
    print_info "Installation complete!"
}

# Uninstall the service
uninstall_service() {
    print_info "Uninstalling $SERVICE_NAME service..."
    
    # Stop the service if running
    systemctl stop $SERVICE_NAME 2>/dev/null
    
    # Disable the service
    systemctl disable $SERVICE_NAME 2>/dev/null
    
    # Remove service file
    rm -f "$SYSTEMD_DIR/$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_info "Service uninstalled successfully"
}

# Start the service
start_service() {
    print_info "Starting $SERVICE_NAME service..."
    systemctl start $SERVICE_NAME
    sleep 2
    systemctl status $SERVICE_NAME --no-pager
}

# Stop the service
stop_service() {
    print_info "Stopping $SERVICE_NAME service..."
    systemctl stop $SERVICE_NAME
    print_info "Service stopped"
}

# Restart the service
restart_service() {
    print_info "Restarting $SERVICE_NAME service..."
    systemctl restart $SERVICE_NAME
    sleep 2
    systemctl status $SERVICE_NAME --no-pager
}

# Show service status
status_service() {
    systemctl status $SERVICE_NAME --no-pager
}

# Show service logs
logs_service() {
    journalctl -u $SERVICE_NAME -f
}

# Show usage
usage() {
    cat << EOF
Usage: sudo $0 [COMMAND]

Commands:
    install     Install and enable the service
    uninstall   Stop and remove the service
    start       Start the service
    stop        Stop the service
    restart     Restart the service
    status      Show service status
    logs        Show service logs (follow mode)
    help        Show this help message

Examples:
    sudo $0 install         # Install and enable service
    sudo $0 start           # Start the service
    sudo $0 status          # Check service status
    sudo $0 logs            # View live logs
    sudo $0 restart         # Restart the service

After installation, the service will:
  - Start automatically on system boot
  - Restart automatically if it crashes
  - Run on port 8000 by default

To modify port or other settings, edit: $SYSTEMD_DIR/$SERVICE_FILE
Then run: sudo systemctl daemon-reload && sudo systemctl restart $SERVICE_NAME
EOF
}

# Main script logic
case "$1" in
    install)
        check_root
        install_service
        ;;
    uninstall)
        check_root
        uninstall_service
        ;;
    start)
        check_root
        start_service
        ;;
    stop)
        check_root
        stop_service
        ;;
    restart)
        check_root
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        logs_service
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        print_error "Invalid command: $1"
        echo ""
        usage
        exit 1
        ;;
esac
