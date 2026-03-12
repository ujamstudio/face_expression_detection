# 🎨 Visualization Guide

## Available Visualization Tools

### 1. Real-time 3D Face Mesh Visualizer
**Location:** `/Users/kim/Desktop/facedetection/facedetection/facedetection/visualizer.py`
**Purpose:** Shows live 3D face mesh with vertices and wireframe

### 2. BlendShapes Data Validator
**Location:** `/Users/kim/Desktop/emotion/scripts/validate_blendshapes.py`
**Purpose:** Analyzes and visualizes BlendShape parameters from saved JSON

### 3. Rule-based Classifier Tester
**Location:** `/Users/kim/Desktop/emotion/scripts/test_rule_classifier.py`
**Purpose:** Visualizes emotion classification results

---

## 🎯 How to Use Each Visualization

### 1. Real-time 3D Face Mesh Visualizer

This shows a live 3D rotating face mesh from the streaming data.

**Start the visualizer:**
```bash
cd /Users/kim/Desktop/facedetection/facedetection/facedetection
python visualizer.py --port 8766
```

**What you'll see:**
- Matplotlib window with 3D face mesh
- Real-time updates as iOS app streams data
- Rotating wireframe view
- ~30 FPS display

**Features:**
- Shows all 1220 vertices
- Wireframe connectivity
- Auto-rotation for better viewing
- Color-coded mesh

**Use cases:**
- Debug face tracking quality
- Verify vertices are captured correctly
- See facial expressions in 3D
- Check mesh deformation

---

### 2. BlendShapes Data Validator

This analyzes saved JSON files and shows BlendShape statistics.

**Validate single file:**
```bash
cd /Users/kim/Desktop/emotion
python scripts/validate_blendshapes.py --file data/streaming/sadness_20251209_145523.json
```

**Validate all files:**
```bash
python scripts/validate_blendshapes.py --dir data/streaming/
```

**What you'll see:**
```
======================================================================
Validating: sadness_20251209_145523.json
======================================================================

✅ Structure validation PASSED

📊 BLENDSHAPES ANALYSIS:
  • Frames: 90
  • Parameters per frame: 52
  • Active features: 12

  Top active features:
    - jawOpen                 : 0.345
    - mouthFrownLeft         : 0.567
    - mouthFrownRight        : 0.554
    - cheekSquintLeft        : 0.423
    - cheekSquintRight       : 0.412

🤖 CLASSIFIER TEST:
  • Expected: sadness
  • Predicted: sadness ✅
  • Confidence: 87.5%
  • Score: 78.2/100
```

---

### 3. Rule-based Classifier Visualization

This shows emotion classification results with score bars.

**Interactive mode:**
```bash
cd /Users/kim/Desktop/emotion
python scripts/test_rule_classifier.py --interactive
```

**Test single file:**
```bash
python scripts/test_rule_classifier.py --input data/streaming/sadness_20251209_145523.json
```

**What you'll see:**
```
======================================================================
分析結果
======================================================================

✨ 予測感情: SADNESS
📊 信頼度: 85.3%
📈 点数: 78.5/100

モ든 感정点수:
  sadness      78.5 │█████████████████████████│ ◀
  fear         23.2 │███████                  │
  neutral      15.7 │█████                    │
  anger        12.3 │████                     │
  joy           5.1 │█                        │

主要 BlendShapes:
  mouthFrownLeft           0.56 │▓▓▓▓▓▓▓▓▓▓▓        │
  mouthFrownRight          0.55 │▓▓▓▓▓▓▓▓▓▓▓        │
  cheekSquintLeft          0.42 │▓▓▓▓▓▓▓▓           │
  jawOpen                  0.34 │▓▓▓▓▓▓             │
```

---

## 📊 Advanced Visualization Options

### Create Custom Visualization

