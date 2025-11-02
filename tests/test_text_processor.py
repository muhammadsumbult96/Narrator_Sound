"""Tests for text processor module."""

import pytest

from src.text_processor import TextProcessor


def test_text_processor_initialization():
    """Test TextProcessor initialization."""
    processor = TextProcessor()
    assert processor is not None


def test_normalize_text():
    """Test text normalization."""
    processor = TextProcessor()
    
    # Test basic normalization
    text = "  Xin   chào  "
    normalized = processor.normalize_text(text)
    assert normalized == "Xin chào"
    
    # Test with Vietnamese characters
    text = "Hôm nay trời đẹp"
    normalized = processor.normalize_text(text)
    assert "đẹp" in normalized


def test_tokenize():
    """Test text tokenization."""
    processor = TextProcessor()
    
    text = "Xin chào bạn"
    tokens = processor.tokenize(text)
    assert len(tokens) > 0
    assert isinstance(tokens, list)


def test_split_sentences():
    """Test sentence splitting."""
    processor = TextProcessor()
    
    text = "Câu đầu tiên. Câu thứ hai! Câu thứ ba?"
    sentences = processor.split_sentences(text)
    assert len(sentences) >= 2


def test_preprocess_for_tts():
    """Test TTS preprocessing."""
    processor = TextProcessor()
    
    # Short text
    text = "Xin chào"
    chunks = processor.preprocess_for_tts(text)
    assert len(chunks) == 1
    assert chunks[0] == "Xin chào"
    
    # Long text (should split)
    text = "A" * 1000
    chunks = processor.preprocess_for_tts(text, max_length=100)
    assert len(chunks) > 1


def test_empty_text():
    """Test handling of empty text."""
    processor = TextProcessor()
    
    assert processor.normalize_text("") == ""
    assert processor.tokenize("") == []
    assert processor.split_sentences("") == []

