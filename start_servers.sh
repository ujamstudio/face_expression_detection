#!/bin/bash

echo "🚀 Starting all servers..."

# Start emotion server
echo "Starting emotion data server on port 8765..."
cd /Users/kim/Desktop/emotion
python scripts/simple_server.py &
EMOTION_PID=$!
echo "  PID: $EMOTION_PID"

sleep 2

# Start visualizer
echo "Starting visualizer on port 8766..."
cd /Users/kim/Desktop/facedetection/facedetection/facedetection
python visualizer.py --port 8766 &
VIZ_PID=$!
echo "  PID: $VIZ_PID"

echo ""
echo "✅ All servers started!"
echo "Emotion Server PID: $EMOTION_PID (port 8765)"
echo "Visualizer PID: $VIZ_PID (port 8766)"