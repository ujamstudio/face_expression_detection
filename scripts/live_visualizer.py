#!/usr/bin/env python3
"""
Live Face Mesh Visualizer (WebSocket Client)

Usage:
    python scripts/live_visualizer.py --server localhost --port 8765
"""

import asyncio
import json
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import websockets
import threading
import queue
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from models.rule_based_classifier import RuleBasedEmotionClassifier
    CLASSIFIER_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Classifier not available: {e}")
    CLASSIFIER_AVAILABLE = False

BG  = '#2B2B2B'
FG  = '#EEEEEE'
DIM = '#888888'

EMOTION_COLORS = {
    'joy':      '#FFD700',
    'sadness':  '#4A90D9',
    'anger':    '#E74C3C',
    'fear':     '#9B59B6',
    'disgust':  '#27AE60',
    'surprise': '#F39C12',
    'neutral':  '#95A5A6',
}


class LiveFaceVisualizer:

    def __init__(self):
        self.current_vertices   = None
        self.current_blendshapes = {}
        self.current_emotion    = "None"
        self.predicted_emotion  = "—"
        self.predicted_confidence = 0.0
        self.all_scores         = {}
        self.frame_count        = 0
        self.is_recording       = False
        self.data_queue         = queue.Queue()
        self.last_update        = time.time()
        self.classifier = RuleBasedEmotionClassifier() if CLASSIFIER_AVAILABLE else None
        self._mesh_view_initialized = False
        self._setup_plot()

    # ── Layout ────────────────────────────────
    def _setup_plot(self):
        self.fig = plt.figure(figsize=(16, 7), facecolor=BG)
        gs = gridspec.GridSpec(
            1, 3, figure=self.fig,
            width_ratios=[1, 1, 1.1],
            wspace=0.06, left=0.03, right=0.97, top=0.93, bottom=0.05
        )
        self.ax_mesh = self.fig.add_subplot(gs[0], projection='3d')
        self.ax_bs   = self.fig.add_subplot(gs[1])
        self.ax_em   = self.fig.add_subplot(gs[2])
        self._init_flat(self.ax_bs, 'BlendShapes')
        self._init_flat(self.ax_em, 'Emotion')
        self._style_3d(self.ax_mesh)
        self._draw_waiting_text(self.ax_bs)
        self._draw_waiting_text(self.ax_em)

    def _style_3d(self, ax):
        ax.set_facecolor(BG)
        for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
            pane.set_facecolor(BG)
            pane.set_edgecolor('#444444')
        ax.tick_params(colors='#555555', labelsize=5)

    def _init_flat(self, ax, title):
        ax.set_facecolor(BG)
        ax.set_title(title, color=FG, fontsize=11, pad=6)
        ax.axis('off')

    def _draw_waiting_text(self, ax):
        ax.text(0.5, 0.5, 'Waiting for data…',
                ha='center', va='center', color=DIM, fontsize=11,
                transform=ax.transAxes)

    # ── Animation callback ─────────────────────
    def process_data(self, data):
        self.data_queue.put(data)

    def update_plot(self, _frame):
        got_new = False
        while not self.data_queue.empty():
            try:
                self._process_frame_data(self.data_queue.get_nowait())
                got_new = True
            except queue.Empty:
                break

        if not got_new:
            return

        self._draw_mesh()
        self._draw_blendshapes()
        self._draw_emotion()

    # ── Panels ────────────────────────────────
    def _draw_mesh(self):
        self.ax_mesh.clear()
        self._style_3d(self.ax_mesh)
        color = EMOTION_COLORS.get(self.predicted_emotion, '#4FC3F7')
        self.ax_mesh.set_title(
            f"{self.predicted_emotion.upper()}  {self.predicted_confidence:.0%}",
            color=color, fontsize=10, fontweight='bold', pad=4
        )
        if self.current_vertices is not None and len(self.current_vertices) > 0:
            v = self.current_vertices
            self.ax_mesh.scatter(v[:, 0], v[:, 1], v[:, 2],
                                 c=color, s=0.8, alpha=0.75)
            self.ax_mesh.set_xlim([-0.12, 0.12])
            self.ax_mesh.set_ylim([-0.12, 0.12])
            self.ax_mesh.set_zlim([-0.12, 0.12])
            if not self._mesh_view_initialized:
                self.ax_mesh.view_init(elev=15, azim=-90)
                self._mesh_view_initialized = True

    def _draw_blendshapes(self):
        self.ax_bs.clear()
        self._init_flat(self.ax_bs, 'BlendShapes')

        if not self.current_blendshapes:
            self._draw_waiting_text(self.ax_bs)
            return

        top = sorted(self.current_blendshapes.items(),
                     key=lambda x: x[1], reverse=True)[:22]

        # 헤더
        self.ax_bs.text(0.03, 0.97, f"{'Name':<22}  {'Bar':^10}  Val",
                        color=DIM, fontsize=7, transform=self.ax_bs.transAxes,
                        fontfamily='monospace', va='top')
        # 구분선 (plot 사용)
        self.ax_bs.plot([0.03, 0.97], [0.945, 0.945],
                        color='#444444', linewidth=0.7,
                        transform=self.ax_bs.transAxes)

        y = 0.91
        dh = 0.038
        for name, val in top:
            if val > 0.5:
                c = '#FF6B6B'
            elif val > 0.25:
                c = '#FFD93D'
            elif val > 0.08:
                c = '#6BCB77'
            else:
                c = '#555555'

            filled = int(val * 10)
            bar = '█' * filled + '▒' * (10 - filled)

            self.ax_bs.text(0.03, y, f"{name:<22}",
                            color=c, fontsize=7.8,
                            transform=self.ax_bs.transAxes,
                            fontfamily='monospace', va='top')
            self.ax_bs.text(0.62, y, bar,
                            color=c, fontsize=6.5,
                            transform=self.ax_bs.transAxes,
                            fontfamily='monospace', va='top')
            self.ax_bs.text(0.95, y, f"{val:.3f}",
                            color=c, fontsize=7.8, ha='right',
                            transform=self.ax_bs.transAxes,
                            fontfamily='monospace', va='top')
            y -= dh

    def _draw_emotion(self):
        self.ax_em.clear()
        self._init_flat(self.ax_em, 'Emotion')

        em_color = EMOTION_COLORS.get(self.predicted_emotion, FG)

        # 예측 감정 크게
        self.ax_em.text(0.5, 0.88,
                        self.predicted_emotion.upper(),
                        ha='center', va='center',
                        fontsize=30, fontweight='bold', color=em_color,
                        transform=self.ax_em.transAxes)
        self.ax_em.text(0.5, 0.78,
                        f"confidence  {self.predicted_confidence:.1%}",
                        ha='center', va='center',
                        fontsize=11, color=DIM,
                        transform=self.ax_em.transAxes)

        # label vs 예측
        if self.is_recording and self.current_emotion not in ('None', 'unknown', '—'):
            match = (self.predicted_emotion == self.current_emotion)
            self.ax_em.text(
                0.5, 0.70,
                f"label: {self.current_emotion}  {'✓' if match else '✗'}",
                ha='center', va='center', fontsize=10,
                color='#6BCB77' if match else '#FF6B6B',
                transform=self.ax_em.transAxes
            )

        # 구분선
        self.ax_em.plot([0.05, 0.95], [0.63, 0.63],
                        color='#444444', linewidth=0.8,
                        transform=self.ax_em.transAxes)

        self.ax_em.text(0.07, 0.59, "All Scores",
                        color=DIM, fontsize=9,
                        transform=self.ax_em.transAxes)

        # 전체 감정 스코어
        if self.all_scores:
            y = 0.52
            for emotion, score in sorted(self.all_scores.items(),
                                         key=lambda x: x[1], reverse=True):
                is_top = (emotion == self.predicted_emotion)
                c  = EMOTION_COLORS.get(emotion, FG)
                fw = 'bold' if is_top else 'normal'
                norm   = min(score / 100.0, 1.0)
                filled = int(norm * 14)
                bar    = '█' * filled + '░' * (14 - filled)
                prefix = '▶' if is_top else ' '

                self.ax_em.text(0.05, y, f"{prefix} {emotion:<10}",
                                color=c, fontsize=9, fontweight=fw,
                                transform=self.ax_em.transAxes,
                                fontfamily='monospace')
                self.ax_em.text(0.42, y, bar,
                                color=c, fontsize=7,
                                transform=self.ax_em.transAxes,
                                fontfamily='monospace')
                self.ax_em.text(0.95, y, f"{score:5.1f}",
                                color=c, fontsize=9, ha='right',
                                transform=self.ax_em.transAxes,
                                fontfamily='monospace')
                y -= 0.065

        # 상태
        rec_c = '#FF6B6B' if self.is_recording else '#555555'
        self.ax_em.text(0.07, 0.04,
                        f"{'● REC' if self.is_recording else '○ IDLE'}"
                        f"   frame {self.frame_count}",
                        color=rec_c, fontsize=9,
                        transform=self.ax_em.transAxes)

    # ── Data ──────────────────────────────────
    def _process_frame_data(self, data):
        msg_type = data.get("type")

        if msg_type == "recording_start":
            self.current_emotion = data.get("emotion", "unknown")
            self.frame_count = 0
            self.is_recording = True

        elif msg_type == "recording_stop":
            self.is_recording = False

        elif msg_type in ["face_data", "frame"]:
            vertices_data = data.get("vertices", [])
            if vertices_data:
                self.current_vertices = np.array(vertices_data)
                self.frame_count += 1
                self.last_update = time.time()

            blendshapes = data.get("blendshapes", {})
            if blendshapes:
                self.current_blendshapes = blendshapes
                if self.classifier:
                    try:
                        result = self.classifier.classify({'blendshapes': blendshapes})
                        self.predicted_emotion    = result['emotion']
                        self.predicted_confidence = result['confidence']
                        self.all_scores           = result.get('all_scores', {})
                    except Exception:
                        pass

            if "emotion" in data:
                self.current_emotion = data["emotion"]


