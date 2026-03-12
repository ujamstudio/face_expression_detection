"""
Installation Test Script

This script verifies that all components are properly installed and working.

Usage:
    python scripts/test_installation.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))


def test_imports():
    """Test that all required packages can be imported."""
    print("="*70)
    print("TESTING PACKAGE IMPORTS")
    print("="*70)

    packages = [
        ('tensorflow', 'TensorFlow'),
        ('transformers', 'Hugging Face Transformers'),
        ('whisper', 'OpenAI Whisper'),
        ('librosa', 'Librosa'),
        ('numpy', 'NumPy'),
        ('scipy', 'SciPy'),
        ('sklearn', 'Scikit-learn'),
        ('matplotlib', 'Matplotlib'),
        ('seaborn', 'Seaborn'),
        ('PIL', 'Pillow'),
        ('yaml', 'PyYAML'),
        ('trimesh', 'Trimesh'),
        ('soundfile', 'SoundFile')
    ]

    failed = []

    for package, name in packages:
        try:
            __import__(package)
            print(f"✅ {name:30s} - OK")
        except ImportError as e:
            print(f"❌ {name:30s} - FAILED: {e}")
            failed.append(name)

    if failed:
        print(f"\n⚠️  {len(failed)} packages failed to import")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print(f"\n✅ All {len(packages)} packages imported successfully!")
        return True


def test_model_builds():
    """Test that all model components build correctly."""
    print("\n" + "="*70)
    print("TESTING MODEL COMPONENTS")
    print("="*70)

    try:
        # Test PointNet
        print("\n1. Testing PointNet...")
        from models.pointnet import build_pointnet_branch
        pointnet = build_pointnet_branch(num_points=2048, output_dim=128)
        print(f"   ✅ PointNet built: {pointnet.count_params():,} parameters")

        # Test Audio CNN
        print("\n2. Testing Audio CNN...")
        from models.audio_cnn import build_audio_cnn_branch
        audio_cnn = build_audio_cnn_branch(input_shape=(128, 128, 3), output_dim=128)
        print(f"   ✅ Audio CNN built: {audio_cnn.count_params():,} parameters")

        # Test Text Encoder (this will download BERT on first run)
        print("\n3. Testing Text Encoder (may download BERT model ~440MB)...")
        from models.text_encoder import build_text_encoder_branch
        text_encoder, bert_model = build_text_encoder_branch(
            model_name='bert-base-uncased',
            max_length=128,
            freeze_bert=True
        )
        print(f"   ✅ Text Encoder built: {text_encoder.count_params():,} parameters")

        # Test Tri-Modal Fusion
        print("\n4. Testing Tri-Modal Fusion Model...")
        from models.tri_modal_fusion import TriModalFusionModel
        fusion_model = TriModalFusionModel()
        model = fusion_model.build_model()
        print(f"   ✅ Fusion Model built: {model.count_params():,} parameters")

        print("\n✅ All models built successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Model build failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preprocessors():
    """Test preprocessing components."""
    print("\n" + "="*70)
    print("TESTING PREPROCESSING COMPONENTS")
    print("="*70)

    try:
        # Test Spectrogram Generator
        print("\n1. Testing Spectrogram Generator...")
        from preprocessing.audio_to_spectrogram import SpectrogramGenerator
        spec_gen = SpectrogramGenerator()
        print("   ✅ Spectrogram Generator initialized")

        # Test Whisper Transcriber (downloads model on first run)
        print("\n2. Testing Whisper Transcriber (may download model ~140MB)...")
        from preprocessing.audio_to_text import WhisperTranscriber
        transcriber = WhisperTranscriber(model_size='base')
        print("   ✅ Whisper Transcriber initialized")

        # Test Point Cloud Processor
        print("\n3. Testing Point Cloud Processor...")
        from preprocessing.pointcloud_processor import PointCloudProcessor
        pc_processor = PointCloudProcessor(num_points=2048)
        print("   ✅ Point Cloud Processor initialized")

        print("\n✅ All preprocessors initialized successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Preprocessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_loader():
    """Test data loader (without actual data)."""
    print("\n" + "="*70)
    print("TESTING DATA LOADER")
    print("="*70)

    try:
        from data.dataset_loader import TriModalDataset

        emotion_to_label = {
            'neutral': 0,
            'joy': 1,
            'sadness': 2
        }

        dataset_loader = TriModalDataset(
            data_root='data/processed',
            emotion_to_label=emotion_to_label,
            tokenizer_name='bert-base-uncased',
            max_text_length=128,
            num_points=2048,
            spec_size=(128, 128)
        )

        print("✅ Data loader initialized successfully!")
        print("   (No actual data checked - this is expected)")
        return True

    except Exception as e:
        print(f"❌ Data loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_evaluation():
    """Test evaluation utilities."""
    print("\n" + "="*70)
    print("TESTING EVALUATION UTILITIES")
    print("="*70)

    try:
        from utils.evaluation import EmotionEvaluator
        import numpy as np

        emotion_labels = {0: 'joy', 1: 'sadness', 2: 'anger'}
        evaluator = EmotionEvaluator(emotion_labels)

        # Create dummy predictions
        y_true = np.array([0, 1, 2, 0, 1])
        y_pred = np.array([0, 1, 2, 1, 1])

        metrics = evaluator.compute_metrics(y_true, y_pred)

        print("✅ Evaluation utilities working!")
        print(f"   Test accuracy: {metrics['accuracy']:.2f}")
        return True

    except Exception as e:
        print(f"❌ Evaluation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_forward_pass():
    """Test a complete forward pass with dummy data."""
    print("\n" + "="*70)
    print("TESTING FORWARD PASS WITH DUMMY DATA")
    print("="*70)

    try:
        import numpy as np
        import tensorflow as tf
        from models.tri_modal_fusion import TriModalFusionModel

        # Build model
        fusion_model = TriModalFusionModel()
        model = fusion_model.build_model()
        model = fusion_model.compile_model(learning_rate=1e-4)

        # Create dummy data
        batch_size = 2
        dummy_data = {
            'face_point_cloud_input': np.random.randn(batch_size, 2048, 3).astype(np.float32),
            'spec_input': np.random.randn(batch_size, 128, 128, 3).astype(np.float32),
            'text_input_ids': np.random.randint(0, 1000, (batch_size, 128), dtype=np.int32),
            'text_attention_mask': np.ones((batch_size, 128), dtype=np.int32)
        }

        # Forward pass
        predictions = model.predict(dummy_data, verbose=0)

        print(f"✅ Forward pass successful!")
        print(f"   Input batch size: {batch_size}")
        print(f"   Output shape: {predictions.shape}")
        print(f"   Probabilities sum to 1.0: {np.allclose(predictions.sum(axis=1), 1.0)}")

        return True

    except Exception as e:
        print(f"❌ Forward pass failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "🔧 "*35)
    print("TRI-MODAL EMOTION CLASSIFICATION - INSTALLATION TEST")
    print("🔧 "*35)

    results = []

    # Run tests
    results.append(("Package Imports", test_imports()))
    results.append(("Model Components", test_model_builds()))
    results.append(("Preprocessors", test_preprocessors()))
    results.append(("Data Loader", test_data_loader()))
    results.append(("Evaluation Utils", test_evaluation()))
    results.append(("Forward Pass", test_forward_pass()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25s} {status}")

    print("\n" + "="*70)

    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("\n✅ Installation is complete and working correctly!")
        print("\nNext steps:")
        print("  1. Collect data (see ios_app/README.md)")
        print("  2. Preprocess: python scripts/preprocess_all.py --input data/raw --output data/processed")
        print("  3. Train: python src/train.py")
        return 0
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("\nPlease fix the failures before proceeding.")
        print("Try: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
