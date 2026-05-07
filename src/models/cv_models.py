"""
Pydantic models for structured CV data extraction.
These models define the schema for extracting and storing CV information
in a relational-database-like format.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class DegreeLevel(str, Enum):
    SSC = "SSC"  # Secondary School Certificate (Matric)
    HSSC = "HSSC"  # Higher Secondary School Certificate (Intermediate)
    BACHELOR_14 = "Bachelor (14-year)"  # Old BSc system
    BACHELOR_16 = "Bachelor (16-year)"  # 4-year BS degree
    MASTER_16 = "Master (16-year)"  # Old MSc system
    MASTER_18 = "Master (18-year)"  # MS/MPhil
    PHD = "PhD"
    OTHER = "Other"


class GradeType(str, Enum):
    PERCENTAGE = "Percentage"
    CGPA_4 = "CGPA (4.0 scale)"
    CGPA_5 = "CGPA (5.0 scale)"
    DIVISION = "Division"
    GRADE = "Grade"


class AuthorRole(str, Enum):
    FIRST_AUTHOR = "First Author"
    CORRESPONDING_AUTHOR = "Corresponding Author"
    FIRST_AND_CORRESPONDING = "First and Corresponding Author"
    CO_AUTHOR = "Co-Author"


# ============== Personal Information ==============
class PersonalInfo(BaseModel):
    """Candidate's personal and contact information"""
    candidate_id: Optional[str] = Field(None, description="Unique identifier for the candidate")
    full_name: str = Field(..., description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Current address")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    google_scholar: Optional[str] = Field(None, description="Google Scholar profile URL")
    orcid: Optional[str] = Field(None, description="ORCID identifier")
    website: Optional[str] = Field(None, description="Personal website URL")


# ============== Education Records ==============
class EducationRecord(BaseModel):
    """Individual education record"""
    candidate_id: Optional[str] = Field(None, description="Reference to candidate")
    degree_level: DegreeLevel = Field(..., description="Level of the degree")
    degree_title: str = Field(..., description="Title of the degree (e.g., BS Computer Science)")
    specialization: Optional[str] = Field(None, description="Area of specialization")
    institution: str = Field(..., description="Name of the institution")
    board: Optional[str] = Field(None, description="Board name (for SSC/HSSC)")
    country: Optional[str] = Field(None, description="Country of institution")
    start_year: Optional[int] = Field(None, description="Year of admission")
    end_year: Optional[int] = Field(None, description="Year of completion")
    grade_value: Optional[str] = Field(None, description="Original grade/marks/CGPA as stated")
    grade_type: Optional[GradeType] = Field(None, description="Type of grading system")
    normalized_percentage: Optional[float] = Field(None, description="Normalized to percentage (0-100)")
    thesis_title: Optional[str] = Field(None, description="Thesis/dissertation title if applicable")


# ============== Professional Experience ==============
class ExperienceRecord(BaseModel):
    """Individual work experience record"""
    candidate_id: Optional[str] = Field(None, description="Reference to candidate")
    job_title: str = Field(..., description="Job title/position")
    organization: str = Field(..., description="Organization/company name")
    department: Optional[str] = Field(None, description="Department or unit")
    location: Optional[str] = Field(None, description="City/Country")
    employment_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract, etc.")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or YYYY)")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    is_current: bool = Field(False, description="Whether this is current position")
    responsibilities: Optional[List[str]] = Field(None, description="Key responsibilities")
    achievements: Optional[List[str]] = Field(None, description="Key achievements")


# ============== Skills ==============
class SkillRecord(BaseModel):
    """Individual skill entry"""
    candidate_id: Optional[str] = Field(None, description="Reference to candidate")
    skill_name: str = Field(..., description="Name of the skill")
    skill_category: Optional[str] = Field(None, description="Category (Technical, Soft, Language, etc.)")
    proficiency_level: Optional[str] = Field(None, description="Proficiency level if mentioned")


# ============== Publications - Journals ==============
class JournalPublication(BaseModel):
    """Journal publication record"""
    candidate_id: Optional[str] = Field(None, description="Reference to candidate")
    title: str = Field(..., description="Paper title")
    journal_name: str = Field(..., description="Journal name")
    issn: Optional[str] = Field(None, description="Journal ISSN")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    volume: Optional[str] = Field(None, description="Volume number")
    issue: Optional[str] = Field(None, description="Issue number")
    pages: Optional[str] = Field(None, description="Page numbers")
    doi: Optional[str] = Field(None, description="DOI")
    authors: List[str] = Field(..., description="List of all authors")
    author_role: Optional[AuthorRole] = Field(None, description="Candidate's role in authorship")
    author_position: Optional[int] = Field(None, description="Candidate's position in author list")
    impact_factor: Optional[float] = Field(None, description="Journal impact factor if known")
    quartile: Optional[str] = Field(None, description="Journal quartile (Q1, Q2, Q3, Q4)")
    is_wos_indexed: Optional[bool] = Field(None, description="Web of Science indexed")
    is_scopus_indexed: Optional[bool] = Field(None, description="Scopus indexed")


