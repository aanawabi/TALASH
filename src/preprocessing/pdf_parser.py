"""
PDF Parser Module
Handles extraction of text content from PDF CVs using multiple methods
for robust text extraction.
"""

# Try to import PyMuPDF, fall back to pdfplumber only if not available
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

import pdfplumber
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not PYMUPDF_AVAILABLE:
    logger.warning("PyMuPDF not installed. Using pdfplumber only for PDF extraction.")


class PDFParser:
    """
    PDF Parser for extracting text from CV documents.
    Uses PyMuPDF as primary method and pdfplumber as fallback.
    """

    def __init__(self):
        self.supported_extensions = ['.pdf']

    def extract_text_pymupdf(self, pdf_path: str) -> str:
        """
        Extract text using PyMuPDF (fitz).
        Best for most PDF types, handles embedded fonts well.
        """
        if not PYMUPDF_AVAILABLE:
            return ""

        text_content = []
        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                text_content.append(text)
            doc.close()
            return "\n".join(text_content)
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return ""

    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text using pdfplumber.
        Good for PDFs with complex layouts and tables.
        """
        text_content = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            return "\n".join(text_content)
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return ""

    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main extraction method. Tries PyMuPDF first, falls back to pdfplumber.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing:
                - text: Extracted text content
                - method: Extraction method used
                - success: Whether extraction was successful
                - page_count: Number of pages
                - file_name: Original file name
        """
        path = Path(pdf_path)

        if not path.exists():
            return {
                "text": "",
                "method": None,
                "success": False,
                "error": f"File not found: {pdf_path}",
                "page_count": 0,
                "file_name": path.name
            }

        if path.suffix.lower() not in self.supported_extensions:
            return {
                "text": "",
                "method": None,
                "success": False,
                "error": f"Unsupported file type: {path.suffix}",
                "page_count": 0,
                "file_name": path.name
            }

        # Get page count
        page_count = 0
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                page_count = len(doc)
                doc.close()
            except:
                pass
        else:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    page_count = len(pdf.pages)
            except:
                pass

        # Try PyMuPDF first if available
        text = ""
        method = "pdfplumber"

        if PYMUPDF_AVAILABLE:
            text = self.extract_text_pymupdf(pdf_path)
            method = "PyMuPDF"

        # If PyMuPDF fails or returns minimal text, try pdfplumber
        if len(text.strip()) < 100:
            logger.info("PyMuPDF extraction yielded minimal text, trying pdfplumber...")
            text_plumber = self.extract_text_pdfplumber(pdf_path)
            if len(text_plumber) > len(text):
                text = text_plumber
                method = "pdfplumber"

        success = len(text.strip()) > 50  # At least 50 chars for a valid CV

        return {
            "text": text,
            "method": method,
            "success": success,
            "page_count": page_count,
            "file_name": path.name,
            "file_path": str(path.absolute())
        }

    def extract_with_layout(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text while preserving some layout information.
        Useful for better section detection.
        """
        result = {
            "pages": [],
            "full_text": "",
            "success": False,
            "file_name": Path(pdf_path).name
        }

        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                all_text = []

                for page_num, page in enumerate(doc):
                    # Get text blocks with position information
                    blocks = page.get_text("dict")["blocks"]
                    page_text = []

                    for block in blocks:
                        if "lines" in block:
                            for line in block["lines"]:
                                line_text = ""
                                for span in line["spans"]:
                                    line_text += span["text"]
                                page_text.append(line_text)

                    page_content = "\n".join(page_text)
                    result["pages"].append({
                        "page_number": page_num + 1,
                        "text": page_content
                    })
                    all_text.append(page_content)

                doc.close()
                result["full_text"] = "\n\n".join(all_text)
                result["success"] = True

            except Exception as e:
                logger.error(f"Layout extraction failed: {e}")
                result["error"] = str(e)
        else:
            # Fallback to pdfplumber
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    all_text = []
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text() or ""
                        result["pages"].append({
                            "page_number": page_num + 1,
                            "text": page_text
                        })
                        all_text.append(page_text)
                    result["full_text"] = "\n\n".join(all_text)
                    result["success"] = True
            except Exception as e:
                logger.error(f"Layout extraction failed: {e}")
                result["error"] = str(e)

        return result


def process_cv_folder(folder_path: str) -> list:
    """
    Process all PDF files in a folder.

    Args:
        folder_path: Path to folder containing CV PDFs

    Returns:
        List of extraction results for each PDF
    """
    parser = PDFParser()
    folder = Path(folder_path)
    results = []

    if not folder.exists():
        logger.error(f"Folder not found: {folder_path}")
        return results

    pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
    logger.info(f"Found {len(pdf_files)} PDF files in {folder_path}")

    for pdf_file in pdf_files:
        logger.info(f"Processing: {pdf_file.name}")
        result = parser.extract_text(str(pdf_file))
        results.append(result)

    return results


if __name__ == "__main__":
    # Test the parser
    import sys
    if len(sys.argv) > 1:
        parser = PDFParser()
        result = parser.extract_text(sys.argv[1])
        print(f"Success: {result['success']}")
        print(f"Method: {result['method']}")
        print(f"Pages: {result['page_count']}")
        print(f"Text length: {len(result['text'])} characters")
        print("\n--- First 1000 characters ---\n")
        print(result['text'][:1000])
