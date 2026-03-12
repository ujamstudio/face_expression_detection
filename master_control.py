#!/usr/bin/env python3
"""
Master Control Script for Unified Emotion + FaceDetection System
Manages servers, data collection, and analysis from one place
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import argparse

# Project paths
EMOTION_DIR = Path("/Users/kim/Desktop/emotion")
FACEDETECTION_DIR = Path("/Users/kim/Desktop/facedetection/facedetection/facedetection")
DATA_DIR = EMOTION_DIR / "data" / "streaming"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

def run_command(cmd, capture=True):
    """Run shell command"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True)
            return None
    except Exception as e:
        print(f"{Colors.RED}Error running command: {e}{Colors.END}")
        return None

def check_port(port):
    """Check if a port is in use"""
    result = run_command(f"lsof -i :{port} 2>/dev/null | grep LISTEN")
    return bool(result)

def get_pid(port):
    """Get PID of process using port"""
    result = run_command(f"lsof -i :{port} 2>/dev/null | grep LISTEN | awk '{{print $2}}'")
    return result if result else None

def status():
    """Check status of all servers"""
    print_header("🔍 System Status")

    # Check emotion server
    if check_port(8765):
        pid = get_pid(8765)
        print(f"{Colors.GREEN}✅ Emotion Server (8765): RUNNING [PID: {pid}]{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Emotion Server (8765): NOT RUNNING{Colors.END}")

    # Check visualizer
    if check_port(8766):
        pid = get_pid(8766)
        print(f"{Colors.GREEN}✅ Visualizer (8766): RUNNING [PID: {pid}]{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️  Visualizer (8766): NOT RUNNING{Colors.END}")

    # Check data directory
    if DATA_DIR.exists():
        json_files = list(DATA_DIR.glob("*.json"))
        print(f"\n{Colors.BLUE}📁 Data Directory: {DATA_DIR}{Colors.END}")
        print(f"   Total recordings: {len(json_files)}")

        if json_files:
            # Count by emotion
            emotions = {}
            for f in json_files:
                emotion = f.stem.split('_')[0]
                emotions[emotion] = emotions.get(emotion, 0) + 1

            print("   Recordings by emotion:")
            for emotion, count in sorted(emotions.items()):
                print(f"      {emotion}: {count}")

    # Show IP address
    ip = run_command("ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -1")
    print(f"\n{Colors.BLUE}💻 Your Mac's IP: {ip}{Colors.END}")
    print(f"{Colors.BLUE}📱 iOS app should connect to: ws://{ip}:8765{Colors.END}")

def start_emotion_server():
    """Start emotion data collection server"""
    print_header("🚀 Starting Emotion Server")

    if check_port(8765):
        print(f"{Colors.YELLOW}Server already running on port 8765{Colors.END}")
        return

    os.chdir(EMOTION_DIR)
    subprocess.Popen(["python", "scripts/simple_server.py"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)

    time.sleep(2)

    if check_port(8765):
        pid = get_pid(8765)
        print(f"{Colors.GREEN}✅ Emotion server started [PID: {pid}]{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Failed to start emotion server{Colors.END}")

def start_visualizer():
    """Start face mesh visualizer"""
    print_header("🎨 Starting Visualizer")

    if check_port(8766):
        print(f"{Colors.YELLOW}Visualizer already running on port 8766{Colors.END}")
        return

    os.chdir(FACEDETECTION_DIR)
    subprocess.Popen(["python", "visualizer.py", "--port", "8766"])

    time.sleep(2)

    if check_port(8766):
        pid = get_pid(8766)
        print(f"{Colors.GREEN}✅ Visualizer started [PID: {pid}]{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Failed to start visualizer{Colors.END}")

def stop_all():
    """Stop all servers"""
    print_header("🛑 Stopping All Servers")

    # Kill by port
    for port in [8765, 8766, 8767]:
        pid = get_pid(port)
        if pid:
            run_command(f"kill {pid}")
            print(f"   Stopped process on port {port} [PID: {pid}]")

    # Kill by name
    run_command("pkill -f 'simple_server.py|visualizer.py|test_server.py|emotion_server.py'")

    time.sleep(1)
    print(f"{Colors.GREEN}✅ All servers stopped{Colors.END}")

def validate_data():
    """Validate all collected data"""
    print_header("🔍 Validating Data")

    if not DATA_DIR.exists():
        print(f"{Colors.RED}Data directory not found{Colors.END}")
        return

    json_files = list(DATA_DIR.glob("*.json"))

    if not json_files:
        print(f"{Colors.YELLOW}No data files found{Colors.END}")
        return

    print(f"Found {len(json_files)} files to validate\n")

    valid_count = 0
    invalid_count = 0

    for file in json_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)

            # Check structure
            has_vertices = 'vertices' in data and len(data['vertices']) > 0
            has_blendshapes = 'blendshapes' in data and len(data['blendshapes']) > 0

            if has_vertices and has_blendshapes:
                frames = len(data['vertices'])
                blendshape_count = len(data['blendshapes'][0]) if data['blendshapes'] else 0
                print(f"   ✅ {file.name}: {frames} frames, {blendshape_count} BlendShapes")
                valid_count += 1
            else:
                print(f"   ❌ {file.name}: Missing data")
                invalid_count += 1

        except Exception as e:
            print(f"   ❌ {file.name}: Error - {e}")
            invalid_count += 1

    print(f"\n{Colors.GREEN}Valid files: {valid_count}{Colors.END}")
    if invalid_count > 0:
        print(f"{Colors.RED}Invalid files: {invalid_count}{Colors.END}")

