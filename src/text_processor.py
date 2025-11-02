"""Text processing module for Vietnamese text normalization and tokenization."""

import logging
import re
from typing import List

try:
    from underthesea import word_tokenize
except ImportError:
    logging.warning("underthesea not available, using simple tokenizer")
    word_tokenize = None

logger = logging.getLogger(__name__)


class TextProcessor:
    """Process and normalize Vietnamese text for TTS."""

    def __init__(self) -> None:
        """Initialize text processor."""
        # Common abbreviations in Vietnamese
        self.abbreviations = {
            "Ông": "ông",
            "Bà": "bà",
            "Anh": "anh",
            "Chị": "chị",
            "Em": "em",
            "Dr.": "tiến sĩ",
            "Mr.": "ông",
            "Mrs.": "bà",
            "Ms.": "cô",
        }

    def normalize_text(self, text: str) -> str:
        """Normalize Vietnamese text for TTS.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text.strip())

        # Normalize Vietnamese diacritics (if needed)
        text = self._normalize_diacritics(text)

        # Handle common abbreviations
        text = self._expand_abbreviations(text)

        # Remove special characters that might cause issues
        text = self._clean_special_chars(text)

        return text.strip()

    def _normalize_diacritics(self, text: str) -> str:
        """Normalize Vietnamese diacritics if needed.

        Args:
            text: Input text

        Returns:
            Text with normalized diacritics
        """
        # This is a placeholder - Vietnamese text should already have proper diacritics
        # Can be extended if needed for handling common typos
        return text

    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations.

        Args:
            text: Input text

        Returns:
            Text with expanded abbreviations
        """
        for abbrev, expansion in self.abbreviations.items():
            # Use word boundaries to match whole words
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)
        return text

    def _clean_special_chars(self, text: str) -> str:
        """Clean special characters that might cause TTS issues.

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        # Keep Vietnamese characters, numbers, basic punctuation
        # Vietnamese Unicode range: U+00C0 to U+1EF9
        text = re.sub(
            r"[^\w\s\u00C0-\u1EF9.,!?;:()\-'\"ÀÁẢÃẠÂẦẤẨẪẬĂẰẮẲẴẶÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐàáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]",
            "",
            text,
        )
        return text

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Vietnamese text.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        if not text:
            return []

        normalized = self.normalize_text(text)

        if word_tokenize is not None:
            try:
                tokens = word_tokenize(normalized)
                return [token for token in tokens if token.strip()]
            except Exception as e:
                logger.warning(f"Error in underthesea tokenization: {e}")

        # Fallback to simple whitespace tokenization
        return [token for token in normalized.split() if token.strip()]

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        if not text:
            return []

        # Split by sentence-ending punctuation
        sentences = re.split(r"[.!?]+\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def preprocess_for_tts(self, text: str, max_length: int = 500) -> List[str]:
        """Preprocess text for TTS input.

        Args:
            text: Input text
            max_length: Maximum length per chunk (characters)

        Returns:
            List of text chunks ready for TTS
        """
        normalized = self.normalize_text(text)

        if len(normalized) <= max_length:
            return [normalized]

        # Split into sentences first
        sentences = self.split_sentences(normalized)
        if not sentences:
            # If no sentence breaks, split by length
            chunks = [
                normalized[i : i + max_length]
                for i in range(0, len(normalized), max_length)
            ]
            return chunks

        # Group sentences into chunks
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

