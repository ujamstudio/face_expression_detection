"""
Batch Preprocessing Script for Tri-Modal Emotion Data

This script automates the complete preprocessing pipeline:
1. Extract audio from video files
2. Generate mel-spectrograms from audio
3. Transcribe audio to text (Whisper)
4. Process 3D point clouds

Usage:
    python scripts/preprocess_all.py --input data/raw --output data/processed

Directory structure expected:
data/raw/
├── videos/
│   ├── joy/
│   │   ├── clip_0001.mp4
│   │   └── ...
│   └── sadness/
│       └── ...
└── meshes/
    ├── joy/
    │   ├── clip_0001.json
    │   └── ...
    └── sadness/
        └── ...
"""

import argparse
import sys
from pathlib import Path
import yaml
from tqdm import tqdm

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from preprocessing.audio_to_spectrogram import SpectrogramGenerator, extract_audio_from_video
from preprocessing.audio_to_text import WhisperTranscriber
from preprocessing.pointcloud_processor import PointCloudProcessor


class TriModalPreprocessor:
    """
    Complete preprocessing pipeline for tri-modal emotion data.
    """

    def __init__(self, config_path='configs/model_config.yaml'):
        """
        Initialize preprocessor with configuration.

        Args:
            config_path: Path to model configuration file
        """
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Load emotion labels
        emotions_config_path = Path(config_path).parent / 'emotions.yaml'
        with open(emotions_config_path, 'r') as f:
            emotions_config = yaml.safe_load(f)

        self.emotions = list(emotions_config['emotions'].values())

        # Initialize preprocessors
        print("Initializing preprocessors...")

        self.spec_generator = SpectrogramGenerator(
            sample_rate=self.config['audio']['sample_rate'],
            n_mels=self.config['audio']['n_mels'],
            n_fft=self.config['audio']['n_fft'],
            hop_length=self.config['audio']['hop_length'],
            duration=self.config['audio']['duration'],
            target_size=(self.config['audio']['spec_height'], self.config['audio']['spec_width'])
        )

        self.transcriber = WhisperTranscriber(
            model_size='base',
            device='cpu',
            language='en'
        )

        self.pointcloud_processor = PointCloudProcessor(
            num_points=self.config['vision']['num_points']
        )

        print("Preprocessors initialized!")

    def extract_audio_from_videos(self, input_dir, output_dir):
        """
        Extract audio from video files.

        Args:
            input_dir: Directory containing video files (organized by emotion)
            output_dir: Directory to save extracted audio files
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        print("\n" + "="*70)
        print("STEP 1: Extracting Audio from Videos")
        print("="*70)

        for emotion in self.emotions:
            emotion_input = input_path / emotion
            emotion_output = output_path / emotion

            if not emotion_input.exists():
                print(f"Skipping {emotion} (no input directory)")
                continue

            emotion_output.mkdir(parents=True, exist_ok=True)

            # Find video files
            video_files = (
                list(emotion_input.glob('*.mp4')) +
                list(emotion_input.glob('*.mov')) +
                list(emotion_input.glob('*.avi'))
            )

            if len(video_files) == 0:
                print(f"No videos found for {emotion}")
                continue

            print(f"\nProcessing {emotion}: {len(video_files)} videos")

            for video_file in tqdm(video_files, desc=f"  {emotion}"):
                try:
                    audio_file = emotion_output / f"{video_file.stem}.wav"
                    extract_audio_from_video(str(video_file), str(audio_file))
                except Exception as e:
                    print(f"    Error processing {video_file.name}: {e}")

    def generate_spectrograms(self, audio_dir, output_dir):
        """
        Generate mel-spectrograms from audio files.

        Args:
            audio_dir: Directory containing audio files
            output_dir: Directory to save spectrograms
        """
        print("\n" + "="*70)
        print("STEP 2: Generating Mel-Spectrograms")
        print("="*70)

        for emotion in self.emotions:
            emotion_input = Path(audio_dir) / emotion
            emotion_output = Path(output_dir) / emotion

            if not emotion_input.exists():
                print(f"Skipping {emotion} (no audio directory)")
                continue

            emotion_output.mkdir(parents=True, exist_ok=True)

            audio_files = list(emotion_input.glob('*.wav'))

            if len(audio_files) == 0:
                print(f"No audio files found for {emotion}")
                continue

            print(f"\nProcessing {emotion}: {len(audio_files)} files")

            for audio_file in tqdm(audio_files, desc=f"  {emotion}"):
                try:
                    spec_file = emotion_output / f"{audio_file.stem}.png"
                    self.spec_generator.process_audio_file(str(audio_file), str(spec_file))
                except Exception as e:
                    print(f"    Error processing {audio_file.name}: {e}")

    def transcribe_audio(self, audio_dir, output_dir):
        """
        Transcribe audio to text using Whisper.

        Args:
            audio_dir: Directory containing audio files
            output_dir: Directory to save transcripts
        """
        print("\n" + "="*70)
        print("STEP 3: Transcribing Audio to Text (Whisper)")
        print("="*70)

        for emotion in self.emotions:
            emotion_input = Path(audio_dir) / emotion
            emotion_output = Path(output_dir) / emotion

            if not emotion_input.exists():
                print(f"Skipping {emotion} (no audio directory)")
                continue

            emotion_output.mkdir(parents=True, exist_ok=True)

            audio_files = list(emotion_input.glob('*.wav'))

            if len(audio_files) == 0:
                print(f"No audio files found for {emotion}")
                continue

            print(f"\nProcessing {emotion}: {len(audio_files)} files")

            for audio_file in tqdm(audio_files, desc=f"  {emotion}"):
                try:
                    text_file = emotion_output / f"{audio_file.stem}.txt"
                    self.transcriber.transcribe_to_file(str(audio_file), str(text_file))
                except Exception as e:
                    print(f"    Error transcribing {audio_file.name}: {e}")

    def process_pointclouds(self, input_dir, output_dir):
        """
        Process 3D point clouds (sample, normalize).

        Args:
            input_dir: Directory containing raw mesh files
            output_dir: Directory to save processed point clouds
        """
        print("\n" + "="*70)
        print("STEP 4: Processing 3D Point Clouds")
        print("="*70)

        for emotion in self.emotions:
            emotion_input = Path(input_dir) / emotion
            emotion_output = Path(output_dir) / emotion

            if not emotion_input.exists():
                print(f"Skipping {emotion} (no mesh directory)")
                continue

            emotion_output.mkdir(parents=True, exist_ok=True)

            mesh_files = list(emotion_input.glob('*.json')) + list(emotion_input.glob('*.ply'))

            if len(mesh_files) == 0:
                print(f"No mesh files found for {emotion}")
                continue

            print(f"\nProcessing {emotion}: {len(mesh_files)} files")

            for mesh_file in tqdm(mesh_files, desc=f"  {emotion}"):
                try:
                    output_file = emotion_output / f"{mesh_file.stem}.json"
                    self.pointcloud_processor.process_pointcloud(
                        str(mesh_file),
                        str(output_file),
                        normalize=True,
                        augment=False
                    )
                except Exception as e:
                    print(f"    Error processing {mesh_file.name}: {e}")

    def run_full_pipeline(self, input_dir, output_dir):
        """
        Run complete preprocessing pipeline.

        Args:
            input_dir: Root input directory
            output_dir: Root output directory
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # Create output directories
        audio_dir = output_path / 'audio_extracted'
        spec_dir = output_path / 'spectrograms'
        text_dir = output_path / 'transcripts'
        mesh_dir = output_path / 'face_meshes'

        print("="*70)
        print("TRI-MODAL PREPROCESSING PIPELINE")
        print("="*70)
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        print(f"Emotions: {len(self.emotions)}")

        # Step 1: Extract audio (if videos exist)
        video_dir = input_path / 'videos'
        if video_dir.exists():
            self.extract_audio_from_videos(video_dir, audio_dir)
        else:
            print("\nNo videos directory found, skipping audio extraction")
            audio_dir = input_path / 'audio'  # Use existing audio

        # Step 2: Generate spectrograms
        self.generate_spectrograms(audio_dir, spec_dir)

        # Step 3: Transcribe audio
        self.transcribe_audio(audio_dir, text_dir)

        # Step 4: Process point clouds
        mesh_input = input_path / 'meshes'
        if mesh_input.exists():
            self.process_pointclouds(mesh_input, mesh_dir)
        else:
            print("\nNo meshes directory found, skipping point cloud processing")

        print("\n" + "="*70)
        print("PREPROCESSING COMPLETE!")
        print("="*70)
        print(f"\nProcessed data saved to: {output_path}")
        print("\nNext steps:")
        print("  1. Verify output files")
        print("  2. Check data quality")
        print("  3. Run training: python src/train.py")


