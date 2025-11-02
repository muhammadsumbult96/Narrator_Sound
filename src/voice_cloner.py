"""Voice cloning module that combines audio processing and TTS."""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional

import numpy as np

from src.audio_processor import AudioProcessor
from src.audio_deepener import deepen_voice
from src.text_processor import TextProcessor
from src.tts_engine import TTSEngine

logger = logging.getLogger(__name__)


class VoiceCloner:
    """Voice cloning system using audio samples and TTS."""

    def __init__(
        self,
        sound_dir: str | Path = "Sound",
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        device: str = "cpu",
    ) -> None:
        """Initialize voice cloner.

        Args:
            sound_dir: Directory containing audio samples
            model_name: TTS model name
            device: Device to use ('cpu' or 'cuda')
        """
        self.audio_processor = AudioProcessor(sound_dir=sound_dir)
        self.text_processor = TextProcessor()
        self.tts_engine = TTSEngine(model_name=model_name, device=device)

        # Cache for selected voice samples
        self._voice_samples: Optional[List[Path]] = None

    def initialize(self, require_transcript: bool = True) -> None:
        """Initialize the voice cloner (discover audio files, select samples).
        
        Args:
            require_transcript: If True, only use audio files that have transcripts
        """
        logger.info("Initializing voice cloner...")
        self.audio_processor.discover_audio_files(require_transcript=require_transcript)
        
        if not self.audio_processor.audio_files:
            if require_transcript:
                raise ValueError(
                    "No audio files with transcripts found! "
                    "Run scripts/transcribe_audio.py first to transcribe audio files."
                )
            else:
                raise ValueError("No audio files found!")
        
        self._select_voice_samples()
        logger.info(f"Voice cloner initialized with {len(self.audio_processor.audio_files)} audio files")

    def _select_voice_samples(self, num_samples: int = 5) -> None:
        """Select best voice samples for cloning.

        Args:
            num_samples: Number of samples to select
        """
        self._voice_samples = self.audio_processor.select_best_voice_samples(
            min_duration=2.0,
            max_duration=15.0,
            max_samples=num_samples,
        )

        if not self._voice_samples:
            # Fallback: use first few files if selection fails
            all_files = self.audio_processor.audio_files
            self._voice_samples = all_files[:num_samples] if all_files else []
            logger.warning("Using fallback voice samples")

        logger.info(f"Selected {len(self._voice_samples)} voice samples")

    def get_voice_samples(self) -> List[Path]:
        """Get list of selected voice samples.

        Returns:
            List of audio file paths
        """
        if self._voice_samples is None:
            self._select_voice_samples()
        return self._voice_samples.copy()

    def clone_voice(
        self,
        text: str,
        speaker_sample: Optional[str | Path] = None,
        language: str = "en",
        output_path: Optional[str | Path] = None,
    ) -> np.ndarray:
        """Clone voice and synthesize text.

        Args:
            text: Text to synthesize
            speaker_sample: Optional path to specific speaker audio.
                If None, uses best available sample.
            language: Language code (default: 'vi')
            output_path: Optional path to save output audio

        Returns:
            Audio array as numpy array
        """
        if not text:
            raise ValueError("Text cannot be empty")
        
        # Validate text length (prevent extremely long texts)
        if len(text) > 10000:
            logger.warning(f"Text is very long ({len(text)} chars), may take a while to process")

        # Preprocess text
        text_chunks = self.text_processor.preprocess_for_tts(text, max_length=500)
        logger.info(f"Text split into {len(text_chunks)} chunks")

        # Select speaker sample
        if speaker_sample is None:
            voice_samples = self.get_voice_samples()
            if not voice_samples:
                raise ValueError("No voice samples available")
            speaker_sample = voice_samples[0]  # Use first sample
            logger.info(f"Using default voice sample: {speaker_sample}")

        speaker_sample = Path(speaker_sample)
        if not speaker_sample.exists():
            raise FileNotFoundError(f"Speaker sample not found: {speaker_sample}")

        # Synthesize each chunk and concatenate
        audio_segments = []
        chunk_files_to_cleanup = []
        
        try:
            for i, chunk in enumerate(text_chunks):
                logger.info(f"Processing chunk {i+1}/{len(text_chunks)}")
                
                # Use temporary file for chunks
                chunk_output = None
                if output_path:
                    # Convert to Path if it's a string
                    output_path_obj = Path(output_path) if isinstance(output_path, str) else output_path
                    chunk_output = Path(tempfile.gettempdir()) / f"chunk_{i}_{output_path_obj.stem}.wav"
                    chunk_files_to_cleanup.append(chunk_output)

                audio = self.tts_engine.synthesize(
                    text=chunk,
                    speaker_wav=speaker_sample,
                    language=language,
                    output_path=chunk_output,
                )
                audio_segments.append(audio)
        finally:
            # Cleanup temporary chunk files
            for chunk_file in chunk_files_to_cleanup:
                try:
                    if chunk_file.exists():
                        chunk_file.unlink()
                except Exception as e:
                    logger.warning(f"Could not cleanup chunk file {chunk_file}: {e}")

        # Ensure all segments have the same sample rate and format
        sample_rate = 22050  # XTTS standard sample rate
        
        # Normalize and concatenate all segments with small pauses
        normalized_segments = []
        pause_duration = 0.2  # 0.2 seconds pause between chunks
        pause_samples = int(sample_rate * pause_duration)
        pause = np.zeros(pause_samples, dtype=np.float32)
        
        for i, audio in enumerate(audio_segments):
            # Ensure audio is 1D array
            if audio.ndim > 1:
                audio = np.mean(audio, axis=0)
            
            # Ensure same sample rate (resample if needed)
            if len(audio) > 0:
                # Normalize audio to prevent clipping
                max_val = np.abs(audio).max()
                if max_val > 0:
                    audio = audio / max_val * 0.95  # Leave headroom
                
                normalized_segments.append(audio)
                
                # Add pause between chunks (except after last one)
                if i < len(audio_segments) - 1:
                    normalized_segments.append(pause)
        
        # Concatenate all segments
        if len(normalized_segments) == 1:
            final_audio = normalized_segments[0]
        else:
            final_audio = np.concatenate(normalized_segments)
        
        # Final normalization to ensure proper range
        max_val = np.abs(final_audio).max()
        if max_val > 0:
            final_audio = final_audio / max_val * 0.95
        
        # Ensure proper dtype
        final_audio = final_audio.astype(np.float32)
        
        # Apply subtle deep voice processing (very light pitch shift)
        # Uses -1.2 semitones for subtle depth while preserving natural voice
        logger.info("Applying subtle deep voice processing...")
        final_audio = deepen_voice(
            audio=final_audio,
            sample_rate=sample_rate,
            pitch_shift_semitones=-1.2,  # Very subtle pitch shift
            enabled=True,
        )

        # Save final output if path provided
        if output_path:
            import soundfile as sf
            
            # Convert to Path if it's a string
            output_path_obj = Path(output_path) if isinstance(output_path, str) else output_path
            
            # Ensure directory exists
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with proper format
            sf.write(
                str(output_path_obj),
                final_audio,
                sample_rate,
                subtype='PCM_16'  # Use 16-bit PCM for better compatibility
            )
            logger.info(f"Saved output to {output_path_obj} (duration: {len(final_audio)/sample_rate:.2f}s)")

        return final_audio

    def synthesize_simple(
        self,
        text: str,
        output_path: Optional[str | Path] = None,
    ) -> np.ndarray:
        """Simple synthesis with automatic voice sample selection.

        Args:
            text: Text to synthesize
            output_path: Optional path to save output

        Returns:
            Audio array
        """
        return self.clone_voice(text=text, output_path=output_path)

