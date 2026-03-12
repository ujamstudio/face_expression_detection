# ✅ Server is Running - Connect Your iOS App Now!

## Current Status
The WebSocket server is running and listening on ALL network interfaces.

## Connection Information

**Your Mac's Network IP:** `192.168.0.101`
**Port:** `8765`
**WebSocket URL for iOS:** `ws://192.168.0.101:8765`

## Update iOS App Configuration

You need to update the iOS app to use your Mac's actual IP address (not localhost/127.0.0.1).

### Method 1: Update LiveStreamManager.swift
Edit `/Users/kim/Desktop/facedetection/facedetection/facedetection/LiveStreamManager.swift`:

```swift
// Find lines 55-56 and update:
var serverHost: String = "192.168.0.101"  // ← YOUR MAC'S IP (not 127.0.0.1!)
var serverPort: UInt16 = 8765
```

### Method 2: Update EmotionSelectionView.swift
Edit `/Users/kim/Desktop/facedetection/facedetection/facedetection/EmotionSelectionView.swift`:

```swift
// Find lines 29-30 and update default values:
@State private var serverIP: String = "192.168.0.101"  // ← YOUR MAC'S IP
@State private var serverPort: String = "8765"
```

### Method 3: Dynamic Configuration in App
If the app has a settings UI for server configuration:
1. Open the iOS app
2. Go to streaming settings
3. Enter Server IP: `192.168.0.101`
4. Enter Port: `8765`
5. Tap Connect

## Verify Connection

### On Your Mac (Server Side)
The server is currently running. When your iPhone connects, you'll see:
```
🔗 Client connected from ('192.168.0.XX', XXXXX)
```

### On Your iPhone (Client Side)
1. Make sure iPhone is on the same Wi-Fi as your Mac
2. Open the iOS app
3. The streaming indicator should show "Connected"
4. Start recording with any emotion

## Test the Full Flow

1. **In iOS App:**
   - Select emotion (e.g., "sadness")
   - Tap "Start" to begin recording
   - Make the facial expression
   - Tap "Stop" after 3 seconds

2. **On Mac Terminal:**
   You should see:
   ```
   🎬 Recording started: sadness
   📊 Frame 0: 1220 vertices, 52 blendshapes
   📊 Frame 30: 1220 vertices, 52 blendshapes
   🛑 Recording stopped: sadness, 90 frames
   💾 Saved recording to data/streaming/sadness_20250109_213945.json
   📈 Recording Analysis:
      Label: sadness
      Predicted: sadness (85% of frames)
      ✅ Correct prediction!
   ```

3. **Check Saved Data:**
   ```bash
   ls -la data/streaming/*.json
   ```

## Common Issues & Solutions

### Still shows "127.0.0.1" or "localhost"?
**Problem:** iOS app is still trying to connect to localhost
**Solution:**
- You MUST update the iOS code to use `192.168.0.101` instead of `127.0.0.1`
- Rebuild and redeploy the app to your iPhone after making changes

### Connection Refused?
**Problem:** iPhone can't reach your Mac
**Solutions:**
1. Verify both devices are on same network:
   - Mac: `ifconfig | grep 192.168`
   - iPhone: Settings > Wi-Fi (check network name)

2. Check server is running:
   ```bash
   lsof -i :8765
   # Should show: python ... TCP *:ultraseek-http (LISTEN)
   ```

3. Test from iPhone's Safari:
   - Open `http://192.168.0.101:8765`
   - Should show error page (that's OK - means it's reachable)

### No BlendShapes in Data?
**Problem:** BlendShapes not appearing in streamed data
**Solution:** The iOS app has been updated to capture BlendShapes. Make sure you:
1. Rebuilt the app after our code changes
2. Are using iPhone X or later with TrueDepth camera

## Server Commands

### Check server status:
```bash
ps aux | grep streaming_server
# Shows: python scripts/streaming_server.py --host 0.0.0.0 --port 8765
```

### View server output:
The server is running in background (PID: 26516). To see live output, you can:
1. Check the terminal where it's running
2. Or restart it in foreground:
   ```bash
   # Kill current server
   kill 26516

   # Start in foreground to see output
   python scripts/streaming_server.py --host 0.0.0.0 --port 8765
   ```

### Stop the server:
```bash
kill 26516
```

## What's Working Now

✅ **Server Status:**
- Listening on `0.0.0.0:8765` (all network interfaces)
- Ready to receive connections from any device on your network
- Will save data to `data/streaming/`
- Has real-time emotion classification

✅ **iOS App Updates:**
- ARFaceTrackingViewController captures BlendShapes
- LiveStreamManager sends BlendShapes with vertices
- JSON export includes both vertices and BlendShapes

✅ **Data Format:**
Each recording will contain:
- 3D vertices (1220 points per frame)
- BlendShapes (52 parameters per frame)
- Emotion label
- Timestamp
- Frame count

## Next Steps

1. **Update iOS app** with IP `192.168.0.101` (not localhost!)
2. **Rebuild and deploy** to iPhone
3. **Test connection** - should see client connect message
4. **Record emotions** - start with the 7 basic emotions
5. **Validate data** using:
   ```bash
   python scripts/validate_blendshapes.py --file data/streaming/[filename].json
   ```

The server is ready and waiting for your iPhone to connect! Just make sure to use `192.168.0.101` instead of `127.0.0.1` in the iOS app.