# Quick Start Guide

Get up and running with the Tri-Modal Emotion Classification system in 5 steps.

## Prerequisites

- Python 3.8+
- TensorFlow 2.13+
- iPhone with TrueDepth camera (for data collection)
- GPU recommended (but not required)

## Step 1: Installation (5 minutes)

```bash
# Clone or navigate to the project
cd emotion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: First run will download ~600MB of models (BERT + Whisper).

## Step 2: Test Model Architecture (2 minutes)

Verify the model builds correctly with dummy data:

```bash
cd src/models
python tri_modal_fusion.py
```

You should see:
```
Building Tri-Modal Fusion Model...
Model: "tri_modal_emotion_classifier"
...
Total parameters: 110,000,000+
```

## Step 3: Collect Sample Data (15 minutes)

### Option A: Use Pre-collected Dataset (Recommended for Testing)

If you have access to a sample dataset:
```bash
# Extract sample data
unzip sample_data.zip -d data/processed/
```

### Option B: Collect Your Own (iPhone Required)

1. Build the iOS app (see `ios_app/README.md`)
2. Record 5-10 clips per emotion (start with 3-4 emotions)
3. Transfer files to your computer
4. Organize files:

```bash
# Face meshes
data/processed/face_meshes/
├── joy/
│   ├── clip_0001.json
│   └── clip_0002.json
└── sadness/
    ├── clip_0001.json
    └── clip_0002.json

# (Similar structure for spectrograms/ and transcripts/)
```

## Step 4: Preprocess Data (10 minutes)

If you collected raw video/audio files, preprocess them:

```python
from src.preprocessing import SpectrogramGenerator, WhisperTranscriber, PointCloudProcessor

# Initialize preprocessors
spec_gen = SpectrogramGenerator()
transcriber = WhisperTranscriber(model_size='base')
pc_processor = PointCloudProcessor(num_points=2048)

# Process for each emotion
emotions = ['joy', 'sadness', 'anger', 'fear']

for emotion in emotions:
    # Audio → Spectrogram
    spec_gen.batch_process(
        f'data/raw/audio/{emotion}/',
        f'data/processed/spectrograms/{emotion}/'
    )

    # Audio → Text
    transcriber.batch_transcribe(
        f'data/raw/audio/{emotion}/',
        f'data/processed/transcripts/{emotion}/'
    )

    # Face mesh normalization
    pc_processor.batch_process(
        f'data/raw/meshes/{emotion}/',
        f'data/processed/face_meshes/{emotion}/'
    )
```

## Step 5: Train Model (1-2 hours)

```bash
# Quick training (for testing, 10 epochs)
python src/train.py --config configs/model_config.yaml

# Full training (100 epochs with early stopping)
# Edit configs/model_config.yaml first if needed
python src/train.py --config configs/model_config.yaml
```

**Expected output:**
```
TRI-MODAL EMOTION CLASSIFICATION - TRAINING
======================================================================
Configuration loaded from configs/model_config.yaml
Number of emotion classes: 20

LOADING DATASETS
======================================================================
Found 2000 samples
train split: 1400 samples
val split: 300 samples
test split: 300 samples

BUILDING MODEL
...

Epoch 1/100
44/44 [==============================] - 45s 1s/step - loss: 2.8934 - accuracy: 0.1243 - val_loss: 2.7234 - val_accuracy: 0.1567
...
```

## Step 6: Inference (2 minutes)

Test your trained model:

```bash
python src/inference.py \
  --model models/run_20250101_120000/final_model.keras \
  --audio test_samples/sample_audio.wav \
  --face-mesh test_samples/sample_mesh.json
```

**Expected output:**
```
PREDICTION RESULTS
======================================================================

Transcript: 'I feel disappointed about the results.'

Predicted Emotion: DISAPPOINTMENT
Confidence: 78.23%

Top 5 Predictions:
  1. disappointment  78.23%  ███████████████████████████████████████
  2. sadness         12.45%  ██████
  3. regret          5.67%   ██
  4. resignation     2.34%   █
  5. neutral         1.02%
```

## Common Issues & Solutions

### Issue: "No data found!"

**Solution**: Check your directory structure matches:
```
data/processed/
├── face_meshes/{emotion}/clip_XXXX.json
├── spectrograms/{emotion}/clip_XXXX.png
└── transcripts/{emotion}/clip_XXXX.txt
```

### Issue: "BERT model not found"

**Solution**: Ensure internet connection for first download, or specify local path in `configs/model_config.yaml`.

### Issue: "Out of memory"

**Solution**: Reduce batch size in `configs/model_config.yaml`:
```yaml
training:
  batch_size: 16  # Reduce from 32
```

### Issue: Very low accuracy (<20%)

**Likely causes**:
1. Insufficient data (need >50 samples per emotion minimum)
2. Poor data quality (blurry faces, noisy audio)
3. Imbalanced dataset (some emotions have way more samples)

## Next Steps

### For Better Performance:

1. **Collect more data**: Aim for 100+ samples per emotion
2. **Balance dataset**: Equal samples across all 20 emotions
3. **Fine-tune BERT**: Run fine-tuning after initial training
   ```bash
   python src/train.py --finetune models/run_XXXXX/best_model.keras --finetune-epochs 10
   ```
4. **Analyze errors**: Check confusion matrix to see which emotions are confused
5. **Augment data**: Use rotation/jitter for point clouds, pitch shift for audio

### For Production Use:

1. Optimize model (quantization, pruning)
2. Build REST API for inference
3. Create real-time webcam demo
4. Deploy to mobile device

## Learning Resources

- **PointNet paper**: Understanding 3D point cloud processing
- **BERT paper**: Understanding contextual embeddings
- **ARKit docs**: Improving face tracking quality
- **Librosa docs**: Audio feature extraction techniques

## Getting Help

If you encounter issues:

1. Check the detailed README.md
2. Review configuration files in `configs/`
3. Test individual components (see `if __name__ == "__main__"` blocks)
4. Open an issue on GitHub

---

**Estimated total time**: 2-3 hours for initial setup and testing
**Estimated time for production model**: 3-4 months (as per blueprint)
