import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.cv_models import (
    ExtractedCV, PersonalInfo, EducationRecord, ExperienceRecord,
    DegreeLevel, GradeType, JournalPublication, ConferencePublication,
    SupervisionRecord, PatentRecord, AuthorRole,
)
from src.analysis.educational_analyzer import EducationalAnalyzer
from src.analysis.experience_analyzer import ExperienceAnalyzer
from src.analysis.research_profile_analyzer import ResearchProfileAnalyzer


# ── Shared fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def full_cv():
    return ExtractedCV(
        personal_info=PersonalInfo(
            full_name="Dr. Ali Hassan",
            email="ali@uet.edu.pk",
            phone="+92-300-1234567",
        ),
        education=[
            EducationRecord(
                degree_level=DegreeLevel.SSC, degree_title="SSC",
                institution="Govt School Lahore", country="Pakistan",
                start_year=1998, end_year=2000,
                grade_value="85%", grade_type=GradeType.PERCENTAGE,
                normalized_percentage=85.0,
            ),
            EducationRecord(
                degree_level=DegreeLevel.BACHELOR_16, degree_title="BS Computer Science",
                institution="UET Lahore", country="Pakistan",
                start_year=2002, end_year=2006,
                grade_value="3.5/4.0", grade_type=GradeType.CGPA_4,
                normalized_percentage=87.5,
            ),
            EducationRecord(
                degree_level=DegreeLevel.MASTER_18, degree_title="MS Computer Science",
                institution="NUST Islamabad", country="Pakistan",
                start_year=2007, end_year=2009,
                grade_value="3.8/4.0", grade_type=GradeType.CGPA_4,
                normalized_percentage=95.0,
                thesis_title="Deep Learning for Urdu NLP",
            ),
            EducationRecord(
                degree_level=DegreeLevel.PHD, degree_title="PhD Computer Science",
                institution="University of Manchester", country="UK",
                start_year=2010, end_year=2014,
                thesis_title="Neural Machine Translation for Low-Resource Languages",
            ),
        ],
        experience=[
            ExperienceRecord(
                job_title="Lecturer", organization="UET Lahore",
                start_date="2006", end_date="2007", is_current=False,
            ),
            ExperienceRecord(
                job_title="Assistant Professor", organization="FAST-NUCES",
                start_date="2014", end_date="2018", is_current=False,
            ),
            ExperienceRecord(
                job_title="Associate Professor", organization="COMSATS University",
                start_date="2018", end_date="Present", is_current=True,
            ),
        ],
        journal_publications=[
            JournalPublication(
                title="Urdu NLP Survey", journal_name="ACM TALLIP",
                publication_year=2016, authors=["Ali Hassan", "B Ahmad"],
                author_role=AuthorRole.FIRST_AUTHOR, author_position=1,
                quartile="Q1", is_wos_indexed=True, is_scopus_indexed=True,
                impact_factor=3.2,
            ),
            JournalPublication(
                title="Low-Resource MT", journal_name="IEEE TASLP",
                publication_year=2018, authors=["Ali Hassan", "C Lee"],
                author_role=AuthorRole.FIRST_AND_CORRESPONDING, author_position=1,
                quartile="Q1", is_wos_indexed=True, is_scopus_indexed=True,
                impact_factor=4.1,
            ),
            JournalPublication(
                title="Transformer for Urdu", journal_name="Info Processing",
                publication_year=2021, authors=["D Khan", "Ali Hassan"],
                author_role=AuthorRole.CO_AUTHOR, author_position=2,
                quartile="Q2", is_wos_indexed=True, impact_factor=2.8,
            ),
            JournalPublication(
                title="Sentiment Analysis", journal_name="Expert Systems",
                publication_year=2023, authors=["Ali Hassan", "E Malik"],
                author_role=AuthorRole.FIRST_AUTHOR, author_position=1,
                quartile="Q2", is_scopus_indexed=True, impact_factor=3.9,
            ),
        ],
        conference_publications=[
            ConferencePublication(
                title="Urdu POS Tagging", conference_name="ACL 2017",
                publication_year=2017, authors=["Ali Hassan"],
                author_role=AuthorRole.FIRST_AUTHOR, author_position=1,
                is_indexed=True,
            ),
            ConferencePublication(
                title="NMT Evaluation", conference_name="EMNLP 2019",
                publication_year=2019, authors=["Ali Hassan", "B Ahmad"],
                author_role=AuthorRole.FIRST_AUTHOR, author_position=1,
                is_indexed=True,
            ),
        ],
        supervisions=[
            SupervisionRecord(
                student_name="F Ahmed", degree_level="MS",
                thesis_title="Urdu Chatbot", role="Main Supervisor",
                institution="COMSATS", start_year=2019,
                completion_year=2021, status="Completed",
            ),
            SupervisionRecord(
                student_name="G Raza", degree_level="PhD",
                role="Main Supervisor", institution="COMSATS",
                start_year=2020, status="In Progress",
            ),
        ],
        patents=[
            PatentRecord(
                patent_number="PK-123", patent_title="Urdu OCR System",
                inventors=["Ali Hassan"], filing_date="2022",
                country="Pakistan", status="Granted",
            ),
        ],
    )


