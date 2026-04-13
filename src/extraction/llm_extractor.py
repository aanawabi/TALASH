"""
LLM Extractor Module
Uses Google Gemini to extract structured information from CV text.
"""

from google import genai
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.cv_models import (
    ExtractedCV, PersonalInfo, EducationRecord, ExperienceRecord,
    SkillRecord, JournalPublication, ConferencePublication,
    SupervisionRecord, PatentRecord, BookRecord,
    DegreeLevel, GradeType, AuthorRole
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CVExtractor:
    """
    Extracts structured CV information using Google Gemini LLM.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-3.1-flash-lite-preview"):
        """
        Initialize the extractor with Gemini API.

        Args:
            api_key: Google AI API key
            model_name: Gemini model to use
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def _get_extraction_prompt(self, cv_text: str) -> str:
        """Generate the prompt for CV extraction."""
        return f'''You are an expert CV/Resume parser. Extract all information from the following CV text and return it as a valid JSON object.

IMPORTANT INSTRUCTIONS:
1. Extract ALL information present in the CV
2. Use null for missing fields, don't make up information
3. For dates, use format "YYYY" or "YYYY-MM" where available
4. For author roles, determine if candidate is "First Author", "Corresponding Author", "First and Corresponding Author", or "Co-Author"
5. Normalize degree levels to: "SSC", "HSSC", "Bachelor (14-year)", "Bachelor (16-year)", "Master (16-year)", "Master (18-year)", "PhD", "Other"
6. For CGPA/grades, identify the type: "Percentage", "CGPA (4.0 scale)", "CGPA (5.0 scale)", "Division", "Grade"

Return a JSON object with this exact structure:
{{
    "personal_info": {{
        "full_name": "string",
        "email": "string or null",
        "phone": "string or null",
        "address": "string or null",
        "linkedin": "string or null",
        "google_scholar": "string or null",
        "orcid": "string or null",
        "website": "string or null"
    }},
    "education": [
        {{
            "degree_level": "string (SSC/HSSC/Bachelor (14-year)/Bachelor (16-year)/Master (16-year)/Master (18-year)/PhD/Other)",
            "degree_title": "string",
            "specialization": "string or null",
            "institution": "string",
            "board": "string or null",
            "country": "string or null",
            "start_year": "integer or null",
            "end_year": "integer or null",
            "grade_value": "string (original value as written)",
            "grade_type": "string (Percentage/CGPA (4.0 scale)/CGPA (5.0 scale)/Division/Grade) or null",
            "normalized_percentage": "float (0-100) or null",
            "thesis_title": "string or null"
        }}
    ],
    "experience": [
        {{
            "job_title": "string",
            "organization": "string",
            "department": "string or null",
            "location": "string or null",
            "employment_type": "string or null",
            "start_date": "string (YYYY or YYYY-MM)",
            "end_date": "string (YYYY or YYYY-MM or 'Present')",
            "is_current": "boolean",
            "responsibilities": ["list of strings"],
            "achievements": ["list of strings"]
        }}
    ],
    "skills": [
        {{
            "skill_name": "string",
            "skill_category": "string (Technical/Soft/Language/Tool/Framework/Other)",
            "proficiency_level": "string or null"
        }}
    ],
    "journal_publications": [
        {{
            "title": "string",
            "journal_name": "string",
            "issn": "string or null",
            "publication_year": "integer or null",
            "volume": "string or null",
            "issue": "string or null",
            "pages": "string or null",
            "doi": "string or null",
            "authors": ["list of author names in order"],
            "author_role": "string (First Author/Corresponding Author/First and Corresponding Author/Co-Author)",
            "author_position": "integer (1-based position in author list)",
            "impact_factor": "float or null",
            "quartile": "string (Q1/Q2/Q3/Q4) or null",
            "is_wos_indexed": "boolean or null",
            "is_scopus_indexed": "boolean or null"
        }}
    ],
    "conference_publications": [
        {{
            "title": "string",
            "conference_name": "string",
            "conference_location": "string or null",
            "publication_year": "integer or null",
            "pages": "string or null",
            "doi": "string or null",
            "authors": ["list of author names in order"],
            "author_role": "string (First Author/Corresponding Author/First and Corresponding Author/Co-Author)",
            "author_position": "integer (1-based position in author list)",
            "conference_rank": "string (A*/A/B/C) or null",
            "publisher": "string (IEEE/ACM/Springer/etc.) or null",
            "is_indexed": "boolean or null"
        }}
    ],
    "supervisions": [
        {{
            "student_name": "string",
            "degree_level": "string (MS/PhD/etc.)",
            "thesis_title": "string or null",
            "role": "string (Main Supervisor/Co-Supervisor)",
            "institution": "string or null",
            "start_year": "integer or null",
            "completion_year": "integer or null",
            "status": "string (Completed/In Progress) or null"
        }}
    ],
    "patents": [
        {{
            "patent_number": "string",
            "patent_title": "string",
            "inventors": ["list of inventor names"],
            "filing_date": "string or null",
            "grant_date": "string or null",
            "country": "string or null",
            "status": "string (Filed/Granted/Pending) or null",
            "verification_link": "string or null"
        }}
    ],
    "books": [
        {{
            "book_title": "string",
            "authors": ["list of author names"],
            "isbn": "string or null",
            "publisher": "string or null",
            "publication_year": "integer or null",
            "edition": "string or null",
            "role": "string (Sole Author/Lead Author/Co-Author/Editor) or null",
            "online_link": "string or null"
        }}
    ]
}}

CV TEXT TO PARSE:
---
{cv_text}
---

Return ONLY the JSON object, no additional text or markdown formatting.'''

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling common issues."""
        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Raw response: {text[:500]}...")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

    def _map_degree_level(self, level_str: str) -> DegreeLevel:
        """Map extracted degree level string to enum."""
        mapping = {
            "ssc": DegreeLevel.SSC,
            "matric": DegreeLevel.SSC,
            "matriculation": DegreeLevel.SSC,
            "hssc": DegreeLevel.HSSC,
            "intermediate": DegreeLevel.HSSC,
            "fsc": DegreeLevel.HSSC,
            "fa": DegreeLevel.HSSC,
            "bachelor (14-year)": DegreeLevel.BACHELOR_14,
            "bsc": DegreeLevel.BACHELOR_14,
            "bachelor (16-year)": DegreeLevel.BACHELOR_16,
            "bs": DegreeLevel.BACHELOR_16,
            "be": DegreeLevel.BACHELOR_16,
            "btech": DegreeLevel.BACHELOR_16,
            "master (16-year)": DegreeLevel.MASTER_16,
            "msc": DegreeLevel.MASTER_16,
            "master (18-year)": DegreeLevel.MASTER_18,
            "ms": DegreeLevel.MASTER_18,
            "mphil": DegreeLevel.MASTER_18,
            "phd": DegreeLevel.PHD,
            "doctorate": DegreeLevel.PHD,
        }
        level_lower = level_str.lower().strip()
        return mapping.get(level_lower, DegreeLevel.OTHER)

    def _map_grade_type(self, type_str: Optional[str]) -> Optional[GradeType]:
        """Map grade type string to enum."""
        if not type_str:
            return None
        mapping = {
            "percentage": GradeType.PERCENTAGE,
            "cgpa (4.0 scale)": GradeType.CGPA_4,
            "cgpa (5.0 scale)": GradeType.CGPA_5,
            "division": GradeType.DIVISION,
            "grade": GradeType.GRADE,
        }
        return mapping.get(type_str.lower().strip())

    def _map_author_role(self, role_str: Optional[str]) -> Optional[AuthorRole]:
        """Map author role string to enum."""
        if not role_str:
            return None
        mapping = {
            "first author": AuthorRole.FIRST_AUTHOR,
            "corresponding author": AuthorRole.CORRESPONDING_AUTHOR,
            "first and corresponding author": AuthorRole.FIRST_AND_CORRESPONDING,
            "co-author": AuthorRole.CO_AUTHOR,
        }
        return mapping.get(role_str.lower().strip())

    def _build_extracted_cv(self, data: Dict[str, Any], source_file: str) -> ExtractedCV:
        """Build ExtractedCV object from parsed JSON data."""

        # Personal Info
        pi_data = data.get("personal_info", {})
        personal_info = PersonalInfo(
            full_name=pi_data.get("full_name", "Unknown"),
            email=pi_data.get("email"),
            phone=pi_data.get("phone"),
            address=pi_data.get("address"),
            linkedin=pi_data.get("linkedin"),
            google_scholar=pi_data.get("google_scholar"),
            orcid=pi_data.get("orcid"),
            website=pi_data.get("website")
        )

        # Education
        education = []
        for edu in data.get("education", []):
            education.append(EducationRecord(
                degree_level=self._map_degree_level(edu.get("degree_level", "Other")),
                degree_title=edu.get("degree_title", ""),
                specialization=edu.get("specialization"),
                institution=edu.get("institution", ""),
                board=edu.get("board"),
                country=edu.get("country"),
                start_year=edu.get("start_year"),
                end_year=edu.get("end_year"),
                grade_value=edu.get("grade_value"),
                grade_type=self._map_grade_type(edu.get("grade_type")),
                normalized_percentage=edu.get("normalized_percentage"),
                thesis_title=edu.get("thesis_title")
            ))

        # Experience
        experience = []
        for exp in data.get("experience", []):
            experience.append(ExperienceRecord(
                job_title=exp.get("job_title", ""),
                organization=exp.get("organization", ""),
                department=exp.get("department"),
                location=exp.get("location"),
                employment_type=exp.get("employment_type"),
                start_date=exp.get("start_date"),
                end_date=exp.get("end_date"),
                is_current=exp.get("is_current", False),
                responsibilities=exp.get("responsibilities"),
                achievements=exp.get("achievements")
            ))

        # Skills
        skills = []
        for skill in data.get("skills", []):
            skills.append(SkillRecord(
                skill_name=skill.get("skill_name", ""),
                skill_category=skill.get("skill_category"),
                proficiency_level=skill.get("proficiency_level")
            ))

        # Journal Publications
        journal_pubs = []
        for pub in data.get("journal_publications", []):
            journal_pubs.append(JournalPublication(
                title=pub.get("title", ""),
                journal_name=pub.get("journal_name", ""),
                issn=pub.get("issn"),
                publication_year=pub.get("publication_year"),
                volume=pub.get("volume"),
                issue=pub.get("issue"),
                pages=pub.get("pages"),
                doi=pub.get("doi"),
                authors=pub.get("authors", []),
                author_role=self._map_author_role(pub.get("author_role")),
                author_position=pub.get("author_position"),
                impact_factor=pub.get("impact_factor"),
                quartile=pub.get("quartile"),
                is_wos_indexed=pub.get("is_wos_indexed"),
                is_scopus_indexed=pub.get("is_scopus_indexed")
            ))

        # Conference Publications
        conf_pubs = []
        for pub in data.get("conference_publications", []):
            conf_pubs.append(ConferencePublication(
                title=pub.get("title", ""),
                conference_name=pub.get("conference_name", ""),
                conference_location=pub.get("conference_location"),
                publication_year=pub.get("publication_year"),
                pages=pub.get("pages"),
                doi=pub.get("doi"),
                authors=pub.get("authors", []),
                author_role=self._map_author_role(pub.get("author_role")),
                author_position=pub.get("author_position"),
                conference_rank=pub.get("conference_rank"),
                publisher=pub.get("publisher"),
                is_indexed=pub.get("is_indexed")
            ))

        # Supervisions
        supervisions = []
        for sup in data.get("supervisions", []):
            supervisions.append(SupervisionRecord(
                student_name=sup.get("student_name", ""),
                degree_level=sup.get("degree_level", ""),
                thesis_title=sup.get("thesis_title"),
                role=sup.get("role", ""),
                institution=sup.get("institution"),
                start_year=sup.get("start_year"),
                completion_year=sup.get("completion_year"),
                status=sup.get("status")
            ))

        # Patents
        patents = []
        for pat in data.get("patents", []):
            patents.append(PatentRecord(
                patent_number=pat.get("patent_number", ""),
                patent_title=pat.get("patent_title", ""),
                inventors=pat.get("inventors", []),
                filing_date=pat.get("filing_date"),
                grant_date=pat.get("grant_date"),
                country=pat.get("country"),
                status=pat.get("status"),
                verification_link=pat.get("verification_link")
            ))

        # Books
        books = []
        for book in data.get("books", []):
            books.append(BookRecord(
                book_title=book.get("book_title", ""),
                authors=book.get("authors", []),
                isbn=book.get("isbn"),
                publisher=book.get("publisher"),
                publication_year=book.get("publication_year"),
                edition=book.get("edition"),
                role=book.get("role"),
                online_link=book.get("online_link")
            ))

        return ExtractedCV(
            personal_info=personal_info,
            education=education,
            experience=experience,
            skills=skills,
            journal_publications=journal_pubs,
            conference_publications=conf_pubs,
            supervisions=supervisions,
            patents=patents,
            books=books,
            extraction_timestamp=datetime.now().isoformat(),
            source_file=source_file
        )

    def extract(self, cv_text: str, source_file: str = "unknown") -> ExtractedCV:
        """
        Extract structured information from CV text.

        Args:
            cv_text: The raw text content of the CV
            source_file: Name of the source file

        Returns:
            ExtractedCV object with all parsed information
        """
        logger.info(f"Extracting CV data using {self.model_name}...")

        prompt = self._get_extraction_prompt(cv_text)

        try:
            response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
               )
            response_text = response.text

            logger.info("LLM response received, parsing JSON...")
            data = self._parse_json_response(response_text)

            logger.info("Building structured CV object...")
            extracted_cv = self._build_extracted_cv(data, source_file)
            extracted_cv.raw_text = cv_text

            logger.info(f"Extraction complete for {source_file}")
            return extracted_cv

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    def extract_to_dict(self, cv_text: str, source_file: str = "unknown") -> Dict[str, Any]:
        """
        Extract CV and return as dictionary (useful for JSON serialization).
        """
        extracted = self.extract(cv_text, source_file)
        return extracted.model_dump()
