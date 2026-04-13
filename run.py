"""
TALASH - Main Runner Script
Run the CV processing pipeline or start the API server.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def run_api():
    """Start the FastAPI server."""
    import uvicorn
    from src.utils.config import Config

    config = Config()
    print(f"\nStarting TALASH API Server...")
    print(f"API URL: http://{config.api_host}:{config.api_port}")
    print(f"Docs URL: http://{config.api_host}:{config.api_port}/docs")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        "src.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )

def run_ui():
    """Start the Streamlit UI."""
    import subprocess
    import sys
    import os

    app_path = os.path.join("src", "ui", "app.py")
    print(f"\nStarting TALASH UI...")
    print(f"URL: http://localhost:8501")
    print("\nPress Ctrl+C to stop\n")

    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])


def run_pipeline(input_folder: str, output_format: str = "excel"):
    """Run the CV processing pipeline."""
    from src.pipeline import run_pipeline as execute_pipeline

    print(f"\nProcessing CVs from: {input_folder}")
    print(f"Output format: {output_format}\n")

    results = execute_pipeline(
        input_folder=input_folder,
        export_format=output_format
    )

    print("\n" + "=" * 60)
    print("PROCESSING RESULTS")
    print("=" * 60)
    print(f"Status: {'Success' if results['success'] else 'Failed'}")
    print(f"Message: {results['message']}")
    print(f"CVs Processed: {results.get('processed_count', 0)}")

    if results.get('duration_seconds'):
        print(f"Duration: {results['duration_seconds']:.2f} seconds")

    if results.get('candidates'):
        print(f"\nCandidates:")
        for name in results['candidates']:
            print(f"  - {name}")

    if results.get('output_files'):
        print(f"\nOutput Files:")
        for key, value in results['output_files'].items():
            if isinstance(value, list):
                print(f"  {key}:")
                for v in value:
                    print(f"    - {v}")
            else:
                print(f"  {key}: {value}")

    return results


def process_single(pdf_path: str):
    """Process a single CV file."""
    from src.utils.config import Config
    from src.pipeline import CVProcessingPipeline

    config = Config()
    pipeline = CVProcessingPipeline(config)

    print(f"\nProcessing: {pdf_path}")
    cv = pipeline.process_single_cv(pdf_path)

    if cv:
        print(f"\nExtracted CV for: {cv.personal_info.full_name}")
        print(f"Email: {cv.personal_info.email}")
        print(f"Education records: {len(cv.education)}")
        print(f"Experience records: {len(cv.experience)}")
        print(f"Skills: {len(cv.skills)}")
        print(f"Journal publications: {len(cv.journal_publications)}")
        print(f"Conference publications: {len(cv.conference_publications)}")

        # Export
        from src.utils.exporter import CVExporter
        exporter = CVExporter(output_dir=config.output_folder)
        json_path = exporter.export_single_cv_to_json(cv)
        print(f"\nExported to: {json_path}")

        excel_path = exporter.export_single_cv_to_excel(cv)  # ADD THIS
        print(f"Exported to: {excel_path}")  # ADD THIS

    else:
        print("Failed to process CV")


def main():
    parser = argparse.ArgumentParser(
        description="TALASH - Smart HR Recruitment System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # API command
    api_parser = subparsers.add_parser("api", help="Start the API server")
    # UI command
    ui_parser = subparsers.add_parser("ui", help="Start the Streamlit UI")

    # Pipeline command
    pipeline_parser = subparsers.add_parser("process", help="Process CVs from folder")
    pipeline_parser.add_argument(
        "-i", "--input",
        default="data/input_cvs",
        help="Input folder containing CVs"
    )
    pipeline_parser.add_argument(
        "-f", "--format",
        choices=["excel", "csv", "both"],
        default="excel",
        help="Output format"
    )

    # Single file command
    single_parser = subparsers.add_parser("single", help="Process a single CV")
    single_parser.add_argument("file", help="Path to PDF file")

    args = parser.parse_args()

    if args.command == "api":
        run_api()
    elif args.command == "process":
        run_pipeline(args.input, args.format)
    elif args.command == "single":
        process_single(args.file)
    elif args.command == "ui":
        run_ui()
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python run.py api                    # Start API server")
        print("  python run.py process -i ./cvs       # Process folder")
        print("  python run.py single resume.pdf      # Process single file")
        print("  python run.py ui                     # Start Streamlit UI")


if __name__ == "__main__":
    main()
