//
//  EmotionSelectionView.swift
//  facedetection
//
//  Created by Minjae Kim on 11/23/25.
//

import SwiftUI

struct EmotionSelectionView: View {
    let emotions = [
        "neutral", "joy", "sadness", "anger", "fear", "disgust", "surprise",
        "regret", "affection", "resignation", "contentment", "disappointment",
        "nostalgia", "guilt", "pride", "shame", "envy", "gratitude", "hope", "despair"
    ]
    
    @State private var selectedEmotion: String = "neutral"
    @State private var isRecording = false
    @State private var showingShareSheet = false
    @State private var recordingDuration: TimeInterval = 0
    @State private var recordingTimer: Timer?
    @State private var exportMessage = ""
    @State private var showExportAlert = false
    @State private var showMeshPoints = true
    
    // Streaming
    @StateObject private var streamManager = LiveStreamManager()
    @State private var showStreamSettings = false
    @AppStorage("serverIP") private var serverIP: String = ""
    @AppStorage("serverPort") private var serverPort: String = "8765"
    
    var body: some View {
        ZStack {
            // AR Face Tracking View (background)
            ARFaceTrackingView(
                isRecording: $isRecording,
                showMeshPoints: $showMeshPoints,
                emotion: selectedEmotion,
                streamManager: streamManager,
                onStartRecording: {
                    startTimer()
                },
                onStopRecording: {
                    stopTimer()
                },
                onDataExported: { success, message in
                    exportMessage = message
                    showExportAlert = true
                }
            )
            .edgesIgnoringSafeArea(.all)
            
            // UI Overlay
            VStack {
                // Top bar
                HStack {
                    Text("Emotion Data Capture")
                        .font(.headline)
                        .padding()
                        .background(.ultraThinMaterial)
                        .cornerRadius(10)
                    
                    Spacer()
                    
                    // Streaming indicator
                    streamingIndicator
                    
                    // Mesh visualization toggle
                    Button(action: {
                        showMeshPoints.toggle()
                    }) {
                        Image(systemName: showMeshPoints ? "eye.fill" : "eye.slash.fill")
                            .font(.title2)
                            .foregroundColor(showMeshPoints ? .green : .gray)
                            .padding()
                            .background(.ultraThinMaterial)
                            .cornerRadius(10)
                    }
                    
                    Button(action: {
                        showingShareSheet = true
                    }) {
                        Image(systemName: "square.and.arrow.up")
                            .font(.title2)
                            .padding()
                            .background(.ultraThinMaterial)
                            .cornerRadius(10)
                    }
                }
                .padding()
                
                Spacer()
                
                // Recording indicator
                if isRecording {
                    VStack(spacing: 8) {
                        HStack(spacing: 12) {
                            Circle()
                                .fill(Color.red)
                                .frame(width: 12, height: 12)
                                .opacity(recordingDuration.truncatingRemainder(dividingBy: 1.0) < 0.5 ? 1.0 : 0.3)
                            
                            Text("Recording \(selectedEmotion.capitalized)")
                                .font(.headline)
                        }
                        
                        Text(String(format: "%.1f seconds", recordingDuration))
                            .font(.subheadline)
                            .monospacedDigit()
                    }
                    .padding()
                    .background(.ultraThinMaterial)
                    .cornerRadius(15)
                    .padding()
                }
                
                Spacer()
                
                // Control panel
                VStack(spacing: 20) {
                    // Streaming controls
                    streamingControls
                    
                    // Emotion picker
                    VStack(spacing: 8) {
                        Text("Select Emotion")
                            .font(.headline)
                        
                        Picker("Emotion", selection: $selectedEmotion) {
                            ForEach(emotions, id: \.self) { emotion in
                                Text(emotion.capitalized).tag(emotion)
                            }
                        }
                        .pickerStyle(.wheel)
                        .frame(height: 150)
                        .disabled(isRecording)
                    }
                    
                    // Recording controls
                    HStack(spacing: 20) {
                        Button(action: {
                            isRecording = true
                        }) {
                            Label("Start", systemImage: "record.circle")
                                .font(.title3)
                                .fontWeight(.semibold)
                                .foregroundStyle(.white)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(isRecording ? Color.gray : Color.red)
                                .cornerRadius(15)
                        }
                        .disabled(isRecording)
                        
                        Button(action: {
                            isRecording = false
                        }) {
                            Label("Stop", systemImage: "stop.circle")
                                .font(.title3)
                                .fontWeight(.semibold)
                                .foregroundStyle(.white)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(isRecording ? Color.blue : Color.gray)
                                .cornerRadius(15)
                        }
                        .disabled(!isRecording)
                    }
                    .padding(.horizontal)
                    
                    // Instructions
                    if !isRecording {
                        Text("Select an emotion, tap Start, speak naturally for 2-3 seconds, then tap Stop")
                            .font(.caption)
                            .multilineTextAlignment(.center)
                            .foregroundStyle(.secondary)
                            .padding(.horizontal)
                    }
                }
                .padding()
                .background(.ultraThinMaterial)
                .cornerRadius(20)
                .padding()
            }
        }
        .alert("Export Status", isPresented: $showExportAlert) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(exportMessage)
        }
        .sheet(isPresented: $showingShareSheet) {
            ShareSheet()
        }
        .sheet(isPresented: $showStreamSettings) {
            streamSettingsSheet
        }
    }
    
    // MARK: - Streaming UI Components
    
    private var streamingIndicator: some View {
        Button(action: {
            showStreamSettings = true
        }) {
            HStack(spacing: 6) {
                Circle()
                    .fill(streamManager.isStreaming ? Color.green : Color.gray)
                    .frame(width: 8, height: 8)
                
                Image(systemName: "wifi")
                    .font(.title2)
                    .foregroundColor(streamManager.isStreaming ? .green : .gray)
            }
            .padding()
            .background(.ultraThinMaterial)
            .cornerRadius(10)
        }
    }
    
    private var streamingControls: some View {
        VStack(spacing: 12) {
            HStack {
                Text("Live Stream")
                    .font(.headline)
                Spacer()
                
                if streamManager.isStreaming {
                    Text("\(streamManager.framesSent) frames")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            
            HStack(spacing: 12) {
                if streamManager.isStreaming {
                    Button(action: {
                        streamManager.disconnect()
                    }) {
                        Label("Disconnect", systemImage: "wifi.slash")
                            .font(.subheadline)
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(Color.orange)
                            .cornerRadius(10)
                    }
                } else {
                    Button(action: {
                        connectToServer()
                    }) {
                        Label("Connect to Server", systemImage: "wifi")
                            .font(.subheadline)
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(Color.blue)
                            .cornerRadius(10)
                    }
                }
                
                Button(action: {
                    showStreamSettings = true
                }) {
                    Image(systemName: "gear")
                        .font(.subheadline)
                        .foregroundStyle(.white)
                        .padding(.vertical, 10)
                        .padding(.horizontal, 16)
                        .background(Color.gray)
                        .cornerRadius(10)
                }
            }
            
            // Connection status
            if case .error(let error) = streamManager.state {
                Text("Error: \(error)")
                    .font(.caption)
                    .foregroundStyle(.red)
                    .multilineTextAlignment(.center)
            } else if case .connecting = streamManager.state {
                Text("Connecting...")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(Color.blue.opacity(0.1))
        .cornerRadius(12)
    }
    
    private var streamSettingsSheet: some View {
        NavigationView {
            Form {
                Section {
                    HStack {
                        Text("Server IP")
                        Spacer()
                        TextField("192.168.x.x", text: $serverIP)
                            .keyboardType(.numbersAndPunctuation)
                            .textInputAutocapitalization(.never)
                            .disableAutocorrection(true)
                            .multilineTextAlignment(.trailing)
                    }

                    HStack {
                        Text("Port")
                        Spacer()
                        TextField("8765", text: $serverPort)
                            .keyboardType(.numbersAndPunctuation)
                            .textInputAutocapitalization(.never)
                            .disableAutocorrection(true)
                            .multilineTextAlignment(.trailing)
                    }
                } header: {
                    Text("Server Settings")
                } footer: {
                    Text("Settings are saved automatically. Enter the IP address shown when you start the Python server.")
                }

                Section {
                    // Quick connect button
                    Button(action: {
                        connectToServer()
                    }) {
                        HStack {
                            Image(systemName: streamManager.isStreaming ? "wifi.slash" : "wifi")
                            Text(streamManager.isStreaming ? "Reconnect" : "Connect Now")
                        }
                    }
                    .disabled(serverIP.isEmpty)

                    HStack {
                        Text("Status")
                        Spacer()
                        statusBadge
                    }

                    if streamManager.isStreaming {
                        HStack {
                            Text("Frames Sent")
                            Spacer()
                            Text("\(streamManager.framesSent)")
                                .foregroundStyle(.secondary)
                        }

                        HStack {
                            Text("Data Sent")
                            Spacer()
                            Text(formatBytes(streamManager.bytesSent))
                                .foregroundStyle(.secondary)
                        }
                    }

                    if !serverIP.isEmpty {
                        HStack {
                            Text("Target")
                            Spacer()
                            Text("ws://\(serverIP):\(serverPort)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                } header: {
                    Text("Connection Info")
                }

                Section {
                    Text("1. Run on your Mac:\n   python3 scripts/master_control.py start")
                        .font(.caption)
                    Text("2. Note the IP address shown (e.g., 192.168.0.100)")
                        .font(.caption)
                    Text("3. Enter that IP above and tap 'Connect Now'")
                        .font(.caption)
                    Text("4. Start recording to stream data live")
                        .font(.caption)
                } header: {
                    Text("Instructions")
                }
            }
            .navigationTitle("Stream Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        showStreamSettings = false
                    }
                }
            }
        }
    }
    
    private var statusBadge: some View {
        Group {
            switch streamManager.state {
            case .connected:
                Label("Connected", systemImage: "checkmark.circle.fill")
                    .foregroundStyle(.green)
            case .connecting:
                Label("Connecting", systemImage: "arrow.clockwise")
                    .foregroundStyle(.orange)
            case .disconnected:
                Label("Disconnected", systemImage: "xmark.circle.fill")
                    .foregroundStyle(.gray)
            case .error:
                Label("Error", systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
            }
        }
        .font(.caption)
    }
    
    private func startTimer() {
        recordingDuration = 0
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            recordingDuration += 0.1
        }
    }
    
    private func stopTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
        recordingDuration = 0
    }
    
    private func connectToServer() {
        // Trim whitespace from IP and port
        let cleanIP = serverIP.trimmingCharacters(in: .whitespacesAndNewlines)
        let cleanPort = serverPort.trimmingCharacters(in: .whitespacesAndNewlines)

        // Debug log
        print("🔌 Attempting connection:")
        print("   Raw IP: '\(serverIP)' -> Clean IP: '\(cleanIP)'")
        print("   Raw Port: '\(serverPort)' -> Clean Port: '\(cleanPort)'")

        // Update stream manager settings
        streamManager.serverHost = cleanIP
        if let port = UInt16(cleanPort) {
            streamManager.serverPort = port
            print("   Parsed Port: \(port)")
        } else {
            print("   ⚠️ Failed to parse port, using default 8765")
            streamManager.serverPort = 8765
        }

        print("   Target: ws://\(streamManager.serverHost):\(streamManager.serverPort)")

        // Connect
        streamManager.connect()
    }
    
    private func formatBytes(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }
}

// MARK: - Share Sheet

struct ShareSheet: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        let controller = UIViewController()
        
        // Get documents directory
        let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        
        do {
            let files = try FileManager.default.contentsOfDirectory(at: documentsURL, includingPropertiesForKeys: nil)
            let dataFiles = files.filter { $0.pathExtension == "json" || $0.pathExtension == "wav" }
            
            if !dataFiles.isEmpty {
                let activityVC = UIActivityViewController(activityItems: dataFiles, applicationActivities: nil)
                
                // For iPad support
                if let popoverController = activityVC.popoverPresentationController {
                    popoverController.sourceView = controller.view
                    popoverController.sourceRect = CGRect(x: controller.view.bounds.midX, 
                                                          y: controller.view.bounds.midY, 
                                                          width: 0, height: 0)
                    popoverController.permittedArrowDirections = []
                }
                
                DispatchQueue.main.async {
                    controller.present(activityVC, animated: true)
                }
            }
        } catch {
            print("Failed to get files: \(error)")
        }
        
        return controller
    }
    
    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {
        // No update needed
    }
}

#Preview {
    EmotionSelectionView()
}
