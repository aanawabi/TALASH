import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.cv_models import (
    ExtractedCV, PersonalInfo, EducationRecord, ExperienceRecord,
    JournalPublication, DegreeLevel, GradeType, AuthorRole,
)
from src.analysis.missing_info_detector import MissingInfoDetector


@pytest.fixture
def complete_cv():
    return ExtractedCV(
        personal_info=PersonalInfo(
            full_name="Dr. Ali Hassan",
            email="ali@uet.edu.pk",
            phone="+92-300-1234567",
            address="Lahore, Pakistan",
            linkedin="linkedin.com/in/alihassan",
        ),
        education=[
            EducationRecord(
                degree_level=DegreeLevel.PHD, degree_title="PhD CS",
                institution="UET Lahore", country="Pakistan",
                start_year=2010, end_year=2014,
                grade_value="Pass", grade_type=GradeType.GRADE,
                normalized_percentage=None,
            )
        ],
        experience=[
            ExperienceRecord(
                job_title="Associate Professor", organization="COMSATS",
                start_date="2018", end_date="Present", is_current=True,
            )
        ],
        journal_publications=[
            JournalPublication(
                title="Test Paper", journal_name="Nature",
                authors=["Ali Hassan"], publication_year=2022,
                doi="10.1234/test", issn="1234-5678",
                impact_factor=5.0, quartile="Q1",
                is_wos_indexed=True, is_scopus_indexed=True,
            )
        ],
    )


@pytest.fixture
def incomplete_cv():
    return ExtractedCV(
        personal_info=PersonalInfo(full_name="Unknown Candidate"),
        education=[
            EducationRecord(
                degree_level=DegreeLevel.BACHELOR_16,
                degree_title="BS Engineering",
                institution="Some Uni",
            )
        ],
        experience=[
            ExperienceRecord(
                job_title="Engineer", organization="Some Co",
                is_current=False,
            )
        ],
        journal_publications=[
            JournalPublication(
                title="A Paper Without Details",
                journal_name="Unknown Journal",
                authors=["Unknown"],
            )
        ],
    )


class TestMissingInfoDetector:

    def test_complete_cv_no_critical_missing(self, complete_cv):
        result = MissingInfoDetector().detect(complete_cv)
        assert result["has_critical_missing"] is False

    def test_incomplete_cv_has_missing(self, incomplete_cv):
        result = MissingInfoDetector().detect(incomplete_cv)
        assert result["has_missing_info"] is True
        assert result["has_critical_missing"] is True

    def test_missing_email_is_critical(self, incomplete_cv):
        result = MissingInfoDetector().detect(incomplete_cv)
        critical = result["missing_by_category"]["contact_critical"]
        assert any("email" in item.lower() for item in critical)

    def test_missing_phone_is_critical(self, incomplete_cv):
        result = MissingInfoDetector().detect(incomplete_cv)
        critical = result["missing_by_category"]["contact_critical"]
        assert any("phone" in item.lower() for item in critical)

    def test_missing_education_dates_detected(self, incomplete_cv):
        result = MissingInfoDetector().detect(incomplete_cv)
        edu_missing = result["missing_by_category"]["education"]
        assert len(edu_missing) > 0
        assert any("year" in item.lower() or "grade" in item.lower() for item in edu_missing)

    def test_missing_experience_dates_detected(self, incomplete_cv):
        result = MissingInfoDetector().detect(incomplete_cv)
        exp_missing = result["missing_by_category"]["experience"]
        assert len(exp_missing) > 0

    def test_missing_publication_details_detected(self, incomplete_cv):
        result = MissingInfoDetector().detect(incomplete_cv)
        pub_missing = result["missing_by_category"]["publications"]
        assert len(pub_missing) > 0
        combined = " ".join(pub_missing).lower()
        assert "doi" in combined or "impact" in combined or "quartile" in combined

    def test_total_missing_count_positive(self, incomplete_cv):
        result = MissingInfoDetector().detect(incomplete_cv)
        assert result["total_missing_fields"] > 0

    def test_complete_cv_low_missing_count(self, complete_cv):
        result = MissingInfoDetector().detect(complete_cv)
        assert result["total_missing_fields"] < 5

    def test_email_template_generated_for_contact_missing(self, incomplete_cv):
        detector = MissingInfoDetector()
        missing = detector.detect(incomplete_cv)
        templates = detector.get_email_template(
            missing, name="Unknown Candidate",
            position="Lecturer", institution="Test University",
        )
        assert "contact" in templates or "general" in templates
        general = templates["general"]
        assert "Unknown Candidate" in general
        assert "Test University" in general

    def test_academic_template_generated_when_edu_missing(self, incomplete_cv):
        detector = MissingInfoDetector()
        missing = detector.detect(incomplete_cv)
        templates = detector.get_email_template(missing, name="Candidate")
        assert "academic" in templates

    def test_publications_template_generated_when_pub_missing(self, incomplete_cv):
        detector = MissingInfoDetector()
        missing = detector.detect(incomplete_cv)
        templates = detector.get_email_template(missing, name="Candidate")
        assert "publications" in templates

    def test_general_template_always_present(self, complete_cv):
        detector = MissingInfoDetector()
        missing = detector.detect(complete_cv)
        templates = detector.get_email_template(missing, name="Dr. Ali Hassan")
        assert "general" in templates

    def test_currently_employed_no_end_date_not_flagged(self):
        cv = ExtractedCV(
            personal_info=PersonalInfo(full_name="Test", email="t@t.com", phone="123"),
            experience=[
                ExperienceRecord(
                    job_title="Professor", organization="Uni",
                    start_date="2020", is_current=True,
                )
            ],
        )
        result = MissingInfoDetector().detect(cv)
        exp_missing = result["missing_by_category"]["experience"]
        assert not any("end date" in m.lower() for m in exp_missing)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])