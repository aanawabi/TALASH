"""
Module 3.9 – Skill Alignment Analyzer
Verifies whether skills claimed in the CV are genuinely supported by the
candidate's job roles, research publications, and an optional target job
description. Classifies each skill as:
  - strongly_evidenced
  - partially_evidenced
  - weakly_evidenced
  - unsupported
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import re

from ..models.cv_models import ExtractedCV


# ── Keyword lookup: skill keywords → evidence keywords ────────────────────────
# Maps a normalized skill token to words that, if found in job
# responsibilities/titles or publication text, count as evidence.
_SKILL_EVIDENCE_MAP: Dict[str, List[str]] = {
    # ML / AI
    "machine learning":       ["machine learning", "ml", "model", "train", "classification", "prediction"],
    "deep learning":          ["deep learning", "neural", "cnn", "rnn", "lstm", "transformer"],
    "natural language processing": ["nlp", "text", "language model", "bert", "sentiment", "named entity"],
    "computer vision":        ["image", "object detection", "segmentation", "visual", "cnn"],
    "data science":           ["data science", "analytics", "data analysis", "pandas", "numpy"],
    "python":                 ["python", "django", "flask", "fastapi", "tensorflow", "pytorch"],
    "tensorflow":             ["tensorflow", "keras", "deep learning", "neural"],
    "pytorch":                ["pytorch", "deep learning", "neural"],
    "r":                      ["r language", "rstudio", "ggplot", "caret", "tidyverse"],
    # Data / DB
    "sql":                    ["sql", "database", "mysql", "postgresql", "query"],
    "database":               ["database", "sql", "nosql", "mongodb", "relational"],
    "big data":               ["hadoop", "spark", "big data", "distributed"],
    # Web / Software
    "software development":   ["software", "development", "programming", "coding", "engineer"],
    "web development":        ["web", "html", "css", "javascript", "react", "django"],
    "java":                   ["java", "spring", "android"],
    "javascript":             ["javascript", "node", "react", "angular", "vue"],
    "c++":                    ["c++", "embedded", "systems programming"],
    # Research
    "research":               ["research", "publication", "journal", "conference", "investigation"],
    "project management":     ["project manager", "project management", "pmo", "agile", "scrum", "lead"],
    "teaching":               ["teaching", "lecturer", "instructor", "course", "curriculum", "professor"],
    "supervision":            ["supervisor", "supervise", "mentor", "student", "thesis"],
    # Security
    "cybersecurity":          ["security", "cyber", "intrusion", "malware", "cryptograph", "firewall"],
    "network security":       ["network security", "firewall", "ids", "ips", "vpn"],
    # Cloud / DevOps
    "cloud computing":        ["cloud", "aws", "azure", "gcp", "serverless"],
    "devops":                 ["devops", "ci/cd", "docker", "kubernetes", "jenkins"],
    "linux":                  ["linux", "unix", "bash", "shell"],
    # Soft skills
    "communication":          ["communication", "presentation", "report", "writing"],
    "leadership":             ["lead", "manager", "head", "director", "coordinator"],
    "teamwork":               ["team", "collaborate", "cross-functional"],
}


def _normalize(text: str) -> str:
    return text.lower().strip()


def _build_evidence_corpus(cv: ExtractedCV) -> str:
    """Build a single string from all jobs, publications, and education."""
    parts: List[str] = []

    for exp in cv.experience:
        parts.append(exp.job_title or "")
        parts.append(exp.organization or "")
        for r in (exp.responsibilities or []):
            parts.append(r)
        for a in (exp.achievements or []):
            parts.append(a)

    for jp in cv.journal_publications:
        parts.append(jp.title or "")
        parts.append(jp.journal_name or "")

    for cp in cv.conference_publications:
        parts.append(cp.title or "")
        parts.append(cp.conference_name or "")

    for edu in cv.education:
        parts.append(edu.degree_title or "")
        parts.append(edu.specialization or "")

    return " ".join(parts).lower()


def _build_job_corpus(cv: ExtractedCV) -> str:
    """Job-specific corpus (titles + responsibilities only). Per Req 3.9 Skill-to-Experience."""
    parts: List[str] = []
    for exp in cv.experience:
        parts.append(exp.job_title or "")
        parts.append(exp.organization or "")
        for r in (exp.responsibilities or []):
            parts.append(r)
        for a in (exp.achievements or []):
            parts.append(a)
    return " ".join(parts).lower()


def _build_pub_corpus(cv: ExtractedCV) -> str:
    """Publication-specific corpus. Per Req 3.9 Skill-to-Publication Alignment."""
    parts: List[str] = []
    for jp in cv.journal_publications:
        parts.append(jp.title or "")
        parts.append(jp.journal_name or "")
    for cp in cv.conference_publications:
        parts.append(cp.title or "")
        parts.append(cp.conference_name or "")
    return " ".join(parts).lower()


def _build_edu_corpus(cv: ExtractedCV) -> str:
    """
    Education corpus: degree titles, specializations, certifications.
    Per Req 3.9 Skill Consistency: "whether the same skills appear consistently
    across education, work experience, research output, projects, and certifications"
    """
    parts: List[str] = []
    for edu in cv.education:
        parts.append(edu.degree_title or "")
        parts.append(edu.specialization or "")
        parts.append(edu.institution or "")
        if edu.thesis_title:
            parts.append(edu.thesis_title)
    return " ".join(parts).lower()


def _find_evidence_keywords(skill_norm: str, corpus: str) -> List[str]:
    """Return which evidence keywords for this skill appear in corpus."""
    # Try direct skill name first
    candidates = _SKILL_EVIDENCE_MAP.get(skill_norm, [skill_norm])
    return [kw for kw in candidates if kw in corpus]


def _classify_skill(
    skill_name: str,
    job_corpus: str,
    pub_corpus: str,
    edu_corpus: str,
    jd_corpus:  str,
) -> Dict[str, Any]:
    """
    Per Req 3.9 Strength of Skill Evidence:
    - strongly_evidenced:  appears in 2+ corpora, or many keyword hits
    - partially_evidenced: appears in exactly 1 corpus
    - weakly_evidenced:    skill name appears somewhere but no keyword hits
    - unsupported:         no evidence anywhere

    Returns per-source evidence detail so callers can show exactly what
    was found in employment, publications, and education records.
    """
    norm = _normalize(skill_name)

    job_hits = _find_evidence_keywords(norm, job_corpus)
    pub_hits = _find_evidence_keywords(norm, pub_corpus)
    edu_hits = _find_evidence_keywords(norm, edu_corpus)

    evidence_sources: List[str] = []
    if job_hits:
        evidence_sources.append("employment")
    if pub_hits:
        evidence_sources.append("publications")
    if edu_hits:
        evidence_sources.append("education")

    all_hits = set(job_hits + pub_hits + edu_hits)
    n_corpora_with_hits = len(evidence_sources)

    # Req 3.9: Skill Consistency Across Profile
    if n_corpora_with_hits >= 2 or len(all_hits) >= 3:
        strength = "strongly_evidenced"
    elif n_corpora_with_hits == 1:
        strength = "partially_evidenced"
    elif norm in (job_corpus + pub_corpus + edu_corpus + jd_corpus):
        strength = "weakly_evidenced"
    else:
        strength = "unsupported"

    # Build a human-readable evidence detail per source
    evidence_detail: Dict[str, Any] = {
        "employment": {
            "matched": bool(job_hits),
            "keywords_found": job_hits,
        },
        "publications": {
            "matched": bool(pub_hits),
            "keywords_found": pub_hits,
        },
        "education": {
            "matched": bool(edu_hits),
            "keywords_found": edu_hits,
        },
    }

    return {
        "skill":                    skill_name,
        "strength":                 strength,
        "evidence_sources":         evidence_sources,
        "evidence_keywords_found":  list(all_hits)[:5],
        "evidence_detail":          evidence_detail,
        "corpora_matched":          n_corpora_with_hits,
    }


class SkillAlignmentAnalyzer:

    def analyze(
        self,
        cv: ExtractedCV,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Per Req 3.9, compares skills against:
        - job titles and responsibilities     (Skill-to-Experience Alignment)
        - research publications and themes    (Skill-to-Publication Alignment)
        - education, specializations          (Skill Consistency Across Profile)
        - target job description if provided  (Job Relevance of Skills)

        Returns per-skill classification:
          strongly_evidenced | partially_evidenced | weakly_evidenced | unsupported
        """
        skills = cv.skills
        if not skills:
            return {
                "total_skills": 0,
                "skill_assessments": [],
                "summary": {
                    "strongly_evidenced": 0,
                    "partially_evidenced": 0,
                    "weakly_evidenced": 0,
                    "unsupported": 0,
                },
                "job_relevant_skills":  [],
                "missing_jd_skills":    [],
                "alignment_score":      None,
                "jd_alignment_label":   None,
                "interpretation":       "No skills listed in CV.",
            }

        job_corpus = _build_job_corpus(cv)
        pub_corpus = _build_pub_corpus(cv)
        edu_corpus = _build_edu_corpus(cv)
        jd_corpus  = _normalize(job_description or "")

        assessments: List[Dict[str, Any]] = []
        summary = {
            "strongly_evidenced": 0,
            "partially_evidenced": 0,
            "weakly_evidenced": 0,
            "unsupported": 0,
        }

        for skill_rec in skills:
            result = _classify_skill(
                skill_rec.skill_name,
                job_corpus,
                pub_corpus,
                edu_corpus,
                jd_corpus,
            )
            assessments.append(result)
            summary[result["strength"]] += 1

        total = len(assessments)

        # ── JD alignment — Req 3.9 Job Relevance of Skills ───────────────────
        job_relevant_skills: List[str] = []
        missing_jd_skills:   List[str] = []
        alignment_score:     Optional[float] = None
        jd_alignment_label:  Optional[str]   = None

        if jd_corpus:
            job_relevant_skills = [
                a["skill"] for a in assessments
                if (_normalize(a["skill"]) in jd_corpus)
                or any(kw in jd_corpus for kw in (a["evidence_keywords_found"] or []))
            ]
            # JD keywords not covered by any CV skill
            jd_words = set(re.findall(r"\b\w{4,}\b", jd_corpus))
            covered  = set()
            for a in assessments:
                covered.update(kw.lower() for kw in a.get("evidence_keywords_found", []))
                covered.add(_normalize(a["skill"]))
            missing_jd_skills = [w for w in sorted(jd_words) if w not in covered][:10]

            matched         = len(job_relevant_skills)
            alignment_score = round(matched / total, 3) if total > 0 else 0.0

            # Req 3.9: label — "closely aligned, partially aligned, or weakly aligned"
            if alignment_score >= 0.70:
                jd_alignment_label = "Closely Aligned"
            elif alignment_score >= 0.40:
                jd_alignment_label = "Partially Aligned"
            else:
                jd_alignment_label = "Weakly Aligned"

        # ── Interpretation ────────────────────────────────────────────────────
        strong_pct = round(summary["strongly_evidenced"] / total * 100) if total else 0
        unsup_pct  = round(summary["unsupported"]        / total * 100) if total else 0

        if strong_pct >= 60:
            interp = (
                f"Strong skill credibility: {strong_pct}% of claimed skills are backed by "
                f"concrete evidence across employment, publications, and/or education records."
            )
        elif unsup_pct >= 40:
            interp = (
                f"Caution: {unsup_pct}% of claimed skills have no supporting evidence "
                f"in the CV's job history, publications, or education. These may be overstated."
            )
        else:
            interp = (
                f"Moderate credibility: {summary['strongly_evidenced']} skill(s) strongly "
                f"evidenced, {summary['partially_evidenced']} partially, "
                f"{summary['weakly_evidenced']} weakly, {summary['unsupported']} unsupported."
            )

        if jd_alignment_label:
            interp += f" JD alignment: {jd_alignment_label} ({alignment_score * 100:.0f}%)."

        return {
            "total_skills":      total,
            "skill_assessments": assessments,
            "summary":           summary,
            # JD alignment (Req 3.9 Job Relevance of Skills)
            "job_relevant_skills": job_relevant_skills,
            "missing_jd_skills":   missing_jd_skills,
            "alignment_score":     alignment_score,
            "jd_alignment_label":  jd_alignment_label,
            # Breakdown by evidence source
            "skills_by_source": {
                "employment_evidenced":  sum(1 for a in assessments if "employment"   in a["evidence_sources"]),
                "publication_evidenced": sum(1 for a in assessments if "publications" in a["evidence_sources"]),
                "education_evidenced":   sum(1 for a in assessments if "education"    in a["evidence_sources"]),
            },
            "interpretation": interp,
        }