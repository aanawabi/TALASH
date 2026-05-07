"""
Extra Credit – Candidate Ranker
Produces a fully quantifiable ranking of all processed candidates based on
weighted scores across Education, Research, Experience, and Skills dimensions.
Each dimension is scored 0–100 and then combined using configurable weights.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import math


# ── Default dimension weights (sum = 1.0) ────────────────────────────────────
DEFAULT_WEIGHTS = {
    "education":   0.25,
    "research":    0.40,
    "experience":  0.25,
    "skills":      0.10,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


# ── Education score (0-100) ───────────────────────────────────────────────────

def _education_score(edu_analysis: Dict[str, Any]) -> float:
    score = 0.0

    # Highest degree
    degree = (edu_analysis.get("highest_degree") or "").lower()
    if "phd" in degree or "ph.d" in degree:
        score += 40
    elif "ms" in degree or "mphil" in degree or "m.s" in degree or "master" in degree:
        score += 28
    elif "bs" in degree or "bachelor" in degree:
        score += 18
    elif "14" in degree or "bsc" in degree:
        score += 12

    # Average academic performance
    avg_pct = edu_analysis.get("average_percentage")
    if avg_pct is not None:
        if avg_pct >= 85:
            score += 20
        elif avg_pct >= 75:
            score += 15
        elif avg_pct >= 65:
            score += 10
        elif avg_pct >= 50:
            score += 5

    # Foreign education bonus
    if edu_analysis.get("has_foreign_education"):
        score += 10

    # Institutional quality (if THE/QS ranking data present)
    ranking_data = edu_analysis.get("institutional_rankings", [])
    if ranking_data:
        best_rank = min(
            (r.get("rank_number", 9999) for r in ranking_data if r.get("rank_number")),
            default=9999,
        )
        if best_rank <= 100:
            score += 20
        elif best_rank <= 500:
            score += 12
        elif best_rank <= 1000:
            score += 6

    # Penalize unexplained gaps
    gaps = edu_analysis.get("unexplained_gaps", [])
    score -= len(gaps) * 3

    return _clamp(score)


# ── Research score (0-100) ────────────────────────────────────────────────────

def _research_score(res_analysis: Dict[str, Any]) -> float:
    score = 0.0

    impact = res_analysis.get("research_impact_score", 0) or 0
    # Normalize impact score (assume 50 is a strong researcher)
    score += _clamp(impact / 50 * 50, 0, 50)

    # Q1/Q2 publications
    hic = res_analysis.get("high_impact_count", 0) or 0
    score += min(hic * 4, 20)

    # Supervision
    phd = res_analysis.get("phd_supervised", 0) or 0
    ms = res_analysis.get("ms_supervised", 0) or 0
    score += min(phd * 3 + ms * 1, 10)

    # Patents
    patents = res_analysis.get("granted_patents", 0) or 0
    score += min(patents * 4, 12)

    # Books
    books = res_analysis.get("total_books", 0) or 0
    score += min(books * 3, 8)

    return _clamp(score)


# ── Experience score (0-100) ──────────────────────────────────────────────────

def _experience_score(exp_analysis: Dict[str, Any]) -> float:
    score = 0.0

    years = exp_analysis.get("total_years_experience") or 0
    score += min(years * 4, 40)  # 4 pts per year, cap 40

    trajectory = (exp_analysis.get("career_trajectory") or "").lower()
    if "ascending" in trajectory or "progressive" in trajectory:
        score += 20
    elif "stable" in trajectory or "lateral" in trajectory:
        score += 10

    positions = exp_analysis.get("number_of_positions") or 0
    score += min(positions * 3, 15)

    # Penalize unexplained professional gaps
    gaps = exp_analysis.get("unexplained_employment_gaps", [])
    score -= len(gaps) * 4

    # Consistency bonus (no overlaps detected)
    overlaps = exp_analysis.get("overlapping_roles", [])
    if not overlaps:
        score += 10

    return _clamp(score)


# ── Skills score (0-100) ──────────────────────────────────────────────────────

def _skills_score(skill_analysis: Optional[Dict[str, Any]], total_skills: int) -> float:
    if not skill_analysis:
        return _clamp(min(total_skills * 3, 40))

    summary = skill_analysis.get("summary", {})
    strong = summary.get("strongly_evidenced", 0)
    partial = summary.get("partially_evidenced", 0)
    total = skill_analysis.get("total_skills", 1) or 1

    credibility_score = ((strong * 2 + partial) / (total * 2)) * 70
    volume_score = min(total * 2, 30)
    return _clamp(credibility_score + volume_score)


# ── Main ranker ───────────────────────────────────────────────────────────────

class CandidateRanker:

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def score_candidate(
        self,
        candidate_name: str,
        candidate_id: str,
        edu_analysis: Dict[str, Any],
        res_analysis: Dict[str, Any],
        exp_analysis: Dict[str, Any],
        skill_analysis: Optional[Dict[str, Any]] = None,
        total_skills: int = 0,
    ) -> Dict[str, Any]:

        edu_score   = _education_score(edu_analysis)
        res_score   = _research_score(res_analysis)
        exp_score   = _experience_score(exp_analysis)
        skill_score = _skills_score(skill_analysis, total_skills)

        composite = (
            edu_score   * self.weights["education"]
            + res_score   * self.weights["research"]
            + exp_score   * self.weights["experience"]
            + skill_score * self.weights["skills"]
        )

        profile_tier = res_analysis.get("profile_tier", "unknown")

        return {
            "candidate_name":  candidate_name,
            "candidate_id":    candidate_id,
            "dimension_scores": {
                "education":   round(edu_score, 1),
                "research":    round(res_score, 1),
                "experience":  round(exp_score, 1),
                "skills":      round(skill_score, 1),
            },
            "composite_score": round(composite, 2),
            "weights_used":    self.weights,
            "profile_tier":    profile_tier,
        }

    def rank_candidates(
        self,
        candidates_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        candidates_data: list of dicts, each with keys:
          name, candidate_id, edu_analysis, res_analysis,
          exp_analysis, skill_analysis (optional), total_skills (optional)
        Returns ranked list with positions and interpretation.
        """
        scored: List[Dict[str, Any]] = []

        for c in candidates_data:
            result = self.score_candidate(
                candidate_name  = c.get("name", "Unknown"),
                candidate_id    = c.get("candidate_id", ""),
                edu_analysis    = c.get("edu_analysis", {}),
                res_analysis    = c.get("res_analysis", {}),
                exp_analysis    = c.get("exp_analysis", {}),
                skill_analysis  = c.get("skill_analysis"),
                total_skills    = c.get("total_skills", 0),
            )
            scored.append(result)

        # Sort descending by composite score
        scored.sort(key=lambda x: x["composite_score"], reverse=True)

        # Assign ranks
        for i, entry in enumerate(scored, 1):
            entry["rank"] = i

        # ── Aggregate stats for dashboard ─────────────────────────────────────
        scores = [s["composite_score"] for s in scored]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        # Per-dimension leaders
        dim_leaders = {}
        for dim in ("education", "research", "experience", "skills"):
            best = max(scored, key=lambda x: x["dimension_scores"].get(dim, 0), default=None)
            if best:
                dim_leaders[dim] = {
                    "name":  best["candidate_name"],
                    "score": best["dimension_scores"][dim],
                }

        return {
            "ranked_candidates": scored,
            "total_candidates":  len(scored),
            "aggregate": {
                "average_composite_score": avg_score,
                "highest_score":           max_score,
                "lowest_score":            min_score,
                "dimension_leaders":       dim_leaders,
            },
            "weights_used": self.weights,
        }
