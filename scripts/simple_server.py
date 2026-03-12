#!/usr/bin/env python3
"""
Simple WebSocket server that saves data to emotion/data/streaming

Usage:
    python scripts/simple_server.py
"""

import asyncio
import websockets
import json
from datetime import datetime
from pathlib import Path

# Setup data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "streaming"
DATA_DIR.mkdir(parents=True, exist_ok=True)

print(f"📁 Data will be saved to: {DATA_DIR.absolute()}")

# Global state
current_recording = None
frame_count = 0

# Connected visualizer clients
visualizer_clients = set()


async def broadcast_to_visualizers(message: str):
    """Send message to all connected visualizer clients"""
    if not visualizer_clients:
        return
    disconnected = set()
    for client in visualizer_clients:
        try:
            await client.send(message)
        except Exception:
            disconnected.add(client)
    visualizer_clients.difference_update(disconnected)


async def handle_client(websocket):
    """Handle WebSocket connection"""
    global current_recording, frame_count

    client_addr = websocket.remote_address
    print(f"✅ Client connected from {client_addr}")

    is_visualizer = False

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')

                # Visualizer registration
                if msg_type == 'visualizer_connect':
                    is_visualizer = True
                    visualizer_clients.add(websocket)
                    print(f"🎨 Visualizer connected from {client_addr}")
                    continue

                if msg_type == 'recording_start':
                    emotion = data.get('emotion', 'unknown')
                    print(f"🎬 Recording started: {emotion}")
                    current_recording = {
                        'emotion': emotion,
                        'vertices': [],
                        'blendshapes': [],
                        'start_time': datetime.now().isoformat()
                    }
                    frame_count = 0
                    await broadcast_to_visualizers(message)

                elif msg_type in ['face_data', 'frame']:
                    if current_recording:
                        frame_num = data.get('frame', frame_count)
                        vertices = data.get('vertices', [])
                        blendshapes = data.get('blendshapes', {})

                        current_recording['vertices'].append(vertices)
                        current_recording['blendshapes'].append(blendshapes)
                        frame_count += 1

                        # Log progress every 30 frames
                        if frame_num % 30 == 0:
                            print(f"📦 Frame {frame_num}: {len(vertices)} vertices, {len(blendshapes)} BlendShapes")

                            # Show sample BlendShapes
                            if blendshapes and isinstance(blendshapes, dict):
                                print("   Sample BlendShapes:")
                                for key in ['jawOpen', 'mouthFrownLeft', 'eyeBlinkLeft']:
                                    if key in blendshapes:
                                        print(f"     {key}: {blendshapes[key]:.3f}")

                    await broadcast_to_visualizers(message)

                elif msg_type == 'recording_stop':
                    if current_recording:
                        emotion = data.get('emotion', current_recording['emotion'])
                        total_frames = len(current_recording['vertices'])
                        print(f"🛑 Recording stopped: {emotion}, {total_frames} frames")

                        # Save to file
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = DATA_DIR / f"{emotion}_{timestamp}.json"

                        save_data = {
                            'emotion': emotion,
                            'timestamp': current_recording['start_time'],
                            'frame_count': total_frames,
                            'vertices': current_recording['vertices'],
                            'blendshapes': current_recording['blendshapes']
                        }

                        with open(filename, 'w') as f:
                            json.dump(save_data, f)

                        print(f"💾 Saved to: {filename.name}")
                        print(f"   Full path: {filename.absolute()}")

                        current_recording = None
                        frame_count = 0
                        await broadcast_to_visualizers(message)

            except json.JSONDecodeError:
                print(f"❌ Invalid JSON received")
            except Exception as e:
                print(f"❌ Error processing message: {e}")

    except websockets.ConnectionClosed:
        print(f"📴 Client disconnected: {client_addr}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        if is_visualizer:
            visualizer_clients.discard(websocket)


async def main():
    """Run the server"""
    HOST = '0.0.0.0'
    PORT = 8765

    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print("=" * 60)
    print("🚀 Simple Emotion Data Server")
    print("=" * 60)
    print(f"📍 Listening on: ws://{HOST}:{PORT}")
    print(f"💻 Your Mac's IP: {local_ip}")
    print(f"📱 iOS app connects to: ws://{local_ip}:{PORT}")
    print(f"📁 Data saves to: {DATA_DIR.absolute()}")
    print("=" * 60)
    print("\nWaiting for connections... (Press Ctrl+C to stop)\n")

    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n👋 Server stopped")
        print(f"📁 Check your data at: {DATA_DIR.absolute()}")