# ── Networking ────────────────────────────────────
async def connect_to_server(visualizer, server_url):
    print(f"🔌 Connecting to {server_url}")
    try:
        async with websockets.connect(server_url) as ws:
            print("✅ Connected!")
            await ws.send(json.dumps({"type": "visualizer_connect", "client": "live_visualizer"}))
            async for message in ws:
                try:
                    visualizer.process_data(json.loads(message))
                except Exception:
                    pass
    except ConnectionRefusedError:
        print(f"❌ Connection refused: {server_url}")
    except Exception as e:
        print(f"❌ {e}")


def run_client(visualizer, host, port):
    async def loop():
        while True:
            try:
                await connect_to_server(visualizer, f"ws://{host}:{port}")
            except Exception:
                pass
            print("Reconnecting in 5s...")
            await asyncio.sleep(5)

    asyncio.new_event_loop().run_until_complete(loop())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="localhost")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    print("=" * 50)
    print("🎨 Live Face Mesh Visualizer")
    print(f"📡 ws://{args.server}:{args.port}")
    print(f"🤖 Classifier: {'loaded' if CLASSIFIER_AVAILABLE else 'unavailable'}")
    print("=" * 50)

    viz = LiveFaceVisualizer()

    threading.Thread(target=run_client, args=(viz, args.server, args.port),
                     daemon=True).start()

    ani = FuncAnimation(viz.fig, viz.update_plot, interval=50,
                        blit=False, cache_frame_data=False)

    try:
        plt.show()
    except KeyboardInterrupt:
        print("\n👋 Stopped")


if __name__ == "__main__":
    main()