def main():
    parser = argparse.ArgumentParser(description='Preprocess tri-modal emotion data')
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input directory containing raw data'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output directory for processed data'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='configs/model_config.yaml',
        help='Configuration file path'
    )
    parser.add_argument(
        '--step',
        type=str,
        choices=['audio', 'spectrogram', 'transcribe', 'pointcloud', 'all'],
        default='all',
        help='Which preprocessing step to run'
    )

    args = parser.parse_args()

    # Initialize preprocessor
    preprocessor = TriModalPreprocessor(config_path=args.config)

    # Run selected step
    if args.step == 'all':
        preprocessor.run_full_pipeline(args.input, args.output)
    elif args.step == 'audio':
        preprocessor.extract_audio_from_videos(
            Path(args.input) / 'videos',
            Path(args.output) / 'audio_extracted'
        )
    elif args.step == 'spectrogram':
        preprocessor.generate_spectrograms(
            Path(args.input) / 'audio',
            Path(args.output) / 'spectrograms'
        )
    elif args.step == 'transcribe':
        preprocessor.transcribe_audio(
            Path(args.input) / 'audio',
            Path(args.output) / 'transcripts'
        )
    elif args.step == 'pointcloud':
        preprocessor.process_pointclouds(
            Path(args.input) / 'meshes',
            Path(args.output) / 'face_meshes'
        )


if __name__ == "__main__":
    main()
