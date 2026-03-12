#!/bin/bash

echo "======================================"
echo "📊 Server Status Check"
echo "======================================"

check_port() {
    local port=$1
    local name=$2
    local result=$(lsof -i :$port 2>/dev/null | grep LISTEN)

    if [ -n "$result" ]; then
        pid=$(echo $result | awk '{print $2}')
        echo "✅ $name (Port $port): RUNNING [PID: $pid]"
    else
        echo "❌ $name (Port $port): NOT RUNNING"
    fi
}

check_port 8765 "Emotion Server"
check_port 8766 "Visualizer    "
check_port 8767 "Test Server   "

echo ""
echo "Your Mac's IP: $(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)"
echo "======================================"