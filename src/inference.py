"""
Inference Pipeline for Tri-Modal Emotion Classification

This script provides end-to-end inference from raw inputs
(video/audio + 3D mesh) to emotion prediction.

Usage:
    python src/inference.py --model models/final_model.keras --video input.mp4 --mesh face_mesh.json
"""

import argparse
import tensorflow as tf
import numpy as np
import yaml
from pathlib import Path

from preprocessing.audio_to_spectrogram import SpectrogramGenerator, extract_audio_from_video
from preprocessing.audio_to_text import WhisperTranscriber
from preprocessing.pointcloud_processor import PointCloudProcessor
from models.text_encoder import get_tokenizer


class EmotionInference:
    """
    End-to-end emotion inference pipeline.
    """

    def __init__(
        self,
        model_path,
        config_path='configs/model_config.yaml',
        emotions_config_path='configs/emotions.yaml'
    ):
        """
        Initialize inference pipeline.

        Args:
            model_path: Path to trained model (.keras)
            config_path: Path to model configuration
            emotions_config_path: Path to emotions configuration
        """
        self.model_path = model_path
        self.config = self._load_config(config_path)
        self.emotions = self._load_emotions(emotions_config_path)

        # Load model
        print(f"Loading model from {model_path}...")
        self.model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully!")

        # Initialize preprocessors
        self._initialize_preprocessors()

    def _load_config(self, config_path):
        """Load model configuration."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_emotions(self, emotions_config_path):
        """Load emotion labels."""
        with open(emotions_config_path, 'r') as f:
            emotions_config = yaml.safe_load(f)
        return {int(idx): name for idx, name in emotions_config['emotions'].items()}

    def _initialize_preprocessors(self):
        """Initialize all preprocessing components."""
        # Spectrogram generator
        self.spec_generator = SpectrogramGenerator(
            sample_rate=self.config['audio']['sample_rate'],
            n_mels=self.config['audio']['n_mels'],
            n_fft=self.config['audio']['n_fft'],
            hop_length=self.config['audio']['hop_length'],
            duration=self.config['audio']['duration'],
            target_size=(self.config['audio']['spec_height'], self.config['audio']['spec_width'])
        )

        # Whisper transcriber
        print("Loading Whisper model for transcription...")
        self.transcriber = WhisperTranscriber(
            model_size='base',
            device='cpu',
            language='en'
        )

        # Point cloud processor
        self.pointcloud_processor = PointCloudProcessor(
            num_points=self.config['vision']['num_points']
        )

        # BERT tokenizer
        self.tokenizer = get_tokenizer(self.config['text']['model_name'])

    def preprocess_audio(self, audio_path):
        """
        Preprocess audio file to spectrogram and text.

        Args:
            audio_path: Path to audio file (.wav)

        Returns:
            Tuple of (spectrogram, transcript)
        """
        # Generate spectrogram
        spectrogram = self.spec_generator.process_audio_file(audio_path)
        spectrogram = spectrogram.astype(np.float32) / 255.0  # Normalize

        # Transcribe to text
        result = self.transcriber.transcribe_audio(audio_path)
        transcript = result['text']

        return spectrogram, transcript

    def preprocess_face_mesh(self, mesh_path):
        """
        Preprocess 3D face mesh.

        Args:
            mesh_path: Path to face mesh file (.json or .ply)

        Returns:
            Processed point cloud (num_points, 3)
        """
        point_cloud = self.pointcloud_processor.process_pointcloud(
            mesh_path,
            normalize=True,
            augment=False
        )
        return point_cloud.astype(np.float32)

    def tokenize_text(self, text):
        """
        Tokenize text for BERT.

        Args:
            text: Input text string

        Returns:
            Dictionary with input_ids and attention_mask
        """
        encoded = self.tokenizer(
            text,
            padding='max_length',
            truncation=True,
            max_length=self.config['text']['max_length'],
            return_tensors='tf'
        )
        return {
            'input_ids': encoded['input_ids'][0],
            'attention_mask': encoded['attention_mask'][0]
        }

    def predict(self, face_mesh_path, audio_path):
        """
        Predict emotion from inputs.

        Args:
            face_mesh_path: Path to 3D face mesh file
            audio_path: Path to audio file

        Returns:
            Dictionary with prediction results
        """
        print("\n" + "="*70)
        print("EMOTION INFERENCE PIPELINE")
        print("="*70)

        # Preprocess inputs
        print("\n1. Preprocessing face mesh...")
        face_mesh = self.preprocess_face_mesh(face_mesh_path)

        print("2. Preprocessing audio...")
        spectrogram, transcript = self.preprocess_audio(audio_path)

        print(f"   Transcript: '{transcript}'")

        print("3. Tokenizing text...")
        text_inputs = self.tokenize_text(transcript)

        # Prepare batch inputs
        batch_inputs = {
            'face_point_cloud_input': tf.expand_dims(face_mesh, axis=0),
            'spec_input': tf.expand_dims(spectrogram, axis=0),
            'text_input_ids': tf.expand_dims(text_inputs['input_ids'], axis=0),
            'text_attention_mask': tf.expand_dims(text_inputs['attention_mask'], axis=0)
        }

        # Predict
        print("\n4. Running model inference...")
        predictions = self.model.predict(batch_inputs, verbose=0)

        # Get top predictions
        probabilities = predictions[0]
        top_indices = np.argsort(probabilities)[::-1][:5]

        results = {
            'predicted_emotion': self.emotions[top_indices[0]],
            'confidence': float(probabilities[top_indices[0]]),
            'top_5_predictions': [
                {
                    'emotion': self.emotions[idx],
                    'probability': float(probabilities[idx])
                }
                for idx in top_indices
            ],
            'transcript': transcript
        }

        return results

    def predict_from_video(self, video_path, face_mesh_path, temp_audio_path='temp_audio.wav'):
        """
        Predict emotion from video file.

        Args:
            video_path: Path to video file
            face_mesh_path: Path to 3D face mesh file
            temp_audio_path: Temporary audio file path

        Returns:
            Dictionary with prediction results
        """
        # Extract audio from video
        print(f"Extracting audio from video: {video_path}")
        extract_audio_from_video(video_path, temp_audio_path)

        # Run prediction
        results = self.predict(face_mesh_path, temp_audio_path)

        # Clean up temporary audio
        Path(temp_audio_path).unlink(missing_ok=True)

        return results

    def print_results(self, results):
        """
        Print prediction results in a formatted way.

        Args:
            results: Dictionary from predict() or predict_from_video()
        """
        print("\n" + "="*70)
        print("PREDICTION RESULTS")
        print("="*70)

        print(f"\nTranscript: '{results['transcript']}'")
        print(f"\nPredicted Emotion: {results['predicted_emotion'].upper()}")
        print(f"Confidence: {results['confidence']:.2%}")

        print("\nTop 5 Predictions:")
        for i, pred in enumerate(results['top_5_predictions'], 1):
            bar = '█' * int(pred['probability'] * 50)
            print(f"  {i}. {pred['emotion']:15s} {pred['probability']:.2%}  {bar}")

        print("\n" + "="*70)


def main():
    """Main inference function."""
    parser = argparse.ArgumentParser(description='Emotion inference from tri-modal inputs')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--face-mesh', type=str, required=True, help='Path to 3D face mesh file')
    parser.add_argument('--audio', type=str, default=None, help='Path to audio file')
    parser.add_argument('--video', type=str, default=None, help='Path to video file')
    parser.add_argument('--config', type=str, default='configs/model_config.yaml', help='Model config')
    parser.add_argument('--emotions', type=str, default='configs/emotions.yaml', help='Emotions config')

    args = parser.parse_args()

    # Initialize inference
    inference = EmotionInference(
        model_path=args.model,
        config_path=args.config,
        emotions_config_path=args.emotions
    )

    # Run prediction
    if args.video:
        results = inference.predict_from_video(args.video, args.face_mesh)
    elif args.audio:
        results = inference.predict(args.face_mesh, args.audio)
    else:
        print("Error: Please provide either --audio or --video")
        return

    # Print results
    inference.print_results(results)


if __name__ == "__main__":
    main()
