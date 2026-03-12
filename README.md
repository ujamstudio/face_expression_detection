# Tri-Modal Emotion Classification System

A deep learning system that classifies **20 nuanced emotions** by fusing three modalities:
- **Vision**: 3D facial mesh from iPhone TrueDepth camera (via ARKit)
- **Audio**: Voice tone and prosody from mel-spectrogram analysis
- **Text**: Semantic content from speech transcription

## Architecture Overview

```
┌─────────────────┐
│   Input Data    │
│  (Video Clip)   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────┐
│ 3D   │  │Audio │
│ Mesh │  │ .wav │
└──┬───┘  └──┬───┘
   │         │
   │    ┌────┴────┐
   │    │         │
   │    ▼         ▼
   │  ┌────┐   ┌────┐
   │  │Spec│   │Text│
   │  └──┬─┘   └──┬─┘
   │     │        │
   ▼     ▼        ▼
┌────┐ ┌────┐ ┌────┐
│PN  │ │CNN │ │BERT│
│Net │ │    │ │    │
└──┬─┘ └──┬─┘ └──┬─┘
   │      │      │
   └──────┴──────┘
          │
          ▼
    ┌──────────┐
    │  Fusion  │
    │ Concat + │
    │ Classify │
    └─────┬────┘
          │
          ▼
    ┌──────────┐
    │ 20 Emos  │
    └──────────┘
```

### Model Components

1. **Vision Branch (PointNet)**
   - Input: 3D point cloud (2048 points × XYZ coordinates)
   - Architecture: Shared MLP → Global Max Pooling
   - Output: 128-dim feature vector

2. **Audio Branch (CNN)**
   - Input: Mel-spectrogram (128×128×3 image)
   - Architecture: Conv2D blocks → Global Average Pooling
   - Output: 128-dim feature vector

3. **Text Branch (BERT)**
   - Input: Tokenized transcript (max 128 tokens)
   - Architecture: Pre-trained BERT → [CLS] token
   - Output: 768-dim feature vector

4. **Fusion Layer**
   - Concatenate: 128 + 128 + 768 = 1024 dimensions
   - Dense layer → Dropout → Softmax (20 classes)

## 20 Emotion Categories

| Basic Emotions | Complex Emotions |
|---------------|------------------|
| Neutral | Regret |
| Joy | Affection |
| Sadness | Resignation |
| Anger | Contentment |
| Fear | Disappointment |
| Disgust | Nostalgia |
| Surprise | Guilt |
| | Pride |
| | Shame |
| | Envy |
| | Gratitude |
| | Hope |
| | Despair |

## Project Structure

```
emotion/
├── configs/
│   ├── emotions.yaml          # 20 emotion definitions
│   └── model_config.yaml      # Model hyperparameters
├── data/
│   ├── raw/                   # Original video clips
│   └── processed/
│       ├── face_meshes/       # 3D point clouds (.json)
│       ├── spectrograms/      # Mel-spectrograms (.png)
│       └── transcripts/       # Text transcripts (.txt)
├── models/                    # Saved model checkpoints
├── src/
│   ├── models/
│   │   ├── pointnet.py        # PointNet implementation
│   │   ├── audio_cnn.py       # Audio CNN
│   │   ├── text_encoder.py    # BERT encoder
│   │   └── tri_modal_fusion.py # Complete model
│   ├── preprocessing/
│   │   ├── audio_to_spectrogram.py
│   │   ├── audio_to_text.py   # Whisper transcription
│   │   └── pointcloud_processor.py
│   ├── data/
│   │   └── dataset_loader.py  # TensorFlow data pipeline
│   ├── utils/
│   │   └── evaluation.py      # Metrics & confusion matrix
│   ├── train.py               # Training script
│   └── inference.py           # Inference pipeline
├── notebooks/                 # Jupyter notebooks
├── ios_app/                   # ARKit data collection app
└── requirements.txt
```

## Installation

### 1. Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Pre-trained Models

The first run will automatically download:
- BERT model (~440MB): `bert-base-uncased`
- Whisper model (~140MB): `base` variant

## Usage

### Data Collection (iOS App)

Build and run the ARKit app on an iPhone with TrueDepth camera:

```bash
cd ios_app
open EmotionCapture.xcodeproj
```

The app will record:
- 3D facial mesh vertices (ARFaceAnchor.geometry.vertices)
- Synchronized audio
- Emotion label (user-tagged)

### Preprocessing

