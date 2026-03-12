# iOS ARKit Data Collection App Guide

This document provides guidance for building the iOS app to collect tri-modal emotion data using ARKit and AVFoundation.

## Overview

The iOS app captures synchronized data streams:
1. **3D Facial Mesh** - ARFaceAnchor vertex positions
2. **Audio** - Synchronized voice recording
3. **Emotion Label** - User-tagged emotion category

## Requirements

- iPhone with TrueDepth camera (iPhone X or later)
- Xcode 14+
- iOS 15.0+ deployment target
- Swift 5.7+

## App Architecture

```
┌─────────────────────────────────┐
│      ARFaceTrackingView         │
│  (ARSCNView for face tracking)  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│    DataCaptureManager           │
│  ┌──────────┐  ┌──────────┐    │
│  │ ARKit    │  │AVFoundation│  │
│  │ Session  │  │  Recorder   │  │
│  └──────────┘  └──────────┘    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│       Data Export               │
│  • face_mesh.json               │
│  • audio.wav                    │
└─────────────────────────────────┘
```

## Implementation Steps

### 1. Create Xcode Project

```bash
# Open Xcode
# File → New → Project
# Select: iOS → App
# Product Name: EmotionCapture
# Interface: SwiftUI
# Language: Swift
```

### 2. Add Required Capabilities

In `Info.plist`, add:

```xml
<key>NSCameraUsageDescription</key>
<string>We need camera access to track facial expressions for emotion recognition</string>

<key>NSMicrophoneUsageDescription</key>
<string>We need microphone access to record audio for emotion analysis</string>

<key>UIRequiredDeviceCapabilities</key>
<array>
    <string>arkit</string>
    <string>front-facing-camera</string>
</array>
```

### 3. Key Components

#### A. ARFaceTrackingViewController.swift

```swift
import ARKit
import AVFoundation

class ARFaceTrackingViewController: UIViewController {

    var sceneView: ARSCNView!
    var audioRecorder: AVAudioRecorder?
    var faceVertices: [[Float]] = []
    var currentEmotion: String = ""
    var isRecording = false

    override func viewDidLoad() {
        super.viewDidLoad()

        // Setup ARSCNView
        sceneView = ARSCNView(frame: view.bounds)
        sceneView.delegate = self
        view.addSubview(sceneView)

        // Setup UI
        setupUI()

        // Request permissions
        requestPermissions()
    }

    func startTracking() {
        guard ARFaceTrackingConfiguration.isSupported else {
            showAlert("TrueDepth camera not available")
            return
        }

        let configuration = ARFaceTrackingConfiguration()
        configuration.isLightEstimationEnabled = true

        sceneView.session.run(configuration)
    }

    func startRecording(emotion: String) {
        currentEmotion = emotion
        isRecording = true
        faceVertices.removeAll()

        // Start audio recording
        setupAudioRecorder()
        audioRecorder?.record()
    }

    func stopRecording() {
        isRecording = false
        audioRecorder?.stop()

        // Export data
        exportData()
    }

    func setupAudioRecorder() {
        let audioFilename = getDocumentsDirectory()
            .appendingPathComponent("recording.wav")

        let settings = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        do {
            audioRecorder = try AVAudioRecorder(url: audioFilename, settings: settings)
        } catch {
            print("Failed to setup audio recorder: \\(error)")
        }
    }

    func exportData() {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let filename = "\\(currentEmotion)_\\(timestamp)"

        // Export face mesh as JSON
        let meshData: [String: Any] = [
            "vertices": faceVertices,
            "timestamp": timestamp,
            "emotion": currentEmotion
        ]

        exportJSON(data: meshData, filename: "\\(filename)_mesh.json")

        // Copy audio file
        let audioURL = getDocumentsDirectory().appendingPathComponent("recording.wav")
        let destURL = getDocumentsDirectory().appendingPathComponent("\\(filename)_audio.wav")

        try? FileManager.default.copyItem(at: audioURL, to: destURL)

        showAlert("Data exported successfully!")
    }

    func exportJSON(data: [String: Any], filename: String) {
        let fileURL = getDocumentsDirectory().appendingPathComponent(filename)

        do {
            let jsonData = try JSONSerialization.data(withJSONObject: data, options: .prettyPrinted)
            try jsonData.write(to: fileURL)
        } catch {
            print("Failed to export JSON: \\(error)")
        }
    }

    func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
}

// MARK: - ARSCNViewDelegate

extension ARFaceTrackingViewController: ARSCNViewDelegate {

    func renderer(_ renderer: SCNSceneRenderer, didUpdate node: SCNNode, for anchor: ARAnchor) {
        guard let faceAnchor = anchor as? ARFaceAnchor else { return }

        if isRecording {
            // Extract vertex positions
            let vertices = faceAnchor.geometry.vertices

            // Convert to array of [x, y, z]
            var vertexArray: [[Float]] = []
            for i in 0..<vertices.count {
                let vertex = vertices[i]
                vertexArray.append([vertex.x, vertex.y, vertex.z])
            }

            // Store (you might want to average over frames)
            faceVertices = vertexArray
        }
    }
}
```

#### B. EmotionSelectionView.swift (SwiftUI)

