"""
Audio CNN Architecture for Spectrogram-based Emotion Recognition

This CNN processes mel-spectrogram images to extract emotional features
from voice tone, pitch, and prosody patterns.

Architecture inspired by VGGNet with adaptations for emotion recognition.
"""

import tensorflow as tf
from tensorflow.keras import layers, models


def conv_block(x, filters, name_prefix=""):
    """
    Convolutional block: Conv2D → BatchNorm → ReLU → MaxPooling

    Args:
        x: Input tensor
        filters: Number of filters
        name_prefix: Prefix for layer names

    Returns:
        Processed tensor
    """
    x = layers.Conv2D(
        filters,
        kernel_size=(3, 3),
        padding='same',
        name=f"{name_prefix}_conv2d"
    )(x)
    x = layers.BatchNormalization(name=f"{name_prefix}_bn")(x)
    x = layers.Activation('relu', name=f"{name_prefix}_relu")(x)
    x = layers.MaxPooling2D(
        pool_size=(2, 2),
        name=f"{name_prefix}_maxpool"
    )(x)
    return x


def build_audio_cnn_branch(
    input_shape=(128, 128, 3),
    output_dim=128,
    name="audio_cnn"
):
    """
    Build CNN architecture for processing mel-spectrogram images.

    Architecture:
        Input: (height, width, channels) - Spectrogram image
        → Conv Block 1: 32 filters
        → Conv Block 2: 64 filters
        → Conv Block 3: 128 filters
        → Global Average Pooling
        → Output: (output_dim,)

    Args:
        input_shape: Shape of spectrogram (default: (128, 128, 3))
        output_dim: Dimension of output feature vector (default: 128)
        name: Name prefix for the branch

    Returns:
        Keras Model
    """
    # Input layer
    spec_input = layers.Input(shape=input_shape, name=f"{name}_input")

    # Convolutional blocks
    x = conv_block(spec_input, 32, name_prefix=f"{name}_block1")
    x = conv_block(x, 64, name_prefix=f"{name}_block2")

    # Additional conv layer without pooling for deeper features
    x = layers.Conv2D(
        128,
        kernel_size=(3, 3),
        padding='same',
        name=f"{name}_block3_conv2d"
    )(x)
    x = layers.BatchNormalization(name=f"{name}_block3_bn")(x)
    x = layers.Activation('relu', name=f"{name}_block3_relu")(x)

    # Global Average Pooling
    # This aggregates spatial information while preserving channel features
    global_features = layers.GlobalAveragePooling2D(
        name=f"{name}_global_avg_pool"
    )(x)

    # Optional: Additional dense layer for feature refinement
    output = layers.Dense(
        output_dim,
        activation='relu',
        name=f"{name}_output"
    )(global_features)

    # Create model
    model = models.Model(
        inputs=spec_input,
        outputs=output,
        name=name
    )

    return model


def build_audio_cnn_deeper(
    input_shape=(128, 128, 3),
    output_dim=128,
    name="audio_cnn_deep"
):
    """
    Deeper CNN variant with more layers for complex emotion patterns.

    Args:
        input_shape: Shape of spectrogram
        output_dim: Output dimension
        name: Model name

    Returns:
        Keras Model
    """
    spec_input = layers.Input(shape=input_shape, name=f"{name}_input")

    # Block 1
    x = conv_block(spec_input, 32, name_prefix=f"{name}_block1")

    # Block 2
    x = conv_block(x, 64, name_prefix=f"{name}_block2")

    # Block 3 (two conv layers before pooling)
    x = layers.Conv2D(128, (3, 3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Conv2D(128, (3, 3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)

    # Block 4
    x = layers.Conv2D(256, (3, 3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)

    # Global pooling
    global_features = layers.GlobalAveragePooling2D()(x)

    # Dense layers
    x = layers.Dense(512, activation='relu')(global_features)
    x = layers.Dropout(0.3)(x)
    output = layers.Dense(output_dim, activation='relu', name=f"{name}_output")(x)

    model = models.Model(inputs=spec_input, outputs=output, name=name)
    return model


if __name__ == "__main__":
    # Test the Audio CNN branch
    print("Building Audio CNN branch...")
    audio_cnn = build_audio_cnn_branch(
        input_shape=(128, 128, 3),
        output_dim=128
    )
    audio_cnn.summary()

    # Test with random spectrogram data
    import numpy as np
    batch_size = 4
    test_data = np.random.randn(batch_size, 128, 128, 3).astype(np.float32)

    print(f"\nTest input shape: {test_data.shape}")
    output = audio_cnn.predict(test_data)
    print(f"Output shape: {output.shape}")
    print(f"Output feature vector (first sample): {output[0][:10]}...")

    print("\n" + "="*50)
    print("Building Deeper Audio CNN variant...")
    audio_cnn_deep = build_audio_cnn_deeper()
    audio_cnn_deep.summary()