```python
from src.preprocessing import SpectrogramGenerator, WhisperTranscriber, PointCloudProcessor

# 1. Convert audio to spectrogram
spec_gen = SpectrogramGenerator()
spec_gen.batch_process('data/raw/audio/', 'data/processed/spectrograms/', emotion_label='joy')

# 2. Transcribe audio to text
transcriber = WhisperTranscriber(model_size='base')
transcriber.batch_transcribe('data/raw/audio/', 'data/processed/transcripts/', emotion_label='joy')

# 3. Process 3D point clouds
pc_processor = PointCloudProcessor(num_points=2048)
pc_processor.batch_process('data/raw/meshes/', 'data/processed/face_meshes/', emotion_label='joy')
```

### Training

```bash
# Train from scratch
python src/train.py --config configs/model_config.yaml

# Fine-tune (unfreeze BERT)
python src/train.py --config configs/model_config.yaml --finetune models/run_20250101_120000/best_model.keras --finetune-epochs 10
```

### Inference

```bash
# From video file
python src/inference.py \
  --model models/final_model.keras \
  --video input_video.mp4 \
  --face-mesh face_mesh.json

# From separate audio and mesh files
python src/inference.py \
  --model models/final_model.keras \
  --audio input_audio.wav \
  --face-mesh face_mesh.json
```

**Example Output:**
```
PREDICTION RESULTS
======================================================================

Transcript: 'I really regret not taking that opportunity.'

Predicted Emotion: REGRET
Confidence: 87.34%

Top 5 Predictions:
  1. regret          87.34%  ███████████████████████████████████████████
  2. disappointment  6.21%   ███
  3. sadness         3.15%   █
  4. resignation     2.01%   █
  5. guilt           0.89%
```

## Model Training Details

### Hyperparameters (default)

| Parameter | Value |
|-----------|-------|
| Batch size | 32 |
| Learning rate (initial) | 1e-4 |
| Learning rate (fine-tune) | 1e-6 |
| Epochs | 100 |
| Early stopping patience | 15 |
| Optimizer | Adam |
| Loss | Sparse Categorical Cross-Entropy |

### Training Strategy

**Phase 1: Transfer Learning**
- Freeze BERT weights
- Train PointNet, Audio CNN, and fusion layers
- Duration: ~50-80 epochs

**Phase 2: Fine-Tuning**
- Unfreeze BERT (or top N layers)
- Very low learning rate (1e-6)
- Duration: ~10-20 epochs

### Expected Performance

With ~2,000 samples (100 clips per emotion × 20 emotions):

| Metric | Target |
|--------|--------|
| Overall Accuracy | >70% |
| Per-Emotion F1 (avg) | >0.65 |
| Complex Emotions F1 | >0.55 |

## Evaluation

The model outputs:
- Confusion matrix heatmap
- Per-emotion precision/recall/F1
- Top classification errors
- Training history plots

```python
from src.utils import EmotionEvaluator

evaluator = EmotionEvaluator(emotion_labels)
metrics = evaluator.evaluate(y_true, y_pred, output_dir='evaluation/')
```

## iOS Data Collection App

### Requirements
- iPhone with TrueDepth camera (iPhone X or later)
- Xcode 14+
- iOS 15+

### Features
- Real-time ARFaceAnchor tracking
- Synchronized audio recording
- Emotion labeling UI
- Export as JSON (mesh) + WAV (audio)

### Data Format

**Face Mesh JSON:**
```json
{
  "vertices": [[x1, y1, z1], [x2, y2, z2], ...],
  "timestamp": "2025-01-01T12:00:00Z",
  "emotion": "regret"
}
```

## Development Timeline

Based on the blueprint's 3-4 month estimate:

- **Weeks 1-2**: iOS app development + emotion definition
- **Weeks 3-8**: Data collection (2,000 clips)
- **Weeks 9-10**: Preprocessing pipeline
- **Weeks 11-12**: Model architecture implementation
- **Weeks 13-16**: Training, evaluation, fine-tuning

## Citation

If you use this system in your research, please cite:

```bibtex
@software{trimodal_emotion_2025,
  title={Tri-Modal Context-Aware Emotion Classification},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/emotion}
}
```

## References

- **PointNet**: Qi et al. "PointNet: Deep Learning on Point Sets for 3D Classification and Segmentation" (CVPR 2017)
- **BERT**: Devlin et al. "BERT: Pre-training of Deep Bidirectional Transformers" (NAACL 2019)
- **Whisper**: Radford et al. "Robust Speech Recognition via Large-Scale Weak Supervision" (2022)
- **ARKit Face Tracking**: [Apple Developer Documentation](https://developer.apple.com/documentation/arkit/arfaceanchor)

## License

MIT License - See LICENSE file for details

## Contact

For questions or collaboration:
- Email: your.email@example.com
- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/emotion/issues)

---

**Note**: This is an academic research project. Model performance depends heavily on data quality and quantity. The 20-emotion classification task is challenging—expect iterative refinement of both data collection and model architecture.
