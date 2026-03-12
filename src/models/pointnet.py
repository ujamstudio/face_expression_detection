"""
PointNet Architecture for 3D Facial Mesh Feature Extraction

PointNet is designed to process unordered point clouds directly.
Key features:
- Permutation invariance through symmetric function (max pooling)
- Local and global feature learning
- Robust to missing data and irregular sampling

Reference: PointNet - Deep Learning on Point Sets for 3D Classification and Segmentation
"""

import tensorflow as tf
from tensorflow.keras import layers, models


def conv_bn_relu(x, filters, kernel_size=1, name_prefix=""):
    """
    Convolutional block with Batch Normalization and ReLU activation.

    Args:
        x: Input tensor
        filters: Number of filters
        kernel_size: Kernel size for Conv1D
        name_prefix: Prefix for layer names

    Returns:
        Processed tensor
    """
    x = layers.Conv1D(
        filters,
        kernel_size=kernel_size,
        padding="valid",
        name=f"{name_prefix}_conv1d"
    )(x)
    x = layers.BatchNormalization(
        momentum=0.0,  # Use batch statistics only
        name=f"{name_prefix}_bn"
    )(x)
    x = layers.Activation("relu", name=f"{name_prefix}_relu")(x)
    return x


def build_pointnet_branch(num_points=2048, output_dim=128, name="pointnet"):
    """
    Build PointNet architecture for processing 3D facial mesh point clouds.

    Architecture:
        Input: (batch, num_points, 3) - XYZ coordinates
        → Shared MLPs (Conv1D): 64 → 128 → 1024
        → Global Max Pooling: (batch, num_points, 1024) → (batch, 1024)
        → Dense: 1024 → output_dim

    Args:
        num_points: Number of points in the point cloud (default: 2048)
        output_dim: Dimension of output feature vector (default: 128)
        name: Name prefix for the branch

    Returns:
        Keras Model with input (num_points, 3) and output (output_dim,)
    """
    # Input layer
    point_cloud_input = layers.Input(
        shape=(num_points, 3),
        name=f"{name}_input"
    )

    # Shared MLP (implemented as Conv1D with kernel_size=1)
    # This applies the same transformation to each point independently
    x = conv_bn_relu(point_cloud_input, 64, name_prefix=f"{name}_mlp1")
    x = conv_bn_relu(x, 128, name_prefix=f"{name}_mlp2")
    x = conv_bn_relu(x, 1024, name_prefix=f"{name}_mlp3")

    # Symmetric function: Global Max Pooling
    # This makes the network permutation-invariant
    # (batch, num_points, 1024) → (batch, 1024)
    global_features = layers.GlobalMaxPooling1D(
        name=f"{name}_global_max_pool"
    )(x)

    # Feature dimension reduction
    output = layers.Dense(
        output_dim,
        activation='relu',
        name=f"{name}_output"
    )(global_features)

    # Create model
    model = models.Model(
        inputs=point_cloud_input,
        outputs=output,
        name=name
    )

    return model


def normalize_point_cloud(points):
    """
    Normalize point cloud to unit sphere centered at origin.

    Args:
        points: Tensor of shape (batch, num_points, 3)

    Returns:
        Normalized point cloud tensor
    """
    # Center point cloud
    centroid = tf.reduce_mean(points, axis=1, keepdims=True)
    points_centered = points - centroid

    # Scale to unit sphere
    max_distance = tf.reduce_max(
        tf.sqrt(tf.reduce_sum(points_centered ** 2, axis=-1, keepdims=True)),
        axis=1,
        keepdims=True
    )
    points_normalized = points_centered / (max_distance + 1e-8)

    return points_normalized


if __name__ == "__main__":
    # Test the PointNet branch
    print("Building PointNet branch...")
    pointnet = build_pointnet_branch(num_points=2048, output_dim=128)
    pointnet.summary()

    # Test with random data
    import numpy as np
    batch_size = 4
    num_points = 2048
    test_data = np.random.randn(batch_size, num_points, 3).astype(np.float32)

    print(f"\nTest input shape: {test_data.shape}")
    output = pointnet.predict(test_data)
    print(f"Output shape: {output.shape}")
    print(f"Output feature vector (first sample): {output[0][:10]}...")
