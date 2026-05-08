"""
Module 3.7 – Co-Author Analyzer
=================================
Identifies collaboration patterns per requirement 3.7:
- extract list of co-authors from each publication
- identify repeated collaborators
- count frequency of same co-authors
- distinguish one-time vs long-term collaborations
- examine team size (small vs large groups)
- identify national vs international collaboration where possible
- detect possible student-supervisor relationships
- output: unique co-authors, frequent collaborators, avg team size,
          network size, proportion recurring, student-supervisor patterns,
          collaboration diversity score
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict

from ..models.cv_models import ExtractedCV


def _normalize_name(name: str) -> str:
    """
    Normalise an author name for deduplication.
    Strips punctuation (dots, commas), collapses whitespace, and lowercases.
    This ensures 'A. B. Smith', 'A B Smith', and 'AB Smith' all map to the
    same key so the same person is never counted twice.
    """
    import re as _re
    # Remove dots and commas (common in abbreviated names: "A. B. Smith")
    cleaned = _re.sub(r"[.,]", "", name)
    # Collapse multiple spaces
    cleaned = _re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def _name_parts(full_name: str) -> List[str]:
    return [p.lower() for p in (full_name or "").split() if len(p) > 1]


def _is_candidate(author: str, cand_parts: List[str]) -> bool:
    """
    True if the author string likely refers to the candidate themselves.

    Handles both full names ('Muhammad Ali Khan') and abbreviated forms
    ('M. A. Khan', 'M Khan', 'Khan') that LLMs sometimes produce for the
    first/corresponding author when parsing a publication list.
    """
    if not cand_parts:
        return False

    import re as _re
    al = _normalize_name(author)

    # Strategy 1: count how many candidate name parts appear in the author string
    # Require at least 2 matching parts (first + last, or last + initial)
    full_hits = sum(1 for p in cand_parts if p in al.split())
    if full_hits >= min(2, len(cand_parts)):
        return True

    # Strategy 2: last name must match, AND at least one initial from the
    # candidate's other name parts must match an initial in the author string.
    # Covers "M. Khan" when candidate is "Muhammad Ali Khan".
    last_name = cand_parts[-1]          # e.g. "khan"
    other_parts = cand_parts[:-1]       # e.g. ["muhammad", "ali"]

    if last_name in al.split():
        # Extract single-letter tokens from the author string
        initials_in_author = set(_re.findall(r"\b([a-z])\b", al))
        candidate_initials = {p[0] for p in other_parts if p}
        if candidate_initials & initials_in_author:
            return True

    return False


# ── Affiliation / country detection ──────────────────────────────────────────
# Common Pakistani institutions (national) — used for national vs international
_PAKISTANI_INSTITUTIONS = [
    "pakistan", "nust", "fast", "lums", "pu ", "punjab", "comsats", "uet",
    "gik", "itu ", "karachi", "lahore", "islamabad", "peshawar", "quetta",
    "seecs", "paf-iast", "air university", "bahria", "ned university",
]

def _guess_national(affiliation: str) -> Optional[bool]:
    """Return True if affiliation suggests Pakistan, False if clearly foreign, None if unknown."""
    if not affiliation:
        return None
    af_lower = affiliation.lower()
    if any(inst in af_lower for inst in _PAKISTANI_INSTITUTIONS):
        return True
    # Common foreign country markers
    foreign_markers = ["usa", "uk", "china", "germany", "france", "australia",
                       "canada", "italy", "japan", "korea", "netherlands", "sweden"]
    if any(m in af_lower for m in foreign_markers):
        return False
    return None


class CoAuthorAnalyzer:

    def analyze(self, cv: ExtractedCV) -> Dict[str, Any]:
        """
        Per requirement 3.7, outputs:
        - total_unique_coauthors
        - most_frequent_collaborators
        - average_authors_per_paper
        - collaboration_network_size
        - proportion_papers_with_recurring
        - possible student-supervisor collaboration patterns
        - collaboration_diversity_score
        - national vs international collaboration split
        """
        full_name  = cv.personal_info.full_name or ""
        cand_parts = _name_parts(full_name)

        journals    = cv.journal_publications
        conferences = cv.conference_publications
        all_pubs    = list(journals) + list(conferences)

        # Build supervised student name parts for cross-referencing (Req 3.7)
        student_name_parts: Dict[str, List[str]] = {}
        for sup in cv.supervisions:
            sname = sup.student_name
            parts = [p.lower() for p in sname.split() if len(p) > 2]
            if parts:
                student_name_parts[sname] = parts

        if not all_pubs:
            return {
                "total_unique_coauthors":          0,
                "total_publications_analyzed":     0,
                "average_authors_per_paper":       0,
                "most_frequent_collaborators":     [],
                "one_time_collaborators_count":    0,
                "recurring_collaborators_count":   0,
                "recurring_collaborator_names":    [],
                "collaboration_network_size":      0,
                "proportion_papers_with_recurring":0.0,
                "collaboration_diversity_score":   0.0,
                "avg_team_size_label":             "N/A",
                "student_supervisor_papers":       0,
                "student_collaborators":           [],
                "national_collaborations":         0,
                "international_collaborations":    0,
                "interpretation":                  "No publications found for co-author analysis.",
            }

        # ── Build co-author frequency map ─────────────────────────────────────
        coauthor_freq: Dict[str, int] = defaultdict(int)
        coauthor_papers: Dict[str, List[str]] = defaultdict(list)
        papers_author_counts: List[int] = []

        # For student-supervisor detection (Req 3.7)
        student_coauthor_papers: List[Dict[str, Any]] = []

        for pub in all_pubs:
            authors = getattr(pub, "authors", []) or []
            title   = getattr(pub, "title",   "") or ""

            papers_author_counts.append(len(authors))

            paper_student_authors = []
            for a in authors:
                if _is_candidate(a, cand_parts):
                    continue  # skip self
                norm = _normalize_name(a)
                if not norm:
                    continue
                coauthor_freq[norm] += 1
                coauthor_papers[norm].append(title)

                # Check if this co-author is a supervised student (Req 3.7)
                for sname, sparts in student_name_parts.items():
                    a_lower = a.lower()
                    if sum(1 for p in sparts if p in a_lower) >= min(2, len(sparts)):
                        paper_student_authors.append({"author": a, "student": sname})
                        break

            if paper_student_authors:
                student_coauthor_papers.append({
                    "title":           title,
                    "year":            getattr(pub, "publication_year", None),
                    "student_authors": paper_student_authors,
                    "candidate_role":  (pub.author_role.value if pub.author_role else None),
                })

        total_pubs    = len(all_pubs)
        total_coauth  = len(coauthor_freq)
        avg_authors   = round(sum(papers_author_counts) / total_pubs, 2) if total_pubs else 0

        # ── Classify recurring vs one-time (Req 3.7) ─────────────────────────
        recurring = {a: c for a, c in coauthor_freq.items() if c >= 2}
        one_time  = {a: c for a, c in coauthor_freq.items() if c == 1}

        top_collabs = sorted(coauthor_freq.items(), key=lambda x: -x[1])[:10]
        top_collabs_fmt = [{"name": n.title(), "papers": c} for n, c in top_collabs]
        recurring_names = [n.title() for n in sorted(recurring, key=lambda x: -recurring[x])][:10]

        # ── Proportion of papers with a recurring collaborator (Req 3.7) ──────
        recurring_set = set(recurring.keys())
        papers_with_recurring = 0
        for pub in all_pubs:
            authors = getattr(pub, "authors", []) or []
            if any(_normalize_name(a) in recurring_set for a in authors if not _is_candidate(a, cand_parts)):
                papers_with_recurring += 1
        prop_recurring = round(papers_with_recurring / total_pubs, 3) if total_pubs else 0.0

        # ── Collaboration diversity score (Req 3.7) ───────────────────────────
        # Measures uniqueness of collaborators relative to collaboration volume
        if total_pubs > 0 and avg_authors > 1:
            raw_div = total_coauth / (total_pubs * (avg_authors - 1))
            diversity_score = round(min(raw_div, 1.0), 3)
        else:
            diversity_score = 0.0

        # ── Team size label (Req 3.7: small vs large groups) ─────────────────
        if avg_authors <= 2:
            team_label = "Solo / Pair"
        elif avg_authors <= 4:
            team_label = "Small Teams (3-4)"
        elif avg_authors <= 7:
            team_label = "Medium Teams (5-7)"
        else:
            team_label = "Large Groups (8+)"

        # ── National vs international (Req 3.7) ──────────────────────────────
        # We attempt to infer from co-author names (limited without affiliation data)
        # More reliable if affiliation data is available in the CV
        national_count = international_count = unknown_count = 0
        for sup in cv.supervisions:
            nat = _guess_national(sup.institution or "")
            if nat is True:
                national_count += 1
            elif nat is False:
                international_count += 1

        # ── Student-supervisor collaboration patterns (Req 3.7) ───────────────
        unique_student_collaborators = list({
            sa["student"]
            for paper in student_coauthor_papers
            for sa in paper["student_authors"]
        })

        # ── Interpretation ────────────────────────────────────────────────────
        if total_coauth == 0:
            interp = "The candidate appears to publish independently with no co-authors recorded."
        elif len(recurring) == 0:
            interp = (
                f"The candidate has {total_coauth} unique co-authors, all one-time collaborations. "
                f"This suggests broad but shallow academic reach."
            )
        else:
            top_name = top_collabs_fmt[0]["name"] if top_collabs_fmt else "N/A"
            sup_note = (
                f" {len(student_coauthor_papers)} paper(s) co-authored with supervised student(s)."
                if student_coauthor_papers else ""
            )
            interp = (
                f"The candidate has {total_coauth} unique co-authors across {total_pubs} papers. "
                f"{len(recurring)} are recurring collaborators; '{top_name}' is the most frequent. "
                f"Average team size: {avg_authors} authors/paper ({team_label}). "
                f"Collaboration diversity score: {diversity_score:.2f}/1.00.{sup_note}"
            )

        return {
            # Core outputs (Req 3.7)
            "total_unique_coauthors":           total_coauth,
            "total_publications_analyzed":      total_pubs,
            "average_authors_per_paper":        avg_authors,
            "most_frequent_collaborators":      top_collabs_fmt,
            "one_time_collaborators_count":     len(one_time),
            "recurring_collaborators_count":    len(recurring),
            "recurring_collaborator_names":     recurring_names,
            "collaboration_network_size":       total_coauth,
            "proportion_papers_with_recurring": prop_recurring,
            "collaboration_diversity_score":    diversity_score,
            "avg_team_size_label":              team_label,
            # Student-supervisor patterns (Req 3.7)
            "student_supervisor_papers":        len(student_coauthor_papers),
            "student_supervisor_paper_details": student_coauthor_papers,
            "student_collaborators":            unique_student_collaborators,
            # National vs international (Req 3.7)
            "national_collaborations":          national_count,
            "international_collaborations":     international_count,
            # Interpretation
            "interpretation":                   interp,
        }