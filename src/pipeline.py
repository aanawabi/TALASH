"""
CV Processing Pipeline
Main module that orchestrates the CV extraction workflow.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .preprocessing.pdf_parser import PDFParser
from .preprocessing.text_cleaner import TextCleaner
from .extraction.llm_extractor import CVExtractor
from .utils.exporter import CVExporter
from .utils.config import Config
from .models.cv_models import ExtractedCV

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CVProcessingPipeline:
    """
    Main pipeline for processing CVs from PDF to structured data.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the pipeline.

        Args:
            config: Configuration object (optional, uses default if not provided)
        """
        self.config = config or Config()
        self.config.validate()

        self.pdf_parser = PDFParser()
        self.text_cleaner = TextCleaner()
        self.extractor = CVExtractor(
            api_key=self.config.gemini_api_key,
            model_name=self.config.gemini_model
        )
        self.exporter = CVExporter(output_dir=self.config.output_folder)

    def process_single_cv(self, pdf_path: str) -> Optional[ExtractedCV]:
        """
        Process a single CV file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ExtractedCV object or None if processing fails
        """
        logger.info(f"Processing CV: {pdf_path}")

        try:
            # Step 1: Extract text from PDF
            extraction_result = self.pdf_parser.extract_text(pdf_path)

            if not extraction_result["success"]:
                logger.error(f"Failed to extract text from {pdf_path}")
                return None

            raw_text = extraction_result["text"]
            logger.info(f"Extracted {len(raw_text)} characters from PDF")

            # Step 2: Clean the text
            cleaned_text = self.text_cleaner.prepare_for_llm(
                raw_text,
                max_length=self.config.max_cv_length
            )
            logger.info(f"Cleaned text: {len(cleaned_text)} characters")

            # Step 3: Extract structured data using LLM
            extracted_cv = self.extractor.extract(
                cleaned_text,
                source_file=extraction_result["file_name"]
            )

            logger.info(f"Successfully extracted CV for: {extracted_cv.personal_info.full_name}")
            return extracted_cv

        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return None

    def process_folder(self, folder_path: Optional[str] = None) -> List[ExtractedCV]:
        """
        Process all CVs in a folder.

        Args:
            folder_path: Path to folder containing CVs (uses config default if not provided)

        Returns:
            List of successfully extracted CVs
        """
        folder = Path(folder_path) if folder_path else self.config.input_path
        logger.info(f"Processing CVs from folder: {folder}")

        if not folder.exists():
            logger.error(f"Folder not found: {folder}")
            return []

        pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
        logger.info(f"Found {len(pdf_files)} PDF files")

        extracted_cvs = []
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"Processing {i}/{len(pdf_files)}: {pdf_file.name}")

            cv = self.process_single_cv(str(pdf_file))
            if cv:
                extracted_cvs.append(cv)
            else:
                logger.warning(f"Failed to process: {pdf_file.name}")

        logger.info(f"Successfully processed {len(extracted_cvs)}/{len(pdf_files)} CVs")
        return extracted_cvs

    def process_and_export(
        self,
        folder_path: Optional[str] = None,
        export_format: str = "excel"
    ) -> Dict[str, Any]:
        """
        Process CVs and export to file.

        Args:
            folder_path: Path to folder containing CVs
            export_format: "excel", "csv", or "both"

        Returns:
            Dictionary with processing results and output file paths
        """
        start_time = datetime.now()

        # Process CVs
        extracted_cvs = self.process_folder(folder_path)

        if not extracted_cvs:
            return {
                "success": False,
                "message": "No CVs were successfully processed",
                "processed_count": 0,
                "output_files": {}
            }

        output_files = {}

        # Export based on format
        if export_format in ["excel", "both"]:
            excel_path = self.exporter.export_to_excel(extracted_cvs)
            output_files["excel"] = excel_path

        if export_format in ["csv", "both"]:
            csv_paths = self.exporter.export_to_csv(extracted_cvs)
            output_files["csv"] = csv_paths

        # Also export individual JSONs
        for cv in extracted_cvs:
            json_path = self.exporter.export_single_cv_to_json(cv)
            output_files.setdefault("json", []).append(json_path)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "success": True,
            "message": f"Successfully processed {len(extracted_cvs)} CVs",
            "processed_count": len(extracted_cvs),
            "duration_seconds": duration,
            "output_files": output_files,
            "candidates": [cv.personal_info.full_name for cv in extracted_cvs]
        }


def run_pipeline(
    input_folder: Optional[str] = None,
    output_folder: Optional[str] = None,
    api_key: Optional[str] = None,
    export_format: str = "excel"
) -> Dict[str, Any]:
    """
    Convenience function to run the pipeline.

    Args:
        input_folder: Path to folder with CVs
        output_folder: Path for output files
        api_key: Gemini API key (uses env variable if not provided)
        export_format: Output format

    Returns:
        Processing results
    """
    config = Config()

    if input_folder:
        config.input_folder = input_folder
    if output_folder:
        config.output_folder = output_folder
    if api_key:
        config.gemini_api_key = api_key

    pipeline = CVProcessingPipeline(config)
    return pipeline.process_and_export(export_format=export_format)


if __name__ == "__main__":
    import sys

    # Simple CLI usage
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        input_dir = "data/input_cvs"

    results = run_pipeline(input_folder=input_dir)
    print("\n" + "=" * 50)
    print("PROCESSING RESULTS")
    print("=" * 50)
    print(f"Success: {results['success']}")
    print(f"Message: {results['message']}")
    print(f"Processed: {results.get('processed_count', 0)} CVs")
    if results.get('duration_seconds'):
        print(f"Duration: {results['duration_seconds']:.2f} seconds")
    if results.get('output_files'):
        print("\nOutput Files:")
        for key, value in results['output_files'].items():
            print(f"  {key}: {value}")
