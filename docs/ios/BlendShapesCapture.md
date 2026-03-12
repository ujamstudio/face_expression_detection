# iOS 앱에 BlendShapes 캡처 추가하기

기존 iOS 앱에 ARKit BlendShapes 캡처 기능을 추가하는 방법입니다.

## 변경사항 요약

1. **DataCaptureManager.swift** 수정 - BlendShapes 데이터 캡처
2. **JSON 저장 형식** 확장 - 정점 + BlendShapes
3. **UI 업데이트** - BlendShapes 실시간 표시 (선택사항)

---

## 1. DataCaptureManager.swift 수정

### 기존 코드에 추가할 부분:

```swift
import ARKit
import AVFoundation

class DataCaptureManager: NSObject, ObservableObject {
    // ... 기존 변수들 ...

    // ⭐ 추가: BlendShapes 저장
    private var capturedBlendShapes: [String: NSNumber] = [:]

    // MARK: - 얼굴 메쉬 캡처 (수정)
    func captureFaceMesh(faceAnchor: ARFaceAnchor) {
        guard isCapturing else { return }

        // 1. 정점 데이터 (기존)
        let vertices = faceAnchor.geometry.vertices
        var vertexArray: [[Float]] = []
        for i in 0..<vertices.count {
            let vertex = vertices[i]
            vertexArray.append([vertex.x, vertex.y, vertex.z])
        }
        capturedVertices = vertexArray

        // ⭐ 2. BlendShapes 데이터 (새로 추가)
        if let blendShapes = faceAnchor.blendShapes as? [ARFaceAnchor.BlendShapeLocation: NSNumber] {
            // BlendShapes를 String 키로 변환
            var blendShapeDict: [String: NSNumber] = [:]

            for (key, value) in blendShapes {
                blendShapeDict[key.rawValue] = value
            }

            capturedBlendShapes = blendShapeDict
        }
    }

    // MARK: - 데이터 저장 (수정)
    private func saveFaceMesh(filename: String) {
        // ⭐ BlendShapes 포함하여 저장
        let meshData: [String: Any] = [
            "vertices": capturedVertices,
            "blendshapes": capturedBlendShapes,  // 추가!
            "timestamp": ISO8601DateFormatter().string(from: captureStartTime ?? Date()),
            "emotion": currentEmotion
        ]

        let fileURL = getDocumentsDirectory().appendingPathComponent(filename)

        do {
            let jsonData = try JSONSerialization.data(withJSONObject: meshData, options: .prettyPrinted)
            try jsonData.write(to: fileURL)
            print("✅ Face mesh with BlendShapes saved: \(filename)")
        } catch {
            print("❌ Failed to save face mesh: \(error)")
        }
    }

    // ... 나머지 코드 ...
}
```

---

## 2. 저장되는 JSON 형식

### 수정 전 (정점만):
```json
{
  "vertices": [
    [0.123, -0.456, 0.789],
    [0.234, -0.345, 0.678],
    ...
  ],
  "timestamp": "2025-01-21T12:00:00Z",
  "emotion": "sadness"
}
```

### 수정 후 (정점 + BlendShapes):
```json
{
  "vertices": [
    [0.123, -0.456, 0.789],
    [0.234, -0.345, 0.678],
    ...
  ],
  "blendshapes": {
    "eyeBlinkLeft": 0.0,
    "eyeBlinkRight": 0.0,
    "eyeWideLeft": 0.0,
    "eyeWideRight": 0.0,
    "jawOpen": 0.3,
    "mouthFrownLeft": 0.5,
    "mouthFrownRight": 0.5,
    "cheekSquintLeft": 0.4,
    "cheekSquintRight": 0.4,
    ... (총 52개)
  },
  "timestamp": "2025-01-21T12:00:00Z",
  "emotion": "sadness"
}
```

---

## 3. 실시간 BlendShapes 표시 (선택사항)

사용자가 녹화 중 자신의 표정을 확인할 수 있도록 UI에 표시:

### BlendShapesDebugView.swift (새 파일)

```swift
import SwiftUI

struct BlendShapesDebugView: View {
    let blendshapes: [String: NSNumber]

    // 주요 BlendShapes만 표시
    let keyBlendShapes = [
        "jawOpen", "mouthSmileLeft", "mouthSmileRight",
        "mouthFrownLeft", "mouthFrownRight",
        "eyeBlinkLeft", "eyeBlinkRight",
        "cheekSquintLeft", "cheekSquintRight",
        "browDownLeft", "browDownRight"
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("표정 분석")
                .font(.caption)
                .fontWeight(.bold)

            ForEach(keyBlendShapes, id: \.self) { key in
                if let value = blendshapes[key] {
                    HStack {
                        Text(key)
                            .font(.caption2)
                            .frame(width: 120, alignment: .leading)

                        ProgressView(value: value.doubleValue, total: 1.0)
                            .frame(width: 80)

                        Text(String(format: "%.2f", value.doubleValue))
                            .font(.caption2)
                            .monospacedDigit()
                    }
                }
            }
        }
        .padding(8)
        .background(Color.black.opacity(0.7))
        .cornerRadius(8)
    }
}
```

