//
//  ContentView.swift
//  facedetection
//
//  Created by Minjae Kim on 11/23/25.
//

import SwiftUI
import ARKit

struct ContentView: View {
    @State private var showMainApp = false
    @State private var deviceSupported = true
    
    var body: some View {
        if !deviceSupported {
            // Device not supported view
            VStack(spacing: 20) {
                Image(systemName: "faceid")
                    .font(.system(size: 80))
                    .foregroundStyle(.red)
                
                Text("TrueDepth Camera Required")
                    .font(.title)
                    .fontWeight(.bold)
                
                Text("This app requires an iPhone X or later with Face ID capability to capture 3D facial data.")
                    .font(.body)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 40)
            }
            .padding()
        } else if !showMainApp {
            // Welcome screen
            VStack(spacing: 30) {
                Spacer()
                
                Image(systemName: "face.smiling")
                    .font(.system(size: 100))
                    .foregroundStyle(.blue)
                
                Text("Emotion Data Capture")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                VStack(alignment: .leading, spacing: 15) {
                    FeatureRow(icon: "camera.fill", 
                             title: "3D Face Tracking", 
                             description: "Captures facial mesh using ARKit")
                    
                    FeatureRow(icon: "waveform", 
                             title: "Audio Recording", 
                             description: "Records synchronized voice data")
                    
                    FeatureRow(icon: "heart.fill", 
                             title: "20 Emotions", 
                             description: "Track joy, sadness, regret, and more")
                    
                    FeatureRow(icon: "square.and.arrow.up", 
                             title: "Easy Export", 
                             description: "Share data via AirDrop or Files")
                }
                .padding()
                
                Spacer()
                
                Button(action: {
                    showMainApp = true
                }) {
                    Text("Get Started")
                        .font(.title3)
                        .fontWeight(.semibold)
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue)
                        .cornerRadius(15)
                }
                .padding(.horizontal, 40)
                
                Text("This app requires camera and microphone access")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.bottom)
            }
            .padding()
        } else {
            // Main app with tabs
            TabView {
                EmotionSelectionView()
                    .tabItem {
                        Label("Record", systemImage: "record.circle")
                    }
                
                ExportedFilesView()
                    .tabItem {
                        Label("Exports", systemImage: "folder")
                    }
            }
        }
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(spacing: 15) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(.blue)
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            Spacer()
        }
    }
}

#Preview {
    ContentView()
}
