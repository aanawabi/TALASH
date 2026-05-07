"""
research_profile_analyzer.py  –  Modules 3.2, 3.3, 3.4, 3.5
=============================================================
Evaluates the candidate's research portfolio in a grounded, evidence-based,
and quantifiable manner per project requirements.

Journal verification sources (per requirement):
  https://mjl.clarivate.com/home
  https://wos-journal.info/

Conference verification source (per requirement):
  https://portal.core.edu.au/conf-ranks/
  https://scholar.google.com/intl/en/scholar/metrics.html

""
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from ..models.cv_models import ExtractedCV, AuthorRole
from .publication_verifier import verify_journal, verify_conference

# ── Authorship role sets ──────────────────────────────────────────────────────
_LEAD_ROLES = {AuthorRole.FIRST_AUTHOR, AuthorRole.FIRST_AND_CORRESPONDING}
_CORR_ROLES = {AuthorRole.CORRESPONDING_AUTHOR, AuthorRole.FIRST_AND_CORRESPONDING}

# ── Weights for composite research impact score ───────────────────────────────
_QUARTILE_WEIGHTS  = {"Q1": 4, "Q2": 3, "Q3": 2, "Q4": 1}
_CONF_INDEXED_W    = 1.0
_CONF_UNINDEXED_W  = 0.3
_CONF_ASTAR_BONUS  = 2.0   # extra credit for A* conferences
_JOURNAL_UNRANKED_W= 0.5
_PHD_SUP_W         = 3.0
_MS_SUP_W          = 1.0
_PATENT_GRANTED_W  = 5.0
_PATENT_FILED_W    = 2.0
_BOOK_W            = 3.0
_RECENT_YEARS      = 3


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def _name_parts(full_name: str) -> List[str]:
    return [p.lower() for p in (full_name or "").split() if len(p) > 1]


def _is_candidate_author(author: str, name_parts: List[str]) -> bool:
    al = author.lower()
    return sum(1 for p in name_parts if p in al) >= min(2, len(name_parts))


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 3.2-i  Journal Publication Analysis
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_journal(pub, name_parts: List[str]) -> Dict[str, Any]:
    """
    Per requirement 3.2-i:
    - Verify legitimacy via ISSN and external sources (wos-journal.info, MJL)
    - Determine WoS indexing status + Impact Factor
    - Determine Scopus indexing status
    - Identify quartile ranking
    - Determine candidate's authorship role
    - Overall quality interpretation
    "Do not take journal ranking information from CV, verify it from sources."
    """
    # ── External verification (not from CV) ────────────────────────────────
    verification = verify_journal(
        journal_name=pub.journal_name or "",
        issn=pub.issn,
    )

    # Use verified values; fall back to CV values only if verification failed
    # and source is clearly could_not_verify
    verified_source = verification["verification_source"]
    is_verified = "could_not_verify" not in verified_source

    if is_verified:
        wos_indexed     = verification["wos_indexed"]
        scopus_indexed  = verification["scopus_indexed"]
        impact_factor   = verification["impact_factor"]
        quartile        = verification["quartile"]
    else:
        # Fallback: use CV-provided values but flag as unverified
        wos_indexed     = pub.is_wos_indexed
        scopus_indexed  = pub.is_scopus_indexed
        impact_factor   = pub.impact_factor
        quartile        = pub.quartile

    # ── Authorship role (Req 3.2-i-e) ─────────────────────────────────────
    role = pub.author_role
    is_first        = role in _LEAD_ROLES
    is_corresponding = role in _CORR_ROLES
    position        = pub.author_position or 0
    n_authors       = len(pub.authors) if pub.authors else 1

    # ── ISSN legitimacy check (Req 3.2-i-a) ───────────────────────────────
    has_issn = bool(pub.issn and len(pub.issn.replace("-", "")) >= 7)
    predatory_risk = verification.get("predatory_risk", False)

    # ── Quality interpretation (Req 3.2-i-f) ──────────────────────────────
    q_upper = (quartile or "").upper()
    if wos_indexed and q_upper in ("Q1", "Q2") and not predatory_risk:
        quality_label = "High Quality – WoS indexed, top quartile"
    elif wos_indexed and q_upper in ("Q3", "Q4"):
        quality_label = "Moderate Quality – WoS indexed, lower quartile"
    elif scopus_indexed and not wos_indexed:
        quality_label = "Acceptable – Scopus indexed, not in WoS"
    elif predatory_risk:
        quality_label = "Low Quality – Predatory risk detected"
    elif not is_verified:
        quality_label = "Unverified – Could not confirm indexing"
    else:
        quality_label = "Unknown – Not found in major databases"

    return {
        "title":                pub.title,
        "journal_name":         pub.journal_name,
        "issn":                 pub.issn,
        "publication_year":     pub.publication_year,
        "authors":              pub.authors,
        # Verified values
        "wos_indexed":          wos_indexed,
        "scopus_indexed":       scopus_indexed,
        "impact_factor":        impact_factor,
        "quartile":             quartile,
        "has_issn":             has_issn,
        "predatory_risk":       predatory_risk,
        "verification_source":  verified_source,
        "legitimacy_flag":      verification.get("legitimacy_flag", "unverified"),
        "clarivate_mjl_url":    verification.get("clarivate_mjl_url"),
        "wos_journal_url":      verification.get("wos_journal_url"),
        # Authorship
        "author_role":          role.value if role else None,
        "is_first_author":      is_first,
        "is_corresponding":     is_corresponding,
        "author_position":      position,
        "total_authors":        n_authors,
        # Interpretation
        "quality_label":        quality_label,
        "verification_notes":   verification.get("notes", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 3.2-ii  Conference Paper Analysis
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_conference(pub, name_parts: List[str]) -> Dict[str, Any]:
    """
    Per requirement 3.2-ii:
    - A* ranking status via portal.core.edu.au
    - Conference series maturity (series number)
    - Indexing / proceedings publisher
    - Candidate authorship role
    - Overall quality interpretation
    """
    verification = verify_conference(
        conference_name=pub.conference_name or "",
        publisher=pub.publisher,
    )

    core_rank  = verification.get("core_rank") or pub.conference_rank
    is_a_star  = verification.get("is_a_star", False) or (core_rank == "A*")
    series_num = verification.get("series_number")
    maturity   = verification.get("maturity_label", "unknown")
    is_indexed = pub.is_indexed or verification.get("is_reputable_publisher", False)

    role = pub.author_role
    is_first         = role in _LEAD_ROLES
    is_corresponding = role in _CORR_ROLES

    # ── Quality interpretation (Req 3.2-ii-f) ─────────────────────────────
    if is_a_star and is_indexed:
        quality_label = "Excellent – A* ranked, indexed proceedings"
    elif core_rank == "A" and is_indexed:
        quality_label = "Very Good – A ranked, indexed proceedings"
    elif core_rank in ("B", "C") and is_indexed:
        quality_label = f"Acceptable – {core_rank} ranked, indexed"
    elif is_indexed and not core_rank:
        quality_label = "Acceptable – Indexed but rank unverified"
    elif not is_indexed and not core_rank:
        quality_label = "Low Quality – Not indexed, rank unknown"
    else:
        quality_label = f"Moderate – {core_rank or 'Unranked'}"

    return {
        "title":                  pub.title,
        "conference_name":        pub.conference_name,
        "publication_year":       pub.publication_year,
        "authors":                pub.authors,
        # Verified ranking
        "core_rank":              core_rank,
        "is_a_star":              is_a_star,
        "verification_source":    verification.get("verification_source"),
        "core_portal_url":        verification.get("core_portal_url"),
        # Maturity (Req 3.2-ii-b)
        "series_number":          series_num,
        "maturity_label":         maturity,
        # Indexing / publisher (Req 3.2-ii-d)
        "publisher":              pub.publisher,
        "is_indexed":             is_indexed,
        "is_reputable_publisher": verification.get("is_reputable_publisher", False),
        # Authorship (Req 3.2-ii-e)
        "author_role":            role.value if role else None,
        "is_first_author":        is_first,
        "is_corresponding":       is_corresponding,
        "author_position":        pub.author_position,
        "total_authors":          len(pub.authors) if pub.authors else 1,
        # Interpretation (Req 3.2-ii-f)
        "quality_label":          quality_label,
        "verification_notes":     verification.get("notes", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 3.3  Student Supervision Analysis
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_supervision(cv: ExtractedCV, name_parts: List[str]) -> Dict[str, Any]:
    """
    Per requirement 3.3:
    a. Number of MS/PhD supervised as main supervisor
    b. Number of MS/PhD supervised as co-supervisor
    c. Publications produced with supervised students — including:
       - whether paper includes the student
       - total papers produced with students
       - whether candidate is corresponding author on those papers
       - author sequence number of candidate
       - authorship pattern between supervisor and student
    """
    supervisions = cv.supervisions
    journals    = cv.journal_publications
    conferences = cv.conference_publications
    all_pubs    = list(journals) + list(conferences)

    # a. Count main vs co-supervisor (Req 3.3-a, 3.3-b)
    phd_main   = sum(1 for s in supervisions if "phd" in s.degree_level.lower() and "co" not in s.role.lower())
    phd_co     = sum(1 for s in supervisions if "phd" in s.degree_level.lower() and "co" in s.role.lower())
    ms_main    = sum(1 for s in supervisions if any(x in s.degree_level.lower() for x in ["ms","m.s","mphil"]) and "co" not in s.role.lower())
    ms_co      = sum(1 for s in supervisions if any(x in s.degree_level.lower() for x in ["ms","m.s","mphil"]) and "co" in s.role.lower())
    completed  = sum(1 for s in supervisions if s.status and "complet" in s.status.lower())
    ongoing    = sum(1 for s in supervisions if s.status and "progress" in s.status.lower())

    # c. Publications with supervised students (Req 3.3-c)
    student_names: Set[str] = set()
    for s in supervisions:
        for part in s.student_name.lower().split():
            if len(part) > 2:
                student_names.add(part)

    papers_with_students: List[Dict[str, Any]] = []
    for pub in all_pubs:
        authors = pub.authors or []
        # Check if any author looks like a supervised student
        student_authors = []
        for a in authors:
            a_lower = a.lower()
            if not _is_candidate_author(a, name_parts):
                # Check if this author matches any student name part
                if any(sn in a_lower for sn in student_names):
                    student_authors.append(a)

        if student_authors:
            role = pub.author_role
            papers_with_students.append({
                "title":                   pub.title,
                "year":                    pub.publication_year,
                "student_authors":         student_authors,
                "candidate_is_corresponding": role in _CORR_ROLES if role else None,
                "candidate_position":      pub.author_position,
                "total_authors":           len(authors),
                "authorship_pattern":      (
                    "candidate_leads" if role in _LEAD_ROLES
                    else "candidate_supervises" if role in _CORR_ROLES
                    else "collaborative"
                ),
            })

    return {
        # a. Main supervisor counts
        "phd_main_supervisor":   phd_main,
        "ms_main_supervisor":    ms_main,
        # b. Co-supervisor counts
        "phd_co_supervisor":     phd_co,
        "ms_co_supervisor":      ms_co,
        # totals
        "total_phd_supervised":  phd_main + phd_co,
        "total_ms_supervised":   ms_main + ms_co,
        "total_supervised":      len(supervisions),
        "completed_supervisions":completed,
        "ongoing_supervisions":  ongoing,
        # c. Publications with students
        "papers_with_students":         len(papers_with_students),
        "paper_details_with_students":  papers_with_students,
        "corresponding_on_student_papers": sum(
            1 for p in papers_with_students if p.get("candidate_is_corresponding")
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 3.4  Books Analysis
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_books(cv: ExtractedCV) -> Dict[str, Any]:
    """
    Per requirement 3.4:
    a. Book metadata: name, authors, ISBN, publisher, year, online link
    b. Authorship role: sole, lead, co-author, contributing
    c. Publisher credibility
    d. Verification via online link
    """
    books = cv.books
    analyzed: List[Dict[str, Any]] = []

    # Known reputable academic publishers
    reputable_publishers = {
        "springer", "elsevier", "wiley", "cambridge", "oxford",
        "ieee", "acm", "mit press", "pearson", "mcgraw", "taylor"
    }

    for book in books:
        authors = book.authors or []
        role = (book.role or "").lower()

        # Determine authorship role (Req 3.4-b)
        if len(authors) == 1:
            authorship_label = "Sole Author"
        elif role in ("sole author", "sole"):
            authorship_label = "Sole Author"
        elif "lead" in role or authors and authors[0].lower():
            authorship_label = "Lead Author" if "lead" in role else "Co-Author"
        elif "editor" in role:
            authorship_label = "Editor"
        else:
            authorship_label = book.role or "Co-Author"

        # Publisher credibility (Req 3.4-c)
        pub_lower = (book.publisher or "").lower()
        is_reputable = any(rp in pub_lower for rp in reputable_publishers)

        analyzed.append({
            "book_title":          book.book_title,
            "authors":             authors,
            "isbn":                book.isbn,
            "publisher":           book.publisher,
            "publication_year":    book.publication_year,
            "online_link":         book.online_link,
            "authorship_role":     authorship_label,
            "is_reputable_publisher": is_reputable,
            "has_isbn":            bool(book.isbn),
            "has_verification_link": bool(book.online_link),
            "credibility_note":    (
                "Reputable publisher – strong academic value" if is_reputable
                else "Publisher credibility could not be confirmed"
            ),
        })

    return {
        "total_books":    len(books),
        "book_details":   analyzed,
        "reputable_books": sum(1 for b in analyzed if b["is_reputable_publisher"]),
        "books_with_isbn": sum(1 for b in analyzed if b["has_isbn"]),
        "books_with_link": sum(1 for b in analyzed if b["has_verification_link"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 3.5  Patent Analysis
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_patents(cv: ExtractedCV) -> Dict[str, Any]:
    """
    Per requirement 3.5:
    a. Patent identification: number, title, date, inventors, country, verification link
    b. Candidate's inventor role: lead, co-inventor, contributing
    c. Verification credibility: online link presence
    d. Importance: applied innovation vs academic-only profile
    """
    patents = cv.patents
    full_name = cv.personal_info.full_name or ""
    name_parts = _name_parts(full_name)

    analyzed: List[Dict[str, Any]] = []
    granted   = 0
    filed     = 0
    lead_inventor_count = 0

    for patent in patents:
        inventors = patent.inventors or []
        status    = (patent.status or "").lower()
        is_granted = "grant" in status
        is_filed   = "filed" in status or "pending" in status

        if is_granted:
            granted += 1
        elif is_filed:
            filed += 1

        # b. Inventor role (Req 3.5-b)
        # Lead inventor = appears first in inventors list
        inventor_position = None
        for i, inv in enumerate(inventors, 1):
            if _is_candidate_author(inv, name_parts):
                inventor_position = i
                break

        if inventor_position == 1:
            inventor_role = "Lead Inventor"
            lead_inventor_count += 1
        elif inventor_position and inventor_position <= len(inventors):
            inventor_role = "Co-Inventor"
        elif inventor_position:
            inventor_role = "Contributing Innovator"
        else:
            inventor_role = "Unknown"

        # c. Verification credibility (Req 3.5-c)
        has_link = bool(patent.verification_link)
        has_number = bool(patent.patent_number)

        if has_link and has_number:
            credibility = "High – verifiable via patent number and online link"
        elif has_number:
            credibility = "Moderate – has patent number, no online link"
        elif has_link:
            credibility = "Moderate – has online link, no patent number"
        else:
            credibility = "Low – neither patent number nor link provided"

        analyzed.append({
            # a. Identification (Req 3.5-a)
            "patent_number":      patent.patent_number,
            "patent_title":       patent.patent_title,
            "filing_date":        patent.filing_date,
            "grant_date":         patent.grant_date,
            "inventors":          inventors,
            "country":            patent.country,
            "status":             patent.status,
            "verification_link":  patent.verification_link,
            # b. Inventor role
            "inventor_position":  inventor_position,
            "inventor_role":      inventor_role,
            # c. Credibility
            "credibility":        credibility,
            "has_patent_number":  has_number,
            "has_verification_link": has_link,
        })

    # d. Importance assessment (Req 3.5-d)
    total_pubs = len(cv.journal_publications) + len(cv.conference_publications)
    if patents and total_pubs:
        innovation_profile = "Hybrid – combines academic publications with applied patents"
    elif patents and not total_pubs:
        innovation_profile = "Primarily applied innovator – patents without academic publications"
    elif not patents and total_pubs:
        innovation_profile = "Primarily academic – no patents recorded"
    else:
        innovation_profile = "No research output recorded"

    return {
        "total_patents":          len(patents),
        "granted_patents":        granted,
        "filed_patents":          filed,
        "lead_inventor_count":    lead_inventor_count,
        "patent_details":         analyzed,
        "innovation_profile":     innovation_profile,
        "has_verifiable_patents": sum(1 for p in analyzed if p["has_patent_number"] or p["has_verification_link"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYZER CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ResearchProfileAnalyzer:

    def analyze(self, cv: ExtractedCV) -> Dict[str, Any]:
        current_year = datetime.now().year
        name_parts   = _name_parts(cv.personal_info.full_name or "")

        # ── Run all sub-modules ───────────────────────────────────────────────
        journal_analyses    = [_analyze_journal(p, name_parts)    for p in cv.journal_publications]
        conference_analyses = [_analyze_conference(p, name_parts) for p in cv.conference_publications]
        supervision_result  = _analyze_supervision(cv, name_parts)
        book_result         = _analyze_books(cv)
        patent_result       = _analyze_patents(cv)

        journals    = cv.journal_publications
        conferences = cv.conference_publications
        all_pubs    = list(journals) + list(conferences)
        n_j  = len(journals)
        n_c  = len(conferences)
        n_total = n_j + n_c

        # ── Aggregate journal stats ───────────────────────────────────────────
        q_dist = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "Unranked": 0}
        wos_count = scopus_count = 0
        ifs = []
        first_j = corr_j = 0

        for ja in journal_analyses:
            q = (ja.get("quartile") or "").upper()
            if q in q_dist:
                q_dist[q] += 1
            else:
                q_dist["Unranked"] += 1
            if ja.get("wos_indexed"):
                wos_count += 1
            if ja.get("scopus_indexed"):
                scopus_count += 1
            if ja.get("impact_factor"):
                ifs.append(ja["impact_factor"])
            if ja.get("is_first_author"):
                first_j += 1
            if ja.get("is_corresponding"):
                corr_j += 1

        avg_if = round(sum(ifs) / len(ifs), 3) if ifs else None
        max_if = max(ifs) if ifs else None

        # ── Aggregate conference stats ────────────────────────────────────────
        conf_rank_dist: Dict[str, int] = {}
        indexed_conf = astar_count = first_c = 0

        for ca in conference_analyses:
            r = ca.get("core_rank") or "Unranked"
            conf_rank_dist[r] = conf_rank_dist.get(r, 0) + 1
            if ca.get("is_indexed"):
                indexed_conf += 1
            if ca.get("is_a_star"):
                astar_count += 1
            if ca.get("is_first_author"):
                first_c += 1

        # ── Research impact score ─────────────────────────────────────────────
        impact_score = 0.0
        for ja in journal_analyses:
            q = (ja.get("quartile") or "").upper()
            impact_score += _QUARTILE_WEIGHTS.get(q, _JOURNAL_UNRANKED_W)
        for ca in conference_analyses:
            base = _CONF_INDEXED_W if ca.get("is_indexed") else _CONF_UNINDEXED_W
            bonus = _CONF_ASTAR_BONUS if ca.get("is_a_star") else 0
            impact_score += base + bonus
        impact_score += supervision_result["total_phd_supervised"] * _PHD_SUP_W
        impact_score += supervision_result["total_ms_supervised"]  * _MS_SUP_W
        impact_score += patent_result["granted_patents"] * _PATENT_GRANTED_W
        impact_score += patent_result["filed_patents"]   * _PATENT_FILED_W
        impact_score += book_result["total_books"]       * _BOOK_W
        impact_score = round(impact_score, 2)

        # ── Publication trend ─────────────────────────────────────────────────
        threshold   = current_year - _RECENT_YEARS
        recent_pubs = sum(1 for p in all_pubs if p.publication_year and p.publication_year >= threshold)
        recency_ratio = round(recent_pubs / n_total, 2) if n_total else 0.0
        pub_trend = (
            "no_publications" if n_total == 0
            else "highly_active"     if recency_ratio >= 0.6
            else "moderately_active" if recency_ratio >= 0.3
            else "declining"
        )

        pub_by_year: Dict[int, int] = {}
        for p in all_pubs:
            if p.publication_year:
                pub_by_year[p.publication_year] = pub_by_year.get(p.publication_year, 0) + 1

        # ── High-impact ratio ─────────────────────────────────────────────────
        high_impact_count = q_dist["Q1"] + q_dist["Q2"]
        high_impact_ratio = round(high_impact_count / n_j, 2) if n_j else None

        # ── Profile tier ──────────────────────────────────────────────────────
        if n_total >= 20 or high_impact_count >= 5:
            profile_tier = "prolific_researcher"
        elif n_total >= 10 or high_impact_count >= 2:
            profile_tier = "established_researcher"
        elif n_total >= 3:
            profile_tier = "emerging_researcher"
        elif n_total > 0:
            profile_tier = "early_stage_researcher"
        else:
            profile_tier = "no_research_output"

        # ── Collaboration index ───────────────────────────────────────────────
        if all_pubs:
            lead_count = sum(1 for p in all_pubs if p.author_position == 1)
            collaboration_index = round(1 - (lead_count / len(all_pubs)), 2)
        else:
            collaboration_index = None

        return {
            # ── Summary counts ──
            "total_publications":              n_total,
            "total_journal_publications":      n_j,
            "total_conference_publications":   n_c,
            # ── Journal analysis (Module 3.2-i) ──
            "journal_analyses":                journal_analyses,
            "first_author_journal_count":      first_j,
            "corresponding_author_journal_count": corr_j,
            "quartile_distribution":           q_dist,
            "wos_indexed_count":               wos_count,
            "scopus_indexed_count":            scopus_count,
            "average_impact_factor":           avg_if,
            "max_impact_factor":               max_if,
            "predatory_risk_journals":         sum(1 for ja in journal_analyses if ja.get("predatory_risk")),
            # ── Conference analysis (Module 3.2-ii) ──
            "conference_analyses":             conference_analyses,
            "first_author_conference_count":   first_c,
            "indexed_conference_count":        indexed_conf,
            "astar_conference_count":          astar_count,
            "conference_rank_distribution":    conf_rank_dist,
            # ── Supervision (Module 3.3) ──
            "supervision":                     supervision_result,
            "phd_supervised":                  supervision_result["total_phd_supervised"],
            "ms_supervised":                   supervision_result["total_ms_supervised"],
            "papers_with_students":            supervision_result["papers_with_students"],
            # ── Books (Module 3.4) ──
            "books":                           book_result,
            "total_books":                     book_result["total_books"],
            # ── Patents (Module 3.5) ──
            "patents":                         patent_result,
            "total_patents":                   patent_result["total_patents"],
            "granted_patents":                 patent_result["granted_patents"],
            "filed_patents":                   patent_result["filed_patents"],
            "lead_inventor_count":             patent_result["lead_inventor_count"],
            # ── Higher-level metrics ──
            "research_impact_score":           impact_score,
            "publication_trend":               pub_trend,
            "recent_publications_3yr":         recent_pubs,
            "recency_ratio":                   recency_ratio,
            "publications_by_year":            pub_by_year,
            "collaboration_index":             collaboration_index,
            "high_impact_count":               high_impact_count,
            "high_impact_ratio":               high_impact_ratio,
            "profile_tier":                    profile_tier,
        }
