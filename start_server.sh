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

python api_server.py $ARGS