# ============== Publications - Conferences ==============
class ConferencePublication(BaseModel):
    """Conference publication record"""
    candidate_id: Optional[str] = Field(None, description="Reference to candidate")
    title: str = Field(..., description="Paper title")
    conference_name: str = Field(..., description="Conference name")
    conference_location: Optional[str] = Field(None, description="Location of conference")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    pages: Optional[str] = Field(None, description="Page numbers")
    doi: Optional[str] = Field(None, description="DOI")
    authors: List[str] = Field(..., description="List of all authors")
    author_role: Optional[AuthorRole] = Field(None, description="Candidate's role in authorship")
    author_position: Optional[int] = Field(None, description="Candidate's position in author list")
    conference_rank: Optional[str] = Field(None, description="Conference rank (A*, A, B, C)")
    publisher: Optional[str] = Field(None, description="Publisher (IEEE, ACM, Springer, etc.)")
    is_indexed: Optional[bool] = Field(None, description="Whether indexed in major databases")


# ============== Student Supervision ==============
class SupervisionRecord(BaseModel):
    """Student supervision record"""
    candidate_id: Optional[str] = Field(None, description="Reference to candidate")
    student_name: str = Field(..., description="Name of supervised student")
    degree_level: str = Field(..., description="MS, PhD, etc.")
    thesis_title: Optional[str] = Field(None, description="Thesis title")
    role: str = Field(..., description="Main Supervisor or Co-Supervisor")
    institution: Optional[str] = Field(None, description="Institution")
    start_year: Optional[int] = Field(None, description="Start year")
    completion_year: Optional[int] = Field(None, description="Completion year")
    status: Optional[str] = Field(None, description="Completed, In Progress, etc.")


# ============== Patents ==============
class PatentRecord(BaseModel):
    """Patent record"""
    candidate_id: Optional[str] = Field(None, description="Reference to candidate")
    patent_number: Optional[str] = Field(None, description="Patent number (may be absent for pending/submitted patents)")
    patent_title: str = Field(..., description="Patent title")
    inventors: List[str] = Field(..., description="List of inventors")
    filing_date: Optional[str] = Field(None, description="Filing date")
    grant_date: Optional[str] = Field(None, description="Grant date if granted")
    country: Optional[str] = Field(None, description="Country of filing")
    status: Optional[str] = Field(None, description="Filed, Granted, Pending")
    verification_link: Optional[str] = Field(None, description="Online verification URL")


# ============== Books ==============
class BookRecord(BaseModel):
    """Book authorship record"""
    candidate_id: Optional[str] = Field(None, description="Reference to candidate")
    book_title: str = Field(..., description="Book title")
    authors: List[str] = Field(..., description="List of authors")
    isbn: Optional[str] = Field(None, description="ISBN")
    publisher: Optional[str] = Field(None, description="Publisher name")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    edition: Optional[str] = Field(None, description="Edition if applicable")
    role: Optional[str] = Field(None, description="Sole Author, Lead Author, Co-Author, Editor")
    online_link: Optional[str] = Field(None, description="Online link to book")


# ============== Complete CV Structure ==============
class ExtractedCV(BaseModel):
    """Complete extracted CV data"""
    personal_info: PersonalInfo
    education: List[EducationRecord] = Field(default_factory=list)
    experience: List[ExperienceRecord] = Field(default_factory=list)
    skills: List[SkillRecord] = Field(default_factory=list)
    journal_publications: List[JournalPublication] = Field(default_factory=list)
    conference_publications: List[ConferencePublication] = Field(default_factory=list)
    supervisions: List[SupervisionRecord] = Field(default_factory=list)
    patents: List[PatentRecord] = Field(default_factory=list)
    books: List[BookRecord] = Field(default_factory=list)
    raw_text: Optional[str] = Field(None, description="Original extracted text from PDF")
    extraction_timestamp: Optional[str] = Field(None, description="When the CV was processed")
    source_file: Optional[str] = Field(None, description="Original PDF filename")