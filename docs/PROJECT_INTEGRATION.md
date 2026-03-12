# 🔗 Unified Emotion + FaceDetection Project Integration

## Project Structure Overview

```
/Users/kim/Desktop/
├── emotion/                      # Python emotion analysis
│   ├── data/
│   │   └── streaming/           # ← Collected data saves here
│   ├── src/
│   │   └── models/
│   │       ├── rule_based_classifier.py
│   │       ├── facial_feature_detector.py
│   │       └── trimodal_fusion_model.py
│   ├── scripts/
│   │   ├── simple_server.py     # Main data collection server
│   │   ├── validate_blendshapes.py
│   │   └── test_rule_classifier.py
│   └── configs/
│       └── facial_rules.yaml
│
└── facedetection/               # iOS Xcode project
    └── facedetection/
        └── facedetection/
            ├── ARFaceTrackingViewController.swift  # Captures BlendShapes
            ├── LiveStreamManager.swift            # Sends to server
            ├── EmotionSelectionView.swift
            ├── visualizer.py                      # 3D visualization
            └── server.py                          # Alternative server

## Unified System Components

### 1. iOS App (facedetection)
- **Purpose:** Capture face data from iPhone TrueDepth camera
- **Captures:** 3D vertices (1220 points) + BlendShapes (52 parameters)
- **Sends to:** Python server on port 8765

### 2. Python Backend (emotion)
- **Purpose:** Process and classify emotions
- **Receives:** Real-time streaming data
- **Saves to:** `emotion/data/streaming/`
- **Analyzes:** Using rule-based and deep learning models

### 3. Visualization (shared)
- **visualizer.py:** Real-time 3D mesh display
- **Port:** 8766 (to avoid conflict with data server)

---

## 🎯 Complete Workflow

### Step 1: Start Data Collection Server
```bash
cd /Users/kim/Desktop/emotion
python scripts/simple_server.py
# Server runs on port 8765
# Saves to emotion/data/streaming/
```

### Step 2: Start Visualizer (Optional)
```bash
cd /Users/kim/Desktop/facedetection/facedetection/facedetection
python visualizer.py --port 8766
# Opens matplotlib window for 3D visualization
```

### Step 3: Run iOS App
```bash
# In Xcode
open /Users/kim/Desktop/facedetection/facedetection.xcodeproj
# Build and run on iPhone
```

### Step 4: Collect Data
1. Select emotion in iOS app
2. Tap "Start" to record
3. Make facial expression
4. Tap "Stop" after 3 seconds

### Step 5: Process Data
```bash
cd /Users/kim/Desktop/emotion

# Validate captured data
python scripts/validate_blendshapes.py --file data/streaming/sadness_*.json

# Test with classifier
python scripts/test_rule_classifier.py --input data/streaming/sadness_*.json

# Batch process all files
python scripts/test_rule_classifier.py --batch data/streaming/
```

---

## 📁 Key Files Reference

### iOS Side (facedetection)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `ARFaceTrackingViewController.swift` | Face capture | `faceBlendShapes` array captures 52 params |
| `LiveStreamManager.swift` | Network streaming | Sends to `192.168.0.101:8765` |
| `EmotionSelectionView.swift` | UI for emotion selection | 20 emotion options |
| `ContentView.swift` | Main app entry | Navigation and permissions |

### Python Side (emotion)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `simple_server.py` | WebSocket server | Receives and saves data |
| `rule_based_classifier.py` | Emotion classification | 7 basic emotions from BlendShapes |
| `facial_feature_detector.py` | Feature extraction | Detects mouth, eyes, cheeks states |
| `validate_blendshapes.py` | Data validation | Checks JSON structure |
| `test_rule_classifier.py` | Testing classifier | Interactive and batch modes |
| `facial_rules.yaml` | Classification rules | Thresholds and weights |

### Visualization

| File | Purpose | Usage |
|------|---------|-------|
| `visualizer.py` | 3D mesh display | `python visualizer.py --port 8766` |
| `server.py` | Alternative server | Has visualization built-in |

---

## 🔧 Configuration

### Network Settings
```swift
// iOS: LiveStreamManager.swift
var serverHost: String = "192.168.0.101"
var serverPort: UInt16 = 8765
```

```python
# Python: simple_server.py
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8765
DATA_DIR = Path(__file__).parent.parent / "data" / "streaming"
```

### Data Format
```json
{
  "emotion": "sadness",
  "timestamp": "2025-12-09T14:45:23",
  "frame_count": 90,
  "vertices": [[[x,y,z], ...], ...],      // 90 frames × 1220 points
  "blendshapes": [{...}, ...],            // 90 frames × 52 parameters
}
```

---

## 🚀 Quick Start Commands

### Complete Setup
```bash
# 1. Start emotion server
cd /Users/kim/Desktop/emotion
python scripts/simple_server.py

