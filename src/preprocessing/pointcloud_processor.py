"""
3D Point Cloud Processing for ARKit Facial Mesh Data

This module handles:
1. Loading 3D facial mesh data from ARKit (JSON format)
2. Sampling/resampling to fixed number of points (2048)
3. Normalization and augmentation
"""

import numpy as np
import json
from pathlib import Path
import trimesh


class PointCloudProcessor:
    """
    Process 3D point cloud data from ARKit facial meshes.
    """

    def __init__(self, num_points=2048):
        """
        Initialize point cloud processor.

        Args:
            num_points: Target number of points for sampling (default: 2048)
        """
        self.num_points = num_points

    def load_from_json(self, json_path):
        """
        Load 3D point cloud from JSON file.

        Expected format:
        {
            "vertices": [[x1, y1, z1], [x2, y2, z2], ...],
            "timestamp": "...",
            "emotion": "..."  # optional
        }

        Args:
            json_path: Path to JSON file

        Returns:
            Numpy array of shape (N, 3) where N is number of vertices
        """
        with open(json_path, 'r') as f:
            data = json.load(f)

        vertices = np.array(data['vertices'], dtype=np.float32)
        return vertices

    def save_to_json(self, vertices, output_path, metadata=None):
        """
        Save point cloud to JSON file.

        Args:
            vertices: Numpy array of shape (N, 3)
            output_path: Path to save JSON file
            metadata: Optional dictionary with additional info
        """
        data = {
            'vertices': vertices.tolist(),
        }

        if metadata:
            data.update(metadata)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_ply(self, ply_path):
        """
        Load 3D point cloud from PLY file.

        Args:
            ply_path: Path to PLY file

        Returns:
            Numpy array of shape (N, 3)
        """
        mesh = trimesh.load(ply_path)

        if isinstance(mesh, trimesh.PointCloud):
            return np.array(mesh.vertices, dtype=np.float32)
        elif isinstance(mesh, trimesh.Trimesh):
            # If it's a mesh, extract vertices
            return np.array(mesh.vertices, dtype=np.float32)
        else:
            raise ValueError(f"Unsupported mesh type: {type(mesh)}")

    def sample_points(self, vertices, num_points=None):
        """
        Sample fixed number of points from point cloud.

        If input has more points: random sampling
        If input has fewer points: repeat points to reach target

        Args:
            vertices: Numpy array of shape (N, 3)
            num_points: Target number of points (default: self.num_points)

        Returns:
            Sampled vertices of shape (num_points, 3)
        """
        if num_points is None:
            num_points = self.num_points

        current_num_points = vertices.shape[0]

        if current_num_points == num_points:
            return vertices

        elif current_num_points > num_points:
            # Random sampling without replacement
            indices = np.random.choice(current_num_points, num_points, replace=False)
            return vertices[indices]

        else:
            # Upsample by repeating points
            repeat_times = num_points // current_num_points
            remainder = num_points % current_num_points

            repeated = np.tile(vertices, (repeat_times, 1))

            if remainder > 0:
                extra_indices = np.random.choice(current_num_points, remainder, replace=False)
                extra_points = vertices[extra_indices]
                return np.vstack([repeated, extra_points])

            return repeated

    def normalize_pointcloud(self, vertices):
        """
        Normalize point cloud to unit sphere centered at origin.

        Steps:
        1. Center by subtracting centroid
        2. Scale to fit in unit sphere

        Args:
            vertices: Numpy array of shape (N, 3)

        Returns:
            Normalized vertices
        """
        # Center
        centroid = np.mean(vertices, axis=0)
        centered = vertices - centroid

        # Scale to unit sphere
        max_distance = np.max(np.linalg.norm(centered, axis=1))
        normalized = centered / (max_distance + 1e-8)

        return normalized

    def augment_rotation(self, vertices, max_angle=15):
        """
        Apply random rotation augmentation.

        Args:
            vertices: Numpy array of shape (N, 3)
            max_angle: Maximum rotation angle in degrees

        Returns:
            Rotated vertices
        """
        # Random rotation angles
        theta_x = np.random.uniform(-max_angle, max_angle) * np.pi / 180
        theta_y = np.random.uniform(-max_angle, max_angle) * np.pi / 180
        theta_z = np.random.uniform(-max_angle, max_angle) * np.pi / 180

        # Rotation matrices
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(theta_x), -np.sin(theta_x)],
            [0, np.sin(theta_x), np.cos(theta_x)]
        ])

        Ry = np.array([
            [np.cos(theta_y), 0, np.sin(theta_y)],
            [0, 1, 0],
            [-np.sin(theta_y), 0, np.cos(theta_y)]
        ])

        Rz = np.array([
            [np.cos(theta_z), -np.sin(theta_z), 0],
            [np.sin(theta_z), np.cos(theta_z), 0],
            [0, 0, 1]
        ])

        # Combined rotation
        R = Rz @ Ry @ Rx
        rotated = vertices @ R.T

        return rotated

    def augment_jitter(self, vertices, sigma=0.01, clip=0.05):
        """
        Apply random jitter (Gaussian noise) to vertices.

        Args:
            vertices: Numpy array of shape (N, 3)
            sigma: Standard deviation of Gaussian noise
            clip: Clip noise to [-clip, clip]

        Returns:
            Jittered vertices
        """
        noise = np.random.normal(0, sigma, vertices.shape)
        noise = np.clip(noise, -clip, clip)
        return vertices + noise

    def augment_scale(self, vertices, scale_range=(0.9, 1.1)):
        """
        Apply random scaling augmentation.

        Args:
            vertices: Numpy array of shape (N, 3)
            scale_range: Tuple of (min_scale, max_scale)

        Returns:
            Scaled vertices
        """
        scale = np.random.uniform(scale_range[0], scale_range[1])
        return vertices * scale

    def process_pointcloud(
        self,
        input_path,
        output_path=None,
        normalize=True,
        augment=False
    ):
        """
        Complete processing pipeline for a single point cloud.

        Args:
            input_path: Path to input file (JSON or PLY)
            output_path: Path to save processed point cloud (optional)
            normalize: Whether to normalize
            augment: Whether to apply augmentation

        Returns:
            Processed point cloud of shape (num_points, 3)
        """
        # Load
        if str(input_path).endswith('.json'):
            vertices = self.load_from_json(input_path)
        elif str(input_path).endswith('.ply'):
            vertices = self.load_from_ply(input_path)
        else:
            raise ValueError(f"Unsupported file format: {input_path}")

        # Sample to fixed number of points
        vertices = self.sample_points(vertices)

        # Normalize
        if normalize:
            vertices = self.normalize_pointcloud(vertices)

        # Augmentation
        if augment:
            if np.random.rand() > 0.5:
                vertices = self.augment_rotation(vertices)
            if np.random.rand() > 0.5:
                vertices = self.augment_jitter(vertices)
            if np.random.rand() > 0.5:
                vertices = self.augment_scale(vertices)

        # Save if output path provided
        if output_path:
            self.save_to_json(vertices, output_path)

        return vertices

    def batch_process(
        self,
        input_dir,
        output_dir,
        emotion_label=None,
        normalize=True
    ):
        """
        Process multiple point cloud files.

        Args:
            input_dir: Directory containing input files
            output_dir: Directory to save processed files
            emotion_label: Optional emotion label for organizing output
            normalize: Whether to normalize

        Returns:
            Number of files processed
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if emotion_label:
            output_path = output_path / emotion_label

        output_path.mkdir(parents=True, exist_ok=True)

        # Find point cloud files
        files = list(input_path.glob('*.json')) + list(input_path.glob('*.ply'))

        print(f"Processing {len(files)} point cloud files...")

        for i, file in enumerate(files):
            try:
                output_file = output_path / f"{file.stem}.json"
                self.process_pointcloud(
                    str(file),
                    str(output_file),
                    normalize=normalize,
                    augment=False
                )

                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(files)} files")

            except Exception as e:
                print(f"Error processing {file}: {e}")

        print(f"Completed! Saved to {output_path}")
        return len(files)


if __name__ == "__main__":
    # Example usage
    print("Point Cloud Processor Test\n" + "="*50)

    # Initialize processor
    processor = PointCloudProcessor(num_points=2048)

    # Create synthetic point cloud (face-like shape)
    print("\nGenerating synthetic facial point cloud...")

    # Create a simple face shape (ellipsoid)
    theta = np.random.uniform(0, 2*np.pi, 3000)
    phi = np.random.uniform(0, np.pi, 3000)

    # Ellipsoid parameters (face-like proportions)
    a, b, c = 1.0, 0.8, 1.2  # width, depth, height

    x = a * np.sin(phi) * np.cos(theta)
    y = b * np.sin(phi) * np.sin(theta)
    z = c * np.cos(phi)

    synthetic_vertices = np.column_stack([x, y, z]).astype(np.float32)

    print(f"Original vertices shape: {synthetic_vertices.shape}")

    # Sample to 2048 points
    sampled = processor.sample_points(synthetic_vertices)
    print(f"Sampled vertices shape: {sampled.shape}")

    # Normalize
    normalized = processor.normalize_pointcloud(sampled)
    print(f"Normalized vertices range: [{normalized.min():.3f}, {normalized.max():.3f}]")

    # Test augmentation
    rotated = processor.augment_rotation(normalized)
    jittered = processor.augment_jitter(normalized)

    print(f"\nAugmentation test:")
    print(f"  Rotated shape: {rotated.shape}")
    print(f"  Jittered shape: {jittered.shape}")

    print("\nTo process real point cloud files:")
    print("  processor.process_pointcloud('face_mesh.json', 'processed.json')")
    print("  processor.batch_process('data/raw/', 'data/processed/', emotion_label='joy')")
