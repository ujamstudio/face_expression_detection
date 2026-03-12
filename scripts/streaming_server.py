#!/usr/bin/env python3
"""
WebSocket Server for receiving face tracking data from iOS app

This server receives:
- 3D face mesh vertices
- ARKit BlendShapes (52 parameters)
- Audio data
- Emotion labels

Usage:
    python scripts/streaming_server.py --host 0.0.0.0 --port 8765
"""

import asyncio
import websockets
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path for classifier access
sys.path.append(str(Path(__file__).parent.parent / 'src'))


class StreamingServer:
    def __init__(self, save_dir: Path = None):
        """
        Initialize streaming server

        Args:
            save_dir: Directory to save received data (optional)
        """
        self.save_dir = save_dir or Path("data/streaming")
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.current_recording = None
        self.frame_buffer = []
        self.clients = set()

        # Statistics
        self.stats = {
            'frames_received': 0,
            'bytes_received': 0,
            'recordings_completed': 0
        }

        # Try to load classifier for real-time analysis
        self.classifier = None
        try:
            from models.rule_based_classifier import RuleBasedEmotionClassifier
            self.classifier = RuleBasedEmotionClassifier()
            logger.info("✅ Rule-based classifier loaded for real-time analysis")
        except Exception as e:
            logger.warning(f"⚠️  Classifier not available: {e}")

    async def handle_client(self, websocket):
        """Handle a WebSocket client connection"""
        client_addr = websocket.remote_address
        logger.info(f"🔗 Client connected from {client_addr}")
        self.clients.add(websocket)

        try:
            async for message in websocket:
                await self.process_message(message, websocket)

        except websockets.ConnectionClosed:
            logger.info(f"📴 Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"❌ Error handling client {client_addr}: {e}")
        finally:
            self.clients.discard(websocket)

    async def process_message(self, message: str, websocket):
        """Process incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')

            if msg_type == 'recording_start':
                await self.handle_recording_start(data)

            elif msg_type == 'face_data':
                await self.handle_face_data(data)

            elif msg_type == 'audio_chunk':
                await self.handle_audio_chunk(data)

            elif msg_type == 'frame':
                await self.handle_frame(data)

            elif msg_type == 'recording_stop':
                await self.handle_recording_stop(data)

            else:
                logger.warning(f"Unknown message type: {msg_type}")

            # Update statistics
            self.stats['bytes_received'] += len(message)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def handle_recording_start(self, data: Dict[str, Any]):
        """Handle recording start event"""
        emotion = data.get('emotion', 'unknown')
        timestamp = data.get('timestamp', datetime.now().isoformat())

        logger.info(f"🎬 Recording started: {emotion}")

        self.current_recording = {
            'emotion': emotion,
            'start_time': timestamp,
            'frames': [],
            'audio_chunks': []
        }
        self.frame_buffer = []

    async def handle_face_data(self, data: Dict[str, Any]):
        """Handle face tracking data"""
        frame_num = data.get('frame', -1)
        vertices = data.get('vertices', [])
        blendshapes = data.get('blendshapes', {})
        emotion = data.get('emotion', 'unknown')

        # Store frame data
        frame_data = {
            'frame_number': frame_num,
            'vertices': vertices,
            'blendshapes': blendshapes,
            'timestamp': data.get('timestamp', 0)
        }

        if self.current_recording:
            self.current_recording['frames'].append(frame_data)

        self.frame_buffer.append(frame_data)
        self.stats['frames_received'] += 1

        # Real-time analysis with classifier
        if self.classifier and blendshapes:
            try:
                result = self.classifier.classify({'blendshapes': blendshapes})
                predicted = result['emotion']
                confidence = result['confidence']

                # Log if prediction differs from label
                if predicted != emotion:
                    logger.info(f"🤖 Frame {frame_num}: Label={emotion}, Predicted={predicted} ({confidence:.1%})")

            except Exception as e:
                logger.debug(f"Classifier error: {e}")

        # Log progress every 30 frames (1 second at 30fps)
        if frame_num % 30 == 0:
            logger.info(f"📊 Frame {frame_num}: {len(vertices)} vertices, {len(blendshapes)} blendshapes")

    async def handle_audio_chunk(self, data: Dict[str, Any]):
        """Handle audio data chunk"""
        chunk_num = data.get('chunk', -1)
        size = data.get('size', 0)

        if self.current_recording:
            self.current_recording['audio_chunks'].append({
                'chunk_number': chunk_num,
                'size': size,
                'timestamp': data.get('timestamp', 0)
            })

        logger.debug(f"🔊 Audio chunk {chunk_num}: {size} bytes")

    async def handle_frame(self, data: Dict[str, Any]):
        """Handle combined frame (face + audio)"""
        frame_num = data.get('frame', -1)
        vertices = data.get('vertices', [])
        blendshapes = data.get('blendshapes', {})
        audio_b64 = data.get('audio', '')

        # Process as face data
        await self.handle_face_data(data)

        # Handle audio if present
        if audio_b64:
            logger.debug(f"🎞️ Frame {frame_num}: Combined face + audio")

    async def handle_recording_stop(self, data: Dict[str, Any]):
        """Handle recording stop event"""
        emotion = data.get('emotion', 'unknown')
        frame_count = data.get('frame_count', 0)

        logger.info(f"🛑 Recording stopped: {emotion}, {frame_count} frames")

        if self.current_recording:
            # Save recording to file
            await self.save_recording()

            # Analyze recording
            await self.analyze_recording()

            self.stats['recordings_completed'] += 1
            self.current_recording = None

    async def save_recording(self):
        """Save current recording to disk"""
        if not self.current_recording:
            return

        emotion = self.current_recording['emotion']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{emotion}_{timestamp}.json"
        filepath = self.save_dir / filename

        # Prepare data for saving
        save_data = {
            'emotion': emotion,
            'timestamp': self.current_recording['start_time'],
            'frame_count': len(self.current_recording['frames']),
            'vertices': [],
            'blendshapes': []
        }

        # Extract vertices and blendshapes
        for frame in self.current_recording['frames']:
            save_data['vertices'].append(frame['vertices'])
            save_data['blendshapes'].append(frame['blendshapes'])

        # Save to file
        try:
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)
            logger.info(f"💾 Saved recording to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save recording: {e}")

    async def analyze_recording(self):
        """Analyze completed recording"""
        if not self.current_recording or not self.classifier:
            return

        frames = self.current_recording['frames']
        emotion_label = self.current_recording['emotion']

        # Analyze all frames
        predictions = []
        for frame in frames:
            if frame['blendshapes']:
                try:
                    result = self.classifier.classify({'blendshapes': frame['blendshapes']})
                    predictions.append(result['emotion'])
                except:
                    pass

        if predictions:
            # Calculate accuracy
            from collections import Counter
            emotion_counts = Counter(predictions)
            most_common = emotion_counts.most_common(1)[0]
            predicted_emotion = most_common[0]
            prediction_rate = most_common[1] / len(predictions)

            # Log analysis
            logger.info(f"📈 Recording Analysis:")
            logger.info(f"   Label: {emotion_label}")
            logger.info(f"   Predicted: {predicted_emotion} ({prediction_rate:.1%} of frames)")
            logger.info(f"   Distribution: {dict(emotion_counts)}")

            # Check accuracy
            if predicted_emotion == emotion_label:
                logger.info(f"   ✅ Correct prediction!")
            else:
                logger.warning(f"   ⚠️  Mismatch: expected {emotion_label}, got {predicted_emotion}")

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            **self.stats,
            'active_clients': len(self.clients),
            'recording_active': self.current_recording is not None
        }

    async def broadcast_stats(self):
        """Broadcast statistics to all clients periodically"""
        while True:
            await asyncio.sleep(5)  # Every 5 seconds

            if self.clients:
                stats = self.get_stats()
                message = json.dumps({
                    'type': 'stats',
                    'data': stats
                })

                # Send to all connected clients
                disconnected = set()
                for client in self.clients:
                    try:
                        await client.send(message)
                    except:
                        disconnected.add(client)

                # Remove disconnected clients
                self.clients -= disconnected


async def main(host: str, port: int, save_dir: Optional[str] = None):
    """Run the WebSocket server"""

    # Get local IP address for display
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Create server
    save_path = Path(save_dir) if save_dir else None
    server = StreamingServer(save_dir=save_path)

    logger.info("=" * 70)
    logger.info("🚀 Face Tracking WebSocket Server")
    logger.info("=" * 70)
    logger.info(f"📍 Listening on: ws://{host}:{port}")
    logger.info(f"💻 Local IP: {local_ip}")
    logger.info(f"📱 iOS app should connect to: ws://{local_ip}:{port}")
    logger.info(f"📁 Saving data to: {server.save_dir}")
    logger.info("=" * 70)
    logger.info("Waiting for connections...")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("")

    # Start statistics broadcaster
    asyncio.create_task(server.broadcast_stats())

    # Start WebSocket server
    async with websockets.serve(server.handle_client, host, port):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='WebSocket server for iOS face tracking data'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind to (0.0.0.0 for all interfaces)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='Port to listen on'
    )
    parser.add_argument(
        '--save-dir',
        type=str,
        default='data/streaming',
        help='Directory to save received data'
    )

    args = parser.parse_args()

    try:
        asyncio.run(main(args.host, args.port, args.save_dir))
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")