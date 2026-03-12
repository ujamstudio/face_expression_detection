"""
Audio to Spectrogram Conversion

This module converts audio files (.wav) to mel-spectrogram images for
use in the audio CNN branch. Spectrograms visualize the frequency content
of audio over time, capturing voice tone, pitch, and prosodic features.
"""

import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import soundfile as sf


class SpectrogramGenerator:
    """
    Generate mel-spectrogram images from audio files.
    """

    def __init__(
        self,
        sample_rate=16000,
        n_mels=128,
        n_fft=2048,
        hop_length=512,
        duration=3.0,
        target_size=(128, 128)
    ):
        """
        Initialize spectrogram generator.

        Args:
            sample_rate: Audio sample rate (Hz)
            n_mels: Number of mel frequency bands
            n_fft: FFT window size
            hop_length: Number of samples between successive frames
            duration: Audio clip duration (seconds)
            target_size: Output image size (height, width)
        """
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.duration = duration
        self.target_size = target_size

    def load_audio(self, audio_path, offset=0.0):
        """
        Load audio file.

        Args:
            audio_path: Path to audio file
            offset: Start reading after this time (seconds)

        Returns:
            Audio time series as numpy array
        """
        audio, sr = librosa.load(
            audio_path,
            sr=self.sample_rate,
            duration=self.duration,
            offset=offset
        )
        return audio

    def extract_mel_spectrogram(self, audio):
        """
        Extract mel-spectrogram from audio time series.

        Args:
            audio: Audio time series (numpy array)

        Returns:
            Mel-spectrogram (2D numpy array)
        """
        # Compute mel-spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=self.sample_rate,
            n_mels=self.n_mels,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )

        # Convert to dB scale (log scale)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        return mel_spec_db

    def spectrogram_to_image(self, mel_spec_db, output_path=None, colormap='viridis'):
        """
        Convert mel-spectrogram to RGB image.

        Args:
            mel_spec_db: Mel-spectrogram in dB scale
            output_path: Path to save image (optional)
            colormap: Matplotlib colormap name

        Returns:
            RGB image as numpy array (height, width, 3)
        """
        # Normalize to [0, 1] range
        normalized = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min() + 1e-8)

        # Create figure without axes
        fig = plt.figure(figsize=(self.target_size[1]/100, self.target_size[0]/100), dpi=100)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)

        # Display spectrogram
        ax.imshow(
            normalized,
            aspect='auto',
            origin='lower',
            cmap=colormap
        )

        # Save or convert to array
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=100)
            plt.close()
            # Load saved image
            from PIL import Image
            img = Image.open(output_path).convert('RGB')
            img = img.resize(self.target_size)
            return np.array(img)
        else:
            # Convert to numpy array
            fig.canvas.draw()
            img_array = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            img_array = img_array.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            plt.close()

            # Resize to target size
            from PIL import Image
            img = Image.fromarray(img_array)
            img = img.resize(self.target_size)
            return np.array(img)

    def process_audio_file(self, audio_path, output_path=None):
        """
        Complete pipeline: audio file -> spectrogram image.

        Args:
            audio_path: Path to input audio file
            output_path: Path to save spectrogram image (optional)

        Returns:
            RGB spectrogram image (numpy array)
        """
        # Load audio
        audio = self.load_audio(audio_path)

        # Extract mel-spectrogram
        mel_spec_db = self.extract_mel_spectrogram(audio)

        # Convert to image
        img = self.spectrogram_to_image(mel_spec_db, output_path)

        return img

    def batch_process(self, input_dir, output_dir, emotion_label=None):
        """
        Process multiple audio files in a directory.

        Args:
            input_dir: Directory containing audio files
            output_dir: Directory to save spectrogram images
            emotion_label: Optional emotion label for organizing output

        Returns:
            Number of files processed
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if emotion_label:
            output_path = output_path / emotion_label

        output_path.mkdir(parents=True, exist_ok=True)

        audio_files = list(input_path.glob('*.wav')) + list(input_path.glob('*.mp3'))

        print(f"Processing {len(audio_files)} audio files...")

        for i, audio_file in enumerate(audio_files):
            try:
                output_file = output_path / f"{audio_file.stem}.png"
                self.process_audio_file(str(audio_file), str(output_file))

                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(audio_files)} files")

            except Exception as e:
                print(f"Error processing {audio_file}: {e}")

        print(f"Completed! Saved to {output_path}")
        return len(audio_files)


def extract_audio_from_video(video_path, output_audio_path):
    """
    Extract audio track from video file.

    Args:
        video_path: Path to video file
        output_audio_path: Path to save extracted audio (.wav)

    Returns:
        Path to extracted audio file
    """
    from moviepy.editor import VideoFileClip

    video = VideoFileClip(video_path)
    audio = video.audio

    if audio is None:
        raise ValueError(f"No audio track found in {video_path}")

    audio.write_audiofile(output_audio_path, codec='pcm_s16le')
    video.close()

    return output_audio_path


if __name__ == "__main__":
    # Example usage
    print("Spectrogram Generator Test\n" + "="*50)

    # Initialize generator
    generator = SpectrogramGenerator(
        sample_rate=16000,
        n_mels=128,
        n_fft=2048,
        hop_length=512,
        duration=3.0,
        target_size=(128, 128)
    )

    # Test with a synthetic audio signal (sine wave)
    print("\nGenerating test audio (440 Hz sine wave)...")
    duration = 3.0
    t = np.linspace(0, duration, int(16000 * duration))
    test_audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz (A4 note)

    # Extract spectrogram
    mel_spec_db = generator.extract_mel_spectrogram(test_audio)
    print(f"Mel-spectrogram shape: {mel_spec_db.shape}")

    # Convert to image
    img = generator.spectrogram_to_image(mel_spec_db)
    print(f"Image shape: {img.shape}")
    print(f"Image dtype: {img.dtype}")
    print(f"Image range: [{img.min()}, {img.max()}]")

    print("\nTo process real audio files:")
    print("generator.process_audio_file('input.wav', 'output.png')")
    print("generator.batch_process('data/audio/', 'data/spectrograms/', emotion_label='joy')")
