//
//  ARFaceTrackingViewController.swift
//  facedetection
//
//  Created by Minjae Kim on 11/23/25.
//

import ARKit
import AVFoundation
import UIKit

class ARFaceTrackingViewController: UIViewController {
    
    var sceneView: ARSCNView!
    var audioRecorder: AVAudioRecorder?
    var faceVertices: [[[Float]]] = [] // Array of frames, each containing vertex arrays
    var faceBlendShapes: [[String: Float]] = [] // Array of frames, each containing BlendShapes
    var currentEmotion: String = ""
    var isRecording = false
    var recordingStartTime: Date?
    
    // Mesh visualization
    var showMeshPoints = true
    var meshPointsNode: SCNNode?
    
    // Live streaming
    var streamManager: LiveStreamManager?
    var frameCounter: Int = 0
    
    // Callbacks
    var onRecordingStatusChanged: ((Bool) -> Void)?
    var onDataExported: ((Bool, String) -> Void)?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Setup ARSCNView
        sceneView = ARSCNView(frame: view.bounds)
        sceneView.delegate = self
        sceneView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(sceneView)
        
        // Configure scene view for mesh visualization
        sceneView.scene = SCNScene()
        sceneView.automaticallyUpdatesLighting = true
        
        // Request permissions
        requestPermissions()
    }
    
    // Toggle mesh point visualization
    func toggleMeshVisualization(_ enabled: Bool) {
        showMeshPoints = enabled
        if !enabled {
            meshPointsNode?.removeFromParentNode()
            meshPointsNode = nil
        }
    }
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        startTracking()
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        sceneView.session.pause()
    }
    
    func requestPermissions() {
        // Request camera permission
        AVCaptureDevice.requestAccess(for: .video) { granted in
            if !granted {
                DispatchQueue.main.async {
                    self.showAlert("Camera access is required for face tracking")
                }
            }
        }
        
        // Request microphone permission
        AVAudioSession.sharedInstance().requestRecordPermission { granted in
            if !granted {
                DispatchQueue.main.async {
                    self.showAlert("Microphone access is required for audio recording")
                }
            }
        }
    }
    
    func startTracking() {
        guard ARFaceTrackingConfiguration.isSupported else {
            showAlert("TrueDepth camera not available. This app requires iPhone X or later.")
            return
        }
        
        let configuration = ARFaceTrackingConfiguration()
        configuration.isLightEstimationEnabled = true
        configuration.maximumNumberOfTrackedFaces = 1
        
        sceneView.session.run(configuration, options: [.resetTracking, .removeExistingAnchors])
    }
    
    func startRecording(emotion: String) {
        currentEmotion = emotion
        isRecording = true
        faceVertices.removeAll()
        faceBlendShapes.removeAll()
        recordingStartTime = Date()
        frameCounter = 0
        
        // Configure audio session
        configureAudioSession()
        
        // Start audio recording
        setupAudioRecorder()
        audioRecorder?.record()
        
        // Notify stream manager
        if let streamManager = streamManager, streamManager.isStreaming {
            streamManager.sendRecordingStart(emotion: emotion)
        }
        
        onRecordingStatusChanged?(true)
        
        print("Started recording emotion: \(emotion)")
    }
    
    func stopRecording() {
        guard isRecording else { return }
        
        isRecording = false
        audioRecorder?.stop()
        
        // Notify stream manager
        if let streamManager = streamManager, streamManager.isStreaming {
            streamManager.sendRecordingStop(emotion: currentEmotion, frameCount: frameCounter)
        }
        
        onRecordingStatusChanged?(false)
        
        // Export data
        exportData()
        
        print("Stopped recording. Captured \(faceVertices.count) frames")
    }
    
    func configureAudioSession() {
        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
            try audioSession.setActive(true)
        } catch {
            print("Failed to configure audio session: \(error)")
        }
    }
    
    func setupAudioRecorder() {
        let audioFilename = getDocumentsDirectory()
            .appendingPathComponent("recording_temp.wav")
        
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        
        do {
            audioRecorder = try AVAudioRecorder(url: audioFilename, settings: settings)
            audioRecorder?.prepareToRecord()
        } catch {
            print("Failed to setup audio recorder: \(error)")
            showAlert("Failed to setup audio recorder")
        }
    }
    
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
    
    func exportData() {
        guard !faceVertices.isEmpty else {
            showAlert("No face data captured")
            onDataExported?(false, "No face data captured")
            return
        }
        
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let filename = "\(currentEmotion)_\(timestamp)"
        
        // Export face mesh as JSON
        let meshData: [String: Any] = [
            "vertices": faceVertices,
            "blendshapes": faceBlendShapes,
            "timestamp": timestamp,
            "emotion": currentEmotion,
            "frame_count": faceVertices.count,
            "recording_duration": recordingStartTime.map { Date().timeIntervalSince($0) } ?? 0
        ]
        
        let meshExported = exportJSON(data: meshData, filename: "\(filename)_mesh.json")
        
        // Copy audio file
        let audioURL = getDocumentsDirectory().appendingPathComponent("recording_temp.wav")
        let destURL = getDocumentsDirectory().appendingPathComponent("\(filename)_audio.wav")
        
        var audioExported = false
        do {
            if FileManager.default.fileExists(atPath: destURL.path) {
                try FileManager.default.removeItem(at: destURL)
            }
            try FileManager.default.copyItem(at: audioURL, to: destURL)
            audioExported = true
        } catch {
            print("Failed to copy audio file: \(error)")
        }
        
        if meshExported && audioExported {
            showAlert("Data exported successfully!\n\(faceVertices.count) frames captured")
            onDataExported?(true, "Exported: \(filename)")
        } else {
            showAlert("Data export incomplete. Check console for errors.")
            onDataExported?(false, "Export failed")
        }
    }
    
    func exportJSON(data: [String: Any], filename: String) -> Bool {
        let fileURL = getDocumentsDirectory().appendingPathComponent(filename)
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: data, options: .prettyPrinted)
            try jsonData.write(to: fileURL)
            print("Exported JSON to: \(fileURL.path)")
            return true
        } catch {
            print("Failed to export JSON: \(error)")
            return false
        }
    }
    
    func shareData() {
        let documentsURL = getDocumentsDirectory()
        
        do {
            let files = try FileManager.default.contentsOfDirectory(at: documentsURL, includingPropertiesForKeys: nil)
            let dataFiles = files.filter { $0.pathExtension == "json" || $0.pathExtension == "wav" }
            
            guard !dataFiles.isEmpty else {
                showAlert("No data files to share")
                return
            }
            
            let activityVC = UIActivityViewController(activityItems: dataFiles, applicationActivities: nil)
            
            // For iPad support
            if let popoverController = activityVC.popoverPresentationController {
                popoverController.sourceView = view
                popoverController.sourceRect = CGRect(x: view.bounds.midX, y: view.bounds.midY, width: 0, height: 0)
                popoverController.permittedArrowDirections = []
            }
            
            present(activityVC, animated: true)
        } catch {
            print("Failed to get data files: \(error)")
            showAlert("Failed to access data files")
        }
    }
    
    func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
    
    func showAlert(_ message: String) {
        let alert = UIAlertController(title: "Face Tracking", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}

// MARK: - ARSCNViewDelegate

extension ARFaceTrackingViewController: ARSCNViewDelegate {
    
    func renderer(_ renderer: SCNSceneRenderer, didUpdate node: SCNNode, for anchor: ARAnchor) {
        guard let faceAnchor = anchor as? ARFaceAnchor else { return }
        
        // Update mesh visualization
        if showMeshPoints {
            updateMeshVisualization(faceAnchor: faceAnchor, node: node)
        }
        
        // Extract vertex positions
        let vertices = faceAnchor.geometry.vertices

        // Convert to array of [x, y, z]
        var vertexArray: [[Float]] = []
        for i in 0..<vertices.count {
            let vertex = vertices[i]
            vertexArray.append([vertex.x, vertex.y, vertex.z])
        }

        // Extract BlendShapes
        var blendShapeDict: [String: Float] = [:]
        for (key, value) in faceAnchor.blendShapes {
            blendShapeDict[key.rawValue] = value.floatValue
        }

        // Always stream if connected (for real-time visualization)
        if let streamManager = streamManager, streamManager.isStreaming {
            let timestamp = Date().timeIntervalSince1970
            streamManager.streamFaceData(
                vertices: vertexArray,
                blendShapes: blendShapeDict,
                emotion: currentEmotion.isEmpty ? "live" : currentEmotion,
                timestamp: timestamp,
                frameNumber: frameCounter
            )
            frameCounter += 1
        }

        // Store locally only when recording
        if isRecording && validateCapture(faceAnchor: faceAnchor) {
            faceVertices.append(vertexArray)
            faceBlendShapes.append(blendShapeDict)
        }
    }
    
    func renderer(_ renderer: SCNSceneRenderer, didAdd node: SCNNode, for anchor: ARAnchor) {
        guard let faceAnchor = anchor as? ARFaceAnchor else { return }
        
        // Create initial mesh visualization
        if showMeshPoints {
            createMeshVisualization(faceAnchor: faceAnchor, node: node)
        }
    }
    
    // MARK: - Mesh Visualization
    
    private func createMeshVisualization(faceAnchor: ARFaceAnchor, node: SCNNode) {
        // Simple point cloud visualization
        createPointCloudVisualization(faceAnchor: faceAnchor, node: node)
    }
    
    private func updateMeshVisualization(faceAnchor: ARFaceAnchor, node: SCNNode) {
        // Simple point cloud update
        updatePointCloudVisualization(faceAnchor: faceAnchor)
    }
    
    // MARK: - Point Cloud Visualization
    
    private func createPointCloudVisualization(faceAnchor: ARFaceAnchor, node: SCNNode) {
        // Create a parent node for mesh points
        meshPointsNode = SCNNode()
        node.addChildNode(meshPointsNode!)
        
        // Create geometry from face anchor
        let geometry = faceAnchor.geometry
        let vertices = geometry.vertices
        let vertexCount = geometry.vertices.count
        
        // Create a point cloud
        var vertexPositions: [SCNVector3] = []
        for i in 0..<vertexCount {
            let vertex = vertices[i]
            vertexPositions.append(SCNVector3(vertex.x, vertex.y, vertex.z))
        }
        
        // Create small spheres for each vertex
        createMeshPoints(positions: vertexPositions)
    }
    
    private func updatePointCloudVisualization(faceAnchor: ARFaceAnchor) {
        guard let meshNode = meshPointsNode else { return }
        
        let geometry = faceAnchor.geometry
        let vertices = geometry.vertices
        
        // Update positions of existing points
        // Show every 5th vertex for performance
        meshNode.childNodes.enumerated().forEach { index, pointNode in
            let actualIndex = index * 5
            if actualIndex < vertices.count {
                let vertex = vertices[actualIndex]
                pointNode.position = SCNVector3(vertex.x, vertex.y, vertex.z)
            }
        }
    }
    
    private func createMeshPoints(positions: [SCNVector3]) {
        guard let meshNode = meshPointsNode else { return }
        
        // Remove existing points
        meshNode.childNodes.forEach { $0.removeFromParentNode() }
        
        // Create a small sphere geometry for points
        let sphereGeometry = SCNSphere(radius: 0.001) // 1mm radius
        
        // Material for the points
        let material = SCNMaterial()
        material.diffuse.contents = UIColor.green
        material.emission.contents = UIColor.green.withAlphaComponent(0.5)
        material.lightingModel = .constant
        material.transparency = 0.8
        sphereGeometry.materials = [material]
        
        // Create a node for each vertex position
        // Only show every 5th point to reduce visual clutter and improve performance
        for (index, position) in positions.enumerated() where index % 5 == 0 {
            let pointNode = SCNNode(geometry: sphereGeometry)
            pointNode.position = position
            meshNode.addChildNode(pointNode)
        }
    }
    
    func session(_ session: ARSession, didFailWithError error: Error) {
        print("AR Session failed: \(error.localizedDescription)")
        showAlert("AR Session failed: \(error.localizedDescription)")
    }
    
    func sessionWasInterrupted(_ session: ARSession) {
        print("AR Session interrupted")
        if isRecording {
            stopRecording()
        }
    }
    
    func sessionInterruptionEnded(_ session: ARSession) {
        print("AR Session interruption ended")
        startTracking()
    }
}
