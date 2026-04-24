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

    def _get_stable_candidate_id(self, cv: ExtractedCV) -> str:
        """Stable ID from source filename — same CV always gets same ID, no uuid."""
        import hashlib
        stable_hash = hashlib.md5((cv.source_file or "unknown").encode()).hexdigest()[:8]
        safe_name = (cv.personal_info.full_name or "unknown").replace(" ", "_")[:20]
        return f"{safe_name}_{stable_hash}"

    def export_to_excel(self, cvs: List[ExtractedCV], filename: str = "talash_all_candidates.xlsx") -> str:
        """
        Export CVs to a single master Excel file (one sheet per table).
        If the file already exists, new candidates are APPENDED and existing
        ones are UPDATED (no duplicates). Safe to call after every CV processed.

        Args:
            cvs: List of extracted CVs to write
            filename: Stable output filename (not timestamped)

        Returns:
            Path to the created/updated file
        """
        filepath = self.output_dir / filename

        # Stable IDs — re-processing same CV won't create duplicate rows
        ids = [self._get_stable_candidate_id(cv) for cv in cvs]

        new_dfs = {
            "candidates":              self._prepare_personal_info_df(cvs, ids),
            "education":               self._prepare_education_df(cvs, ids),
            "experience":              self._prepare_experience_df(cvs, ids),
            "skills":                  self._prepare_skills_df(cvs, ids),
            "journal_publications":    self._prepare_journal_publications_df(cvs, ids),
            "conference_publications": self._prepare_conference_publications_df(cvs, ids),
            "supervisions":            self._prepare_supervisions_df(cvs, ids),
            "patents":                 self._prepare_patents_df(cvs, ids),
            "books":                   self._prepare_books_df(cvs, ids),
        }

        # If file exists, load and merge — drop stale rows for candidates being rewritten
        if filepath.exists():
            try:
                existing = pd.read_excel(filepath, sheet_name=None, dtype=str)
            except Exception as e:
                logger.warning(f"Could not read existing Excel ({e}), starting fresh")
                existing = {}
            combined = {}
            for sheet, new_df in new_dfs.items():
                old_df = existing.get(sheet, pd.DataFrame())
                if not old_df.empty and "candidate_id" in old_df.columns and not new_df.empty:
                    old_df = old_df[~old_df["candidate_id"].isin(ids)]
                combined[sheet] = pd.concat([old_df, new_df], ignore_index=True)
        else:
            combined = new_dfs

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            for sheet_name, df in combined.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Excel updated → {filepath}  ({len(cvs)} candidate(s) added/updated)")
        return str(filepath)

    def export_to_csv(self, cvs: List[ExtractedCV]) -> Dict[str, str]:
        """
        Export CVs to a set of STABLE master CSV files (one per table).
        Files are named talash_candidates.csv, talash_education.csv, etc.

        If a file already exists, new candidates are APPENDED and existing
        ones are UPDATED (no duplicates). Safe to call after every CV processed.

        Args:
            cvs: List of extracted CVs to write

        Returns:
            Dictionary mapping table name to file path
        """
        # Stable IDs — re-processing same CV won't create duplicate rows
        ids = [self._get_stable_candidate_id(cv) for cv in cvs]

        new_dfs = {
            "candidates":              self._prepare_personal_info_df(cvs, ids),
            "education":               self._prepare_education_df(cvs, ids),
            "experience":              self._prepare_experience_df(cvs, ids),
            "skills":                  self._prepare_skills_df(cvs, ids),
            "journal_publications":    self._prepare_journal_publications_df(cvs, ids),
            "conference_publications": self._prepare_conference_publications_df(cvs, ids),
            "supervisions":            self._prepare_supervisions_df(cvs, ids),
            "patents":                 self._prepare_patents_df(cvs, ids),
            "books":                   self._prepare_books_df(cvs, ids),
        }

        output_files = {}
        for table_name, new_df in new_dfs.items():
            filepath = self.output_dir / f"talash_{table_name}.csv"

            if filepath.exists():
                try:
                    old_df = pd.read_csv(filepath, dtype=str)
                    # Remove stale rows for candidates being rewritten
                    if "candidate_id" in old_df.columns and not new_df.empty:
                        old_df = old_df[~old_df["candidate_id"].isin(ids)]
                    combined_df = pd.concat([old_df, new_df], ignore_index=True)
                except Exception as e:
                    logger.warning(f"Could not read {filepath.name} ({e}), overwriting")
                    combined_df = new_df
            else:
                combined_df = new_df

            if not combined_df.empty:
                combined_df.to_csv(filepath, index=False)
                output_files[table_name] = str(filepath)
                logger.info(f"CSV updated → {filepath.name}  "
                            f"({len(new_df)} new rows, {len(combined_df)} total)")

        return output_files

    def export_single_cv_to_excel(self, cv: ExtractedCV, filename: str = "talash_candidates.xlsx") -> str:
        """
        Export or APPEND a single CV to the master Excel file.

        If the Excel already exists, reads all existing sheets and appends
        the new candidate's rows, then rewrites the file.  This way, calling
        this after every individual /process API call builds up one growing
        Excel with all candidates — no separate "batch export" step needed.

        If the file does not exist yet, it is created fresh.

        Args:
            cv: The single ExtractedCV to add
            filename: Master Excel filename (default: talash_candidates.xlsx)

        Returns:
            Path to the Excel file
        """
        import hashlib
        filepath = self.output_dir / filename

        # Stable candidate_id derived from filename — NOT a random uuid.
        # This means re-processing the same PDF won't duplicate rows.
        stable_hash = hashlib.md5((cv.source_file or "unknown").encode()).hexdigest()[:8]
        safe_name   = (cv.personal_info.full_name or "unknown").replace(" ", "_")[:15]
        candidate_id = f"{safe_name}_{stable_hash}"

        # Build DataFrames for this single candidate
        new_data = {
            "candidates":              self._prepare_personal_info_df([cv], [candidate_id]),
            "education":               self._prepare_education_df([cv], [candidate_id]),
            "experience":              self._prepare_experience_df([cv], [candidate_id]),
            "skills":                  self._prepare_skills_df([cv], [candidate_id]),
            "journal_publications":    self._prepare_journal_publications_df([cv], [candidate_id]),
            "conference_publications": self._prepare_conference_publications_df([cv], [candidate_id]),
            "supervisions":            self._prepare_supervisions_df([cv], [candidate_id]),
            "patents":                 self._prepare_patents_df([cv], [candidate_id]),
            "books":                   self._prepare_books_df([cv], [candidate_id]),
        }

        # If the file already exists, load existing data and merge
        if filepath.exists():
            try:
                existing_sheets = pd.read_excel(filepath, sheet_name=None, dtype=str)
            except Exception as e:
                logger.warning(f"Could not read existing Excel ({e}), creating fresh file")
                existing_sheets = {}

            combined = {}
            for sheet_name, new_df in new_data.items():
                old_df = existing_sheets.get(sheet_name, pd.DataFrame())

                # Avoid duplicating the same candidate (match on candidate_id)
                if not old_df.empty and "candidate_id" in old_df.columns and not new_df.empty:
                    old_df = old_df[old_df["candidate_id"] != candidate_id]

                if not new_df.empty:
                    combined[sheet_name] = pd.concat(
                        [old_df, new_df], ignore_index=True
                    )
                else:
                    combined[sheet_name] = old_df
        else:
            combined = new_data

        # Write the merged data back to Excel
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            for sheet_name, df in combined.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Appended '{cv.personal_info.full_name}' → {filepath}  (id: {candidate_id})")
        return str(filepath)

    def export_analysis_to_excel(
        self,
        results: List[Dict[str, Any]],
        filename: str = "talash_analysis.xlsx",
    ) -> str:
        """
        Export per-candidate analysis results to a dedicated analysis Excel file.
        Sheets: analysis_summary, education_analysis, experience_analysis,
                research_analysis, missing_info, draft_emails.

        Args:
            results: List of dicts, each containing keys:
                     'cv', 'edu_analysis', 'exp_analysis', 'res_analysis',
                     'missing_info', 'email_files' (optional)
            filename: Output filename

        Returns:
            Path to the created file
        """
        filepath = self.output_dir / filename

        summary_rows = []
        edu_rows = []
        exp_rows = []
        res_rows = []
        missing_rows = []
        email_rows = []

        for r in results:
            cv = r["cv"]
            name = cv.personal_info.full_name
            edu = r.get("edu_analysis", {})
            exp = r.get("exp_analysis", {})
            res = r.get("res_analysis", {})
            mis = r.get("missing_info", {})
            emails = r.get("email_files", {})

            summary_rows.append({
                "candidate_name": name,
                "highest_degree": edu.get("highest_degree"),
                "highest_degree_institution": edu.get("highest_degree_institution"),
                "has_phd": edu.get("has_phd"),
                "has_foreign_education": edu.get("has_foreign_education"),
                "total_years_experience": exp.get("total_years_experience"),
                "current_position": exp.get("current_position"),
                "career_trajectory": exp.get("career_trajectory"),
                "total_publications": res.get("total_publications"),
                "research_impact_score": res.get("research_impact_score"),
                "profile_tier": res.get("profile_tier"),
                "has_missing_info": mis.get("has_missing_info"),
                "has_critical_missing": mis.get("has_critical_missing"),
                "total_missing_fields": mis.get("total_missing_fields"),
            })

            edu_rows.append({
                "candidate_name": name,
                "highest_degree": edu.get("highest_degree"),
                "highest_degree_institution": edu.get("highest_degree_institution"),
                "highest_degree_year": edu.get("highest_degree_year"),
                "has_phd": edu.get("has_phd"),
                "has_foreign_education": edu.get("has_foreign_education"),
                "foreign_institutions": ", ".join(edu.get("foreign_institutions") or []),
                "average_percentage": edu.get("average_percentage"),
                "degree_progression": " → ".join(edu.get("degree_progression") or []),
                "gaps_detected": "; ".join(edu.get("gaps_detected") or []),
            })

            exp_rows.append({
                "candidate_name": name,
                "total_years_experience": exp.get("total_years_experience"),
                "number_of_positions": exp.get("number_of_positions"),
                "is_currently_employed": exp.get("is_currently_employed"),
                "current_position": exp.get("current_position"),
                "current_organization": exp.get("current_organization"),
                "career_trajectory": exp.get("career_trajectory"),
                "average_tenure_years": exp.get("average_tenure_years"),
                "longest_role": exp.get("longest_role"),
            })

            q = res.get("quartile_distribution", {})
            res_rows.append({
                "candidate_name": name,
                "profile_tier": res.get("profile_tier"),
                "total_publications": res.get("total_publications"),
                "total_journal_publications": res.get("total_journal_publications"),
                "total_conference_publications": res.get("total_conference_publications"),
                "Q1": q.get("Q1", 0),
                "Q2": q.get("Q2", 0),
                "Q3": q.get("Q3", 0),
                "Q4": q.get("Q4", 0),
                "Unranked": q.get("Unranked", 0),
                "wos_indexed_count": res.get("wos_indexed_count"),
                "scopus_indexed_count": res.get("scopus_indexed_count"),
                "average_impact_factor": res.get("average_impact_factor"),
                "research_impact_score": res.get("research_impact_score"),
                "publication_trend": res.get("publication_trend"),
                "high_impact_ratio": res.get("high_impact_ratio"),
                "ms_supervised": res.get("ms_supervised"),
                "phd_supervised": res.get("phd_supervised"),
                "total_patents": res.get("total_patents"),
                "granted_patents": res.get("granted_patents"),
            })

            if mis.get("has_missing_info"):
                by_cat = mis.get("missing_by_category", {})
                for item in mis.get("all_missing", []):
                    missing_rows.append({
                        "candidate_name": name,
                        "missing_item": item,
                        "total_missing_fields": mis.get("total_missing_fields"),
                        "has_critical_missing": mis.get("has_critical_missing"),
                    })

            for template_type, file_path in emails.items():
                email_rows.append({
                    "candidate_name": name,
                    "template_type": template_type,
                    "file_path": file_path,
                })

        sheets = {
            "analysis_summary": pd.DataFrame(summary_rows),
            "education_analysis": pd.DataFrame(edu_rows),
            "experience_analysis": pd.DataFrame(exp_rows),
            "research_analysis": pd.DataFrame(res_rows),
            "missing_info": pd.DataFrame(missing_rows) if missing_rows else pd.DataFrame(
                columns=["candidate_name", "missing_item", "total_missing_fields", "has_critical_missing"]
            ),
            "draft_emails": pd.DataFrame(email_rows) if email_rows else pd.DataFrame(
                columns=["candidate_name", "template_type", "file_path"]
            ),
        }

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Analysis Excel written → {filepath}")
        return str(filepath)

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