"""Audio processing module for reading and normalizing audio files."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import librosa
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

# Standard audio parameters for TTS
TARGET_SAMPLE_RATE = 22050
TARGET_DURATION_MAX = 30.0  # Maximum duration in seconds


class AudioProcessor:
    """Process and normalize audio files for voice cloning."""

    def __init__(
        self,
        sound_dir: str | Path = "Sound",
        target_sample_rate: int = TARGET_SAMPLE_RATE,
    ) -> None:
        """Initialize audio processor.

        Args:
            sound_dir: Directory containing audio files
            target_sample_rate: Target sample rate for audio normalization
        """
        self.sound_dir = Path(sound_dir)
        self.target_sample_rate = target_sample_rate
        self.audio_files: List[Path] = []

    def discover_audio_files(self) -> List[Path]:
        """Discover all WAV files in the sound directory.

        Returns:
            List of paths to audio files
        """
        if not self.sound_dir.exists():
            logger.warning(f"Sound directory {self.sound_dir} does not exist")
            return []

        audio_files = list(self.sound_dir.glob("*.wav"))
        self.audio_files = sorted(audio_files)
        logger.info(f"Discovered {len(self.audio_files)} audio files")
        return self.audio_files

    def load_audio(
        self,
        audio_path: str | Path,
        duration: Optional[float] = None,
    ) -> Tuple[np.ndarray, int]:
        """Load and normalize audio file.

        Args:
            audio_path: Path to audio file
            duration: Maximum duration to load (in seconds). If None, loads entire file.

        Returns:
            Tuple of (audio_array, sample_rate)
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            # Load audio with librosa (automatically resamples to target_sample_rate)
            audio, sr = librosa.load(
                str(audio_path),
                sr=self.target_sample_rate,
                duration=duration,
                mono=True,
            )

            # Normalize audio to [-1, 1] range
            if audio.max() > 0:
                audio = audio / np.abs(audio).max()

            logger.debug(
                f"Loaded audio: {audio_path.name}, "
                f"duration: {len(audio) / sr:.2f}s, "
                f"sample_rate: {sr}"
            )
            return audio, sr

        except Exception as e:
            logger.error(f"Error loading audio {audio_path}: {e}")
            raise

    def get_audio_info(self, audio_path: str | Path) -> dict:
        """Get information about an audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with audio information (duration, sample_rate, channels, etc.)
        """
        audio_path = Path(audio_path)
        try:
            info = sf.info(str(audio_path))
            duration = info.duration
            sample_rate = info.samplerate
            channels = info.channels

            return {
                "path": str(audio_path),
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": channels,
                "format": info.format,
                "subtype": info.subtype,
            }
        except Exception as e:
            logger.error(f"Error getting info for {audio_path}: {e}")
            raise

    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio array to [-1, 1] range.

        Args:
            audio: Audio array

        Returns:
            Normalized audio array
        """
        if len(audio) == 0:
            return audio

        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val

        return audio

    def trim_silence(
        self,
        audio: np.ndarray,
        top_db: int = 20,
    ) -> np.ndarray:
        """Trim leading and trailing silence from audio.

        Args:
            audio: Audio array
            top_db: Threshold in decibels below the reference

        Returns:
            Trimmed audio array
        """
        trimmed, _ = librosa.effects.trim(audio, top_db=top_db)
        return trimmed

    def get_all_audio_info(self) -> List[dict]:
        """Get information for all discovered audio files.

        Returns:
            List of audio info dictionaries
        """
        if not self.audio_files:
            self.discover_audio_files()

        audio_info_list = []
        for audio_file in self.audio_files:
            try:
                info = self.get_audio_info(audio_file)
                audio_info_list.append(info)
            except Exception as e:
                logger.warning(f"Skipping {audio_file}: {e}")

        return audio_info_list

    def select_best_voice_samples(
        self,
        min_duration: float = 2.0,
        max_duration: float = 15.0,
        max_samples: int = 10,
    ) -> List[Path]:
        """Select best audio samples for voice cloning.

        Args:
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
            max_samples: Maximum number of samples to return

        Returns:
            List of selected audio file paths
        """
        if not self.audio_files:
            self.discover_audio_files()

        selected = []
        for audio_file in self.audio_files:
            try:
                info = self.get_audio_info(audio_file)
                duration = info["duration"]

                if min_duration <= duration <= max_duration:
                    selected.append(audio_file)

                if len(selected) >= max_samples:
                    break

            except Exception as e:
                logger.debug(f"Skipping {audio_file} for selection: {e}")

        logger.info(f"Selected {len(selected)} voice samples")
        return selected

