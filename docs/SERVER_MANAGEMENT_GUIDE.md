# 🚀 Server Management Guide

## Quick Reference

| Server | Port | Purpose | Status Check |
|--------|------|---------|--------------|
| Emotion Data Server | 8765 | iOS app data collection | `lsof -i :8765` |
| Face Visualizer | 8766 | Real-time mesh display | `lsof -i :8766` |
| Test Server | 8767 | Connection testing | `lsof -i :8767` |

---

## 🟢 Starting Servers

### 1. Emotion Data Collection Server (Port 8765)
**Purpose:** Receives data from iOS app and saves to `emotion/data/streaming/`

```bash
# Start the server
cd /Users/kim/Desktop/emotion
python scripts/simple_server.py

# Or run in background
cd /Users/kim/Desktop/emotion
nohup python scripts/simple_server.py > server.log 2>&1 &
```

### 2. Face Mesh Visualizer (Port 8766)
**Purpose:** Real-time 3D visualization of face tracking data

```bash
# Start visualizer
cd /Users/kim/Desktop/facedetection/facedetection/facedetection
python visualizer.py --port 8766

# Or use the helper script
cd /Users/kim/Desktop/emotion
./run_visualizer.sh
```

### 3. Test Server (Port 8767)
**Purpose:** Simple server for testing connectivity

```bash
# Start test server
cd /Users/kim/Desktop/emotion
python scripts/test_server.py --port 8767
```

---

## 🔴 Stopping Servers

### Stop Individual Servers

#### Stop Emotion Server (Port 8765)
```bash
# Method 1: Find and kill by port
lsof -i :8765 | grep python | awk '{print $2}' | xargs kill

# Method 2: Kill by script name
pkill -f simple_server.py

# Method 3: Kill specific PID (check PID first with lsof)
kill [PID]
```

#### Stop Visualizer (Port 8766)
```bash
# Method 1: Find and kill by port
lsof -i :8766 | grep python | awk '{print $2}' | xargs kill

# Method 2: Kill by script name
pkill -f visualizer.py
```

#### Stop Test Server (Port 8767)
```bash
# Method 1: Find and kill by port
lsof -i :8767 | grep python | awk '{print $2}' | xargs kill

# Method 2: Kill by script name
pkill -f test_server.py
```

### Stop All Servers at Once
```bash
# Kill all Python servers on our ports
for port in 8765 8766 8767; do
    lsof -i :$port | grep python | awk '{print $2}' | xargs kill 2>/dev/null
done

# Or kill all our server scripts
pkill -f "simple_server.py|visualizer.py|test_server.py|emotion_server.py|streaming_server.py"
```

---

## 🔄 Restarting Servers

### Restart Emotion Server
```bash
# Kill existing and start new
pkill -f simple_server.py
sleep 1
cd /Users/kim/Desktop/emotion
python scripts/simple_server.py
```

### Restart Visualizer
```bash
# Kill existing and start new
pkill -f visualizer.py
sleep 1
cd /Users/kim/Desktop/facedetection/facedetection/facedetection
python visualizer.py --port 8766
```

---

## 📊 Checking Server Status

### Check All Servers
```bash
# See what's running on our ports
echo "=== Server Status ==="
echo "Port 8765 (Emotion Server):"
lsof -i :8765 2>/dev/null || echo "  Not running"
echo ""
echo "Port 8766 (Visualizer):"
lsof -i :8766 2>/dev/null || echo "  Not running"
echo ""
echo "Port 8767 (Test Server):"
lsof -i :8767 2>/dev/null || echo "  Not running"
```

### Check by Process Name
```bash
# List all running server processes
ps aux | grep -E "simple_server|visualizer|test_server|emotion_server" | grep -v grep
```

### Get Process IDs
```bash
# Get PIDs for all servers
echo "Server PIDs:"
pgrep -f simple_server.py && echo "  simple_server.py: $(pgrep -f simple_server.py)"
pgrep -f visualizer.py && echo "  visualizer.py: $(pgrep -f visualizer.py)"
pgrep -f test_server.py && echo "  test_server.py: $(pgrep -f test_server.py)"
```

---

## 🛠️ Helper Scripts

### Create Start All Script
```bash
cat > /Users/kim/Desktop/emotion/start_servers.sh << 'EOF'
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
EOF

chmod +x /Users/kim/Desktop/emotion/start_servers.sh
```

### Create Stop All Script
```bash
cat > /Users/kim/Desktop/emotion/stop_servers.sh << 'EOF'
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
pkill -f "simple_server.py|visualizer.py|test_server.py|emotion_server.py" 2>/dev/null

echo "✅ All servers stopped!"
EOF

chmod +x /Users/kim/Desktop/emotion/stop_servers.sh
```

### Create Status Check Script
```bash
cat > /Users/kim/Desktop/emotion/check_servers.sh << 'EOF'
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
EOF

chmod +x /Users/kim/Desktop/emotion/check_servers.sh
```

---

## 🎯 Common Workflows

### For iOS Data Collection
```bash
# 1. Check status
./check_servers.sh

# 2. Start emotion server if needed
python scripts/simple_server.py

# 3. Connect iOS app and record

# 4. Check saved data
ls -la data/streaming/
```

### For Visualization Testing
```bash
# 1. Start both servers
./start_servers.sh

# 2. Connect iOS app for live visualization

# 3. Stop when done
./stop_servers.sh
```

### For Debugging Connection Issues
```bash
# 1. Stop everything
./stop_servers.sh

# 2. Start test server
python scripts/test_server.py --port 8765

# 3. Test iOS connection

# 4. If working, switch to emotion server
pkill -f test_server.py
python scripts/simple_server.py
```

---

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Find what's using the port
lsof -i :8765

# Force kill if needed
lsof -i :8765 | grep python | awk '{print $2}' | xargs kill -9
```

### Server Won't Start
```bash
# Check if port is blocked by firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Check if another process is using the port
netstat -an | grep 8765
```

### iOS App Can't Connect
```bash
# 1. Verify server is running
lsof -i :8765

# 2. Check your IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 3. Ensure iOS app has correct IP in LiveStreamManager.swift
```

### Server Crashes Immediately
```bash
# Run in foreground to see errors
python scripts/simple_server.py

# Check Python version (should be 3.x)
python --version

# Check websockets is installed
pip list | grep websockets
```

---

## 📝 Quick Commands Cheatsheet

```bash
# START
python scripts/simple_server.py          # Start emotion server
./run_visualizer.sh                      # Start visualizer
./start_servers.sh                       # Start all

# STOP
pkill -f simple_server.py                # Stop emotion server
pkill -f visualizer.py                   # Stop visualizer
./stop_servers.sh                        # Stop all

# CHECK
./check_servers.sh                       # Check all status
lsof -i :8765                           # Check specific port
ps aux | grep simple_server             # Check specific process

# RESTART
./stop_servers.sh && ./start_servers.sh  # Restart all
```

---

## 📍 Current Configuration

- **Your Mac's IP:** `192.168.0.101`
- **Emotion Server Port:** `8765`
- **Visualizer Port:** `8766`
- **Data Location:** `/Users/kim/Desktop/emotion/data/streaming/`
- **iOS App Target:** `ws://192.168.0.101:8765`