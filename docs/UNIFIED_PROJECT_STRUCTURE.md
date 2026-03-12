# 🏗️ Unified Project Structure Plan

## Current Separate Structure

```
/Users/kim/Desktop/
├── emotion/                     # Python project
│   ├── data/
│   ├── scripts/
│   ├── src/
│   └── configs/
│
└── facedetection/              # iOS Xcode project
    └── facedetection/
        └── facedetection/
            ├── *.swift files
            ├── visualizer.py
            └── server.py
```

## Proposed Unified Structure

```
/Users/kim/Desktop/EmotionAnalysisSystem/
│
├── README.md                    # Project overview
├── requirements.txt             # Python dependencies
├── .gitignore
│
├── ios/                         # iOS Application
│   ├── facedetection.xcodeproj
│   └── facedetection/
│       ├── App/
│       │   ├── ContentView.swift
│       │   ├── EmotionSelectionView.swift
│       │   └── facedetectionApp.swift
│       ├── FaceTracking/
│       │   ├── ARFaceTrackingViewController.swift
│       │   └── ARFaceTrackingView.swift
│       ├── Networking/
│       │   └── LiveStreamManager.swift
│       ├── Models/
│       │   └── EmotionData.swift
│       └── Info.plist
│
├── python/                      # Python Backend
│   ├── __init__.py
│   ├── servers/
│   │   ├── emotion_server.py   # Main WebSocket server
│   │   ├── simple_server.py    # Lightweight server
│   │   └── test_server.py      # Testing server
│   ├── models/
│   │   ├── __init__.py
│   │   ├── rule_based_classifier.py
│   │   ├── facial_feature_detector.py
│   │   └── trimodal_fusion_model.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validate_blendshapes.py
│   │   └── data_processor.py
│   └── visualization/
│       ├── __init__.py
│       ├── face_mesh_visualizer.py
│       └── emotion_dashboard.py
│
├── data/                        # Shared Data Storage
│   ├── raw/                    # Raw recordings
│   │   └── streaming/
│   ├── processed/              # Processed data
│   └── models/                # Trained models
│
├── configs/                    # Configuration Files
│   ├── network_config.yaml    # Server/client settings
│   ├── facial_rules.yaml      # Emotion rules
│   └── model_config.yaml      # Model parameters
│
├── scripts/                    # Utility Scripts
│   ├── setup.sh               # Environment setup
│   ├── start_all.sh           # Start all services
│   ├── stop_all.sh            # Stop all services
│   ├── check_status.sh        # Check system status
│   └── master_control.py      # Python master control
│
├── tests/                      # Test Suite
│   ├── test_classifier.py
│   ├── test_server.py
│   └── test_data/
│
├── docs/                       # Documentation
│   ├── API.md
│   ├── SETUP.md
│   ├── USAGE.md
│   └── TROUBLESHOOTING.md
│
└── notebooks/                  # Jupyter Notebooks
    ├── data_exploration.ipynb
    ├── model_training.ipynb
    └── analysis_results.ipynb
```

## Migration Steps

### Step 1: Create New Unified Directory
```bash
# Create main project directory
mkdir -p /Users/kim/Desktop/EmotionAnalysisSystem
cd /Users/kim/Desktop/EmotionAnalysisSystem

# Create subdirectories
mkdir -p ios python/{servers,models,utils,visualization}
mkdir -p data/{raw/streaming,processed,models}
mkdir -p configs scripts tests docs notebooks
```

### Step 2: Move iOS Files
```bash
# Copy iOS project (preserving Xcode structure)
cp -r /Users/kim/Desktop/facedetection/facedetection.xcodeproj ios/
cp -r /Users/kim/Desktop/facedetection/facedetection ios/

# Organize Swift files by functionality
mkdir -p ios/facedetection/App
mkdir -p ios/facedetection/FaceTracking
mkdir -p ios/facedetection/Networking
mkdir -p ios/facedetection/Models

# Move files to appropriate folders
mv ios/facedetection/ContentView.swift ios/facedetection/App/
mv ios/facedetection/EmotionSelectionView.swift ios/facedetection/App/
mv ios/facedetection/ARFaceTracking*.swift ios/facedetection/FaceTracking/
mv ios/facedetection/LiveStreamManager.swift ios/facedetection/Networking/
```