### ContentView.swift에 추가:

```swift
struct ContentView: View {
    @StateObject private var captureManager = DataCaptureManager()
    // ...

    var body: some View {
        ZStack {
            ARFaceTrackingView(captureManager: captureManager)

            VStack {
                // ⭐ BlendShapes 디버그 뷰 추가
                if !captureManager.capturedBlendShapes.isEmpty {
                    BlendShapesDebugView(blendshapes: captureManager.capturedBlendShapes)
                        .padding()
                }

                Spacer()

                // 기존 UI들...
            }
        }
    }
}
```

---

## 4. 주요 BlendShapes 목록

ARKit는 총 52개의 BlendShapes를 제공합니다:

### 눈 (Eyes)
- `eyeBlinkLeft`, `eyeBlinkRight` - 눈 깜빡임
- `eyeWideLeft`, `eyeWideRight` - 눈 크게 뜨기
- `eyeLookUpLeft`, `eyeLookUpRight` - 눈 위로
- `eyeLookDownLeft`, `eyeLookDownRight` - 눈 아래로
- `eyeLookInLeft`, `eyeLookInRight` - 눈 안쪽
- `eyeLookOutLeft`, `eyeLookOutRight` - 눈 바깥쪽

### 눈썹 (Eyebrows)
- `browDownLeft`, `browDownRight` - 눈썹 내림
- `browInnerUp` - 눈썹 안쪽 올림
- `browOuterUpLeft`, `browOuterUpRight` - 눈썹 바깥쪽 올림

### 입 (Mouth)
- `jawOpen` - 입 벌림
- `mouthSmileLeft`, `mouthSmileRight` - 입꼬리 올림 (웃음)
- `mouthFrownLeft`, `mouthFrownRight` - 입꼬리 내림
- `mouthPucker` - 입 오므리기
- `mouthFunnel` - 입 깔때기 모양
- `mouthUpperUpLeft`, `mouthUpperUpRight` - 윗입술 올림
- `mouthLowerDownLeft`, `mouthLowerDownRight` - 아랫입술 내림
- `mouthLeft`, `mouthRight` - 입 옆으로
- ... 외 다수

### 뺨 (Cheeks)
- `cheekSquintLeft`, `cheekSquintRight` - 뺨 올림 (눈 가늘게)
- `cheekPuff` - 뺨 부풀리기

### 코 (Nose)
- `noseSneerLeft`, `noseSneerRight` - 코 주름

---

## 5. 테스트 방법

### 1단계: 앱 빌드 및 실행
```bash
# Xcode에서 빌드 후 iPhone에 설치
```

### 2단계: 데이터 수집
```
1. 앱 실행
2. 감정 선택 (예: "sadness")
3. 녹화 시작 (3초)
4. 슬픔 표정 짓기:
   - 입 벌림
   - 입꼬리 내림
   - 뺨 올림
   - 시선 아래
5. 녹화 중지
```

### 3단계: 데이터 확인
```bash
# iPhone에서 JSON 파일 확인
# Files 앱 → On My iPhone → EmotionCapture

# Mac으로 전송
# AirDrop 또는 Finder 연결

# JSON 파일 열기
cat sadness_2025-01-21T12:00:00Z_mesh.json
```

### 4단계: Python 테스트
```bash
# 규칙 기반 분류기로 테스트
python scripts/test_rule_classifier.py \
  --input data/test_samples/sadness_mesh.json
```

---

## 6. 문제 해결

### BlendShapes가 빈 값으로 저장되는 경우
```swift
// ARFaceAnchor를 제대로 받고 있는지 확인
func session(_ session: ARSession, didUpdate anchors: [ARAnchor]) {
    guard let faceAnchor = anchors.first as? ARFaceAnchor else {
        print("⚠️ No ARFaceAnchor found")
        return
    }

    print("✓ BlendShapes count: \(faceAnchor.blendShapes.count)")  // 52개여야 함
    captureManager.captureFaceMesh(faceAnchor: faceAnchor)
}
```

### 값이 모두 0인 경우
- 얼굴이 제대로 인식되지 않음
- 조명을 밝게 하고 카메라 정면을 보세요
- ARKit이 얼굴을 추적 중인지 확인 (`faceAnchor.isTracked`)

---

## 7. 다음 단계

BlendShapes 데이터 수집 후:

1. **테스트**: 규칙 기반 분류기로 정확도 확인
2. **데이터 수집**: 20개 감정 × 100개 샘플
3. **딥러닝 융합**: 규칙 기반 + PointNet + 오디오 + 텍스트

---

## 참고 자료

- [ARKit Face Tracking](https://developer.apple.com/documentation/arkit/arfaceanchor)
- [BlendShapes 목록](https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation)
- [Face Tracking Best Practices](https://developer.apple.com/documentation/arkit/tracking_and_visualizing_faces)