def test_classifier():
    """Run classifier on latest data"""
    print_header("🤖 Testing Classifier")

    json_files = sorted(DATA_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime)

    if not json_files:
        print(f"{Colors.YELLOW}No data files found{Colors.END}")
        return

    latest = json_files[-1]
    print(f"Testing with latest file: {latest.name}\n")

    os.chdir(EMOTION_DIR)
    subprocess.run(["python", "scripts/test_rule_classifier.py", "--input", str(latest)])

def analyze_emotion(emotion):
    """Analyze all recordings for a specific emotion"""
    print_header(f"📊 Analyzing: {emotion}")

    files = list(DATA_DIR.glob(f"{emotion}_*.json"))

    if not files:
        print(f"{Colors.YELLOW}No recordings found for {emotion}{Colors.END}")
        return

    print(f"Found {len(files)} recordings for {emotion}\n")

    total_frames = 0
    total_duration = 0

    for file in files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)

            frames = data.get('frame_count', 0)
            duration = data.get('recording_duration', 0)

            total_frames += frames
            total_duration += duration

            print(f"   📁 {file.name}")
            print(f"      Frames: {frames}")
            print(f"      Duration: {duration:.1f}s")

        except Exception as e:
            print(f"   ❌ Error reading {file.name}: {e}")

    if files:
        print(f"\n{Colors.BLUE}Summary:{Colors.END}")
        print(f"   Total recordings: {len(files)}")
        print(f"   Total frames: {total_frames}")
        print(f"   Total duration: {total_duration:.1f}s")
        print(f"   Avg frames/recording: {total_frames/len(files):.0f}")
        print(f"   Avg duration: {total_duration/len(files):.1f}s")

def open_xcode():
    """Open Xcode project"""
    print_header("📱 Opening Xcode Project")
    xcode_proj = "/Users/kim/Desktop/facedetection/facedetection.xcodeproj"
    subprocess.run(["open", xcode_proj])
    print(f"{Colors.GREEN}✅ Xcode project opened{Colors.END}")

def list_recent():
    """List recent recordings"""
    print_header("📝 Recent Recordings")

    json_files = sorted(DATA_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not json_files:
        print(f"{Colors.YELLOW}No recordings found{Colors.END}")
        return

    print(f"Showing last 10 recordings:\n")

    for i, file in enumerate(json_files[:10], 1):
        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        size = file.stat().st_size / 1024  # KB

        emotion = file.stem.split('_')[0]

        print(f"   {i:2d}. {file.name}")
        print(f"       Emotion: {emotion}")
        print(f"       Time: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"       Size: {size:.1f} KB")

def main():
    parser = argparse.ArgumentParser(
        description='Master Control for Emotion + FaceDetection System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status          Check status of all servers
  start-emotion   Start emotion data server (port 8765)
  start-viz       Start visualizer (port 8766)
  start-all       Start all servers
  stop            Stop all servers
  validate        Validate all collected data
  test            Test classifier on latest data
  analyze         Analyze recordings for specific emotion
  recent          List recent recordings
  xcode           Open Xcode project

Examples:
  python master_control.py status
  python master_control.py start-all
  python master_control.py analyze sadness
        """
    )

    parser.add_argument('command',
                       choices=['status', 'start-emotion', 'start-viz', 'start-all',
                               'stop', 'validate', 'test', 'analyze', 'recent', 'xcode'],
                       help='Command to execute')

    parser.add_argument('--emotion', type=str, help='Emotion to analyze (for analyze command)')

    args = parser.parse_args()

    # Execute command
    if args.command == 'status':
        status()
    elif args.command == 'start-emotion':
        start_emotion_server()
    elif args.command == 'start-viz':
        start_visualizer()
    elif args.command == 'start-all':
        start_emotion_server()
        start_visualizer()
        status()
    elif args.command == 'stop':
        stop_all()
    elif args.command == 'validate':
        validate_data()
    elif args.command == 'test':
        test_classifier()
    elif args.command == 'analyze':
        if args.emotion:
            analyze_emotion(args.emotion)
        else:
            print(f"{Colors.RED}Please specify emotion with --emotion{Colors.END}")
    elif args.command == 'recent':
        list_recent()
    elif args.command == 'xcode':
        open_xcode()

if __name__ == "__main__":
    main()