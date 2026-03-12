//
//  ExportedFilesView.swift
//  facedetection
//
//  Created by Minjae Kim on 11/23/25.
//

import SwiftUI

struct ExportedFilesView: View {
    @State private var exports: [DataExportManager.ExportInfo] = []
    @State private var showingDeleteAlert = false
    @State private var showingShareSheet = false
    
    var body: some View {
        NavigationView {
            List {
                if exports.isEmpty {
                    VStack(spacing: 20) {
                        Image(systemName: "tray")
                            .font(.system(size: 60))
                            .foregroundStyle(.secondary)
                        
                        Text("No recordings yet")
                            .font(.headline)
                        
                        Text("Start recording emotions to see your data here")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                } else {
                    ForEach(exports.indices, id: \.self) { index in
                        ExportRow(export: exports[index])
                    }
                    .onDelete(perform: deleteExports)
                }
            }
            .navigationTitle("Exported Data")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button(action: {
                            showingShareSheet = true
                        }) {
                            Label("Share All", systemImage: "square.and.arrow.up")
                        }
                        .disabled(exports.isEmpty)
                        
                        Button(role: .destructive, action: {
                            showingDeleteAlert = true
                        }) {
                            Label("Delete All", systemImage: "trash")
                        }
                        .disabled(exports.isEmpty)
                        
                        Button(action: {
                            refreshExports()
                        }) {
                            Label("Refresh", systemImage: "arrow.clockwise")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .onAppear {
                refreshExports()
            }
            .alert("Delete All Recordings?", isPresented: $showingDeleteAlert) {
                Button("Cancel", role: .cancel) { }
                Button("Delete", role: .destructive) {
                    deleteAllExports()
                }
            } message: {
                Text("This action cannot be undone. All \(exports.count) recording(s) will be permanently deleted.")
            }
            .sheet(isPresented: $showingShareSheet) {
                ShareAllFilesSheet()
            }
        }
    }
    
    private func refreshExports() {
        exports = DataExportManager.shared.getExportInfo()
    }
    
    private func deleteExports(at offsets: IndexSet) {
        for index in offsets {
            let export = exports[index]
            
            do {
                if let meshURL = export.meshFileURL {
                    try DataExportManager.shared.deleteFile(url: meshURL)
                }
                if let audioURL = export.audioFileURL {
                    try DataExportManager.shared.deleteFile(url: audioURL)
                }
            } catch {
                print("Failed to delete files: \(error)")
            }
        }
        
        refreshExports()
    }
    
    private func deleteAllExports() {
        do {
            try DataExportManager.shared.deleteAllFiles()
            refreshExports()
        } catch {
            print("Failed to delete all files: \(error)")
        }
    }
}

struct ExportRow: View {
    let export: DataExportManager.ExportInfo
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Emotion badge
                Text(export.emotion.capitalized)
                    .font(.headline)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(emotionColor(for: export.emotion))
                    .foregroundStyle(.white)
                    .cornerRadius(8)
                
                Spacer()
                
                // File size
                Text(DataExportManager.shared.formatBytes(export.totalSize))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            // Timestamp
            Text(formatDate(export.timestamp))
                .font(.subheadline)
                .foregroundStyle(.secondary)
            
            // Files status
            HStack(spacing: 16) {
                Label {
                    Text("Mesh")
                } icon: {
                    Image(systemName: export.meshFileURL != nil ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .foregroundStyle(export.meshFileURL != nil ? .green : .red)
                }
                .font(.caption)
                
                Label {
                    Text("Audio")
                } icon: {
                    Image(systemName: export.audioFileURL != nil ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .foregroundStyle(export.audioFileURL != nil ? .green : .red)
                }
                .font(.caption)
            }
        }
        .padding(.vertical, 4)
    }
    
    private func emotionColor(for emotion: String) -> Color {
        switch emotion.lowercased() {
        case "joy", "contentment", "pride", "gratitude", "hope":
            return .green
        case "sadness", "disappointment", "despair", "resignation":
            return .blue
        case "anger", "disgust", "envy":
            return .red
        case "fear", "guilt", "shame":
            return .purple
        case "surprise":
            return .orange
        case "affection":
            return .pink
        case "regret", "nostalgia":
            return .indigo
        default:
            return .gray
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

struct ShareAllFilesSheet: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        let controller = UIViewController()
        
        let files = DataExportManager.shared.listExportedFiles()
        
        if !files.isEmpty {
            let activityVC = UIActivityViewController(activityItems: files, applicationActivities: nil)
            
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
        
        return controller
    }
    
    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {
        // No update needed
    }
}

#Preview {
    ExportedFilesView()
}
