//
//  ARFaceTrackingView.swift
//  facedetection
//
//  Created by Minjae Kim on 11/23/25.
//

import SwiftUI
import UIKit
import ARKit

struct ARFaceTrackingView: UIViewControllerRepresentable {
    
    @Binding var isRecording: Bool
    @Binding var showMeshPoints: Bool
    var emotion: String
    var streamManager: LiveStreamManager?
    var onStartRecording: () -> Void
    var onStopRecording: () -> Void
    var onDataExported: (Bool, String) -> Void
    
    func makeUIViewController(context: Context) -> ARFaceTrackingViewController {
        let controller = ARFaceTrackingViewController()
        controller.streamManager = streamManager
        controller.onRecordingStatusChanged = { recording in
            DispatchQueue.main.async {
                isRecording = recording
            }
        }
        controller.onDataExported = { success, message in
            DispatchQueue.main.async {
                onDataExported(success, message)
            }
        }
        context.coordinator.controller = controller
        return controller
    }
    
    func updateUIViewController(_ uiViewController: ARFaceTrackingViewController, context: Context) {
        // Update stream manager reference
        uiViewController.streamManager = streamManager
        
        // Handle recording state changes from SwiftUI
        if isRecording && !uiViewController.isRecording {
            uiViewController.startRecording(emotion: emotion)
            onStartRecording()
        } else if !isRecording && uiViewController.isRecording {
            uiViewController.stopRecording()
            onStopRecording()
        }
        
        // Update mesh visualization
        uiViewController.toggleMeshVisualization(showMeshPoints)
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator {
        weak var controller: ARFaceTrackingViewController?
        
        func shareData() {
            controller?.shareData()
        }
    }
    
    static func dismantleUIViewController(_ uiViewController: ARFaceTrackingViewController, coordinator: Coordinator) {
        uiViewController.sceneView.session.pause()
    }
}