### Step 3: Move Python Files
```bash
# Copy Python emotion files
cp -r /Users/kim/Desktop/emotion/src/models/* python/models/
cp /Users/kim/Desktop/emotion/scripts/simple_server.py python/servers/
cp /Users/kim/Desktop/emotion/scripts/test_server.py python/servers/
cp /Users/kim/Desktop/emotion/scripts/validate_blendshapes.py python/utils/

# Move visualization
cp /Users/kim/Desktop/facedetection/facedetection/facedetection/visualizer.py python/visualization/face_mesh_visualizer.py

# Copy configs
cp /Users/kim/Desktop/emotion/configs/* configs/

# Copy existing data
cp -r /Users/kim/Desktop/emotion/data/streaming/* data/raw/streaming/

# Copy scripts
cp /Users/kim/Desktop/emotion/*.sh scripts/
cp /Users/kim/Desktop/emotion/master_control.py scripts/
```

### Step 4: Update Import Paths

#### Python Files
```python
# Update imports in Python files
# Old: from src.models.rule_based_classifier import ...
# New: from python.models.rule_based_classifier import ...

# Or add to PYTHONPATH
export PYTHONPATH=/Users/kim/Desktop/EmotionAnalysisSystem:$PYTHONPATH
```

#### iOS Files
```swift
// Update server connection in LiveStreamManager.swift
var serverHost: String = "192.168.0.101"
var serverPort: UInt16 = 8765
```

### Step 5: Create Unified Configuration

Create `configs/network_config.yaml`:
```yaml
server:
  host: 0.0.0.0
  port: 8765
  data_dir: ../data/raw/streaming

client:
  ios_ip: 192.168.0.101
  ios_port: 8765

visualization:
  port: 8766
  fps: 30
```

### Step 6: Create Master Launcher

Create `scripts/launch.py`:
```python
#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def start_emotion_server():
    os.chdir(PROJECT_ROOT / 'python/servers')
    subprocess.run(['python', 'emotion_server.py'])

def start_visualizer():
    os.chdir(PROJECT_ROOT / 'python/visualization')
    subprocess.run(['python', 'face_mesh_visualizer.py'])

# Add more functions as needed
```

## Benefits of Unified Structure

1. **Single Project Root** - Everything in one place
2. **Clear Separation** - iOS, Python, Data clearly separated
3. **Shared Resources** - Data and configs accessible to both
4. **Easier Deployment** - Single repository to manage
5. **Better Organization** - Logical grouping of functionality
6. **Scalability** - Easy to add new components

## Commands After Migration

```bash
cd /Users/kim/Desktop/EmotionAnalysisSystem

# Start emotion server
python python/servers/emotion_server.py

# Start visualizer
python python/visualization/face_mesh_visualizer.py

# Run iOS app
open ios/facedetection.xcodeproj

# Check status
python scripts/master_control.py status

# Access data
ls data/raw/streaming/
```

## Git Repository Setup

```bash
cd /Users/kim/Desktop/EmotionAnalysisSystem
git init
echo "*.pyc" >> .gitignore
echo "data/raw/" >> .gitignore
echo ".DS_Store" >> .gitignore
git add .
git commit -m "Initial unified project structure"
```

## Environment Setup

Create `requirements.txt`:
```
websockets>=10.0
numpy>=1.21.0
matplotlib>=3.5.0
pyyaml>=6.0
tensorflow>=2.13.0
transformers>=4.30.0
librosa>=0.10.0
soundfile>=0.12.0
```

## Docker Support (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "python/servers/emotion_server.py"]
```

This unified structure will make your project more maintainable and professional!