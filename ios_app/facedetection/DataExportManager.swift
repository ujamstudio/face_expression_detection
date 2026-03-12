//
//  DataExportManager.swift
//  facedetection
//
//  Created by Minjae Kim on 11/23/25.
//

import Foundation

/// Manages data export and file operations
class DataExportManager {
    
    static let shared = DataExportManager()
    
    private init() {}
    
    // MARK: - File Management
    
    func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
    
    func listExportedFiles() -> [URL] {
        let documentsURL = getDocumentsDirectory()
        
        do {
            let files = try FileManager.default.contentsOfDirectory(
                at: documentsURL,
                includingPropertiesForKeys: [.creationDateKey, .fileSizeKey],
                options: .skipsHiddenFiles
            )
            
            let dataFiles = files.filter { 
                $0.pathExtension == "json" || $0.pathExtension == "wav" 
            }
            
            // Sort by creation date (newest first)
            return dataFiles.sorted { url1, url2 in
                let date1 = try? url1.resourceValues(forKeys: [.creationDateKey]).creationDate
                let date2 = try? url2.resourceValues(forKeys: [.creationDateKey]).creationDate
                return (date1 ?? Date.distantPast) > (date2 ?? Date.distantPast)
            }
        } catch {
            print("Failed to list files: \(error)")
            return []
        }
    }
    
    func getFileSize(url: URL) -> String {
        do {
            let resourceValues = try url.resourceValues(forKeys: [.fileSizeKey])
            if let fileSize = resourceValues.fileSize {
                return formatBytes(fileSize)
            }
        } catch {
            print("Failed to get file size: \(error)")
        }
        return "Unknown"
    }
    
    func formatBytes(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }
    
    func deleteFile(url: URL) throws {
        try FileManager.default.removeItem(at: url)
    }
    
    func deleteAllFiles() throws {
        let files = listExportedFiles()
        for file in files {
            try deleteFile(url: file)
        }
    }
    
    // MARK: - Export Information
    
    struct ExportInfo {
        let emotion: String
        let timestamp: Date
        let meshFileURL: URL?
        let audioFileURL: URL?
        let totalSize: Int
    }
    
    func getExportInfo() -> [ExportInfo] {
        let files = listExportedFiles()
        
        // Group by base name (emotion_timestamp)
        var groups: [String: (mesh: URL?, audio: URL?)] = [:]
        
        for file in files {
            let filename = file.deletingPathExtension().lastPathComponent
            let components = filename.split(separator: "_")
            
            // Extract base name without extension suffix
            var baseName = filename
            if filename.hasSuffix("_mesh") {
                baseName = String(filename.dropLast(5))
            } else if filename.hasSuffix("_audio") {
                baseName = String(filename.dropLast(6))
            }
            
            if groups[baseName] == nil {
                groups[baseName] = (nil, nil)
            }
            
            if file.pathExtension == "json" {
                groups[baseName]?.mesh = file
            } else if file.pathExtension == "wav" {
                groups[baseName]?.audio = file
            }
        }
        
        // Convert to ExportInfo array
        var exports: [ExportInfo] = []
        
        for (baseName, urls) in groups {
            let components = baseName.split(separator: "_")
            let emotion = components.first.map(String.init) ?? "unknown"
            
            // Parse timestamp
            let timestampString = components.dropFirst().joined(separator: "_")
            let formatter = ISO8601DateFormatter()
            let timestamp = formatter.date(from: timestampString) ?? Date()
            
            // Calculate total size
            var totalSize = 0
            if let meshURL = urls.mesh {
                let values = try? meshURL.resourceValues(forKeys: [.fileSizeKey])
                totalSize += values?.fileSize ?? 0
            }
            if let audioURL = urls.audio {
                let values = try? audioURL.resourceValues(forKeys: [.fileSizeKey])
                totalSize += values?.fileSize ?? 0
            }
            
            exports.append(ExportInfo(
                emotion: emotion,
                timestamp: timestamp,
                meshFileURL: urls.mesh,
                audioFileURL: urls.audio,
                totalSize: totalSize
            ))
        }
        
        return exports.sorted { $0.timestamp > $1.timestamp }
    }
    
    // MARK: - Validation
    
    func validateExport(meshURL: URL, audioURL: URL) -> (isValid: Bool, message: String) {
        // Check if files exist
        guard FileManager.default.fileExists(atPath: meshURL.path) else {
            return (false, "Mesh file not found")
        }
        
        guard FileManager.default.fileExists(atPath: audioURL.path) else {
            return (false, "Audio file not found")
        }
        
        // Validate JSON structure
        do {
            let jsonData = try Data(contentsOf: meshURL)
            if let json = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any] {
                guard let vertices = json["vertices"] as? [[[Float]]] else {
                    return (false, "Invalid mesh format: missing vertices")
                }
                
                guard !vertices.isEmpty else {
                    return (false, "No face data captured")
                }
                
                let frameCount = vertices.count
                if frameCount < 10 {
                    return (false, "Warning: Only \(frameCount) frames captured (recommended: 60+)")
                }
            }
        } catch {
            return (false, "Failed to validate mesh file: \(error.localizedDescription)")
        }
        
        // Validate audio file size
        do {
            let audioAttributes = try FileManager.default.attributesOfItem(atPath: audioURL.path)
            if let fileSize = audioAttributes[.size] as? Int {
                if fileSize < 1000 {
                    return (false, "Audio file too small: \(fileSize) bytes")
                }
            }
        } catch {
            return (false, "Failed to validate audio file: \(error.localizedDescription)")
        }
        
        return (true, "Export is valid")
    }
}
