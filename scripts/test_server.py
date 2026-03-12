#!/usr/bin/env python3
"""
Simple WebSocket test server to verify iOS app connectivity

Usage:
    python scripts/test_server.py
"""

import asyncio
import websockets
import json
from datetime import datetime


async def handle_client(websocket, path):
    """Handle incoming WebSocket connections"""
    client_addr = websocket.remote_address
    print(f"✅ Client connected from {client_addr}")

    try:
        async for message in websocket:
            # Parse and log the message
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')

                if msg_type == 'face_data':
                    frame = data.get('frame', -1)
                    vertices_count = len(data.get('vertices', []))
                    blendshapes = data.get('blendshapes', {})
                    blendshapes_count = len(blendshapes) if blendshapes else 0

                    print(f"📦 Frame {frame}: {vertices_count} vertices, {blendshapes_count} BlendShapes")

                    # Show some BlendShape values if available
                    if blendshapes and frame % 30 == 0:  # Every second at 30fps
                        print("   BlendShapes sample:")
                        for key in ['jawOpen', 'mouthSmileLeft', 'mouthFrownLeft', 'eyeBlinkLeft']:
                            if key in blendshapes:
                                print(f"     {key}: {blendshapes[key]:.3f}")

                elif msg_type == 'recording_start':
                    emotion = data.get('emotion', 'unknown')
                    print(f"🎬 Recording started: {emotion}")

                elif msg_type == 'recording_stop':
                    emotion = data.get('emotion', 'unknown')
                    frame_count = data.get('frame_count', 0)
                    print(f"🛑 Recording stopped: {emotion}, {frame_count} frames")

                else:
                    print(f"📨 Message type: {msg_type}")

            except json.JSONDecodeError:
                print(f"❌ Invalid JSON received")
            except Exception as e:
                print(f"❌ Error processing message: {e}")

    except websockets.ConnectionClosed:
        print(f"📴 Client disconnected: {client_addr}")
    except Exception as e:
        print(f"❌ Connection error: {e}")


async def main():
    """Run the test server"""
    HOST = '0.0.0.0'  # Listen on all interfaces
    PORT = 8765

    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print("=" * 60)
    print("🚀 WebSocket Test Server")
    print("=" * 60)
    print(f"📍 Listening on: ws://{HOST}:{PORT}")
    print(f"💻 Your computer's IP: {local_ip}")
    print(f"📱 Configure iOS app to connect to: ws://{local_ip}:{PORT}")
    print("=" * 60)
    print("\n⚠️  Make sure your iPhone and computer are on the same network!")
    print("\nWaiting for connections... (Press Ctrl+C to stop)\n")

    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if port 8765 is already in use")
        print("2. Try: pip install websockets")
        print("3. Check firewall settings")