"""
Audio to Text Transcription using OpenAI Whisper

This module transcribes audio files to text for semantic/contextual analysis
in the text branch of the tri-modal model.

Whisper is a robust speech-to-text model trained on diverse audio data.
"""

import whisper
import numpy as np
from pathlib import Path
import json


class WhisperTranscriber:
    """
    Transcribe audio files to text using OpenAI Whisper.
    """

    def __init__(self, model_size='base', device='cpu', language='en'):
        """
        Initialize Whisper transcriber.

        Args:
            model_size: Whisper model size
                        'tiny', 'base', 'small', 'medium', 'large'
                        (larger = more accurate but slower)
            device: 'cpu' or 'cuda' for GPU acceleration
            language: Language code ('en' for English, None for auto-detect)
        """
        self.model_size = model_size
        self.device = device
        self.language = language

        print(f"Loading Whisper model '{model_size}'...")
        self.model = whisper.load_model(model_size, device=device)
        print("Whisper model loaded successfully!")

    def transcribe_audio(self, audio_path, verbose=False):
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            verbose: Print detailed transcription info

        Returns:
            Dictionary containing:
                - 'text': Full transcription
                - 'segments': List of timestamped segments
                - 'language': Detected language
        """
        result = self.model.transcribe(
            str(audio_path),
            language=self.language,
            verbose=verbose
        )

        return {
            'text': result['text'].strip(),
            'segments': result.get('segments', []),
            'language': result.get('language', 'unknown')
        }

    def transcribe_to_file(self, audio_path, output_path):
        """
        Transcribe audio and save to text file.

        Args:
            audio_path: Path to audio file
            output_path: Path to save transcription (.txt)

        Returns:
            Transcription text
        """
        result = self.transcribe_audio(audio_path)
        text = result['text']

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return text

    def transcribe_to_json(self, audio_path, output_path):
        """
        Transcribe audio and save detailed results to JSON.

        Args:
            audio_path: Path to audio file
            output_path: Path to save JSON file

        Returns:
            Full transcription result dictionary
        """
        result = self.transcribe_audio(audio_path)

        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return result

    def batch_transcribe(
        self,
        input_dir,
        output_dir,
        emotion_label=None,
        save_format='txt'
    ):
        """
        Transcribe multiple audio files in a directory.

        Args:
            input_dir: Directory containing audio files
            output_dir: Directory to save transcriptions
            emotion_label: Optional emotion label for organizing output
            save_format: 'txt' or 'json'

        Returns:
            Dictionary mapping filenames to transcriptions
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if emotion_label:
            output_path = output_path / emotion_label

        output_path.mkdir(parents=True, exist_ok=True)

        # Find audio files
        audio_files = (
            list(input_path.glob('*.wav')) +
            list(input_path.glob('*.mp3')) +
            list(input_path.glob('*.m4a'))
        )

        print(f"Transcribing {len(audio_files)} audio files...")

        results = {}

        for i, audio_file in enumerate(audio_files):
            try:
                if save_format == 'txt':
                    output_file = output_path / f"{audio_file.stem}.txt"
                    text = self.transcribe_to_file(str(audio_file), str(output_file))
                    results[audio_file.name] = text
                else:  # json
                    output_file = output_path / f"{audio_file.stem}.json"
                    result = self.transcribe_to_json(str(audio_file), str(output_file))
                    results[audio_file.name] = result

                if (i + 1) % 5 == 0:
                    print(f"Transcribed {i + 1}/{len(audio_files)} files")

            except Exception as e:
                print(f"Error transcribing {audio_file}: {e}")
                results[audio_file.name] = None

        print(f"Completed! Saved to {output_path}")
        return results

    def get_word_timestamps(self, audio_path):
        """
        Get word-level timestamps from transcription.

        Args:
            audio_path: Path to audio file

        Returns:
            List of (word, start_time, end_time) tuples
        """
        result = self.model.transcribe(
            str(audio_path),
            language=self.language,
            word_timestamps=True
        )

        words = []
        for segment in result.get('segments', []):
            for word_info in segment.get('words', []):
                words.append((
                    word_info['word'],
                    word_info['start'],
                    word_info['end']
                ))

        return words


def extract_emotion_keywords(text):
    """
    Extract emotion-related keywords from transcription.

    This is a simple keyword-based approach. For production,
    consider using NLP libraries like spaCy or NLTK.

    Args:
        text: Transcribed text

    Returns:
        List of detected emotion keywords
    """
    emotion_keywords = {
        'joy': ['happy', 'joyful', 'excited', 'delighted', 'cheerful'],
        'sadness': ['sad', 'unhappy', 'depressed', 'miserable', 'sorrowful'],
        'anger': ['angry', 'furious', 'mad', 'irritated', 'outraged'],
        'fear': ['afraid', 'scared', 'frightened', 'terrified', 'anxious'],
        'disgust': ['disgusted', 'revolted', 'repulsed', 'sick'],
        'surprise': ['surprised', 'shocked', 'amazed', 'astonished'],
        'regret': ['regret', 'remorse', 'sorry', 'apologize'],
        'disappointment': ['disappointed', 'let down', 'frustrated'],
        'gratitude': ['grateful', 'thankful', 'appreciate', 'thanks']
    }

    detected = []
    text_lower = text.lower()

    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected.append((emotion, keyword))

    return detected


if __name__ == "__main__":
    # Example usage
    print("Whisper Transcriber Test\n" + "="*50)

    # Initialize transcriber
    # Note: First run will download the model (~140MB for 'base')
    transcriber = WhisperTranscriber(
        model_size='base',
        device='cpu',
        language='en'
    )

    print("\nTranscriber initialized successfully!")
    print("\nTo transcribe audio files:")
    print("  text = transcriber.transcribe_to_file('audio.wav', 'transcript.txt')")
    print("  transcriber.batch_transcribe('data/audio/', 'data/transcripts/', emotion_label='joy')")

    # Example: Extract emotion keywords
    sample_text = "I'm so disappointed. I really regret not taking that opportunity."
    keywords = extract_emotion_keywords(sample_text)
    print(f"\nExample text: '{sample_text}'")
    print(f"Detected emotion keywords: {keywords}")
