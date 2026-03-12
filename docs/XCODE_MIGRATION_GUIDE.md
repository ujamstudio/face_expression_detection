# 📱 Xcode Project Migration Guide

## ⚠️ Important: Xcode Project Structure

Xcode projects maintain internal references to files. Simply copying files will break these references. Here's the proper way to migrate.

## Current Xcode Project Structure

```
/Users/kim/Desktop/facedetection/
├── facedetection.xcodeproj/       # Project file (contains references)
│   └── project.pbxproj           # Internal project configuration
└── facedetection/                 # Source files
    └── facedetection/
        ├── Assets.xcassets/
        ├── *.swift files
        ├── Info.plist
        └── Python files (server.py, visualizer.py)
```

## Option 1: Keep Xcode Project in Original Location (Recommended)

This is the safest approach - keep iOS project where it is and create unified access.

### Step 1: Create Unified Structure with Links

```bash
# Create unified project directory
mkdir -p /Users/kim/Desktop/EmotionAnalysisSystem

cd /Users/kim/Desktop/EmotionAnalysisSystem

# Create symbolic link to iOS project
ln -s /Users/kim/Desktop/facedetection ios_project

# Create Python backend structure
mkdir -p python/{servers,models,utils,visualization}
mkdir -p data/{raw/streaming,processed,models}
mkdir -p configs scripts docs

# Copy Python files to unified location
cp /Users/kim/Desktop/emotion/src/models/*.py python/models/
cp /Users/kim/Desktop/emotion/scripts/*.py python/servers/
cp /Users/kim/Desktop/emotion/configs/*.yaml configs/
```

### Step 2: Create Unified Launcher

```bash
cat > /Users/kim/Desktop/EmotionAnalysisSystem/launch.command << 'EOF'
#!/bin/bash

# Unified launcher that works with original Xcode location

echo "🚀 Emotion Analysis System Launcher"
echo "===================================="
echo ""
echo "Select option:"
echo "1) Open Xcode Project"
echo "2) Start Emotion Server"
echo "3) Start Visualizer"
echo "4) Check Status"
echo "5) Start All Services"
echo "0) Exit"
echo ""
read -p "Choice: " choice

case $choice in
    1)
        echo "Opening Xcode..."
        open /Users/kim/Desktop/facedetection/facedetection.xcodeproj
        ;;
    2)
        echo "Starting Emotion Server..."
        cd /Users/kim/Desktop/EmotionAnalysisSystem
        python python/servers/simple_server.py
        ;;
    3)
        echo "Starting Visualizer..."
        cd /Users/kim/Desktop/facedetection/facedetection/facedetection
        python visualizer.py --port 8766
        ;;
    4)
        echo "Checking Status..."
        cd /Users/kim/Desktop/emotion
        python master_control.py status
        ;;
    5)
        echo "Starting All Services..."
        # Start emotion server in background
        cd /Users/kim/Desktop/EmotionAnalysisSystem
        python python/servers/simple_server.py &

        # Open Xcode
        open /Users/kim/Desktop/facedetection/facedetection.xcodeproj
        ;;
    0)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        ;;
esac
EOF

chmod +x /Users/kim/Desktop/EmotionAnalysisSystem/launch.command
```

## Option 2: Properly Migrate Xcode Project (Advanced)

If you really want to move the Xcode project, you need to update all file references.

### Step 1: Copy Entire iOS Project

```bash
# Copy entire facedetection directory preserving structure
cp -R /Users/kim/Desktop/facedetection /Users/kim/Desktop/EmotionAnalysisSystem/ios
```

### Step 2: Update File References in Xcode

1. **Open the project in NEW location:**
   ```bash
   open /Users/kim/Desktop/EmotionAnalysisSystem/ios/facedetection.xcodeproj
   ```

2. **Fix Missing Files (Red Files):**
   - In Xcode, you'll see red (missing) files
   - For each red file:
     - Right-click → "Show in Finder"
     - Navigate to the file in new location
     - Confirm the reference

3. **Update Build Settings:**
   - Select project in navigator
   - Go to Build Settings
   - Search for paths containing old location
   - Update any hardcoded paths

4. **Update Info.plist Path:**
   - Build Settings → Search "Info.plist"
   - Update path if needed

5. **Clean and Build:**
   ```
   Product → Clean Build Folder (Shift+Cmd+K)
   Product → Build (Cmd+B)
   ```

## Option 3: Create New Xcode Project References (Cleanest)

Create a new Xcode project that references files in unified structure.

### Step 1: Organize Files First