# 2. (Optional) Start visualizer in new terminal
cd /Users/kim/Desktop/facedetection/facedetection/facedetection
python visualizer.py --port 8766

# 3. Build and run iOS app in Xcode

# 4. Check status
cd /Users/kim/Desktop/emotion
./check_servers.sh
```

### Data Processing Pipeline
```bash
# After collecting data
cd /Users/kim/Desktop/emotion

# 1. List collected files
ls -la data/streaming/

# 2. Validate structure
python scripts/validate_blendshapes.py --dir data/streaming/

# 3. Test classification
python scripts/test_rule_classifier.py --batch data/streaming/

# 4. Analyze specific emotion
python scripts/test_rule_classifier.py --input data/streaming/sadness_*.json
```

---

## 📊 Monitoring Tools

### Server Status
```bash
cd /Users/kim/Desktop/emotion
./check_servers.sh
```

### Live Server Output
```bash
# Watch emotion server
# (Server must be in foreground, not background)
python scripts/simple_server.py

# You'll see:
# 🎬 Recording started: sadness
# 📦 Frame 30: 1220 vertices, 52 BlendShapes
# 💾 Saved to: sadness_20251209_145523.json
```

### Data Statistics
```bash
# Count recordings per emotion
cd /Users/kim/Desktop/emotion/data/streaming
for emotion in neutral joy sadness anger fear disgust surprise; do
    count=$(ls -1 ${emotion}_*.json 2>/dev/null | wc -l)
    echo "$emotion: $count recordings"
done
```

---

## 🔄 Development Workflow

### For iOS Development
1. Edit Swift files in Xcode
2. Focus on: `ARFaceTrackingViewController.swift`, `LiveStreamManager.swift`
3. Test on iPhone X or later

### For Python Development
1. Edit in `emotion/src/models/` for classifiers
2. Edit in `emotion/scripts/` for utilities
3. Test with collected data in `emotion/data/streaming/`

### For Integration Testing
1. Run both servers (emotion + visualizer)
2. Connect iOS app
3. Record test data
4. Validate in real-time

---

## 🎯 Combined System Features

### What Works Now
- ✅ iOS captures vertices + BlendShapes
- ✅ Real-time streaming to Python server
- ✅ Data saves to unified location
- ✅ Rule-based emotion classification
- ✅ 3D visualization of face mesh
- ✅ Validation and testing tools

### Data Flow
```
iPhone TrueDepth Camera
    ↓
ARKit (Vertices + BlendShapes)
    ↓
iOS App (LiveStreamManager)
    ↓
WebSocket (port 8765)
    ↓
Python Server (simple_server.py)
    ↓
Save to emotion/data/streaming/
    ↓
Classification & Analysis
```

---

## 📝 Next Steps

1. **Collect Training Data**
   - Record 100+ samples per emotion
   - Use diverse facial expressions
   - Vary lighting and angles

2. **Enhance Classification**
   - Train deep learning model
   - Implement tri-modal fusion
   - Fine-tune rule thresholds

3. **Build Production System**
   - Create unified API
   - Add real-time dashboard
   - Implement batch processing

---

## 🛠 Troubleshooting

### iOS Can't Connect
```bash
# Check server is running
cd /Users/kim/Desktop/emotion
./check_servers.sh

# Verify IP address
ifconfig | grep "inet 192.168"
```

### No BlendShapes in Data
- Rebuild iOS app after code changes
- Ensure iPhone X or later
- Check ARKit permissions

### Server Crashes
```bash
# Restart with error output
cd /Users/kim/Desktop/emotion
python scripts/simple_server.py

# Check Python version (needs 3.x)
python --version

# Reinstall websockets
pip install --upgrade websockets
```

---

## 📞 Support Commands

```bash
# Quick status check
cd /Users/kim/Desktop/emotion && ./check_servers.sh

# View recent recordings
ls -lt data/streaming/ | head -10

# Test latest recording
python scripts/test_rule_classifier.py --input $(ls -t data/streaming/*.json | head -1)

# Count total frames collected
python -c "
import json
import glob
total = 0
for f in glob.glob('data/streaming/*.json'):
    with open(f) as file:
        data = json.load(file)
        total += data.get('frame_count', 0)
print(f'Total frames collected: {total}')
"
```

This unified system combines the best of both projects for complete emotion analysis!