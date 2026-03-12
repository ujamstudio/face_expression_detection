# 🎯 Quick Server Commands

## Most Used Commands

### Check Status
```bash
./check_servers.sh
```

### Start Emotion Server (iOS Data Collection)
```bash
python scripts/simple_server.py
```

### Stop Emotion Server
```bash
pkill -f simple_server.py
```

### Restart Emotion Server
```bash
./restart_emotion_server.sh
```

### Stop All Servers
```bash
./stop_servers.sh
```

---

## Current Status

Run this to check what's running now:
```bash
./check_servers.sh
```

Output shows:
- ✅ = Running
- ❌ = Not running
- PID = Process ID (use to kill: `kill PID`)

---

## Quick Copy-Paste Commands

```bash
# CHECK
./check_servers.sh

# START
python scripts/simple_server.py

# STOP
pkill -f simple_server.py

# RESTART
./restart_emotion_server.sh

# STOP ALL
./stop_servers.sh
```

---

## Server Purposes

| Server | Port | What it does |
|--------|------|--------------|
| `simple_server.py` | 8765 | Receives iOS app data, saves to `data/streaming/` |
| `visualizer.py` | 8766 | Shows 3D face mesh in real-time |
| `test_server.py` | 8767 | Tests connectivity |

---

## Your Configuration

- **Mac IP:** `192.168.0.101`
- **iOS connects to:** `ws://192.168.0.101:8765`
- **Data saves to:** `/Users/kim/Desktop/emotion/data/streaming/`

---

## If Something Goes Wrong

1. **Port already in use:**
   ```bash
   ./stop_servers.sh
   ./restart_emotion_server.sh
   ```

2. **iOS can't connect:**
   ```bash
   ./check_servers.sh  # Make sure emotion server shows ✅
   ```

3. **Kill everything and restart:**
   ```bash
   ./stop_servers.sh
   python scripts/simple_server.py
   ```