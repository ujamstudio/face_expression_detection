#!/usr/bin/env python3
"""
Emotion Data Collection Server
Receives face tracking data from iOS app and saves to emotion/data/streaming

Usage:
    python scripts/emotion_server.py
"""

import asyncio
import websockets
import json
from datetime import datetime
from pathlib import Path
import sys

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent  # emotion directory
DATA_DIR = PROJECT_ROOT / "data" / "streaming"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Add src to path for classifier
sys.path.append(str(PROJECT_ROOT / "src"))

print(f"📁 Data will be saved to: {DATA_DIR}")

class EmotionDataCollector:
    def __init__(self):
        self.current_recording = None
        self.frames_received = 0
        self.total_recordings = 0

        # Try to load classifier
        self.classifier = None
        try:
            from models.rule_based_classifier import RuleBasedEmotionClassifier
            self.classifier = RuleBasedEmotionClassifier()
            print("✅ Classifier loaded for real-time analysis")
        except:
            print("⚠️  Classifier not available")

    async def handle_client(self, websocket):
        """Handle WebSocket connection"""
        client_addr = websocket.remote_address
        print(f"✅ Client connected from {client_addr}")

        try:
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')

                if msg_type == 'recording_start':
                    self.start_recording(data)

                elif msg_type == 'face_data':
                    self.process_frame(data)

                elif msg_type == 'recording_stop':
                    self.stop_recording(data)

                elif msg_type == 'frame':
                    self.process_frame(data)

        except websockets.ConnectionClosed:
            print(f"📴 Client disconnected: {client_addr}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def start_recording(self, data):
        """Start new recording"""
        emotion = data.get('emotion', 'unknown')
        print(f"🎬 Recording started: {emotion}")

        self.current_recording = {
            'emotion': emotion,
            'vertices': [],
            'blendshapes': [],
            'timestamps': [],
            'start_time': datetime.now()
        }
        self.frames_received = 0

    def process_frame(self, data):
        """Process incoming frame data"""
        if not self.current_recording:
            return

        frame_num = data.get('frame', self.frames_received)
        vertices = data.get('vertices', [])
        blendshapes = data.get('blendshapes', {})

        # Store data
        self.current_recording['vertices'].append(vertices)
        self.current_recording['blendshapes'].append(blendshapes)
        self.current_recording['timestamps'].append(data.get('timestamp', 0))

        self.frames_received += 1

        # Log every 30 frames (1 second at 30fps)
        if frame_num % 30 == 0:
            print(f"📦 Frame {frame_num}: {len(vertices)} vertices, {len(blendshapes)} BlendShapes")

            # Show sample BlendShapes
            if blendshapes:
                print("   BlendShapes sample:")
                for key in ['jawOpen', 'mouthSmileLeft', 'mouthFrownLeft', 'eyeBlinkLeft', 'cheekSquintLeft']:
                    if key in blendshapes:
                        print(f"     {key}: {blendshapes[key]:.3f}")

        # Real-time classification
        if self.classifier and blendshapes and frame_num % 30 == 0:
            try:
                result = self.classifier.classify({'blendshapes': blendshapes})
                predicted = result['emotion']
                confidence = result['confidence']
                expected = self.current_recording['emotion']

                if predicted != expected:
                    print(f"   🤖 Prediction: {predicted} ({confidence:.1%}) [Expected: {expected}]")
            except:
                pass

    def stop_recording(self, data):
        """Stop recording and save"""
        if not self.current_recording:
            return

        emotion = data.get('emotion', 'unknown')
        frame_count = data.get('frame_count', self.frames_received)

        print(f"🛑 Recording stopped: {emotion}, {frame_count} frames")

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = DATA_DIR / f"{emotion}_{timestamp}.json"

        save_data = {
            'emotion': emotion,
            'timestamp': self.current_recording['start_time'].isoformat(),
            'frame_count': len(self.current_recording['vertices']),
            'recording_duration': (datetime.now() - self.current_recording['start_time']).total_seconds(),
            'vertices': self.current_recording['vertices'],
            'blendshapes': self.current_recording['blendshapes']
        }

        try:
            with open(filename, 'w') as f:
                json.dump(save_data, f)
            print(f"💾 Saved to: {filename}")

            # Analyze if classifier available
            if self.classifier and self.current_recording['blendshapes']:
                self.analyze_recording()

        except Exception as e:
            print(f"❌ Failed to save: {e}")

        self.current_recording = None
        self.total_recordings += 1
        print(f"📊 Total recordings: {self.total_recordings}")

    def analyze_recording(self):
        """Analyze the completed recording"""
        if not self.current_recording or not self.classifier:
            return

        emotion_label = self.current_recording['emotion']
        blendshapes_list = self.current_recording['blendshapes']

        # Classify each frame
        predictions = []
        for bs in blendshapes_list:
            if bs:
                try:
                    result = self.classifier.classify({'blendshapes': bs})
                    predictions.append(result['emotion'])
                except:
                    pass

        if predictions:
            from collections import Counter
            emotion_counts = Counter(predictions)
            most_common = emotion_counts.most_common(1)[0]
            predicted = most_common[0]
            accuracy = most_common[1] / len(predictions)

            print(f"\n📈 Analysis Results:")
            print(f"   Expected: {emotion_label}")
            print(f"   Predicted: {predicted} ({accuracy:.1%} of frames)")
            print(f"   Distribution: {dict(emotion_counts)}")

            if predicted == emotion_label:
                print(f"   ✅ Correct classification!")
            else:
                print(f"   ⚠️  Mismatch detected")
            print()


async def main():
    """Run the server"""
    HOST = '0.0.0.0'
    PORT = 8765

    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    collector = EmotionDataCollector()

    print("=" * 60)
    print("🚀 Emotion Data Collection Server")
    print("=" * 60)
    print(f"📍 Listening on: ws://{HOST}:{PORT}")
    print(f"💻 Your Mac's IP: {local_ip}")
    print(f"📱 iOS app should connect to: ws://{local_ip}:{PORT}")
    print(f"📁 Data saves to: {DATA_DIR}")
    print("=" * 60)
    print("\nWaiting for connections... (Press Ctrl+C to stop)\n")

    async with websockets.serve(collector.handle_client, HOST, PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    # First kill the test server
    import subprocess
    try:
        subprocess.run(['pkill', '-f', 'test_server.py'], check=False)
        print("Stopped test server")
    except:
        pass

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        print(f"📁 Data saved to: {DATA_DIR}")