#!/bin/bash

echo "🛑 Stopping all servers..."

# Kill by port
for port in 8765 8766 8767; do
    echo "Checking port $port..."
    lsof -i :$port | grep python | awk '{print $2}' | while read pid; do
        echo "  Killing PID $pid"
        kill $pid 2>/dev/null
    done
done

# Also kill by name to be sure
pkill -f "simple_server.py|visualizer.py|test_server.py|emotion_server.py|streaming_server.py" 2>/dev/null

echo "✅ All servers stopped!"