"""
Simple Installation Test (No crashes)

This tests components one at a time to avoid segmentation faults.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))


def test_step(description, test_func):
    """Run a single test step."""
    try:
        print(f"\n{description}...")
        test_func()
        print(f"✅ {description} - PASSED")
        return True
    except Exception as e:
        print(f"❌ {description} - FAILED: {e}")
        return False


def test_numpy():
    """Test NumPy."""
    import numpy as np
    arr = np.array([1, 2, 3])
    assert arr.sum() == 6


def test_tensorflow():
    """Test TensorFlow."""
    import tensorflow as tf
    print(f"   TensorFlow version: {tf.__version__}")
    # Simple operation
    a = tf.constant([[1, 2], [3, 4]])
    b = tf.constant([[5, 6], [7, 8]])
    c = tf.matmul(a, b)
    assert c.shape == (2, 2)


def test_transformers():
    """Test Transformers."""
    from transformers import BertTokenizer
    # Just test import, don't download yet
    print("   Transformers library available")


def test_audio():
    """Test audio libraries."""
    import librosa
    import soundfile
    print("   Audio libraries available")


def test_basic_model():
    """Test basic Keras model."""
    import tensorflow as tf
    from tensorflow.keras import layers, models

    # Very simple model
    model = models.Sequential([
        layers.Dense(10, activation='relu', input_shape=(5,)),
        layers.Dense(3, activation='softmax')
    ])
    print(f"   Simple model created: {model.count_params()} parameters")


def test_pointnet_import():
    """Test PointNet import."""
    from models.pointnet import build_pointnet_branch
    print("   PointNet module imported")


def main():
    print("="*70)
    print("SIMPLE INSTALLATION TEST")
    print("="*70)

    tests = [
        ("Test NumPy", test_numpy),
        ("Test TensorFlow", test_tensorflow),
        ("Test Transformers", test_transformers),
        ("Test Audio Libraries", test_audio),
        ("Test Basic Keras Model", test_basic_model),
        ("Test PointNet Import", test_pointnet_import),
    ]

    results = []
    for description, test_func in tests:
        results.append(test_step(description, test_func))

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"{passed}/{total} tests passed")

    if passed == total:
        print("\n✅ Basic installation successful!")
        print("\nNext: Run 'python src/models/audio_cnn.py' to test audio model")
    else:
        print("\n⚠️  Some tests failed. Please install missing packages.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
