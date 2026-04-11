"""
Text Cleaner Module
Handles cleaning and preprocessing of extracted CV text before LLM processing.
"""

import re
from typing import List, Optional


class TextCleaner:
    """
    Cleans and preprocesses raw text extracted from PDFs.
    """

    def __init__(self):
        # Common section headers in CVs
        self.section_headers = [
            "education", "academic", "qualification", "experience", "employment",
            "work history", "skills", "technical skills", "publications", "research",
            "journal", "conference", "patents", "books", "supervision", "students",
            "projects", "certifications", "awards", "honors", "achievements",
            "professional", "contact", "personal", "summary", "objective",
            "references", "interests", "languages", "training", "courses"
        ]

    def remove_extra_whitespace(self, text: str) -> str:
        """Remove excessive whitespace while preserving paragraph structure."""
        # Replace multiple spaces with single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Replace more than 2 newlines with 2 newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)

    def remove_special_characters(self, text: str) -> str:
        """Remove problematic special characters while keeping useful ones."""
        # Keep alphanumeric, common punctuation, and useful symbols
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text

    def normalize_bullets(self, text: str) -> str:
        """Normalize various bullet point styles to a standard format."""
        bullet_patterns = [
            r'[•●○◦▪▸►◆]',  # Common bullet symbols
            r'^[\-\*]\s',  # Dash or asterisk at start of line
            r'^\d+[\.\)]\s',  # Numbered lists
        ]
        for pattern in bullet_patterns:
            text = re.sub(pattern, '- ', text, flags=re.MULTILINE)
        return text

    def fix_line_breaks(self, text: str) -> str:
        """
        Fix improperly broken lines that should be continuous.
        CVs often have text that wraps mid-sentence.
        """
        lines = text.split('\n')
        fixed_lines = []
        buffer = ""

        for line in lines:
            line = line.strip()
            if not line:
                if buffer:
                    fixed_lines.append(buffer)
                    buffer = ""
                fixed_lines.append("")
                continue

            # Check if this might be a section header
            is_header = any(
                header in line.lower() for header in self.section_headers
            ) and len(line) < 50

            if is_header:
                if buffer:
                    fixed_lines.append(buffer)
                    buffer = ""
                fixed_lines.append(line)
            elif buffer and not buffer.endswith(('.', ':', ';', '!', '?')):
                # Previous line didn't end with punctuation, might be continuation
                buffer += " " + line
            else:
                if buffer:
                    fixed_lines.append(buffer)
                buffer = line

        if buffer:
            fixed_lines.append(buffer)

        return '\n'.join(fixed_lines)

    def extract_sections(self, text: str) -> dict:
        """
        Attempt to identify and extract major CV sections.
        Returns a dictionary of section_name -> content.
        """
        sections = {}
        current_section = "header"
        current_content = []

        lines = text.split('\n')

        for line in lines:
            line_lower = line.lower().strip()

            # Check if this line is a section header
            is_section_header = False
            detected_section = None

            for header in self.section_headers:
                if header in line_lower and len(line) < 60:
                    # Likely a section header
                    is_section_header = True
                    detected_section = header
                    break

            if is_section_header and detected_section:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = detected_section
                current_content = [line]
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def clean(self, text: str, aggressive: bool = False) -> str:
        """
        Main cleaning method. Applies all cleaning steps.

        Args:
            text: Raw text to clean
            aggressive: If True, applies more aggressive cleaning

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Apply cleaning steps in order
        text = self.remove_special_characters(text)
        text = self.normalize_bullets(text)
        text = self.remove_extra_whitespace(text)

        if aggressive:
            text = self.fix_line_breaks(text)

        return text.strip()

    def prepare_for_llm(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Prepare text for LLM processing.
        Cleans and optionally truncates to fit context limits.

        Args:
            text: Raw text
            max_length: Maximum character length (optional)

        Returns:
            Prepared text ready for LLM
        """
        cleaned = self.clean(text)

        if max_length and len(cleaned) > max_length:
            # Try to truncate at a sentence boundary
            truncated = cleaned[:max_length]
            last_period = truncated.rfind('.')
            if last_period > max_length * 0.8:  # If period is in last 20%, use it
                truncated = truncated[:last_period + 1]
            cleaned = truncated + "\n\n[Content truncated due to length...]"

        return cleaned


if __name__ == "__main__":
    # Test the cleaner
    sample_text = """
    JOHN DOE
    Email: john@example.com   Phone: +1234567890

    EDUCATION

    •  PhD Computer Science
       University of Example, 2020-2024
       Thesis: Machine Learning for NLP

    •  MS Computer Science
       Another University, 2018-2020
       CGPA: 3.8/4.0

    EXPERIENCE

    Senior Software Engineer
    Tech Company Inc.
    2020 - Present
    - Led development of ML pipeline
    - Managed team of 5 engineers
    """

    cleaner = TextCleaner()
    cleaned = cleaner.clean(sample_text)
    print("Cleaned text:")
    print(cleaned)
    print("\n--- Sections ---")
    sections = cleaner.extract_sections(cleaned)
    for section, content in sections.items():
        print(f"\n[{section.upper()}]")
        print(content[:200] + "..." if len(content) > 200 else content)