```bash
# Create organized structure
mkdir -p /Users/kim/Desktop/EmotionAnalysisSystem/ios/Sources/{App,FaceTracking,Networking,Models,Views}

# Copy Swift files to organized locations
cp /Users/kim/Desktop/facedetection/facedetection/facedetection/ContentView.swift \
   /Users/kim/Desktop/EmotionAnalysisSystem/ios/Sources/App/

cp /Users/kim/Desktop/facedetection/facedetection/facedetection/EmotionSelectionView.swift \
   /Users/kim/Desktop/EmotionAnalysisSystem/ios/Sources/App/

cp /Users/kim/Desktop/facedetection/facedetection/facedetection/ARFaceTracking*.swift \
   /Users/kim/Desktop/EmotionAnalysisSystem/ios/Sources/FaceTracking/

cp /Users/kim/Desktop/facedetection/facedetection/facedetection/LiveStreamManager.swift \
   /Users/kim/Desktop/EmotionAnalysisSystem/ios/Sources/Networking/

# Copy resources
cp -R /Users/kim/Desktop/facedetection/facedetection/facedetection/Assets.xcassets \
   /Users/kim/Desktop/EmotionAnalysisSystem/ios/
```

### Step 2: Update Xcode Project to Reference New Locations

1. Open original Xcode project
2. Remove file references (but keep files)
3. Add files from new locations
4. Update folder references to new structure

## Recommended Approach: Hybrid Structure

Keep Xcode where it is, but organize everything else:

```bash
# Final structure
/Users/kim/Desktop/
├── EmotionAnalysisSystem/        # Unified project
│   ├── ios -> ../facedetection   # Symbolic link to iOS
│   ├── python/                   # All Python code
│   │   ├── servers/
│   │   ├── models/
│   │   └── visualization/
│   ├── data/                     # Unified data
│   ├── configs/                  # Configuration
│   ├── scripts/                  # Control scripts
│   └── README.md
│
├── facedetection/                # Original iOS location (unchanged)
│   ├── facedetection.xcodeproj
│   └── facedetection/
│
└── emotion/                      # Can be removed after migration
```

## Update iOS Code for Unified Structure

After migration, update server connection in iOS:

```swift
// LiveStreamManager.swift
// Update to ensure iOS app knows where server is

class LiveStreamManager: ObservableObject {
    // Configuration
    var serverHost: String = "192.168.0.101"  // Your Mac's IP
    var serverPort: UInt16 = 8765

    // Data will save to unified location
    // Server now at: EmotionAnalysisSystem/python/servers/simple_server.py
}
```

## Testing After Migration

### 1. Test Xcode Build
```bash
# Open Xcode project (from original or new location)
open [project location]/facedetection.xcodeproj

# Build project (Cmd+B)
# Run on device (Cmd+R)
```

### 2. Test Server Connection
```bash
# Start server from unified location
cd /Users/kim/Desktop/EmotionAnalysisSystem
python python/servers/simple_server.py

# Server should start on port 8765
# iOS app should connect when running
```

### 3. Verify Data Flow
```bash
# Check if data saves to unified location
ls -la /Users/kim/Desktop/EmotionAnalysisSystem/data/raw/streaming/
```

## Quick Setup Script

```bash
#!/bin/bash
# quick_setup.sh - Set up unified structure with Xcode in place

# Create unified structure
mkdir -p ~/Desktop/EmotionAnalysisSystem/{python,data,configs,scripts}

# Link to iOS project
ln -s ~/Desktop/facedetection ~/Desktop/EmotionAnalysisSystem/ios

# Copy Python files
cp -r ~/Desktop/emotion/src/models ~/Desktop/EmotionAnalysisSystem/python/
cp -r ~/Desktop/emotion/scripts ~/Desktop/EmotionAnalysisSystem/python/

# Create launcher
cat > ~/Desktop/EmotionAnalysisSystem/start.sh << 'EOF'
#!/bin/bash
echo "Starting Emotion Analysis System..."

# Start Python server
python python/servers/simple_server.py &
SERVER_PID=$!

# Open Xcode
open ios/facedetection.xcodeproj

echo "Server PID: $SERVER_PID"
echo "System ready!"
EOF

chmod +x ~/Desktop/EmotionAnalysisSystem/start.sh

echo "✅ Unified structure created!"
echo "📱 Xcode project remains at original location"
echo "🔗 Symbolic link created for unified access"
```

## Important Notes

⚠️ **Don't just copy .xcodeproj** - It contains file references that will break
⚠️ **Test after migration** - Ensure build still works
⚠️ **Keep backups** - Before making changes to Xcode project
✅ **Symbolic links are safe** - They don't modify the original project
✅ **Update server paths** - Python scripts should save to unified data location

The safest approach is Option 1: Keep Xcode in place and create unified access structure!