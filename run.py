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
    from src.analysis.topic_variability_analyzer import TopicVariabilityAnalyzer
    from src.analysis.coauthor_analyzer import CoAuthorAnalyzer
    from src.analysis.skill_alignment_analyzer import SkillAlignmentAnalyzer
    from src.analysis.candidate_ranker import CandidateRanker
    from src.analysis.publication_verifier import verify_journal, verify_conference
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
        cv_obj = entry["cv"]

        # Run new analyzers for this candidate
        edu_a   = entry.get("edu_analysis") or {}
        exp_a   = entry.get("exp_analysis") or {}
        res_a   = entry.get("res_analysis") or {}
        topic_a = TopicVariabilityAnalyzer().analyze(cv_obj)
        coauth_a= CoAuthorAnalyzer().analyze(cv_obj)
        skill_a = SkillAlignmentAnalyzer().analyze(cv_obj)
        rank_r  = CandidateRanker().score_candidate(
            candidate_name = name,
            candidate_id   = str(cv_obj.personal_info.email or "unknown"),
            edu_analysis   = edu_a,
            res_analysis   = res_a,
            exp_analysis   = exp_a,
            skill_analysis = skill_a,
            total_skills   = len(cv_obj.skills),
        )

        print(f"\n  [{name}]")
        print(f"    Missing fields       : {mis.get('total_missing_fields', 0)}")
        if emails:
            print(f"    Email drafts         : {len(emails)} file(s) -> {list(emails.values())[0]}")
        if charts:
            print(f"    Charts               : {len(charts)} generated")

        # Topic variability
        print(f"    Topic variability    : {topic_a['variability_label']} "
              f"(diversity={topic_a['diversity_score']}, "
              f"dominant='{topic_a['dominant_theme']}' {topic_a['dominant_theme_percentage']}%)")

        # Co-author
        print(f"    Co-author network    : {coauth_a['total_unique_coauthors']} unique, "
              f"{coauth_a['recurring_collaborators_count']} recurring, "
              f"avg {coauth_a['average_authors_per_paper']} authors/paper "
              f"({coauth_a['avg_team_size_label']})")

        # Skill alignment
        smry = skill_a['summary']
        print(f"    Skill alignment      : {skill_a['total_skills']} skills — "
              f"strong={smry['strongly_evidenced']} partial={smry['partially_evidenced']} "
              f"weak={smry['weakly_evidenced']} unsupported={smry['unsupported']}")

        # Publication verification (first 3 journals only for pipeline mode)
        jps = cv_obj.journal_publications[:3]
        if jps:
            verified_legit = sum(
                1 for jp in jps
                if verify_journal(jp.journal_name or "", getattr(jp, 'issn', None))
                   .get('legitimacy_flag') == 'verified_legitimate'
            )
            print(f"    Pub verification     : {verified_legit}/{len(jps)} journals verified legitimate (sample)")

        # Ranking score
        dim = rank_r['dimension_scores']
        print(f"    Composite score      : {rank_r['composite_score']:.1f}/100 "
              f"(edu={dim['education']} res={dim['research']} "
              f"exp={dim['experience']} skills={dim['skills']})")

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
    from src.analysis.topic_variability_analyzer import TopicVariabilityAnalyzer
    from src.analysis.coauthor_analyzer import CoAuthorAnalyzer
    from src.analysis.skill_alignment_analyzer import SkillAlignmentAnalyzer
    from src.analysis.candidate_ranker import CandidateRanker
    from src.analysis.publication_verifier import verify_journal, verify_conference
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
    edu_analysis   = EducationalAnalyzer().analyze(cv)
    exp_analysis   = ExperienceAnalyzer().analyze(cv)
    res_analysis   = ResearchProfileAnalyzer().analyze(cv)
    missing_info   = MissingInfoDetector().detect(cv)
    topic_analysis = TopicVariabilityAnalyzer().analyze(cv)
    coauth_analysis= CoAuthorAnalyzer().analyze(cv)
    skill_analysis = SkillAlignmentAnalyzer().analyze(cv)
    rank_result    = CandidateRanker().score_candidate(
        candidate_name = cv.personal_info.full_name,
        candidate_id   = str(cv.personal_info.email or "unknown"),
        edu_analysis   = edu_analysis,
        res_analysis   = res_analysis,
        exp_analysis   = exp_analysis,
        skill_analysis = skill_analysis,
        total_skills   = len(cv.skills),
    )

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
    print(f"  Avg tenure:           {exp_analysis['average_tenure_years']} years")
    print(f"  Longest role:         {exp_analysis['longest_role']}")

    print(f"\n  {'─'*54}")
    print("  CAREER PROGRESSION (3.8-i-e)")
    print(f"  {'─'*54}")
    print(f"  Trajectory:           {exp_analysis['career_trajectory_label']}")
    print(f"  Progressive:          {exp_analysis['is_progressive']}")
    print(f"  Narrative:            {exp_analysis['progression_narrative']}")
    if exp_analysis['seniority_scores']:
        print(f"  Seniority ladder:")
        for title, score in exp_analysis['seniority_scores']:
            print(f"    [{score:2d}] {title}")

    print(f"\n  {'─'*54}")
    print("  TIMELINE CONSISTENCY (3.8-i-a/b/c/d)")
    print(f"  {'─'*54}")
    print(f"  Consistent:           {exp_analysis['timeline_consistent']}")
    if exp_analysis['consistency_flags']:
        for flag in exp_analysis['consistency_flags']:
            print(f"  ⚠  {flag}")

    # Education–Employment Overlaps (3.8-i-a)
    print(f"\n  Edu–Employment overlaps: {exp_analysis['edu_employment_overlap_count']}"
          f"  (scrutiny required: {exp_analysis['edu_employment_scrutiny_count']})")
    for o in exp_analysis['edu_employment_overlaps']:
        marker = "⚠" if not o['is_likely_legitimate'] else "✓"
        print(f"  {marker} {o['job_title']} overlaps {o['degree_level']} "
              f"({o['overlap_months']} months) — {o['interpretation']}")

    # Job–Job Overlaps (3.8-i-b)
    print(f"\n  Job–Job overlaps:        {exp_analysis['job_overlap_count']}"
          f"  (suspicious: {exp_analysis['suspicious_overlap_count']})")
    for o in exp_analysis['job_overlaps']:
        marker = "⚠" if o['flag'] == 'suspicious' else "✓"
        print(f"  {marker} [{o['flag']}] {o['role_a']}  ↔  {o['role_b']}"
              f"  ({o['overlap_months']} months)")
        print(f"       {o['interpretation']}")

    # Employment Gaps (3.8-i-c+d)
    print(f"\n  Employment gaps:         {exp_analysis['total_gap_count']}"
          f"  (unexplained: {exp_analysis['unexplained_gap_count']},"
          f"  total gap: {exp_analysis['total_gap_months']} months)")
    for g in exp_analysis['employment_gaps']:
        marker = "⚠" if not g['is_explained'] else "✓"
        print(f"  {marker} [{g['severity']}] {g['gap_months']} months"
              f"  ({g['gap_start']} → {g['gap_end']})")
        print(f"       Between: {g['after_role']}  →  {g['before_role']}")
        print(f"       Justification: {g['justification']}")

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

    # ── Topic Variability ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("TOPIC VARIABILITY ANALYSIS")
    print(f"{'='*60}")
    print(f"  Publications analyzed: {topic_analysis['total_publications_analyzed']}")
    print(f"  Variability label:     {topic_analysis['variability_label']}")
    print(f"  Diversity score:       {topic_analysis['diversity_score']}")
    print(f"  Dominant theme:        {topic_analysis['dominant_theme']} ({topic_analysis['dominant_theme_percentage']}%)")
    print(f"  Theme count:           {topic_analysis['theme_count']}")
    print(f"  Focus shifted:         {topic_analysis.get('focus_shifted_over_time', False)}")
    if topic_analysis.get('theme_distribution'):
        print(f"  Theme breakdown:")
        for theme, data in list(topic_analysis['theme_distribution'].items())[:6]:
            print(f"    • {theme}: {data['count']} pubs ({data['percentage']}%)")
    print(f"  Interpretation: {topic_analysis['interpretation']}")

    # ── Co-Author Network ─────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("CO-AUTHOR NETWORK ANALYSIS")
    print(f"{'='*60}")
    print(f"  Unique co-authors:     {coauth_analysis['total_unique_coauthors']}")
    print(f"  Publications analyzed: {coauth_analysis['total_publications_analyzed']}")
    print(f"  Avg authors/paper:     {coauth_analysis['average_authors_per_paper']}")
    print(f"  Team size:             {coauth_analysis['avg_team_size_label']}")
    print(f"  Recurring collabs:     {coauth_analysis['recurring_collaborators_count']}")
    print(f"  One-time collabs:      {coauth_analysis['one_time_collaborators_count']}")
    print(f"  Recurring proportion:  {coauth_analysis['proportion_papers_with_recurring']:.1%}")
    print(f"  Diversity score:       {coauth_analysis['collaboration_diversity_score']}")
    print(f"  Student-sup. papers:   {coauth_analysis['student_supervisor_papers']}")
    if coauth_analysis['most_frequent_collaborators']:
        print(f"  Top collaborators:")
        for c in coauth_analysis['most_frequent_collaborators'][:5]:
            print(f"    • {c['name']} ({c['papers']} papers)")
    print(f"  Interpretation: {coauth_analysis['interpretation']}")

    # ── Skill Alignment ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("SKILL ALIGNMENT ANALYSIS")
    print(f"{'='*60}")
    print(f"  Total skills:          {skill_analysis['total_skills']}")
    smry = skill_analysis['summary']
    print(f"  Strongly evidenced:    {smry['strongly_evidenced']}")
    print(f"  Partially evidenced:   {smry['partially_evidenced']}")
    print(f"  Weakly evidenced:      {smry['weakly_evidenced']}")
    print(f"  Unsupported:           {smry['unsupported']}")
    src_breakdown = skill_analysis.get('skills_by_source', {})
    print(f"  Employment-evidenced:  {src_breakdown.get('employment_evidenced', 'N/A')}")
    print(f"  Publication-evidenced: {src_breakdown.get('publication_evidenced', 'N/A')}")
    print(f"  Education-evidenced:   {src_breakdown.get('education_evidenced', 'N/A')}")

    # Per-skill breakdown with evidence
    assessments = skill_analysis.get('skill_assessments', [])
    if assessments:
        print(f"\n  Per-skill evidence breakdown:")
        _STRENGTH_ICON = {
            "strongly_evidenced":  "✓✓",
            "partially_evidenced": "✓ ",
            "weakly_evidenced":    "~ ",
            "unsupported":         "✗ ",
        }
        for a in assessments:
            icon = _STRENGTH_ICON.get(a['strength'], "  ")
            label = a['strength'].replace("_", " ").title()
            sources = ", ".join(a['evidence_sources']) if a['evidence_sources'] else "none"
            print(f"    [{icon}] {a['skill']:<30}  ({label})")
            print(f"           Sources : {sources}")
            detail = a.get('evidence_detail', {})
            for src_key, src_label in [("employment", "Employment"), ("publications", "Publications"), ("education", "Education")]:
                src_info = detail.get(src_key, {})
                if src_info.get('matched') and src_info.get('keywords_found'):
                    kws = ", ".join(src_info['keywords_found'])
                    print(f"           {src_label:<14}: {kws}")

    print(f"\n  Interpretation: {skill_analysis['interpretation']}")

    # ── Publication Verification ──────────────────────────────────────────
    print(f"\n{'='*60}")
    print("PUBLICATION VERIFICATION")
    print(f"{'='*60}")
    journals_to_check = cv.journal_publications[:5]
    if journals_to_check:
        print(f"  Verifying up to 5 journal publications...")
        for jp in journals_to_check:
            vr = verify_journal(jp.journal_name or "", getattr(jp, 'issn', None))
            wos  = "✓ WoS" if vr.get('wos_indexed') else "✗ WoS"
            scop = "✓ Scopus" if vr.get('scopus_indexed') else "✗ Scopus"
            q    = vr.get('quartile') or "?"
            IF   = vr.get('impact_factor') or "?"
            src  = vr.get('verification_source', 'unknown')
            flag = vr.get('legitimacy_flag', 'unverified')
            print(f"    [{q}] IF={IF} | {wos} | {scop} | {flag}")
            print(f"         {jp.journal_name} (source: {src})")
    conferences_to_check = cv.conference_publications[:5]
    if conferences_to_check:
        print(f"  Verifying up to 5 conference publications...")
        for cp in conferences_to_check:
            vc = verify_conference(cp.conference_name or "", getattr(cp, 'publisher', None))
            rank   = vc.get('core_rank') or "?"
            star   = "A*" if vc.get('is_a_star') else rank
            mature = vc.get('maturity_label', 'unknown')
            series = vc.get('series_number')
            src    = vc.get('verification_source', 'unknown')
            series_str = f" ({series}th edition)" if series else ""
            print(f"    [CORE: {star}] {mature}{series_str}")
            print(f"         {cp.conference_name} (source: {src})")
    if not journals_to_check and not conferences_to_check:
        print("  No publications to verify.")

    # ── Candidate Ranking Score ───────────────────────────────────────────
    print(f"\n{'='*60}")
    print("CANDIDATE RANKING SCORE")
    print(f"{'='*60}")
    dim = rank_result['dimension_scores']
    print(f"  Composite score:  {rank_result['composite_score']:.2f} / 100")
    print(f"  Education  score: {dim['education']} / 100")
    print(f"  Research   score: {dim['research']} / 100")
    print(f"  Experience score: {dim['experience']} / 100")
    print(f"  Skills     score: {dim['skills']} / 100")
    print(f"  Profile tier:     {rank_result['profile_tier']}")
    w = rank_result['weights_used']
    print(f"  Weights used:     edu={w['education']} | res={w['research']} | exp={w['experience']} | skills={w['skills']}")

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