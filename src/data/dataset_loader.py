"""
TensorFlow Data Loader for Tri-Modal Emotion Dataset

This module creates tf.data.Dataset pipelines for efficiently loading
and batching the three modalities: 3D point clouds, spectrograms, and text.
"""

import tensorflow as tf
import numpy as np
import json
from pathlib import Path
from transformers import BertTokenizer
from PIL import Image


class TriModalDataset:
    """
    Dataset loader for tri-modal emotion classification.

    Expected directory structure:
    data_root/
    ├── face_meshes/
    │   ├── emotion_0/
    │   │   ├── clip_0001.json
    │   │   └── ...
    │   └── emotion_1/
    ├── spectrograms/
    │   ├── emotion_0/
    │   │   ├── clip_0001.png
    │   │   └── ...
    │   └── emotion_1/
    └── transcripts/
        ├── emotion_0/
        │   ├── clip_0001.txt
        │   └── ...
        └── emotion_1/
    """

    def __init__(
        self,
        data_root,
        emotion_to_label,
        tokenizer_name='bert-base-uncased',
        max_text_length=128,
        num_points=2048,
        spec_size=(128, 128)
    ):
        """
        Initialize dataset loader.

        Args:
            data_root: Root directory containing processed data
            emotion_to_label: Dictionary mapping emotion names to integer labels
            tokenizer_name: BERT tokenizer name
            max_text_length: Maximum text sequence length
            num_points: Number of points in point cloud
            spec_size: Spectrogram image size (height, width)
        """
        self.data_root = Path(data_root)
        self.emotion_to_label = emotion_to_label
        self.label_to_emotion = {v: k for k, v in emotion_to_label.items()}
        self.max_text_length = max_text_length
        self.num_points = num_points
        self.spec_size = spec_size

        # Load BERT tokenizer
        self.tokenizer = BertTokenizer.from_pretrained(tokenizer_name)

        # Paths
        self.face_meshes_dir = self.data_root / 'face_meshes'
        self.spectrograms_dir = self.data_root / 'spectrograms'
        self.transcripts_dir = self.data_root / 'transcripts'

    def collect_file_paths(self):
        """
        Collect all triplet file paths (face mesh, spectrogram, transcript).

        Returns:
            List of tuples: (face_mesh_path, spec_path, transcript_path, label)
        """
        triplets = []

        for emotion_name, label in self.emotion_to_label.items():
            # Check if directories exist
            face_dir = self.face_meshes_dir / emotion_name
            spec_dir = self.spectrograms_dir / emotion_name
            text_dir = self.transcripts_dir / emotion_name

            if not face_dir.exists():
                print(f"Warning: {face_dir} does not exist")
                continue

            # Get all files for this emotion
            face_files = sorted(face_dir.glob('*.json'))

            for face_file in face_files:
                # Construct corresponding file paths
                stem = face_file.stem
                spec_file = spec_dir / f"{stem}.png"
                text_file = text_dir / f"{stem}.txt"

                # Check if all three files exist
                if spec_file.exists() and text_file.exists():
                    triplets.append((
                        str(face_file),
                        str(spec_file),
                        str(text_file),
                        label
                    ))
                else:
                    if not spec_file.exists():
                        print(f"Warning: Missing spectrogram {spec_file}")
                    if not text_file.exists():
                        print(f"Warning: Missing transcript {text_file}")

        return triplets

    def load_face_mesh(self, path):
        """Load 3D point cloud from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        vertices = np.array(data['vertices'], dtype=np.float32)

        # Ensure correct shape
        if vertices.shape[0] != self.num_points:
            # Simple resampling (in practice, use proper sampling)
            if vertices.shape[0] > self.num_points:
                indices = np.random.choice(vertices.shape[0], self.num_points, replace=False)
                vertices = vertices[indices]
            else:
                # Pad by repeating
                repeats = self.num_points // vertices.shape[0] + 1
                vertices = np.tile(vertices, (repeats, 1))[:self.num_points]

        return vertices

    def load_spectrogram(self, path):
        """Load spectrogram image."""
        img = Image.open(path).convert('RGB')
        img = img.resize(self.spec_size)
        img_array = np.array(img, dtype=np.float32) / 255.0  # Normalize to [0, 1]
        return img_array

    def load_transcript(self, path):
        """Load text transcript."""
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        return text

    def tokenize_text(self, text):
        """Tokenize text using BERT tokenizer."""
        encoded = self.tokenizer(
            text,
            padding='max_length',
            truncation=True,
            max_length=self.max_text_length,
            return_tensors='np'
        )
        return encoded['input_ids'][0], encoded['attention_mask'][0]

    def create_dataset(self, split='train', batch_size=32, shuffle=True, seed=42):
        """
        Create tf.data.Dataset for training/validation/testing.

        Args:
            split: 'train', 'val', or 'test'
            batch_size: Batch size
            shuffle: Whether to shuffle data
            seed: Random seed for shuffling

        Returns:
            tf.data.Dataset
        """
        # Collect all triplets
        all_triplets = self.collect_file_paths()

        if len(all_triplets) == 0:
            raise ValueError("No data found! Please check your data directories.")

        print(f"Found {len(all_triplets)} samples")

        # Split data
        np.random.seed(seed)
        indices = np.random.permutation(len(all_triplets))

        # Split ratios: 70% train, 15% val, 15% test
        train_end = int(0.7 * len(indices))
        val_end = int(0.85 * len(indices))

        if split == 'train':
            selected_indices = indices[:train_end]
        elif split == 'val':
            selected_indices = indices[train_end:val_end]
        elif split == 'test':
            selected_indices = indices[val_end:]
        else:
            raise ValueError(f"Invalid split: {split}")

        selected_triplets = [all_triplets[i] for i in selected_indices]
        print(f"{split} split: {len(selected_triplets)} samples")

        # Create dataset from paths
        face_paths = [t[0] for t in selected_triplets]
        spec_paths = [t[1] for t in selected_triplets]
        text_paths = [t[2] for t in selected_triplets]
        labels = [t[3] for t in selected_triplets]

        # Create TensorFlow dataset
        def load_triplet(face_path, spec_path, text_path, label):
            """Load and process all three modalities."""
            # Decode paths
            face_path = face_path.numpy().decode('utf-8')
            spec_path = spec_path.numpy().decode('utf-8')
            text_path = text_path.numpy().decode('utf-8')
            label = label.numpy()

            # Load data
            face_mesh = self.load_face_mesh(face_path)
            spectrogram = self.load_spectrogram(spec_path)
            text = self.load_transcript(text_path)

            # Tokenize text
            input_ids, attention_mask = self.tokenize_text(text)

            return (
                face_mesh.astype(np.float32),
                spectrogram.astype(np.float32),
                input_ids.astype(np.int32),
                attention_mask.astype(np.int32),
                label.astype(np.int32)
            )

        dataset = tf.data.Dataset.from_tensor_slices((
            face_paths,
            spec_paths,
            text_paths,
            labels
        ))

        # Map loading function
        dataset = dataset.map(
            lambda f, s, t, l: tf.py_function(
                load_triplet,
                [f, s, t, l],
                [tf.float32, tf.float32, tf.int32, tf.int32, tf.int32]
            ),
            num_parallel_calls=tf.data.AUTOTUNE
        )

        # Set shapes
        dataset = dataset.map(lambda f, s, i, a, l: (
            {
                'face_point_cloud_input': tf.ensure_shape(f, [self.num_points, 3]),
                'spec_input': tf.ensure_shape(s, [self.spec_size[0], self.spec_size[1], 3]),
                'text_input_ids': tf.ensure_shape(i, [self.max_text_length]),
                'text_attention_mask': tf.ensure_shape(a, [self.max_text_length])
            },
            tf.ensure_shape(l, [])
        ))

        # Shuffle and batch
        if shuffle:
            dataset = dataset.shuffle(buffer_size=1000, seed=seed)

        dataset = dataset.batch(batch_size)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)

        return dataset


if __name__ == "__main__":
    # Example usage
    print("Tri-Modal Dataset Loader Test\n" + "="*70)

    # Define emotion mapping
    emotion_to_label = {
        'neutral': 0,
        'joy': 1,
        'sadness': 2,
        'anger': 3,
        # ... (add all 20 emotions)
    }

    # Initialize dataset
    dataset_loader = TriModalDataset(
        data_root='data/processed',
        emotion_to_label=emotion_to_label,
        tokenizer_name='bert-base-uncased',
        max_text_length=128,
        num_points=2048,
        spec_size=(128, 128)
    )

    print("\nTo create datasets:")
    print("  train_ds = dataset_loader.create_dataset(split='train', batch_size=32)")
    print("  val_ds = dataset_loader.create_dataset(split='val', batch_size=32)")
    print("  test_ds = dataset_loader.create_dataset(split='test', batch_size=32)")