```python
# Load and visualize your data
import json
import matplotlib.pyplot as plt
import numpy as np

# Load data
with open('data/streaming/sadness_20251209_145523.json') as f:
    data = json.load(f)

# Plot BlendShapes over time
blendshapes = data['blendshapes']
frames = range(len(blendshapes))

# Extract specific BlendShape
jaw_values = [frame.get('jawOpen', 0) for frame in blendshapes]
frown_left = [frame.get('mouthFrownLeft', 0) for frame in blendshapes]

# Plot
plt.figure(figsize=(12, 6))
plt.plot(frames, jaw_values, label='Jaw Open')
plt.plot(frames, frown_left, label='Mouth Frown Left')
plt.xlabel('Frame')
plt.ylabel('BlendShape Value')
plt.title('BlendShapes Over Time')
plt.legend()
plt.show()
```

### Visualize Emotion Distribution

```bash
cd /Users/kim/Desktop/emotion
python -c "
import json
import glob
from collections import Counter
import matplotlib.pyplot as plt

# Count emotions
emotions = []
for f in glob.glob('data/streaming/*.json'):
    emotion = f.split('/')[-1].split('_')[0]
    emotions.append(emotion)

counts = Counter(emotions)

# Plot
plt.figure(figsize=(10, 6))
plt.bar(counts.keys(), counts.values())
plt.xlabel('Emotion')
plt.ylabel('Number of Recordings')
plt.title('Collected Data Distribution')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
"
```

---

## 🚀 Quick Visualization Commands

### Start all visualizations:
```bash
# Terminal 1: Start 3D visualizer
cd /Users/kim/Desktop/facedetection/facedetection/facedetection
python visualizer.py --port 8766

# Terminal 2: Validate latest data
cd /Users/kim/Desktop/emotion
python scripts/validate_blendshapes.py --file $(ls -t data/streaming/*.json | head -1)

# Terminal 3: Test classifier interactively
python scripts/test_rule_classifier.py --interactive
```

### Using Master Control:
```bash
cd /Users/kim/Desktop/emotion

# Check everything
python master_control.py status

# Start visualizer
python master_control.py start-viz

# Validate all data
python master_control.py validate

# Test latest recording
python master_control.py test
```

---

## 🎮 Visualization Controls

### For 3D Visualizer (matplotlib window):
- **Rotate:** Click and drag with mouse
- **Zoom:** Scroll wheel or right-click drag
- **Pan:** Middle-click drag
- **Reset:** Home button in toolbar

### For Terminal Visualizations:
- **Scroll:** Use terminal scroll
- **Copy:** Select text and copy
- **Clear:** `clear` or `Cmd+K`

---

## 📈 Visualization Workflow

1. **Collect Data** (iOS App → Server)
   ```bash
   python scripts/simple_server.py
   ```

2. **Real-time View** (During recording)
   ```bash
   python visualizer.py --port 8766
   ```

3. **Post Analysis** (After recording)
   ```bash
   python scripts/validate_blendshapes.py --file data/streaming/latest.json
   python scripts/test_rule_classifier.py --input data/streaming/latest.json
   ```

4. **Batch Analysis** (Multiple files)
   ```bash
   python scripts/test_rule_classifier.py --batch data/streaming/
   ```

---

## 🔧 Troubleshooting Visualization

### Visualizer won't start:
```bash
# Check if port is in use
lsof -i :8766

# Kill if needed
pkill -f visualizer.py

# Try different port
python visualizer.py --port 8767
```

### No data showing:
```bash
# Verify server is running
lsof -i :8765

# Check data exists
ls -la data/streaming/

# Test with sample data
python scripts/test_rule_classifier.py --interactive
```

### Matplotlib issues:
```bash
# Install/update matplotlib
pip install --upgrade matplotlib

# Use different backend
export MPLBACKEND=TkAgg
python visualizer.py --port 8766
```

---

## 📊 Sample Visualization Output

When everything is working, you'll see:

1. **3D Visualizer:** Rotating face mesh in real-time
2. **BlendShape Validator:** Statistics and classification results
3. **Classifier Tester:** Emotion scores with visual bars
4. **Master Control:** Comprehensive system status

All visualization tools are ready to help you analyze the emotion data!