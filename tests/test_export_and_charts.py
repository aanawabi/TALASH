import sys
import tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.cv_models import (
    ExtractedCV, PersonalInfo, EducationRecord, ExperienceRecord,
    JournalPublication, SkillRecord, DegreeLevel, GradeType,
)
from src.analysis.educational_analyzer import EducationalAnalyzer
from src.analysis.experience_analyzer import ExperienceAnalyzer
from src.analysis.research_profile_analyzer import ResearchProfileAnalyzer
from src.analysis.missing_info_detector import MissingInfoDetector
from src.utils.exporter import CVExporter
from src.visualization.chart_generator import ChartGenerator


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def sample_cv():
    return ExtractedCV(
        personal_info=PersonalInfo(
            full_name="Dr. Sara Khan",
            email="sara@example.com",
            phone="+92-300-9876543",
        ),
        education=[
            EducationRecord(
                degree_level=DegreeLevel.PHD,
                degree_title="PhD Computer Science",
                institution="NUST",
                country="Pakistan",
                start_year=2010,
                end_year=2015,
                grade_value="Pass",
                grade_type=GradeType.GRADE,
            )
        ],
        experience=[
            ExperienceRecord(
                job_title="Assistant Professor",
                organization="COMSATS",
                start_date="2016",
                end_date="Present",
                is_current=True,
            )
        ],
        skills=[
            SkillRecord(skill_name="Python", skill_category="Programming"),
            SkillRecord(skill_name="Machine Learning", skill_category="AI/ML"),
        ],
        journal_publications=[
            JournalPublication(
                title="Deep Learning for NLP",
                journal_name="IEEE Transactions",
                authors=["Sara Khan"],
                publication_year=2020,
                doi="10.1234/abc",
                impact_factor=3.5,
                quartile="Q1",
                is_wos_indexed=True,
                is_scopus_indexed=True,
            )
        ],
    )


@pytest.fixture
def analyses(sample_cv):
    edu = EducationalAnalyzer().analyze(sample_cv)
    exp = ExperienceAnalyzer().analyze(sample_cv)
    res = ResearchProfileAnalyzer().analyze(sample_cv)
    mis = MissingInfoDetector().detect(sample_cv)
    return edu, exp, res, mis


# ── Email file writer tests ────────────────────────────────────────────────────

class TestEmailFileWriter:

    def test_writes_general_template_always(self, sample_cv, analyses, tmp_path):
        _, _, _, mis = analyses
        detector = MissingInfoDetector()
        written = detector.write_emails_to_files(
            mis, name=sample_cv.personal_info.full_name, emails_dir=str(tmp_path)
        )
        assert "general" in written
        assert Path(written["general"]).exists()

    def test_written_file_contains_candidate_name(self, sample_cv, analyses, tmp_path):
        _, _, _, mis = analyses
        detector = MissingInfoDetector()
        written = detector.write_emails_to_files(
            mis, name=sample_cv.personal_info.full_name, emails_dir=str(tmp_path)
        )
        content = Path(written["general"]).read_text(encoding="utf-8")
        assert "Dr. Sara Khan" in content

    def test_creates_candidate_subfolder(self, sample_cv, analyses, tmp_path):
        _, _, _, mis = analyses
        detector = MissingInfoDetector()
        written = detector.write_emails_to_files(
            mis, name=sample_cv.personal_info.full_name, emails_dir=str(tmp_path)
        )
        assert len(written) > 0
        candidate_dir = Path(list(written.values())[0]).parent
        assert candidate_dir.is_dir()

    def test_incomplete_cv_generates_multiple_templates(self, tmp_path):
        cv = ExtractedCV(
            personal_info=PersonalInfo(full_name="Incomplete Candidate"),
            education=[
                EducationRecord(
                    degree_level=DegreeLevel.BACHELOR_16,
                    degree_title="BS CS",
                    institution="Some Uni",
                )
            ],
            journal_publications=[
                JournalPublication(
                    title="A Paper",
                    journal_name="Unknown Journal",
                    authors=["Author"],
                )
            ],
        )
        mis = MissingInfoDetector().detect(cv)
        written = MissingInfoDetector().write_emails_to_files(
            mis, name="Incomplete Candidate", emails_dir=str(tmp_path)
        )
        assert len(written) >= 2

    def test_txt_extension_used(self, sample_cv, analyses, tmp_path):
        _, _, _, mis = analyses
        detector = MissingInfoDetector()
        written = detector.write_emails_to_files(
            mis, name=sample_cv.personal_info.full_name, emails_dir=str(tmp_path)
        )
        for path in written.values():
            assert path.endswith(".txt")


# ── Analysis Excel export tests ───────────────────────────────────────────────

