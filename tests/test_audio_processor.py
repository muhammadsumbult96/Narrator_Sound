"""Tests for audio processor module."""

import pytest
from pathlib import Path

from src.audio_processor import AudioProcessor


def test_audio_processor_initialization():
    """Test AudioProcessor initialization."""
    processor = AudioProcessor(sound_dir="Sound")
    assert processor.sound_dir == Path("Sound")
    assert processor.target_sample_rate == 22050


def test_discover_audio_files(tmp_path):
    """Test audio file discovery."""
    # Create a temporary directory with some WAV files
    test_dir = tmp_path / "sound"
    test_dir.mkdir()
    
    # Create dummy WAV files
    (test_dir / "test1.wav").touch()
    (test_dir / "test2.wav").touch()
    
    processor = AudioProcessor(sound_dir=test_dir)
    files = processor.discover_audio_files()
    
    assert len(files) == 2
    assert all(f.suffix == ".wav" for f in files)


def test_get_audio_info(tmp_path):
    """Test getting audio file info."""
    import soundfile as sf
    import numpy as np
    
    # Create a temporary WAV file
    test_dir = tmp_path / "sound"
    test_dir.mkdir()
    test_file = test_dir / "test.wav"
    
    # Write a simple audio file
    sample_rate = 22050
    duration = 1.0
    samples = np.random.randn(int(sample_rate * duration)).astype(np.float32)
    sf.write(str(test_file), samples, sample_rate)
    
    processor = AudioProcessor(sound_dir=test_dir)
    info = processor.get_audio_info(test_file)
    
    assert "duration" in info
    assert "sample_rate" in info
    assert info["sample_rate"] == sample_rate


def test_normalize_audio():
    """Test audio normalization."""
    import numpy as np
    
    processor = AudioProcessor()
    
    # Test with audio that needs normalization
    audio = np.array([0.5, -0.5, 1.0, -1.0])
    normalized = processor.normalize_audio(audio)
    
    assert np.abs(normalized).max() <= 1.0
    
    # Test with empty array
    empty_audio = np.array([])
    normalized = processor.normalize_audio(empty_audio)
    assert len(normalized) == 0

