//
//  LiveStreamManager.swift
//  facedetection
//
//  Created by Minjae Kim on 12/9/25.
//

import Foundation
import Network
import Combine

/// Manages live streaming of face tracking data over WebSocket or UDP
@MainActor
class LiveStreamManager: ObservableObject {
    
    enum StreamProtocol {
        case webSocket
        case udp
    }
    
    enum StreamState: Equatable {
        case disconnected
        case connecting
        case connected
        case error(String)
        
        static func == (lhs: StreamState, rhs: StreamState) -> Bool {
            switch (lhs, rhs) {
            case (.disconnected, .disconnected),
                 (.connecting, .connecting),
                 (.connected, .connected):
                return true
            case (.error(let lhsMsg), .error(let rhsMsg)):
                return lhsMsg == rhsMsg
            default:
                return false
            }
        }
    }
    
    // MARK: - Published Properties
    @Published var state: StreamState = .disconnected
    @Published var isStreaming: Bool = false
    @Published var bytesSent: Int = 0
    @Published var framesSent: Int = 0
    @Published var lastError: String?
    
    // MARK: - Private Properties
    private var connection: NWConnection?
    private var listener: NWListener?
    private let streamProtocol: StreamProtocol
    private let queue = DispatchQueue(label: "com.facedetection.streaming")
    
    // Configuration - No hardcoded defaults, must be set by user
    var serverHost: String = ""
    var serverPort: UInt16 = 8765
    
    // MARK: - Initialization
    init(streamProtocol: StreamProtocol = .webSocket) {
        self.streamProtocol = streamProtocol
    }
    
    // MARK: - Connection Management
    
    /// Connect to the server
    func connect() {
        Task { @MainActor in
            // Validate server host
            guard !serverHost.isEmpty else {
                state = .error("Server IP not set. Please configure in Settings.")
                return
            }

            disconnect()  // Clean up any existing connection

            state = .connecting
            print("🔄 Connecting to \(serverHost):\(serverPort)...")

            switch streamProtocol {
            case .webSocket:
                connectWebSocket()
            case .udp:
                connectUDP()
            }
        }
    }
    
    /// Disconnect from the server
    func disconnect() {
        connection?.cancel()
        connection = nil
        listener?.cancel()
        listener = nil
        
        Task { @MainActor in
            state = .disconnected
            isStreaming = false
        }
    }
    
    // MARK: - WebSocket Connection
    
    private func connectWebSocket() {
        let url = URL(string: "ws://\(serverHost):\(serverPort)")!
        
        // Create WebSocket options
        let options = NWProtocolWebSocket.Options()
        options.autoReplyPing = true
        
        let parameters = NWParameters.tcp
        parameters.defaultProtocolStack.applicationProtocols.insert(options, at: 0)
        
        // Create connection
        connection = NWConnection(
            to: .url(url),
            using: parameters
        )
        
        setupConnectionHandlers()
        connection?.start(queue: queue)
    }
    
    // MARK: - UDP Connection
    
    private func connectUDP() {
        let host = NWEndpoint.Host(serverHost)
        let port = NWEndpoint.Port(integerLiteral: serverPort)
        
        let connection = NWConnection(
            host: host,
            port: port,
            using: .udp
        )
        
        self.connection = connection
        setupConnectionHandlers()
        connection.start(queue: queue)
    }
    
    // MARK: - Connection Handlers
    