class TestAnalysisExcelExport:

    def test_creates_excel_file(self, sample_cv, analyses, tmp_path):
        edu, exp, res, mis = analyses
        exporter = CVExporter(output_dir=str(tmp_path))
        result = [{"cv": sample_cv, "edu_analysis": edu, "exp_analysis": exp,
                   "res_analysis": res, "missing_info": mis, "email_files": {}}]
        path = exporter.export_analysis_to_excel(result, filename="test_analysis.xlsx")
        assert Path(path).exists()

    def test_excel_has_required_sheets(self, sample_cv, analyses, tmp_path):
        import pandas as pd
        edu, exp, res, mis = analyses
        exporter = CVExporter(output_dir=str(tmp_path))
        result = [{"cv": sample_cv, "edu_analysis": edu, "exp_analysis": exp,
                   "res_analysis": res, "missing_info": mis, "email_files": {}}]
        path = exporter.export_analysis_to_excel(result, filename="test_analysis.xlsx")
        sheets = pd.read_excel(path, sheet_name=None)
        for expected in ("analysis_summary", "education_analysis", "experience_analysis",
                         "research_analysis", "missing_info", "draft_emails"):
            assert expected in sheets

    def test_summary_sheet_contains_candidate(self, sample_cv, analyses, tmp_path):
        import pandas as pd
        edu, exp, res, mis = analyses
        exporter = CVExporter(output_dir=str(tmp_path))
        result = [{"cv": sample_cv, "edu_analysis": edu, "exp_analysis": exp,
                   "res_analysis": res, "missing_info": mis, "email_files": {}}]
        path = exporter.export_analysis_to_excel(result, filename="test_analysis.xlsx")
        df = pd.read_excel(path, sheet_name="analysis_summary")
        assert "Dr. Sara Khan" in df["candidate_name"].values

    def test_research_sheet_has_quartile_columns(self, sample_cv, analyses, tmp_path):
        import pandas as pd
        edu, exp, res, mis = analyses
        exporter = CVExporter(output_dir=str(tmp_path))
        result = [{"cv": sample_cv, "edu_analysis": edu, "exp_analysis": exp,
                   "res_analysis": res, "missing_info": mis, "email_files": {}}]
        path = exporter.export_analysis_to_excel(result, filename="test_analysis.xlsx")
        df = pd.read_excel(path, sheet_name="research_analysis")
        for col in ("Q1", "Q2", "Q3", "Q4", "Unranked"):
            assert col in df.columns

    def test_email_files_recorded_in_draft_emails_sheet(self, sample_cv, analyses, tmp_path):
        import pandas as pd
        edu, exp, res, mis = analyses
        email_files = {"general": str(tmp_path / "general_email.txt")}
        exporter = CVExporter(output_dir=str(tmp_path))
        result = [{"cv": sample_cv, "edu_analysis": edu, "exp_analysis": exp,
                   "res_analysis": res, "missing_info": mis, "email_files": email_files}]
        path = exporter.export_analysis_to_excel(result, filename="test_analysis.xlsx")
        df = pd.read_excel(path, sheet_name="draft_emails")
        assert len(df) == 1
        assert df.iloc[0]["template_type"] == "general"


# ── Chart generator subfolder tests ───────────────────────────────────────────

class TestChartGeneratorSubfolders:

    def test_candidate_charts_go_in_subfolder(self, sample_cv, analyses, tmp_path):
        edu, exp, res, _ = analyses
        cg = ChartGenerator(output_dir=str(tmp_path))
        paths = cg.generate_all_candidate_charts(sample_cv, edu, exp, res)
        for path in paths.values():
            p = Path(path)
            assert p.parent.name == "Dr__Sara_Khan" or "_Sara_" in str(p.parent)

    def test_aggregate_charts_go_in_aggregate_subfolder(self, sample_cv, analyses, tmp_path):
        edu, exp, res, _ = analyses
        cv2 = ExtractedCV(
            personal_info=PersonalInfo(full_name="Dr. Ali Hassan", email="ali@example.com"),
            experience=[
                ExperienceRecord(
                    job_title="Professor",
                    organization="UET",
                    start_date="2005",
                    end_date="Present",
                    is_current=True,
                )
            ],
        )
        edu2 = EducationalAnalyzer().analyze(cv2)
        exp2 = ExperienceAnalyzer().analyze(cv2)
        res2 = ResearchProfileAnalyzer().analyze(cv2)

        cg = ChartGenerator(output_dir=str(tmp_path))
        paths = cg.generate_all_aggregate_charts(
            [sample_cv, cv2], [edu, edu2], [exp, exp2], [res, res2]
        )
        for path in paths.values():
            assert Path(path).parent.name == "aggregate"

    def test_education_timeline_returns_path(self, sample_cv, analyses, tmp_path):
        edu, _, _, _ = analyses
        cg = ChartGenerator(output_dir=str(tmp_path))
        path = cg.education_timeline(sample_cv, edu)
        assert path and Path(path).exists()

    def test_skills_chart_returns_path(self, sample_cv, tmp_path):
        cg = ChartGenerator(output_dir=str(tmp_path))
        path = cg.skills_chart(sample_cv)
        assert path and Path(path).exists()

    def test_overview_chart_saved_in_candidate_dir(self, sample_cv, analyses, tmp_path):
        edu, exp, res, _ = analyses
        cg = ChartGenerator(output_dir=str(tmp_path))
        path = cg.candidate_overview(sample_cv, edu, exp, res)
        assert path and Path(path).exists()
        assert Path(path).name == "overview.png"
        assert Path(path).parent != tmp_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])