```swift
import SwiftUI

struct EmotionSelectionView: View {
    let emotions = [
        "neutral", "joy", "sadness", "anger", "fear", "disgust", "surprise",
        "regret", "affection", "resignation", "contentment", "disappointment",
        "nostalgia", "guilt", "pride", "shame", "envy", "gratitude", "hope", "despair"
    ]

    @State private var selectedEmotion: String = "neutral"
    @State private var isRecording = false

    var body: some View {
        VStack {
            Text("Select Emotion")
                .font(.largeTitle)
                .padding()

            // Emotion picker
            Picker("Emotion", selection: $selectedEmotion) {
                ForEach(emotions, id: \\.self) { emotion in
                    Text(emotion.capitalized).tag(emotion)
                }
            }
            .pickerStyle(.wheel)

            // Recording controls
            HStack(spacing: 20) {
                Button(action: {
                    startRecording()
                }) {
                    Label("Start", systemImage: "record.circle")
                        .font(.title2)
                        .foregroundColor(.white)
                        .padding()
                        .background(Color.red)
                        .cornerRadius(10)
                }
                .disabled(isRecording)

                Button(action: {
                    stopRecording()
                }) {
                    Label("Stop", systemImage: "stop.circle")
                        .font(.title2)
                        .foregroundColor(.white)
                        .padding()
                        .background(Color.gray)
                        .cornerRadius(10)
                }
                .disabled(!isRecording)
            }
            .padding()

            if isRecording {
                Text("Recording \\(selectedEmotion)...")
                    .font(.headline)
                    .foregroundColor(.red)
                    .padding()
            }
        }
    }

    func startRecording() {
        isRecording = true
        // Call your ARFaceTrackingViewController's startRecording
    }

    func stopRecording() {
        isRecording = false
        // Call your ARFaceTrackingViewController's stopRecording
    }
}
```

### 4. Data Export Format

**Face Mesh JSON (`regret_2025-01-01T12:00:00Z_mesh.json`):**
```json
{
  "vertices": [
    [0.123, -0.456, 0.789],
    [0.234, -0.345, 0.678],
    ...
  ],
  "timestamp": "2025-01-01T12:00:00Z",
  "emotion": "regret"
}
```

**Audio WAV (`regret_2025-01-01T12:00:00Z_audio.wav`):**
- Format: Linear PCM
- Sample rate: 16000 Hz
- Channels: Mono (1)
- Bit depth: 16-bit

### 5. Best Practices for Data Collection

#### Recording Guidelines:

1. **Duration**: 2-3 seconds per clip
2. **Lighting**: Consistent, frontal lighting
3. **Distance**: 30-50 cm from camera
4. **Expression**: Natural, not exaggerated
5. **Audio**: Clear speech, minimal background noise

#### Emotion Elicitation:

For authentic emotions, use:
- **Regret**: "I should have taken that opportunity..."
- **Affection**: "I really care about you"
- **Resignation**: "Well, there's nothing I can do about it"
- **Contentment**: "This is exactly what I needed"

#### Data Quality Checks:

```swift
func validateCapture(faceAnchor: ARFaceAnchor) -> Bool {
    // Check tracking quality
    guard faceAnchor.isTracked else { return false }

    // Check vertex count (should be ~1220 for ARKit)
    guard faceAnchor.geometry.vertices.count > 1000 else { return false }

    // Check if face is centered
    let transform = faceAnchor.transform
    let position = SIMD3<Float>(transform.columns.3.x,
                                transform.columns.3.y,
                                transform.columns.3.z)

    guard abs(position.x) < 0.2 && abs(position.y) < 0.2 else {
        return false  // Face not centered
    }

    return true
}
```

### 6. Exporting Data to Computer

#### Option 1: AirDrop
```swift
func shareData(urls: [URL]) {
    let activityVC = UIActivityViewController(activityItems: urls, applicationActivities: nil)
    present(activityVC, animated: true)
}
```

#### Option 2: Files App
- Export to `On My iPhone/EmotionCapture/`
- Access via Finder on Mac

#### Option 3: Custom Server Upload
```swift
func uploadData(meshURL: URL, audioURL: URL) {
    // Implement HTTP upload to your server
}
```

## Testing

### Unit Test Checklist:
- [ ] ARFaceTracking initializes correctly
- [ ] Audio recording starts/stops
- [ ] Vertex data is captured (>1000 vertices)
- [ ] JSON export is valid
- [ ] WAV file is playable
- [ ] Files are saved with correct naming

### Integration Test:
1. Launch app
2. Grant camera/microphone permissions
3. Select emotion "joy"
4. Record 3-second clip
5. Verify exported files exist
6. Verify JSON contains vertices array
7. Verify WAV audio is audible

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "TrueDepth not available" | Test on iPhone X or later |
| No vertices captured | Check `isTracked` flag |
| Audio not recording | Check microphone permissions |
| Files not exporting | Check Documents directory permissions |

## Next Steps

After data collection:
1. Transfer files to your Mac
2. Organize by emotion: `data/raw/meshes/regret/clip_0001.json`
3. Run preprocessing pipeline (see main README)
4. Verify data quality before training

## Resources

- [ARKit Face Tracking Documentation](https://developer.apple.com/documentation/arkit/arfaceanchor)
- [AVFoundation Audio Recording](https://developer.apple.com/documentation/avfoundation/avaudiosession)
- [ARKit Sample Code](https://developer.apple.com/documentation/arkit/tracking_and_visualizing_faces)

---

**Note**: This is a reference implementation. Adapt the code to your specific needs and iOS version requirements.
