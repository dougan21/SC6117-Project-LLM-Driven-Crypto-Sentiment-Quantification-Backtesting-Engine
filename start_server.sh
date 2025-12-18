#!/bin/bash

# init
ARGS=""

# parse script arguments and pass them through to the Python script
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--port) ARGS="$ARGS --port $2"; shift ;;
        -h|--host) ARGS="$ARGS --host $2"; shift ;;
        --reload) ARGS="$ARGS --reload" ;; 
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo "Starting API Server via Python Script..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use virtual environment Python if available, otherwise use system Python
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    "$SCRIPT_DIR/venv/bin/python" api_server.py $ARGS
else
    python api_server.py $ARGS
fi