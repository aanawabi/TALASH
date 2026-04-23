"""
CV Exporter Module
Exports extracted CV data to CSV/Excel in relational database format.
Creates separate sheets/files for each entity type with foreign key relationships.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid

from ..models.cv_models import ExtractedCV

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CVExporter:
    """
    Exports extracted CV data to CSV or Excel format.
    Creates relational tables with candidate_id as foreign key.
    """

    def __init__(self, output_dir: str = "data/output"):
        """
        Initialize exporter.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_candidate_id(self, cv: ExtractedCV) -> str:
        """Generate a unique candidate ID."""
        # Use name + timestamp hash for uniqueness
        name_part = cv.personal_info.full_name.replace(" ", "_")[:20]
        unique_part = uuid.uuid4().hex[:8]
        return f"{name_part}_{unique_part}"

    def _prepare_personal_info_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare personal information dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            pi = cv.personal_info
            records.append({
                "candidate_id": cid,
                "full_name": pi.full_name,
                "email": pi.email,
                "phone": pi.phone,
                "address": pi.address,
                "linkedin": pi.linkedin,
                "google_scholar": pi.google_scholar,
                "orcid": pi.orcid,
                "website": pi.website,
                "source_file": cv.source_file,
                "extraction_timestamp": cv.extraction_timestamp
            })
        return pd.DataFrame(records)

    def _prepare_education_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare education records dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            for edu in cv.education:
                records.append({
                    "candidate_id": cid,
                    "degree_level": edu.degree_level.value if edu.degree_level else None,
                    "degree_title": edu.degree_title,
                    "specialization": edu.specialization,
                    "institution": edu.institution,
                    "board": edu.board,
                    "country": edu.country,
                    "start_year": edu.start_year,
                    "end_year": edu.end_year,
                    "grade_value": edu.grade_value,
                    "grade_type": edu.grade_type.value if edu.grade_type else None,
                    "normalized_percentage": edu.normalized_percentage,
                    "thesis_title": edu.thesis_title
                })
        return pd.DataFrame(records)

    def _prepare_experience_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare experience records dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            for exp in cv.experience:
                records.append({
                    "candidate_id": cid,
                    "job_title": exp.job_title,
                    "organization": exp.organization,
                    "department": exp.department,
                    "location": exp.location,
                    "employment_type": exp.employment_type,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "is_current": exp.is_current,
                    "responsibilities": "; ".join(exp.responsibilities) if exp.responsibilities else None,
                    "achievements": "; ".join(exp.achievements) if exp.achievements else None
                })
        return pd.DataFrame(records)

    def _prepare_skills_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare skills dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            for skill in cv.skills:
                records.append({
                    "candidate_id": cid,
                    "skill_name": skill.skill_name,
                    "skill_category": skill.skill_category,
                    "proficiency_level": skill.proficiency_level
                })
        return pd.DataFrame(records)

    def _prepare_journal_publications_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare journal publications dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            for pub in cv.journal_publications:
                records.append({
                    "candidate_id": cid,
                    "title": pub.title,
                    "journal_name": pub.journal_name,
                    "issn": pub.issn,
                    "publication_year": pub.publication_year,
                    "volume": pub.volume,
                    "issue": pub.issue,
                    "pages": pub.pages,
                    "doi": pub.doi,
                    "authors": "; ".join(pub.authors) if pub.authors else None,
                    "author_role": pub.author_role.value if pub.author_role else None,
                    "author_position": pub.author_position,
                    "impact_factor": pub.impact_factor,
                    "quartile": pub.quartile,
                    "is_wos_indexed": pub.is_wos_indexed,
                    "is_scopus_indexed": pub.is_scopus_indexed
                })
        return pd.DataFrame(records)

    def _prepare_conference_publications_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare conference publications dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            for pub in cv.conference_publications:
                records.append({
                    "candidate_id": cid,
                    "title": pub.title,
                    "conference_name": pub.conference_name,
                    "conference_location": pub.conference_location,
                    "publication_year": pub.publication_year,
                    "pages": pub.pages,
                    "doi": pub.doi,
                    "authors": "; ".join(pub.authors) if pub.authors else None,
                    "author_role": pub.author_role.value if pub.author_role else None,
                    "author_position": pub.author_position,
                    "conference_rank": pub.conference_rank,
                    "publisher": pub.publisher,
                    "is_indexed": pub.is_indexed
                })
        return pd.DataFrame(records)

    def _prepare_supervisions_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare supervision records dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            for sup in cv.supervisions:
                records.append({
                    "candidate_id": cid,
                    "student_name": sup.student_name,
                    "degree_level": sup.degree_level,
                    "thesis_title": sup.thesis_title,
                    "role": sup.role,
                    "institution": sup.institution,
                    "start_year": sup.start_year,
                    "completion_year": sup.completion_year,
                    "status": sup.status
                })
        return pd.DataFrame(records)

    def _prepare_patents_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare patents dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            for pat in cv.patents:
                records.append({
                    "candidate_id": cid,
                    "patent_number": pat.patent_number,
                    "patent_title": pat.patent_title,
                    "inventors": "; ".join(pat.inventors) if pat.inventors else None,
                    "filing_date": pat.filing_date,
                    "grant_date": pat.grant_date,
                    "country": pat.country,
                    "status": pat.status,
                    "verification_link": pat.verification_link
                })
        return pd.DataFrame(records)

    def _prepare_books_df(self, cvs: List[ExtractedCV], ids: List[str]) -> pd.DataFrame:
        """Prepare books dataframe."""
        records = []
        for cv, cid in zip(cvs, ids):
            for book in cv.books:
                records.append({
                    "candidate_id": cid,
                    "book_title": book.book_title,
                    "authors": "; ".join(book.authors) if book.authors else None,
                    "isbn": book.isbn,
                    "publisher": book.publisher,
                    "publication_year": book.publication_year,
                    "edition": book.edition,
                    "role": book.role,
                    "online_link": book.online_link
                })
        return pd.DataFrame(records)

    def export_to_excel(self, cvs: List[ExtractedCV], filename: str = None) -> str:
        """
        Export multiple CVs to a single Excel file with multiple sheets.

        Args:
            cvs: List of extracted CVs
            filename: Output filename (optional)

        Returns:
            Path to the created file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cv_extraction_{timestamp}.xlsx"

        filepath = self.output_dir / filename

        # Generate candidate IDs
        ids = [self._generate_candidate_id(cv) for cv in cvs]

        # Prepare all dataframes
        dfs = {
            "candidates": self._prepare_personal_info_df(cvs, ids),
            "education": self._prepare_education_df(cvs, ids),
            "experience": self._prepare_experience_df(cvs, ids),
            "skills": self._prepare_skills_df(cvs, ids),
            "journal_publications": self._prepare_journal_publications_df(cvs, ids),
            "conference_publications": self._prepare_conference_publications_df(cvs, ids),
            "supervisions": self._prepare_supervisions_df(cvs, ids),
            "patents": self._prepare_patents_df(cvs, ids),
            "books": self._prepare_books_df(cvs, ids)
        }

        # Write to Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in dfs.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Exported {len(cvs)} CVs to {filepath}")
        return str(filepath)

    def export_to_csv(self, cvs: List[ExtractedCV], prefix: str = None) -> Dict[str, str]:
        """
        Export multiple CVs to separate CSV files for each entity.

        Args:
            cvs: List of extracted CVs
            prefix: Prefix for filenames (optional)

        Returns:
            Dictionary mapping entity names to file paths
        """
        if not prefix:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"cv_extraction_{timestamp}"

        # Generate candidate IDs
        ids = [self._generate_candidate_id(cv) for cv in cvs]

        # Prepare all dataframes
        dfs = {
            "candidates": self._prepare_personal_info_df(cvs, ids),
            "education": self._prepare_education_df(cvs, ids),
            "experience": self._prepare_experience_df(cvs, ids),
            "skills": self._prepare_skills_df(cvs, ids),
            "journal_publications": self._prepare_journal_publications_df(cvs, ids),
            "conference_publications": self._prepare_conference_publications_df(cvs, ids),
            "supervisions": self._prepare_supervisions_df(cvs, ids),
            "patents": self._prepare_patents_df(cvs, ids),
            "books": self._prepare_books_df(cvs, ids)
        }

        # Write CSV files
        output_files = {}
        for entity_name, df in dfs.items():
            if not df.empty:
                filepath = self.output_dir / f"{prefix}_{entity_name}.csv"
                df.to_csv(filepath, index=False)
                output_files[entity_name] = str(filepath)
                logger.info(f"Exported {entity_name} to {filepath}")

        return output_files

    def export_single_cv_to_json(self, cv: ExtractedCV, filename: str = None) -> str:
        """
        Export a single CV to JSON format.

        Args:
            cv: Extracted CV
            filename: Output filename (optional)

        Returns:
            Path to the created file
        """
        import json

        if not filename:
            name_part = cv.personal_info.full_name.replace(" ", "_")[:30]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name_part}_{timestamp}.json"

        filepath = self.output_dir / filename

        # Convert to dict and write
        cv_dict = cv.model_dump()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cv_dict, f, indent=2, default=str)

        logger.info(f"Exported CV to {filepath}")
        return str(filepath)
