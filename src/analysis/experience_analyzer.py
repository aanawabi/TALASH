from typing import Optional, List, Dict, Any
from datetime import datetime
import re
from ..models.cv_models import ExtractedCV

_PRESENT_TOKENS = {"present", "current", "now", "ongoing", "till date", "to date"}

_SENIORITY_MAP = {
    "intern": 0, "trainee": 0,
    "junior": 1, "assistant": 2, "associate": 3,
    "engineer": 4, "analyst": 4, "officer": 4, "executive": 4, "lecturer": 4,
    "senior": 5, "lead": 6, "principal": 6,
    "assistant professor": 5, "associate professor": 6, "professor": 7,
    "manager": 7, "head": 8, "director": 9,
    "vp": 10, "vice president": 10,
    "chief": 11, "cto": 11, "ceo": 11, "dean": 11,
}


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    s = date_str.strip().lower()
    if s in _PRESENT_TOKENS:
        return datetime.now()
    m = re.match(r"^(\d{4})-(\d{2})$", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), 1)
    m = re.match(r"^(\d{4})$", s)
    if m:
        return datetime(int(m.group(1)), 6, 1)
    return None


def _years_between(start: Optional[datetime], end: Optional[datetime]) -> Optional[float]:
    if start is None or end is None:
        return None
    diff = (end - start).days / 365.25
    return round(max(diff, 0.0), 2)


def _seniority_score(title: str) -> int:
    tl = title.lower()
    score = 0
    for kw, val in _SENIORITY_MAP.items():
        if kw in tl:
            score = max(score, val)
    return score


class ExperienceAnalyzer:

    def analyze(self, cv: ExtractedCV) -> Dict[str, Any]:
        records = cv.experience
        if not records:
            return self._empty_result()

        now = datetime.now()

        # Identify current roles
        current_records = [
            r for r in records
            if r.is_current or (
                r.end_date and r.end_date.strip().lower() in _PRESENT_TOKENS
            )
        ]

        # Compute per-role durations
        role_durations: List[Dict[str, Any]] = []
        for r in records:
            start = _parse_date(r.start_date)
            is_current = r.is_current or (r.end_date and r.end_date.strip().lower() in _PRESENT_TOKENS)
            end = now if is_current else _parse_date(r.end_date)
            duration = _years_between(start, end)
            role_durations.append({
                "job_title": r.job_title,
                "organization": r.organization,
                "start_date": r.start_date,
                "end_date": r.end_date,
                "is_current": is_current,
                "duration_years": duration,
                "seniority_score": _seniority_score(r.job_title),
            })

        # Total experience: prefer sum of individual durations (more accurate than span).
        # Fall back to span only when no individual durations are available.
        tenure_sum = sum(rd["duration_years"] for rd in role_durations if rd["duration_years"] is not None)
        dated_count = sum(1 for rd in role_durations if rd["duration_years"] is not None)
        undated_current = any(
            rd["is_current"] and rd["duration_years"] is None for rd in role_durations
        )

        if dated_count > 0:
            total_years = round(tenure_sum, 2)
        else:
            # Absolute fallback: span from earliest known start to latest known end
            all_starts = [_parse_date(r.start_date) for r in records if r.start_date]
            all_ends = []
            for r in records:
                is_c = r.is_current or (r.end_date and r.end_date.strip().lower() in _PRESENT_TOKENS)
                all_ends.append(now if is_c else _parse_date(r.end_date))
            valid_starts = [d for d in all_starts if d]
            valid_ends = [d for d in all_ends if d]
            total_years = round((max(valid_ends) - min(valid_starts)).days / 365.25, 2) if (valid_starts and valid_ends) else None

        # Tenure stats from per-role durations
        tenure_vals = [rd["duration_years"] for rd in role_durations if rd["duration_years"] is not None]
        avg_tenure = round(sum(tenure_vals) / len(tenure_vals), 2) if tenure_vals else None
        longest_val = max(tenure_vals) if tenure_vals else None
        longest_tenure = round(longest_val, 2) if longest_val is not None else None

        longest_role = None
        if role_durations and tenure_vals:
            idx = next(
                (i for i, rd in enumerate(role_durations) if rd["duration_years"] == longest_val),
                0
            )
            r = role_durations[idx]
            longest_role = f"{r['job_title']} at {r['organization']}"

        # Career trajectory based on seniority over time
        # Roles with no start date sort to the end (assumed recent/current)
        sorted_roles = sorted(
            role_durations,
            key=lambda rd: _parse_date(rd["start_date"]) or datetime.max
        )
        scores = [rd["seniority_score"] for rd in sorted_roles]
        trajectory = "insufficient_data"
        if len(scores) >= 2:
            ups = sum(1 for i in range(len(scores) - 1) if scores[i + 1] > scores[i])
            downs = sum(1 for i in range(len(scores) - 1) if scores[i + 1] < scores[i])
            if ups > downs:
                trajectory = "ascending"
            elif downs > ups:
                trajectory = "descending"
            else:
                trajectory = "lateral"
        elif len(scores) == 1:
            trajectory = "single_position"

        # Employment type and organization diversity
        emp_types = list({r.employment_type for r in records if r.employment_type})
        organizations = list({r.organization for r in records if r.organization})
        job_titles = [r.job_title for r in records]

        current_position = current_records[0].job_title if current_records else None
        current_org = current_records[0].organization if current_records else None

        return {
            "total_years_experience": total_years,
            "number_of_positions": len(records),
            "is_currently_employed": len(current_records) > 0,
            "current_position": current_position,
            "current_organization": current_org,
            "average_tenure_years": avg_tenure,
            "longest_tenure_years": longest_tenure,
            "longest_role": longest_role,
            "career_trajectory": trajectory,
            "employment_types": emp_types,
            "organizations": organizations,
            "job_titles": job_titles,
            "role_details": role_durations,
            "has_undated_current_role": undated_current,
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "total_years_experience": None,
            "number_of_positions": 0,
            "is_currently_employed": False,
            "current_position": None,
            "current_organization": None,
            "average_tenure_years": None,
            "longest_tenure_years": None,
            "longest_role": None,
            "career_trajectory": "no_experience",
            "employment_types": [],
            "organizations": [],
            "job_titles": [],
            "role_details": [],
            "has_undated_current_role": False,
        }