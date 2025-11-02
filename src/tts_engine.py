"""TTS engine module using Coqui TTS with voice cloning support."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import torch

# Workaround for bnnumerizer import issue
# Try to install bnnumerizer if not available
try:
    import bnnumerizer
except ImportError:
    logging.warning("bnnumerizer not found, attempting to install...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "bnnumerizer", "--quiet"])
        import bnnumerizer
    except Exception as e:
        logging.warning(f"Could not install bnnumerizer: {e}")
        # Continue anyway - may work if Bangla phonemizer is not used

from TTS.api import TTS

logger = logging.getLogger(__name__)

# Force CPU usage and optimize for CPU
os.environ["CUDA_VISIBLE_DEVICES"] = ""
# Optimize CPU inference
torch.set_num_threads(4)  # Limit threads to avoid overloading


class TTSEngine:
    """TTS engine with voice cloning capabilities."""

    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        device: Optional[str] = None,
    ) -> None:
        """Initialize TTS engine.

        Args:
            model_name: Name of the TTS model to use
            device: Device to use ('cpu' or 'cuda'). If None, auto-detect.
        """
        if device is None:
            device = "cpu"  # Force CPU for this project

        self.device = device
        self.model_name = model_name
        self.tts: Optional[TTS] = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the TTS model."""
        try:
            logger.info(f"Initializing TTS model: {self.model_name}")
            logger.info(f"Using device: {self.device}")

            self.tts = TTS(model_name=self.model_name, progress_bar=True)
            self.tts.to(self.device)

            logger.info("TTS model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TTS model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        speaker_wav: Optional[str | Path] = None,
        language: str = "vi",
        output_path: Optional[str | Path] = None,
    ) -> np.ndarray:
        """Synthesize speech from text.

        Args:
            text: Input text to synthesize
            speaker_wav: Path to speaker reference audio file (for voice cloning)
            language: Language code (default: 'vi' for Vietnamese)
            output_path: Optional path to save output audio

        Returns:
            Audio array as numpy array
        """
        if self.tts is None:
            raise RuntimeError("TTS model not initialized")

        if not text:
            raise ValueError("Text cannot be empty")

        try:
            # Use temporary output path if not provided
            if output_path is None:
                output_path = Path("temp_output.wav")
            else:
                output_path = Path(output_path)

            # Synthesize speech
            if speaker_wav is not None:
                # Voice cloning mode
                logger.info(f"Synthesizing with voice cloning from {speaker_wav}")
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=str(speaker_wav),
                    language=language,
                    file_path=str(output_path),
                )
            else:
                # Standard TTS mode
                logger.info("Synthesizing without voice cloning")
                self.tts.tts_to_file(
                    text=text,
                    language=language,
                    file_path=str(output_path),
                )

            # Load the generated audio
            import soundfile as sf

            audio, sample_rate = sf.read(str(output_path))

            # Clean up temp file if it was auto-created
            if output_path.name == "temp_output.wav" and output_path.exists():
                output_path.unlink()

            logger.info(f"Successfully synthesized {len(audio) / sample_rate:.2f}s of audio")
            return audio

        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise

    def is_available(self) -> bool:
        """Check if TTS engine is available.

        Returns:
            True if engine is initialized and ready
        """
        return self.tts is not None

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language codes
        """
        if self.tts is None:
            return []

        try:
            # XTTS v2 supports multiple languages
            return ["vi", "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"]
        except Exception:
            return ["vi", "en"]  # Default fallback

