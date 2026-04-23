from typing import Dict, Any, List
from datetime import datetime
from ..models.cv_models import ExtractedCV, AuthorRole

# ── Weights for composite research impact score ─────────────────────────────
_QUARTILE_WEIGHTS = {"Q1": 4, "Q2": 3, "Q3": 2, "Q4": 1}
_JOURNAL_UNRANKED_WEIGHT = 0.5
_CONF_INDEXED_WEIGHT = 1.0
_CONF_UNINDEXED_WEIGHT = 0.3
_PHD_SUPERVISION_WEIGHT = 3.0
_MS_SUPERVISION_WEIGHT = 1.0
_PATENT_GRANTED_WEIGHT = 5.0
_PATENT_FILED_WEIGHT = 2.0
_BOOK_WEIGHT = 3.0

_LEAD_ROLES = {AuthorRole.FIRST_AUTHOR, AuthorRole.FIRST_AND_CORRESPONDING}
_CORR_ROLES = {AuthorRole.CORRESPONDING_AUTHOR, AuthorRole.FIRST_AND_CORRESPONDING}

_RECENT_YEARS = 3


class ResearchProfileAnalyzer:

    def analyze(self, cv: ExtractedCV) -> Dict[str, Any]:
        journals = cv.journal_publications
        conferences = cv.conference_publications
        supervisions = cv.supervisions
        patents = cv.patents
        books = cv.books
        current_year = datetime.now().year

        # ── Basic publication counts ──────────────────────────────────────────
        n_journals = len(journals)
        n_conferences = len(conferences)
        n_total = n_journals + n_conferences

        # Authorship roles
        first_author_j = sum(1 for p in journals if p.author_role in _LEAD_ROLES)
        corresponding_j = sum(1 for p in journals if p.author_role in _CORR_ROLES)
        first_author_c = sum(1 for p in conferences if p.author_role in _LEAD_ROLES)

        # Quartile breakdown
        q_dist = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "Unranked": 0}
        for p in journals:
            key = (p.quartile or "").upper()
            if key in q_dist:
                q_dist[key] += 1
            else:
                q_dist["Unranked"] += 1

        # Indexing
        wos_count = sum(1 for p in journals if p.is_wos_indexed)
        scopus_count = sum(1 for p in journals if p.is_scopus_indexed)
        indexed_conf = sum(1 for p in conferences if p.is_indexed)

        # Conference rank breakdown
        conf_rank_dist: Dict[str, int] = {}
        for p in conferences:
            r = p.conference_rank or "Unranked"
            conf_rank_dist[r] = conf_rank_dist.get(r, 0) + 1

        # Impact factor stats
        ifs = [p.impact_factor for p in journals if p.impact_factor is not None]
        avg_if = round(sum(ifs) / len(ifs), 3) if ifs else None
        max_if = max(ifs) if ifs else None

        # ── Supervision ───────────────────────────────────────────────────────
        phd_supervised = sum(
            1 for s in supervisions
            if "phd" in s.degree_level.lower() or "ph.d" in s.degree_level.lower()
        )
        ms_supervised = sum(
            1 for s in supervisions
            if "ms" in s.degree_level.lower() or "m.s" in s.degree_level.lower()
        )
        completed_sup = sum(
            1 for s in supervisions
            if s.status and "complet" in s.status.lower()
        )
        ongoing_sup = sum(
            1 for s in supervisions
            if s.status and "progress" in s.status.lower()
        )

        # ── Patents ───────────────────────────────────────────────────────────
        granted_patents = sum(
            1 for p in patents
            if p.status and "grant" in p.status.lower()
        )
        filed_patents = sum(
            1 for p in patents
            if p.status and ("filed" in p.status.lower() or "pending" in p.status.lower())
        )

        # ── Higher-level metric 1: Research Impact Score ──────────────────────
        # Weighted sum across all research output types
        impact_score = 0.0
        for p in journals:
            q = (p.quartile or "").upper()
            impact_score += _QUARTILE_WEIGHTS.get(q, _JOURNAL_UNRANKED_WEIGHT)
        for p in conferences:
            impact_score += _CONF_INDEXED_WEIGHT if p.is_indexed else _CONF_UNINDEXED_WEIGHT
        impact_score += phd_supervised * _PHD_SUPERVISION_WEIGHT
        impact_score += ms_supervised * _MS_SUPERVISION_WEIGHT
        impact_score += granted_patents * _PATENT_GRANTED_WEIGHT
        impact_score += filed_patents * _PATENT_FILED_WEIGHT
        impact_score += len(books) * _BOOK_WEIGHT
        impact_score = round(impact_score, 2)

        # ── Higher-level metric 2: Publication trend ──────────────────────────
        recent_threshold = current_year - _RECENT_YEARS
        all_pubs = journals + conferences
        recent_pubs = sum(
            1 for p in all_pubs
            if p.publication_year and p.publication_year >= recent_threshold
        )
        older_pubs = n_total - recent_pubs
        recency_ratio = round(recent_pubs / n_total, 2) if n_total > 0 else 0.0

        if n_total == 0:
            pub_trend = "no_publications"
        elif recency_ratio >= 0.6:
            pub_trend = "highly_active"
        elif recency_ratio >= 0.3:
            pub_trend = "moderately_active"
        else:
            pub_trend = "declining"

        # Publications by year (for timeline chart)
        pub_by_year: Dict[int, int] = {}
        for p in all_pubs:
            if p.publication_year:
                pub_by_year[p.publication_year] = pub_by_year.get(p.publication_year, 0) + 1

        # ── Higher-level metric 3: Collaboration index ────────────────────────
        # Fraction of publications where candidate is NOT the sole/first author
        if all_pubs:
            lead_count = sum(
                1 for p in all_pubs
                if p.author_position is not None and p.author_position == 1
            )
            collaboration_index = round(1 - (lead_count / len(all_pubs)), 2)
        else:
            collaboration_index = None

        # ── Higher-level metric 4: High-impact ratio ──────────────────────────
        high_impact_count = q_dist["Q1"] + q_dist["Q2"]
        high_impact_ratio = round(high_impact_count / n_journals, 2) if n_journals > 0 else None

        # ── Higher-level metric 5: Profile tier ──────────────────────────────
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

        return {
            # ── Basic metrics ──
            "total_publications": n_total,
            "total_journal_publications": n_journals,
            "total_conference_publications": n_conferences,
            "first_author_journal_count": first_author_j,
            "corresponding_author_journal_count": corresponding_j,
            "first_author_conference_count": first_author_c,
            "quartile_distribution": q_dist,
            "wos_indexed_count": wos_count,
            "scopus_indexed_count": scopus_count,
            "indexed_conference_count": indexed_conf,
            "conference_rank_distribution": conf_rank_dist,
            "average_impact_factor": avg_if,
            "max_impact_factor": max_if,
            "total_supervisions": len(supervisions),
            "phd_supervised": phd_supervised,
            "ms_supervised": ms_supervised,
            "completed_supervisions": completed_sup,
            "ongoing_supervisions": ongoing_sup,
            "total_patents": len(patents),
            "granted_patents": granted_patents,
            "filed_patents": filed_patents,
            "total_books": len(books),
            # ── Higher-level metrics ──
            "research_impact_score": impact_score,
            "publication_trend": pub_trend,
            "recent_publications_3yr": recent_pubs,
            "older_publications": older_pubs,
            "recency_ratio": recency_ratio,
            "publications_by_year": pub_by_year,
            "collaboration_index": collaboration_index,
            "high_impact_ratio": high_impact_ratio,
            "high_impact_count": high_impact_count,
            "profile_tier": profile_tier,
        }