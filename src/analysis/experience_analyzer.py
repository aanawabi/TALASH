"""
experience_analyzer.py    Module 3.8
======================================
Evaluates the candidate's professional experience, employment history,
career progression, and timeline consistency per project requirements.

Requirements covered:
  3.8-i-a  Overlap between Education and Employment
  3.8-i-b  Overlap between Multiple Jobs (concurrent roles)
  3.8-i-c  Professional Gaps (duration + flag)
  3.8-i-d  Gap Justification (education, research, etc.)
  3.8-i-e  Career Continuity and Progression
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from ..models.cv_models import ExtractedCV

_PRESENT_TOKENS = {"present", "current", "now", "ongoing", "till date", "to date"}

_LEGITIMATE_CONCURRENT_KEYWORDS = {
    "adjunct", "visiting", "consultant", "freelance", "part-time",
    "research assistant", "teaching assistant", " ta ", " ra ",
    "associate lecturer", "part time", "honorary",
}

_GAP_JUSTIFICATION_KEYWORDS = {
    "phd":          "Higher Education (PhD)",
    "ms ":          "Higher Education (MS)",
    "m.s":          "Higher Education (MS)",
    "mphil":        "Higher Education (MPhil)",
    "research":     "Research / Independent Research",
    "freelance":    "Freelancing / Consulting",
    "consult":      "Freelancing / Consulting",
    "entrepren":    "Entrepreneurship",
    "startup":      "Entrepreneurship",
    "training":     "Professional Training",
    "certif":       "Professional Training / Certification",
    "sabbatical":   "Sabbatical",
    "family":       "Family / Personal Leave",
    "medical":      "Medical / Health Leave",
}

_SENIORITY_MAP: Dict[str, int] = {
    "intern": 0,    "trainee": 0,
    "junior": 1,    "assistant": 2,     "associate": 3,
    "engineer": 4,  "analyst": 4,       "officer": 4,
    "executive": 4, "lecturer": 4,      "researcher": 4,
    "senior": 5,    "lead": 6,          "principal": 6,
    "assistant professor": 5,
    "associate professor": 6,
    "professor": 7,
    "manager": 7,   "head": 8,          "director": 9,
    "vp": 10,       "vice president": 10,
    "chief": 11,    "cto": 11,          "ceo": 11,    "dean": 11,
}

_GAP_FLAG_MONTHS = 3


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
    m = re.match(r"^([a-z]{3})[- ](\d{4})$", s)
    if m:
        month_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
                     "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        mon = month_map.get(m.group(1), 6)
        return datetime(int(m.group(2)), mon, 1)
    return None


def _years_between(start, end):
    if start is None or end is None:
        return None
    return round(max((end - start).days / 365.25, 0.0), 2)


def _months_between(start, end):
    if start is None or end is None:
        return None
    return round(max((end - start).days / 30.44, 0.0), 1)


def _seniority_score(title: str) -> int:
    tl = title.lower()
    score = 0
    for kw, val in _SENIORITY_MAP.items():
        if kw in tl:
            score = max(score, val)
    return score


def _is_current(r) -> bool:
    return r.is_current or bool(r.end_date and r.end_date.strip().lower() in _PRESENT_TOKENS)


# ── 3.8-i-a  Education–Employment Overlaps ───────────────────────────────────

def _detect_edu_employment_overlaps(cv: ExtractedCV) -> List[Dict[str, Any]]:
    overlaps = []
    edu_periods = []
    for e in cv.education:
        if e.start_year:
            edu_periods.append({
                "degree_title":  e.degree_title,
                "degree_level":  e.degree_level.value,
                "institution":   e.institution,
                "start":         datetime(e.start_year, 1, 1),
                "end":           datetime(e.end_year, 12, 31) if e.end_year else datetime.now(),
                "start_year":    e.start_year,
                "end_year":      e.end_year,
            })

    for job in cv.experience:
        j_start = _parse_date(job.start_date)
        cur = _is_current(job)
        j_end = datetime.now() if cur else _parse_date(job.end_date)
        if not j_start:
            continue
        job_title_l  = job.job_title.lower()
        emp_type_l   = (job.employment_type or "").lower()
        for edu in edu_periods:
            ov_start = max(j_start, edu["start"])
            ov_end   = min(j_end or datetime.now(), edu["end"])
            if ov_start >= ov_end:
                continue
            ov_months = round((ov_end - ov_start).days / 30.44, 1)
            legit = any(kw in job_title_l or kw in emp_type_l
                        for kw in _LEGITIMATE_CONCURRENT_KEYWORDS) \
                    or "part" in emp_type_l \
                    or "phd" in edu["degree_level"].lower()
            overlaps.append({
                "degree_title":         edu["degree_title"],
                "degree_level":         edu["degree_level"],
                "institution":          edu["institution"],
                "edu_period":           f"{edu['start_year']} – {edu.get('end_year','present')}",
                "job_title":            job.job_title,
                "organization":         job.organization,
                "job_period":           f"{job.start_date} – {'Present' if cur else job.end_date or '?'}",
                "overlap_months":       ov_months,
                "is_likely_legitimate": legit,
                "interpretation":       (
                    "Likely legitimate – part-time, research, or teaching role during studies"
                    if legit else
                    "Requires scrutiny – full-time job overlap with formal degree program"
                ),
            })
    return overlaps


# ── 3.8-i-b  Job–Job Overlaps ────────────────────────────────────────────────

def _detect_job_overlaps(cv: ExtractedCV) -> List[Dict[str, Any]]:
    jobs = []
    for r in cv.experience:
        start = _parse_date(r.start_date)
        cur   = _is_current(r)
        end   = datetime.now() if cur else _parse_date(r.end_date)
        if start:
            jobs.append({
                "job_title":       r.job_title,
                "organization":    r.organization,
                "employment_type": r.employment_type or "",
                "start":           start,
                "end":             end or datetime.now(),
                "start_str":       r.start_date,
                "end_str":         "Present" if cur else r.end_date or "?",
            })

    overlaps = []
    for i in range(len(jobs)):
        for j in range(i + 1, len(jobs)):
            a, b = jobs[i], jobs[j]
            ov_start = max(a["start"], b["start"])
            ov_end   = min(a["end"],   b["end"])
            if ov_start >= ov_end:
                continue
            ov_months = round((ov_end - ov_start).days / 30.44, 1)
            a_tl = a["job_title"].lower() + " " + a["employment_type"].lower()
            b_tl = b["job_title"].lower() + " " + b["employment_type"].lower()
            legit = any(kw in a_tl or kw in b_tl for kw in _LEGITIMATE_CONCURRENT_KEYWORDS)
            if legit:
                flag = "likely_legitimate"
                interp = "Concurrent roles appear legitimate (advisory, consulting, part-time, or academic appointment)"
            elif ov_months <= 2:
                flag = "transitional"
                interp = "Short overlap (≤2 months) – likely a transition period between roles"
            else:
                flag = "suspicious"
                interp = "Significant overlap between full-time positions – requires clarification"
            overlaps.append({
                "role_a":         f"{a['job_title']} at {a['organization']}",
                "role_b":         f"{b['job_title']} at {b['organization']}",
                "period_a":       f"{a['start_str']} → {a['end_str']}",
                "period_b":       f"{b['start_str']} → {b['end_str']}",
                "overlap_months": ov_months,
                "flag":           flag,
                "interpretation": interp,
            })
    return overlaps


# ── 3.8-i-c+d  Gaps + Justification ─────────────────────────────────────────

def _detect_employment_gaps(cv: ExtractedCV) -> List[Dict[str, Any]]:
    jobs_with_dates = []
    for r in cv.experience:
        start = _parse_date(r.start_date)
        cur   = _is_current(r)
        end   = datetime.now() if cur else _parse_date(r.end_date)
        if start:
            jobs_with_dates.append((start, end or start, r.job_title, r.organization))
    if len(jobs_with_dates) < 2:
        return []

    jobs_with_dates.sort(key=lambda x: x[0])

    all_cv_text = " ".join(filter(None, [
        cv.personal_info.full_name,
        " ".join(e.degree_title for e in cv.education),
        " ".join(r.job_title + " " + (r.organization or "") for r in cv.experience),
        " ".join(p.title for p in cv.journal_publications),
        " ".join(p.title for p in cv.conference_publications),
    ])).lower()

    edu_ranges = []
    for e in cv.education:
        if e.start_year and e.end_year:
            edu_ranges.append((
                datetime(e.start_year, 1, 1),
                datetime(e.end_year, 12, 31),
                e.degree_title,
                e.degree_level.value,
            ))

    gaps = []
    for i in range(1, len(jobs_with_dates)):
        prev_end   = jobs_with_dates[i - 1][1]
        curr_start = jobs_with_dates[i][0]
        if curr_start <= prev_end:
            continue
        gap_months = round((curr_start - prev_end).days / 30.44, 1)
        if gap_months < _GAP_FLAG_MONTHS:
            continue

        justification = None
        justification_source = None

        for edu_start, edu_end, deg_title, deg_level in edu_ranges:
            ov_s = max(prev_end, edu_start)
            ov_e = min(curr_start, edu_end)
            if ov_s < ov_e:
                justification = f"Covered by {deg_level} studies ({deg_title})"
                justification_source = "education_record"
                break

        if not justification:
            for keyword, label in _GAP_JUSTIFICATION_KEYWORDS.items():
                if keyword in all_cv_text:
                    justification = f"Possible: {label} (inferred from CV content)"
                    justification_source = "keyword_inference"
                    break

        if not justification:
            justification = "No justification found in CV"
            justification_source = "unexplained"

        severity = (
            "minor"      if gap_months <= 6
            else "moderate"   if gap_months <= 18
            else "significant"
        )

        gaps.append({
            "after_role":            f"{jobs_with_dates[i-1][2]} at {jobs_with_dates[i-1][3]}",
            "before_role":           f"{jobs_with_dates[i][2]} at {jobs_with_dates[i][3]}",
            "gap_start":             prev_end.strftime("%Y-%m"),
            "gap_end":               curr_start.strftime("%Y-%m"),
            "gap_months":            gap_months,
            "gap_years":             round(gap_months / 12, 1),
            "severity":              severity,
            "justification":         justification,
            "justification_source":  justification_source,
            "is_explained":          justification_source in ("education_record", "keyword_inference"),
        })
    return gaps


# ── 3.8-i-e  Career Progression ──────────────────────────────────────────────

def _assess_career_progression(role_details: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not role_details:
        return {
            "trajectory": "no_experience",
            "trajectory_label": "No Experience Recorded",
            "seniority_scores": [],
            "progression_narrative": "No professional experience records found.",
            "is_progressive": False,
        }

    sorted_roles = sorted(
        role_details,
        key=lambda rd: _parse_date(rd.get("start_date")) or datetime.min
    )
    scores = [rd["seniority_score"] for rd in sorted_roles]

    if len(scores) == 1:
        return {
            "trajectory": "single_position",
            "trajectory_label": "Single Position",
            "seniority_scores": list(zip([rd["job_title"] for rd in sorted_roles], scores)),
            "progression_narrative": (
                f"Only one role recorded: {sorted_roles[0]['job_title']} "
                f"at {sorted_roles[0]['organization']}. "
                "Career progression cannot be assessed with a single data point."
            ),
            "is_progressive": False,
        }

    ups   = sum(1 for i in range(len(scores) - 1) if scores[i + 1] > scores[i])
    downs = sum(1 for i in range(len(scores) - 1) if scores[i + 1] < scores[i])
    total = len(scores) - 1

    if ups > downs and ups >= total * 0.5:
        trajectory = "ascending"
        label      = "Ascending (Clear Growth)"
        narrative  = (
            "The candidate demonstrates a clear upward career trajectory, progressing "
            "from lower to higher seniority roles. This reflects professional maturity and growth."
        )
        progressive = True
    elif ups > 0 and downs > 0:
        trajectory = "lateral"
        label      = "Lateral / Mixed"
        narrative  = (
            "The candidate's career shows mixed movement – some progression alongside lateral "
            "transitions. This may reflect domain changes or specialisation shifts."
        )
        progressive = False
    elif ups == downs:
        trajectory = "lateral"
        label      = "Lateral (Similar Seniority)"
        narrative  = (
            "The candidate transitioned between roles of similar seniority. "
            "This may reflect specialisation rather than hierarchical growth."
        )
        progressive = False
    else:
        trajectory = "descending"
        label      = "Descending (Declining Seniority)"
        narrative  = (
            "The candidate's career shows a declining seniority pattern. "
            "This may reflect deliberate choices (e.g., moving from industry to academia) "
            "or sector changes that warrant clarification."
        )
        progressive = False

    return {
        "trajectory":            trajectory,
        "trajectory_label":      label,
        "seniority_scores":      list(zip([rd["job_title"] for rd in sorted_roles], scores)),
        "progression_narrative": narrative,
        "is_progressive":        progressive,
    }


# ── Main Analyzer Class ───────────────────────────────────────────────────────

class ExperienceAnalyzer:

    def analyze(self, cv: ExtractedCV) -> Dict[str, Any]:
        records = cv.experience
        if not records:
            return self._empty_result()

        now = datetime.now()

        role_details: List[Dict[str, Any]] = []
        for r in records:
            start = _parse_date(r.start_date)
            cur   = _is_current(r)
            end   = now if cur else _parse_date(r.end_date)
            dur_y = _years_between(start, end)
            role_details.append({
                "job_title":        r.job_title,
                "organization":     r.organization,
                "department":       r.department,
                "location":         r.location,
                "employment_type":  r.employment_type,
                "start_date":       r.start_date,
                "end_date":         r.end_date,
                "is_current":       cur,
                "duration_years":   dur_y,
                "duration_months":  round(dur_y * 12, 1) if dur_y is not None else None,
                "seniority_score":  _seniority_score(r.job_title),
                "responsibilities": r.responsibilities or [],
                "achievements":     r.achievements or [],
            })

        tenure_vals = [rd["duration_years"] for rd in role_details if rd["duration_years"] is not None]
        tenure_sum  = round(sum(tenure_vals), 2) if tenure_vals else None
        avg_tenure  = round(sum(tenure_vals) / len(tenure_vals), 2) if tenure_vals else None
        longest_val = max(tenure_vals) if tenure_vals else None
        longest_idx = next((i for i, rd in enumerate(role_details) if rd["duration_years"] == longest_val), None)
        longest_role = (
            f"{role_details[longest_idx]['job_title']} at {role_details[longest_idx]['organization']}"
            if longest_idx is not None else None
        )

        current_records = [rd for rd in role_details if rd["is_current"]]

        edu_emp_overlaps  = _detect_edu_employment_overlaps(cv)
        job_overlaps      = _detect_job_overlaps(cv)
        employment_gaps   = _detect_employment_gaps(cv)
        progression       = _assess_career_progression(role_details)

        suspicious_overlaps = [o for o in job_overlaps if o["flag"] == "suspicious"]
        unexplained_gaps    = [g for g in employment_gaps if not g["is_explained"]]
        explained_gaps      = [g for g in employment_gaps if g["is_explained"]]
        total_gap_months    = round(sum(g["gap_months"] for g in employment_gaps), 1)

        is_timeline_consistent = (
            len(suspicious_overlaps) == 0 and len(unexplained_gaps) == 0
        )
        consistency_flags = []
        if suspicious_overlaps:
            consistency_flags.append(f"{len(suspicious_overlaps)} suspicious job overlap(s) detected")
        if unexplained_gaps:
            consistency_flags.append(f"{len(unexplained_gaps)} unexplained employment gap(s)")
        scrutiny_count = sum(1 for o in edu_emp_overlaps if not o["is_likely_legitimate"])
        if scrutiny_count:
            consistency_flags.append(f"{scrutiny_count} education–employment overlap(s) requiring scrutiny")

        return {
            # Basic
            "total_years_experience":         tenure_sum,
            "number_of_positions":            len(records),
            "is_currently_employed":          bool(current_records),
            "current_position":               current_records[0]["job_title"]    if current_records else None,
            "current_organization":           current_records[0]["organization"] if current_records else None,
            "average_tenure_years":           avg_tenure,
            "longest_tenure_years":           round(longest_val, 2) if longest_val is not None else None,
            "longest_role":                   longest_role,
            "employment_types":               list({r.employment_type for r in records if r.employment_type}),
            "organizations":                  list({r.organization for r in records if r.organization}),
            "job_titles":                     [r.job_title for r in records],
            "role_details":                   role_details,
            # 3.8-i-a
            "edu_employment_overlaps":        edu_emp_overlaps,
            "edu_employment_overlap_count":   len(edu_emp_overlaps),
            "edu_employment_scrutiny_count":  scrutiny_count,
            # 3.8-i-b
            "job_overlaps":                   job_overlaps,
            "job_overlap_count":              len(job_overlaps),
            "suspicious_overlap_count":       len(suspicious_overlaps),
            # 3.8-i-c+d
            "employment_gaps":                employment_gaps,
            "total_gap_count":                len(employment_gaps),
            "unexplained_gap_count":          len(unexplained_gaps),
            "explained_gap_count":            len(explained_gaps),
            "total_gap_months":               total_gap_months,
            # 3.8-i-e
            "career_trajectory":              progression["trajectory"],
            "career_trajectory_label":        progression["trajectory_label"],
            "progression_narrative":          progression["progression_narrative"],
            "is_progressive":                 progression["is_progressive"],
            "seniority_scores":               progression["seniority_scores"],
            # Overall
            "timeline_consistent":            is_timeline_consistent,
            "consistency_flags":              consistency_flags,
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "total_years_experience":         None,
            "number_of_positions":            0,
            "is_currently_employed":          False,
            "current_position":               None,
            "current_organization":           None,
            "average_tenure_years":           None,
            "longest_tenure_years":           None,
            "longest_role":                   None,
            "employment_types":               [],
            "organizations":                  [],
            "job_titles":                     [],
            "role_details":                   [],
            "edu_employment_overlaps":        [],
            "edu_employment_overlap_count":   0,
            "edu_employment_scrutiny_count":  0,
            "job_overlaps":                   [],
            "job_overlap_count":              0,
            "suspicious_overlap_count":       0,
            "employment_gaps":                [],
            "total_gap_count":                0,
            "unexplained_gap_count":          0,
            "explained_gap_count":            0,
            "total_gap_months":               0,
            "career_trajectory":              "no_experience",
            "career_trajectory_label":        "No Experience Recorded",
            "progression_narrative":          "No professional experience records found.",
            "is_progressive":                 False,
            "seniority_scores":               [],
            "timeline_consistent":            True,
            "consistency_flags":              [],
        }