    private func setupConnectionHandlers() {
        connection?.stateUpdateHandler = { [weak self] newState in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                switch newState {
                case .ready:
                    self.state = .connected
                    self.isStreaming = true
                    print("✅ Connected to server at \(self.serverHost):\(self.serverPort)")
                    
                case .failed(let error):
                    self.state = .error(error.localizedDescription)
                    self.lastError = error.localizedDescription
                    self.isStreaming = false
                    print("❌ Connection failed: \(error)")
                    
                case .waiting(let error):
                    self.state = .connecting
                    print("⏳ Connection waiting: \(error)")
                    
                default:
                    break
                }
            }
        }
    }
    
    // MARK: - Data Streaming
    
    /// Stream face tracking data
    func streamFaceData(
        vertices: [[Float]],
        blendShapes: [String: Float]? = nil,
        emotion: String,
        timestamp: TimeInterval,
        frameNumber: Int
    ) {
        guard isStreaming, connection != nil else { return }

        // Create data packet
        var packet: [String: Any] = [
            "type": "face_data",
            "emotion": emotion,
            "timestamp": timestamp,
            "frame": frameNumber,
            "vertex_count": vertices.count,
            "vertices": vertices
        ]

        // Add BlendShapes if provided
        if let blendShapes = blendShapes {
            packet["blendshapes"] = blendShapes
        }

        sendJSON(packet)
    }
    
    /// Stream audio chunk
    func streamAudioChunk(
        data: Data,
        emotion: String,
        timestamp: TimeInterval,
        chunkNumber: Int
    ) {
        guard isStreaming, connection != nil else { return }
        
        // For audio, we'll send metadata first, then raw audio data
        let metadata: [String: Any] = [
            "type": "audio_chunk",
            "emotion": emotion,
            "timestamp": timestamp,
            "chunk": chunkNumber,
            "size": data.count
        ]
        
        // Send metadata as JSON
        if let jsonData = try? JSONSerialization.data(withJSONObject: metadata) {
            sendData(jsonData)
        }
        
        // Send raw audio data
        sendData(data)
    }
    
    /// Stream combined frame (face + audio)
    func streamFrame(
        vertices: [[Float]],
        blendShapes: [String: Float]? = nil,
        audioData: Data?,
        emotion: String,
        timestamp: TimeInterval,
        frameNumber: Int
    ) {
        guard isStreaming, connection != nil else { return }

        var packet: [String: Any] = [
            "type": "frame",
            "emotion": emotion,
            "timestamp": timestamp,
            "frame": frameNumber,
            "vertex_count": vertices.count,
            "vertices": vertices
        ]

        // Add BlendShapes if provided
        if let blendShapes = blendShapes {
            packet["blendshapes"] = blendShapes
        }

        if let audioData = audioData {
            // Convert audio data to base64 for JSON transmission
            packet["audio"] = audioData.base64EncodedString()
            packet["audio_size"] = audioData.count
        }

        sendJSON(packet)
    }
    
    /// Send recording start event
    func sendRecordingStart(emotion: String) {
        let packet: [String: Any] = [
            "type": "recording_start",
            "emotion": emotion,
            "timestamp": Date().timeIntervalSince1970
        ]
        sendJSON(packet)
    }
    
    /// Send recording stop event
    func sendRecordingStop(emotion: String, frameCount: Int) {
        let packet: [String: Any] = [
            "type": "recording_stop",
            "emotion": emotion,
            "frame_count": frameCount,
            "timestamp": Date().timeIntervalSince1970
        ]
        sendJSON(packet)
    }
    
    // MARK: - Low-level Sending
    
    private func sendJSON(_ object: [String: Any]) {
        guard let jsonData = try? JSONSerialization.data(withJSONObject: object) else {
            print("Failed to serialize JSON")
            return
        }
        
        sendData(jsonData)
    }
    
    private func sendData(_ data: Data) {
        guard let connection = connection else { return }
        
        switch streamProtocol {
        case .webSocket:
            sendWebSocketMessage(data, connection: connection)
        case .udp:
            sendUDPPacket(data, connection: connection)
        }
        
        // Update statistics
        DispatchQueue.main.async {
            self.bytesSent += data.count
            self.framesSent += 1
        }
    }
    
    private func sendWebSocketMessage(_ data: Data, connection: NWConnection) {
        let metadata = NWProtocolWebSocket.Metadata(opcode: .text)
        let context = NWConnection.ContentContext(
            identifier: "context",
            metadata: [metadata]
        )
        
        connection.send(
            content: data,
            contentContext: context,
            isComplete: true,
            completion: .contentProcessed { [weak self] error in
                if let error = error {
                    print("WebSocket send error: \(error)")
                    DispatchQueue.main.async {
                        self?.lastError = error.localizedDescription
                    }
                }
            }
        )
    }
    
    private func sendUDPPacket(_ data: Data, connection: NWConnection) {
        // For UDP, we might need to chunk large packets
        let maxPacketSize = 65000  // Leave room for headers
        
        if data.count <= maxPacketSize {
            connection.send(
                content: data,
                completion: .contentProcessed { [weak self] error in
                    if let error = error {
                        print("UDP send error: \(error)")
                        DispatchQueue.main.async {
                            self?.lastError = error.localizedDescription
                        }
                    }
                }
            )
        } else {
            // Chunk the data for large payloads
            var offset = 0
            var chunkIndex = 0
            let totalChunks = (data.count + maxPacketSize - 1) / maxPacketSize
            
            while offset < data.count {
                let chunkSize = min(maxPacketSize, data.count - offset)
                let chunk = data.subdata(in: offset..<(offset + chunkSize))
                
                // Add header with chunk info
                let header: [String: Any] = [
                    "chunk": chunkIndex,
                    "total": totalChunks,
                    "size": chunkSize
                ]
                
                if let headerData = try? JSONSerialization.data(withJSONObject: header) {
                    var packetData = Data()
                    packetData.append(UInt32(headerData.count).littleEndian.data)
                    packetData.append(headerData)
                    packetData.append(chunk)
                    
                    connection.send(content: packetData, completion: .contentProcessed { _ in })
                }
                
                offset += chunkSize
                chunkIndex += 1
            }
        }
    }
}

// MARK: - Helper Extensions

extension FixedWidthInteger {
    var data: Data {
        withUnsafeBytes(of: self) { Data($0) }
    }
}
