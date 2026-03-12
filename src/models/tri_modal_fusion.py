"""
Tri-Modal Fusion Model for Context-Aware Emotion Classification

This model combines three modalities:
1. Vision: 3D facial mesh (PointNet)
2. Audio: Voice tone spectrogram (CNN)
3. Text: Transcribed speech content (BERT)

The fusion strategy concatenates feature vectors from all three branches
and passes them through a classifier head.
"""

import tensorflow as tf
from tensorflow.keras import layers, models
import yaml

from .pointnet import build_pointnet_branch
from .audio_cnn import build_audio_cnn_branch
from .text_encoder import build_text_encoder_branch


class TriModalFusionModel:
    """
    Tri-modal emotion classification model combining vision, audio, and text.
    """

    def __init__(self, config_path=None):
        """
        Initialize the tri-modal fusion model.

        Args:
            config_path: Path to YAML configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.model = None
        self.bert_model = None

    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        if config_path is None:
            # Use default configuration
            return {
                'vision': {
                    'num_points': 2048,
                    'feature_dim': 128
                },
                'audio': {
                    'spec_height': 128,
                    'spec_width': 128,
                    'feature_dim': 128
                },
                'text': {
                    'model_name': 'bert-base-uncased',
                    'max_length': 128,
                    'freeze_bert': True
                },
                'fusion': {
                    'hidden_dim': 256,
                    'dropout_rate': 0.5
                },
                'model': {
                    'num_classes': 20
                }
            }
        else:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)

    def build_model(self):
        """
        Build the complete tri-modal fusion model.

        Returns:
            Compiled Keras model
        """
        # --- 1. Define Inputs ---
        # Vision input: 3D point cloud
        face_input = layers.Input(
            shape=(self.config['vision']['num_points'], 3),
            name='face_point_cloud_input'
        )

        # Audio input: Spectrogram
        spec_input = layers.Input(
            shape=(
                self.config['audio']['spec_height'],
                self.config['audio']['spec_width'],
                3
            ),
            name='spec_input'
        )

        # Text inputs: Token IDs and Attention Mask
        text_input_ids = layers.Input(
            shape=(self.config['text']['max_length'],),
            dtype=tf.int32,
            name='text_input_ids'
        )
        text_attention_mask = layers.Input(
            shape=(self.config['text']['max_length'],),
            dtype=tf.int32,
            name='text_attention_mask'
        )

        # --- 2. Build Feature Extraction Branches ---

        # Vision Branch (PointNet)
        pointnet = build_pointnet_branch(
            num_points=self.config['vision']['num_points'],
            output_dim=self.config['vision']['feature_dim'],
            name='vision_branch'
        )
        vision_features = pointnet(face_input)  # (batch, 128)

        # Audio Branch (CNN)
        audio_cnn = build_audio_cnn_branch(
            input_shape=(
                self.config['audio']['spec_height'],
                self.config['audio']['spec_width'],
                3
            ),
            output_dim=self.config['audio']['feature_dim'],
            name='audio_branch'
        )
        audio_features = audio_cnn(spec_input)  # (batch, 128)

        # Text Branch (BERT)
        text_encoder, self.bert_model = build_text_encoder_branch(
            model_name=self.config['text']['model_name'],
            max_length=self.config['text']['max_length'],
            freeze_bert=self.config['text']['freeze_bert'],
            name='text_branch'
        )
        text_features = text_encoder({
            'input_ids': text_input_ids,
            'attention_mask': text_attention_mask
        })  # (batch, 768)

        # --- 3. Fusion Layer ---
        # Concatenate all feature vectors
        # (128 + 128 + 768 = 1024)
        combined_features = layers.Concatenate(name='fusion_concatenate')([
            vision_features,
            audio_features,
            text_features
        ])

        # --- 4. Classifier Head ---
        x = layers.Dense(
            self.config['fusion']['hidden_dim'],
            activation='relu',
            name='classifier_dense'
        )(combined_features)

        x = layers.Dropout(
            self.config['fusion']['dropout_rate'],
            name='classifier_dropout'
        )(x)

        # Final output layer
        output = layers.Dense(
            self.config['model']['num_classes'],
            activation='softmax',
            name='emotion_output'
        )(x)

        # --- 5. Create Model ---
        self.model = models.Model(
            inputs={
                'face_point_cloud_input': face_input,
                'spec_input': spec_input,
                'text_input_ids': text_input_ids,
                'text_attention_mask': text_attention_mask
            },
            outputs=output,
            name='tri_modal_emotion_classifier'
        )

        return self.model

    def compile_model(self, learning_rate=1e-4):
        """
        Compile the model with optimizer and loss.

        Args:
            learning_rate: Learning rate for Adam optimizer
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        return self.model

    def summary(self):
        """Print model summary."""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        self.model.summary()

    def get_model(self):
        """Get the compiled model."""
        return self.model

    def save_model(self, filepath):
        """
        Save the model to disk.

        Args:
            filepath: Path to save the model (.keras format)
        """
        if self.model is None:
            raise ValueError("Model not built.")
        self.model.save(filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath):
        """
        Load a saved model from disk.

        Args:
            filepath: Path to the saved model
        """
        self.model = tf.keras.models.load_model(filepath)
        print(f"Model loaded from {filepath}")
        return self.model


def build_tri_modal_model(config_path=None, learning_rate=1e-4):
    """
    Convenience function to build and compile the tri-modal model.

    Args:
        config_path: Path to configuration file
        learning_rate: Learning rate for optimizer

    Returns:
        Compiled Keras model
    """
    fusion_model = TriModalFusionModel(config_path=config_path)
    model = fusion_model.build_model()
    model = fusion_model.compile_model(learning_rate=learning_rate)
    return model, fusion_model


if __name__ == "__main__":
    # Test building the tri-modal fusion model
    print("Building Tri-Modal Fusion Model...")

    fusion_model = TriModalFusionModel()
    model = fusion_model.build_model()
    fusion_model.compile_model(learning_rate=1e-4)

    print("\n" + "="*70)
    fusion_model.summary()

    print("\n" + "="*70)
    print("Model Structure:")
    print(f"Total parameters: {model.count_params():,}")

    # Test with dummy data
    import numpy as np

    batch_size = 2
    dummy_data = {
        'face_point_cloud_input': np.random.randn(batch_size, 2048, 3).astype(np.float32),
        'spec_input': np.random.randn(batch_size, 128, 128, 3).astype(np.float32),
        'text_input_ids': np.random.randint(0, 1000, (batch_size, 128), dtype=np.int32),
        'text_attention_mask': np.ones((batch_size, 128), dtype=np.int32)
    }

    print("\n" + "="*70)
    print("Testing forward pass with dummy data...")
    predictions = model.predict(dummy_data)
    print(f"Predictions shape: {predictions.shape}")
    print(f"Sample prediction (20 emotion probabilities): {predictions[0]}")
    print(f"Sum of probabilities: {predictions[0].sum():.4f}")
