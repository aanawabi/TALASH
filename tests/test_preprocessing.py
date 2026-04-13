"""
Tests for the preprocessing module.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.text_cleaner import TextCleaner


class TestTextCleaner:
    """Tests for TextCleaner class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cleaner = TextCleaner()

    def test_remove_extra_whitespace(self):
        """Test whitespace normalization."""
        text = "Hello    World\n\n\n\nTest"
        result = self.cleaner.remove_extra_whitespace(text)
        assert "    " not in result
        assert "\n\n\n\n" not in result

    def test_normalize_bullets(self):
        """Test bullet point normalization."""
        text = "• Item 1\n● Item 2\n- Item 3"
        result = self.cleaner.normalize_bullets(text)
        assert "•" not in result
        assert "●" not in result

    def test_clean_empty_string(self):
        """Test cleaning empty string."""
        result = self.cleaner.clean("")
        assert result == ""

    def test_clean_preserves_content(self):
        """Test that cleaning preserves meaningful content."""
        text = "John Doe\nSoftware Engineer\nPython, JavaScript"
        result = self.cleaner.clean(text)
        assert "John Doe" in result
        assert "Software Engineer" in result
        assert "Python" in result

    def test_prepare_for_llm_truncation(self):
        """Test text truncation for LLM."""
        long_text = "A" * 10000
        result = self.cleaner.prepare_for_llm(long_text, max_length=1000)
        assert len(result) <= 1100  # Allow for truncation message

    def test_extract_sections(self):
        """Test section extraction."""
        text = """
        John Doe

        EDUCATION
        BS Computer Science

        EXPERIENCE
        Software Engineer at Tech Corp
        """
        sections = self.cleaner.extract_sections(text)
        assert "education" in sections or "header" in sections


class TestPDFParser:
    """Tests for PDFParser class (requires actual PDF files)."""

    def test_supported_extensions(self):
        """Test that PDF extension is supported."""
        from src.preprocessing.pdf_parser import PDFParser
        parser = PDFParser()
        assert ".pdf" in parser.supported_extensions

    def test_extract_nonexistent_file(self):
        """Test extraction from non-existent file."""
        from src.preprocessing.pdf_parser import PDFParser
        parser = PDFParser()
        result = parser.extract_text("nonexistent_file.pdf")
        assert result["success"] is False
        assert "not found" in result.get("error", "").lower()

    def test_extract_unsupported_format(self):
        """Test extraction from unsupported file format."""
        from src.preprocessing.pdf_parser import PDFParser
        parser = PDFParser()
        result = parser.extract_text("document.docx")
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