@pytest.fixture
def empty_cv():
    return ExtractedCV(
        personal_info=PersonalInfo(full_name="Unknown Candidate"),
    )


# ── Educational Analyzer tests ───────────────────────────────────────────────

class TestEducationalAnalyzer:

    def test_highest_degree_is_phd(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        assert result["highest_degree"] == "PhD"

    def test_has_phd_flag(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        assert result["has_phd"] is True

    def test_has_masters_flag(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        assert result["has_masters"] is True

    def test_foreign_education_detected(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        assert result["has_foreign_education"] is True
        assert any("Manchester" in inst for inst in result["foreign_institutions"])

    def test_total_degrees_count(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        assert result["total_degrees"] == 4

    def test_grade_stats(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        assert result["average_percentage"] is not None
        assert result["highest_percentage"] == 95.0
        assert result["lowest_percentage"] == 85.0

    def test_degree_progression_order(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        prog = result["degree_progression"]
        assert prog[0] == "SSC/Matric"
        assert prog[-1] == "PhD"

    def test_theses_extracted(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        assert len(result["theses"]) == 2

    def test_gap_detection(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        # Gap between BS (ends 2006) and MS (starts 2007) — 1 year, not flagged
        # Gap between MS (ends 2009) and PhD (starts 2010) — 1 year, not flagged
        assert isinstance(result["gaps_detected"], list)

    def test_empty_cv_returns_safe_defaults(self, empty_cv):
        result = EducationalAnalyzer().analyze(empty_cv)
        assert result["total_degrees"] == 0
        assert result["has_phd"] is False
        assert result["highest_degree"] is None

    def test_education_detail_list(self, full_cv):
        result = EducationalAnalyzer().analyze(full_cv)
        assert len(result["education_detail"]) == 4
        for rec in result["education_detail"]:
            assert "degree_level" in rec
            assert "institution" in rec


# ── Experience Analyzer tests ────────────────────────────────────────────────

class TestExperienceAnalyzer:

    def test_currently_employed(self, full_cv):
        result = ExperienceAnalyzer().analyze(full_cv)
        assert result["is_currently_employed"] is True

    def test_current_position(self, full_cv):
        result = ExperienceAnalyzer().analyze(full_cv)
        assert result["current_position"] == "Associate Professor"
        assert result["current_organization"] == "COMSATS University"

    def test_number_of_positions(self, full_cv):
        result = ExperienceAnalyzer().analyze(full_cv)
        assert result["number_of_positions"] == 3

    def test_total_years_positive(self, full_cv):
        result = ExperienceAnalyzer().analyze(full_cv)
        assert result["total_years_experience"] is not None
        assert result["total_years_experience"] > 10

    def test_ascending_trajectory(self, full_cv):
        result = ExperienceAnalyzer().analyze(full_cv)
        # Lecturer → Assistant Prof → Associate Prof = ascending
        assert result["career_trajectory"] == "ascending"

    def test_tenure_stats(self, full_cv):
        result = ExperienceAnalyzer().analyze(full_cv)
        assert result["average_tenure_years"] is not None
        assert result["longest_tenure_years"] is not None
        assert result["longest_tenure_years"] >= result["average_tenure_years"]

    def test_organizations_list(self, full_cv):
        result = ExperienceAnalyzer().analyze(full_cv)
        assert "UET Lahore" in result["organizations"]
        assert "COMSATS University" in result["organizations"]

    def test_role_details_populated(self, full_cv):
        result = ExperienceAnalyzer().analyze(full_cv)
        assert len(result["role_details"]) == 3
        for rd in result["role_details"]:
            assert "job_title" in rd
            assert "duration_years" in rd

    def test_empty_cv_returns_safe_defaults(self, empty_cv):
        result = ExperienceAnalyzer().analyze(empty_cv)
        assert result["number_of_positions"] == 0
        assert result["is_currently_employed"] is False
        assert result["career_trajectory"] == "no_experience"

    def test_undated_current_role_trajectory(self):
        """Current role with no dates should sort to end, not distort trajectory."""
        cv = ExtractedCV(
            personal_info=PersonalInfo(full_name="Test"),
            experience=[
                ExperienceRecord(job_title="Data Engineer", organization="CompanyX",
                                 start_date=None, end_date=None, is_current=True),
                ExperienceRecord(job_title="ML Intern", organization="CompanyY",
                                 start_date="2023-06", end_date="2023-09", is_current=False),
                ExperienceRecord(job_title="Junior Analyst", organization="CompanyZ",
                                 start_date="2022-01", end_date="2023-01", is_current=False),
            ],
        )
        result = ExperienceAnalyzer().analyze(cv)
        # Intern(0) → Junior Analyst(4)... → Data Engineer(4) = ascending/lateral, NOT descending
        assert result["career_trajectory"] != "descending"
        assert result["is_currently_employed"] is True
        assert result["has_undated_current_role"] is True
        # Total years should be sum of dated roles only (~1.75 yr), not span to now
        assert result["total_years_experience"] is not None
        assert result["total_years_experience"] < 3


# ── Research Profile Analyzer tests ─────────────────────────────────────────

class TestResearchProfileAnalyzer:

    def test_total_publications(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        assert result["total_publications"] == 6
        assert result["total_journal_publications"] == 4
        assert result["total_conference_publications"] == 2

    def test_quartile_distribution(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        q = result["quartile_distribution"]
        assert q["Q1"] == 2
        assert q["Q2"] == 2

    def test_first_author_count(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        # Q1 paper (TALLIP) + Q1 first-and-corr (TASLP) + Q2 (Expert Systems)
        assert result["first_author_journal_count"] == 3

    def test_indexing_counts(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        assert result["wos_indexed_count"] == 3
        assert result["scopus_indexed_count"] == 3
        assert result["indexed_conference_count"] == 2

    def test_supervision_counts(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        assert result["total_supervisions"] == 2
        assert result["ms_supervised"] == 1
        assert result["phd_supervised"] == 1
        assert result["completed_supervisions"] == 1
        assert result["ongoing_supervisions"] == 1

    def test_patent_counts(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        assert result["total_patents"] == 1
        assert result["granted_patents"] == 1

    def test_impact_factor_stats(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        assert result["average_impact_factor"] is not None
        assert result["max_impact_factor"] == 4.1

    def test_research_impact_score_positive(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        assert result["research_impact_score"] > 0
        # Q1*2 + Q2*2 + 2 indexed conf + 1 MS sup + 1 PhD sup + 1 granted patent
        # = 4+4 + 3+3 + 1+1 + 1 + 3 + 5 = 25
        assert result["research_impact_score"] == 25.0

    def test_high_impact_ratio(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        # 2 Q1 + 2 Q2 = 4 high-impact out of 4 journals → 1.0
        assert result["high_impact_ratio"] == 1.0

    def test_collaboration_index(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        # 5 of 6 pubs have author_position=1, 1 has position=2
        assert result["collaboration_index"] is not None
        assert 0 <= result["collaboration_index"] <= 1

    def test_profile_tier(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        # 6 pubs, 2 Q1 → established_researcher
        assert result["profile_tier"] == "established_researcher"

    def test_publications_by_year(self, full_cv):
        result = ResearchProfileAnalyzer().analyze(full_cv)
        by_year = result["publications_by_year"]
        assert 2016 in by_year
        assert 2023 in by_year

    def test_empty_cv_zeros(self, empty_cv):
        result = ResearchProfileAnalyzer().analyze(empty_cv)
        assert result["total_publications"] == 0
        assert result["research_impact_score"] == 0.0
        assert result["profile_tier"] == "no_research_output"
        assert result["publication_trend"] == "no_publications"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])