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
    """Run the full CV processing pipeline with analysis, charts, and email drafts."""
    from src.utils.config import Config
    from src.pipeline import CVProcessingPipeline
    from pathlib import Path

    config = Config()
    if input_folder:
        config.input_folder = input_folder

    charts_dir = str(Path(config.output_folder).parent / "charts")
    emails_dir = str(Path(config.output_folder).parent / "emails")

    pipeline = CVProcessingPipeline(config)

    print(f"\nProcessing CVs from: {input_folder}")
    print(f"Output format: {output_format}\n")

    results = pipeline.process_folder_with_analysis(
        folder_path=input_folder,
        export_format=output_format,
        emails_dir=emails_dir,
        charts_dir=charts_dir,
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

    for entry in results.get("results", []):
        name = entry["cv"].personal_info.full_name
        mis = entry.get("missing_info", {})
        emails = entry.get("email_files", {})
        charts = entry.get("chart_paths", {})
        print(f"\n  [{name}]")
        print(f"    Missing fields : {mis.get('total_missing_fields', 0)}")
        if emails:
            print(f"    Email drafts   : {len(emails)} file(s) -> {list(emails.values())[0]}")
        if charts:
            print(f"    Charts         : {len(charts)} generated")

    if results.get('output_files'):
        print(f"\nOutput Files:")
        for key, value in results['output_files'].items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k2, v2 in value.items():
                    print(f"    {k2}: {v2}")
            elif isinstance(value, list):
                print(f"  {key}:")
                for v in value:
                    print(f"    - {v}")
            else:
                print(f"  {key}: {value}")

    return results


def process_single(pdf_path: str):
    """Process a single CV file — extract, analyse, generate charts, and export."""
    from src.utils.config import Config
    from src.pipeline import CVProcessingPipeline
    from src.utils.exporter import CVExporter
    from src.analysis.educational_analyzer import EducationalAnalyzer
    from src.analysis.experience_analyzer import ExperienceAnalyzer
    from src.analysis.research_profile_analyzer import ResearchProfileAnalyzer
    from src.analysis.missing_info_detector import MissingInfoDetector
    from src.analysis.candidate_summarizer import CandidateSummarizer
    from src.visualization.chart_generator import ChartGenerator

    config = Config()
    pipeline = CVProcessingPipeline(config)

    print(f"\nProcessing: {pdf_path}")
    cv = pipeline.process_single_cv(pdf_path)

    if not cv:
        print("Failed to process CV")
        return

    name = cv.personal_info.full_name

    print(f"\n{'='*60}")
    print(f"EXTRACTION RESULTS — {name}")
    print(f"{'='*60}")
    print(f"  Email:                {cv.personal_info.email}")
    print(f"  Phone:                {cv.personal_info.phone}")
    print(f"  Education records:    {len(cv.education)}")
    print(f"  Experience records:   {len(cv.experience)}")
    print(f"  Skills:               {len(cv.skills)}")
    print(f"  Journal pubs:         {len(cv.journal_publications)}")
    print(f"  Conference pubs:      {len(cv.conference_publications)}")
    print(f"  Supervisions:         {len(cv.supervisions)}")
    print(f"  Patents:              {len(cv.patents)}")
    print(f"  Books:                {len(cv.books)}")

    # ── Analysis ──────────────────────────────────────────────────────────
    edu_analysis = EducationalAnalyzer().analyze(cv)
    exp_analysis = ExperienceAnalyzer().analyze(cv)
    res_analysis = ResearchProfileAnalyzer().analyze(cv)
    missing_info = MissingInfoDetector().detect(cv)

    print(f"\n{'='*60}")
    print("EDUCATIONAL PROFILE ANALYSIS")
    print(f"{'='*60}")
    print(f"  Highest degree:       {edu_analysis['highest_degree']}")
    print(f"  Institution:          {edu_analysis['highest_degree_institution']}")
    print(f"  Year:                 {edu_analysis['highest_degree_year']}")
    print(f"  Has PhD:              {edu_analysis['has_phd']}")
    print(f"  Foreign education:    {edu_analysis['has_foreign_education']}")
    if edu_analysis['foreign_institutions']:
        print(f"  Foreign inst.:        {', '.join(edu_analysis['foreign_institutions'])}")
    print(f"  Avg. percentage:      {edu_analysis['average_percentage']}")
    print(f"  Degree progression:   {' → '.join(edu_analysis['degree_progression'])}")
    if edu_analysis['gaps_detected']:
        print(f"  Gaps:                 {'; '.join(edu_analysis['gaps_detected'])}")

    print(f"\n{'='*60}")
    print("PROFESSIONAL EXPERIENCE ANALYSIS")
    print(f"{'='*60}")
    print(f"  Total experience:     {exp_analysis['total_years_experience']} years")
    print(f"  Positions:            {exp_analysis['number_of_positions']}")
    print(f"  Currently employed:   {exp_analysis['is_currently_employed']}")
    if exp_analysis['current_position']:
        print(f"  Current role:         {exp_analysis['current_position']} @ {exp_analysis['current_organization']}")
    print(f"  Career trajectory:    {exp_analysis['career_trajectory']}")
    print(f"  Avg tenure:           {exp_analysis['average_tenure_years']} years")
    print(f"  Longest role:         {exp_analysis['longest_role']}")

    print(f"\n{'='*60}")
    print("RESEARCH PROFILE ANALYSIS")
    print(f"{'='*60}")
    print(f"  Profile tier:         {res_analysis['profile_tier']}")
    print(f"  Total publications:   {res_analysis['total_publications']} ({res_analysis['total_journal_publications']} journal, {res_analysis['total_conference_publications']} conf.)")
    q = res_analysis['quartile_distribution']
    print(f"  Quartile breakdown:   Q1={q['Q1']}  Q2={q['Q2']}  Q3={q['Q3']}  Q4={q['Q4']}  Unranked={q['Unranked']}")
    print(f"  WoS indexed:          {res_analysis['wos_indexed_count']}")
    print(f"  Scopus indexed:       {res_analysis['scopus_indexed_count']}")
    print(f"  Avg impact factor:    {res_analysis['average_impact_factor']}")
    print(f"  Research impact score:{res_analysis['research_impact_score']}")
    print(f"  Publication trend:    {res_analysis['publication_trend']}")
    print(f"  High-impact ratio:    {res_analysis['high_impact_ratio']}")
    print(f"  Supervisions:         MS={res_analysis['ms_supervised']}  PhD={res_analysis['phd_supervised']}")
    print(f"  Patents:              {res_analysis['total_patents']} ({res_analysis['granted_patents']} granted)")

    print(f"\n{'='*60}")
    print("MISSING INFORMATION")
    print(f"{'='*60}")
    print(f"  Has missing info:     {missing_info['has_missing_info']}")
    print(f"  Critical missing:     {missing_info['has_critical_missing']}")
    print(f"  Total missing fields: {missing_info['total_missing_fields']}")
    if missing_info['all_missing']:
        for item in missing_info['all_missing'][:8]:
            print(f"    • {item}")
        if len(missing_info['all_missing']) > 8:
            print(f"    … and {len(missing_info['all_missing']) - 8} more")

    # ── Candidate summary (LLM narrative) ────────────────────────────────
    print(f"\n{'='*60}")
    print("CANDIDATE SUMMARY")
    print(f"{'='*60}")
    try:
        summarizer = CandidateSummarizer(
            api_key=config.gemini_api_key,
            model_name=config.gemini_model
        )
        summary = summarizer.summarize(cv, edu_analysis, exp_analysis, res_analysis, missing_info)
        print(f"\n{summary['narrative']}")
    except Exception as e:
        print(f"  (Summary generation failed: {e})")
        summary = {"stats": {}, "narrative": ""}

    # ── Charts ────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("CHARTS")
    print(f"{'='*60}")
    charts_dir = str(Path(config.output_folder).parent / "charts")
    cg = ChartGenerator(output_dir=charts_dir)
    chart_paths = cg.generate_all_candidate_charts(cv, edu_analysis, exp_analysis, res_analysis)
    for chart_name, path in chart_paths.items():
        print(f"  {chart_name}: {path}")

    # ── Export ────────────────────────────────────────────────────────────
    exporter = CVExporter(output_dir=config.output_folder)
    json_path = exporter.export_single_cv_to_json(cv)
    excel_path = exporter.export_single_cv_to_excel(cv)
    print(f"\n{'='*60}")
    print("OUTPUT FILES")
    print(f"{'='*60}")
    print(f"  JSON:   {json_path}")
    print(f"  Excel:  {excel_path}")

def run_react():
    import subprocess, sys, os
    ui_path = os.path.join("src", "ui", "react")
    print("\nStarting TALASH React UI...")
    print("URL: http://localhost:3000\n")
    subprocess.run(["npm", "start"], cwd=ui_path, shell=True)

def main():
    parser = argparse.ArgumentParser(
        description="TALASH - Smart HR Recruitment System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # API command
    api_parser = subparsers.add_parser("api", help="Start the API server")
    # UI command
    ui_parser = subparsers.add_parser("ui", help="Start the Streamlit UI")
    #react command
    react_parser = subparsers.add_parser("react", help="Start the React UI")

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
    elif args.command == "react":
        run_react()
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python run.py api                    # Start API server")
        print("  python run.py process -i ./cvs       # Process folder")
        print("  python run.py single resume.pdf      # Process single file")
        print("  python run.py ui                     # Start Streamlit UI")


if __name__ == "__main__":
    main()
