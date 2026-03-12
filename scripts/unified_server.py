#!/usr/bin/env python3
"""
Unified Emotion Server with Real-time Classification

Features:
- Receives face data from iOS app (vertices + BlendShapes)
- Real-time emotion classification using rule-based classifier
- Broadcasts data to connected visualizers
- Saves recordings to data/streaming/

Usage:
    python scripts/unified_server.py
"""

import asyncio
import websockets
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import sys

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "streaming"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Add src to path for classifier
sys.path.insert(0, str(PROJECT_ROOT / "src"))

print(f"📁 Data saves to: {DATA_DIR}")


class UnifiedEmotionServer:
    """Unified server with classification and visualization support"""

    def __init__(self):
        # Connected clients
        self.ios_clients = set()        # iOS apps sending data
        self.visualizer_clients = set()  # Visualizers receiving data

        # Current recording state
        self.current_recording = None
        self.frames_received = 0
        self.total_recordings = 0

        # Classification stats
        self.classification_results = defaultdict(int)

        # Load classifier
        self.classifier = None
        self._load_classifier()

    def _load_classifier(self):
        """Load the rule-based classifier"""
        try:
            from models.rule_based_classifier import RuleBasedEmotionClassifier
            self.classifier = RuleBasedEmotionClassifier()
            print("✅ Rule-based classifier loaded")
        except Exception as e:
            print(f"⚠️  Classifier not loaded: {e}")
            print("   Classification will be disabled")

    async def handle_client(self, websocket, path):
        """Handle new WebSocket connection"""
        client_addr = websocket.remote_address
        client_type = "unknown"

        try:
            # Wait for first message to determine client type
            first_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(first_msg)

            # Check if it's a visualizer
            if data.get("type") == "visualizer_connect":
                client_type = "visualizer"
                self.visualizer_clients.add(websocket)
                print(f"🎨 Visualizer connected: {client_addr}")

                # Send current state
                await websocket.send(json.dumps({
                    "type": "server_state",
                    "recording": self.current_recording is not None,
                    "total_recordings": self.total_recordings
                }))
            else:
                # It's an iOS client
                client_type = "ios"
                self.ios_clients.add(websocket)
                print(f"📱 iOS client connected: {client_addr}")

                # Process the first message
                await self._process_message(data, websocket)

            # Process subsequent messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data, websocket)
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON from {client_type}")
                except Exception as e:
                    print(f"❌ Error processing message: {e}")

        except asyncio.TimeoutError:
            print(f"⏰ Client timeout: {client_addr}")
        except websockets.ConnectionClosed:
            print(f"📴 {client_type.capitalize()} disconnected: {client_addr}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
        finally:
            # Clean up
            self.ios_clients.discard(websocket)
            self.visualizer_clients.discard(websocket)

    async def _process_message(self, data, websocket):
        """Process incoming message"""
        msg_type = data.get("type", "unknown")

        if msg_type == "recording_start":
            await self._handle_recording_start(data)

        elif msg_type in ["face_data", "frame"]:
            await self._handle_face_data(data)

        elif msg_type == "recording_stop":
            await self._handle_recording_stop(data)

        elif msg_type == "visualizer_connect":
            pass  # Already handled in handle_client

        else:
            print(f"Unknown message type: {msg_type}")

    async def _handle_recording_start(self, data):
        """Handle recording start"""
        emotion = data.get("emotion", "unknown")

        print(f"\n🎬 Recording started: {emotion}")

        self.current_recording = {
            "emotion": emotion,
            "vertices": [],
            "blendshapes": [],
            "classifications": [],
            "start_time": datetime.now()
        }
        self.frames_received = 0
        self.classification_results.clear()

        # Broadcast to visualizers
        await self._broadcast_to_visualizers({
            "type": "recording_start",
            "emotion": emotion,
            "timestamp": datetime.now().isoformat()
        })

    async def _handle_face_data(self, data):
        """Handle face tracking data with classification"""
        if not self.current_recording:
            return

        frame_num = data.get("frame", self.frames_received)
        vertices = data.get("vertices", [])
        blendshapes = data.get("blendshapes", {})
        emotion_label = self.current_recording["emotion"]

        # Store data
        self.current_recording["vertices"].append(vertices)
        self.current_recording["blendshapes"].append(blendshapes)
        self.frames_received += 1

        # Classify emotion if classifier available and BlendShapes present
        classification = None
        if self.classifier and blendshapes:
            try:
                classification = self.classifier.classify({"blendshapes": blendshapes})
                predicted = classification["emotion"]
                confidence = classification["confidence"]

                # Track classification results
                self.classification_results[predicted] += 1
                self.current_recording["classifications"].append(predicted)

                # Log if prediction differs from label (every 30 frames)
                if frame_num % 30 == 0:
                    match = "✅" if predicted == emotion_label else "❌"
                    print(f"   Frame {frame_num}: {predicted} ({confidence:.0%}) {match}")

            except Exception as e:
                if frame_num == 0:
                    print(f"   Classification error: {e}")

        # Log every 30 frames
        if frame_num % 30 == 0:
            print(f"📦 Frame {frame_num}: {len(vertices)} vertices, {len(blendshapes)} BlendShapes")

            # Show top BlendShapes
            if blendshapes:
                top_bs = sorted(blendshapes.items(), key=lambda x: x[1], reverse=True)[:3]
                for name, value in top_bs:
                    print(f"      {name}: {value:.3f}")

        # Broadcast to visualizers (with classification)
        broadcast_data = {
            "type": "face_data",
            "frame": frame_num,
            "vertices": vertices,
            "blendshapes": blendshapes,
            "emotion": emotion_label,
            "timestamp": data.get("timestamp", 0)
        }

        if classification:
            broadcast_data["classification"] = {
                "predicted": classification["emotion"],
                "confidence": classification["confidence"],
                "all_scores": classification.get("all_scores", {})
            }

        await self._broadcast_to_visualizers(broadcast_data)

    async def _handle_recording_stop(self, data):
        """Handle recording stop with analysis"""
        if not self.current_recording:
            return

        emotion = data.get("emotion", self.current_recording["emotion"])
        frame_count = len(self.current_recording["vertices"])

        print(f"\n🛑 Recording stopped: {emotion}, {frame_count} frames")

        # Analyze classification results
        if self.classification_results:
            print("\n📊 Classification Analysis:")
            total = sum(self.classification_results.values())

            for emo, count in sorted(self.classification_results.items(),
                                    key=lambda x: x[1], reverse=True):
                pct = count / total * 100
                match = "◀" if emo == emotion else ""
                print(f"   {emo:12s}: {count:3d} frames ({pct:5.1f}%) {match}")

            # Accuracy
            correct = self.classification_results.get(emotion, 0)
            accuracy = correct / total * 100 if total > 0 else 0

            print(f"\n   Expected: {emotion}")
            print(f"   Accuracy: {accuracy:.1f}%")

            if accuracy >= 70:
                print("   ✅ Good classification!")
            elif accuracy >= 50:
                print("   ⚠️  Moderate classification")
            else:
                print("   ❌ Poor classification - check expression")

        # Save recording
        await self._save_recording(emotion)

        # Broadcast to visualizers
        await self._broadcast_to_visualizers({
            "type": "recording_stop",
            "emotion": emotion,
            "frame_count": frame_count,
            "classification_results": dict(self.classification_results),
            "timestamp": datetime.now().isoformat()
        })

        # Reset state
        self.current_recording = None
        self.total_recordings += 1
        print(f"\n📊 Total recordings: {self.total_recordings}\n")

    async def _save_recording(self, emotion):
        """Save recording to file"""
        if not self.current_recording:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = DATA_DIR / f"{emotion}_{timestamp}.json"

        save_data = {
            "emotion": emotion,
            "timestamp": self.current_recording["start_time"].isoformat(),
            "frame_count": len(self.current_recording["vertices"]),
            "recording_duration": (datetime.now() - self.current_recording["start_time"]).total_seconds(),
            "vertices": self.current_recording["vertices"],
            "blendshapes": self.current_recording["blendshapes"],
            "classification_results": dict(self.classification_results)
        }

        try:
            with open(filename, "w") as f:
                json.dump(save_data, f)
            print(f"💾 Saved: {filename.name}")
        except Exception as e:
            print(f"❌ Save failed: {e}")

    async def _broadcast_to_visualizers(self, data):
        """Broadcast data to all connected visualizers"""
        if not self.visualizer_clients:
            return

        message = json.dumps(data)
        disconnected = set()

        for client in self.visualizer_clients:
            try:
                await client.send(message)
            except websockets.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                print(f"Broadcast error: {e}")
                disconnected.add(client)

        # Clean up disconnected clients
        self.visualizer_clients -= disconnected


async def main():
    """Run the unified server"""
    HOST = "0.0.0.0"
    PORT = 8765

    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    server = UnifiedEmotionServer()

    print("=" * 60)
    print("🚀 Unified Emotion Server")
    print("=" * 60)
    print(f"📍 Listening on: ws://{HOST}:{PORT}")
    print(f"💻 Your Mac's IP: {local_ip}")
    print(f"📱 iOS app connects to: ws://{local_ip}:{PORT}")
    print(f"🎨 Visualizer connects to: ws://{local_ip}:{PORT}")
    print(f"📁 Data saves to: {DATA_DIR}")
    print("=" * 60)
    print("\nFeatures:")
    print("  ✓ Real-time BlendShapes classification")
    print("  ✓ Live visualization broadcast")
    print("  ✓ Automatic data saving")
    print("  ✓ Classification accuracy analysis")
    print("=" * 60)
    print("\nWaiting for connections... (Press Ctrl+C to stop)\n")

    async with websockets.serve(server.handle_client, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        print(f"📁 Data saved to: {DATA_DIR}")