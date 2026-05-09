from __future__ import annotations
import re
from typing import Optional, List, Dict, Any, Tuple
from ..models.cv_models import ExtractedCV, DegreeLevel

# ── Degree metadata ───────────────────────────────────────────────────────────

DEGREE_RANK: Dict[DegreeLevel, int] = {
    DegreeLevel.SSC: 1,
    DegreeLevel.HSSC: 2,
    DegreeLevel.BACHELOR_14: 3,
    DegreeLevel.BACHELOR_16: 4,
    DegreeLevel.MASTER_16: 5,
    DegreeLevel.MASTER_18: 6,
    DegreeLevel.PHD: 7,
    DegreeLevel.OTHER: 0,
}

DEGREE_LABELS: Dict[DegreeLevel, str] = {
    DegreeLevel.SSC: "SSC/Matric",
    DegreeLevel.HSSC: "HSSC/Intermediate",
    DegreeLevel.BACHELOR_14: "Bachelor (14-year)",
    DegreeLevel.BACHELOR_16: "Bachelor (16-year)",
    DegreeLevel.MASTER_16: "Master (16-year)",
    DegreeLevel.MASTER_18: "Master (18-year)",
    DegreeLevel.PHD: "PhD",
    DegreeLevel.OTHER: "Other",
}

PAKISTAN_IDENTIFIERS = {"pakistan", "pk", ""}

# ── QS / THE University Rankings (static lookup) ─────────────────────────────
# Format: normalized_key → (qs_rank, official_name)
# Sources: QS World University Rankings 2024 (top universities + major Pakistani ones)

_QS_DB: Dict[str, Tuple[int, str]] = {
    # Top 10 global
    "massachusetts institute of technology": (1,  "Massachusetts Institute of Technology"),
    "mit":                                   (1,  "Massachusetts Institute of Technology"),
    "imperial college london":               (2,  "Imperial College London"),
    "university of oxford":                  (3,  "University of Oxford"),
    "oxford":                                (3,  "University of Oxford"),
    "university of cambridge":               (5,  "University of Cambridge"),
    "cambridge":                             (5,  "University of Cambridge"),
    "harvard university":                    (4,  "Harvard University"),
    "harvard":                               (4,  "Harvard University"),
    "stanford university":                   (5,  "Stanford University"),
    "stanford":                              (5,  "Stanford University"),
    "eth zurich":                            (7,  "ETH Zurich"),
    "national university of singapore":      (8,  "National University of Singapore"),
    "nus":                                   (8,  "National University of Singapore"),
    "university college london":             (9,  "University College London"),
    "ucl":                                   (9,  "University College London"),
    "university of california berkeley":     (10, "UC Berkeley"),
    "uc berkeley":                           (10, "UC Berkeley"),
    # 11–50
    "california institute of technology":    (11, "California Institute of Technology"),
    "caltech":                               (11, "California Institute of Technology"),
    "university of chicago":                 (11, "University of Chicago"),
    "carnegie mellon university":            (52, "Carnegie Mellon University"),
    "columbia university":                   (22, "Columbia University"),
    "yale university":                       (16, "Yale University"),
    "princeton university":                  (17, "Princeton University"),
    "cornell university":                    (13, "Cornell University"),
    "university of pennsylvania":            (14, "University of Pennsylvania"),
    "upenn":                                 (14, "University of Pennsylvania"),
    "johns hopkins university":              (31, "Johns Hopkins University"),
    "university of michigan":                (23, "University of Michigan"),
    "duke university":                       (66, "Duke University"),
    "northwestern university":               (46, "Northwestern University"),
    "university of toronto":                 (21, "University of Toronto"),
    "university of edinburgh":               (22, "University of Edinburgh"),
    "edinburgh":                             (22, "University of Edinburgh"),
    "university of manchester":              (32, "University of Manchester"),
    "manchester":                            (32, "University of Manchester"),
    "london school of economics":            (45, "London School of Economics"),
    "lse":                                   (45, "London School of Economics"),
    "kings college london":                  (40, "King's College London"),
    "university of warwick":                 (67, "University of Warwick"),
    "university of bristol":                 (55, "University of Bristol"),
    "university of glasgow":                 (80, "University of Glasgow"),
    "university of southampton":             (91, "University of Southampton"),
    "university of leeds":                   (92, "University of Leeds"),
    "university of sheffield":               (104,"University of Sheffield"),
    "university of birmingham":              (84, "University of Birmingham"),
    "university of nottingham":              (103,"University of Nottingham"),
    "durham university":                     (78, "Durham University"),
    "university of sydney":                  (19, "University of Sydney"),
    "university of melbourne":               (14, "University of Melbourne"),
    "australian national university":        (30, "Australian National University"),
    "anu":                                   (30, "Australian National University"),
    "university of queensland":              (40, "University of Queensland"),
    "monash university":                     (42, "Monash University"),
    "university of new south wales":         (19, "UNSW Sydney"),
    "unsw":                                  (19, "UNSW Sydney"),
    "tsinghua university":                   (25, "Tsinghua University"),
    "peking university":                     (17, "Peking University"),
    "nanyang technological university":      (26, "Nanyang Technological University"),
    "ntu":                                   (26, "Nanyang Technological University"),
    "seoul national university":             (41, "Seoul National University"),
    "korea advanced institute of science":   (42, "KAIST"),
    "kaist":                                 (42, "KAIST"),
    "university of tokyo":                   (28, "University of Tokyo"),
    "tokyo":                                 (28, "University of Tokyo"),
    "kyoto university":                      (46, "Kyoto University"),
    "technische universitat munchen":        (37, "Technical University of Munich"),
    "tu munich":                             (37, "Technical University of Munich"),
    "rwth aachen university":                (98, "RWTH Aachen University"),
    "epfl":                                  (16, "EPFL"),
    "ecole polytechnique federale":          (16, "EPFL"),
    # Pakistan universities
    "national university of sciences and technology": (400, "NUST"),
    "nust":                                  (400, "NUST"),
    "lahore university of management sciences": (400, "LUMS"),
    "lums":                                  (400, "LUMS"),
    "aga khan university":                   (451, "Aga Khan University"),
    "quaid i azam university":               (501, "Quaid-i-Azam University"),
    "qau":                                   (501, "Quaid-i-Azam University"),
    "university of the punjab":              (601, "University of the Punjab"),
    "punjab university":                     (601, "University of the Punjab"),
    "pu lahore":                             (601, "University of the Punjab"),
    "university of engineering and technology lahore": (601, "UET Lahore"),
    "uet lahore":                            (601, "UET Lahore"),
    "uet":                                   (601, "UET Lahore"),
    "comsats university":                    (601, "COMSATS University Islamabad"),
    "comsats":                               (601, "COMSATS University Islamabad"),
    "university of karachi":                 (701, "University of Karachi"),
    "karachi university":                    (701, "University of Karachi"),
    "university of agriculture faisalabad":  (701, "University of Agriculture Faisalabad"),
    "bahria university":                     (801, "Bahria University"),
    "air university":                        (801, "Air University"),
    "ghulam ishaq khan institute":           (801, "GIK Institute"),
    "giki":                                  (801, "GIK Institute"),
    "institute of business administration":  (801, "IBA Karachi"),
    "iba karachi":                           (801, "IBA Karachi"),
    "fast national university":              (801, "FAST-NUCES"),
    "fast nuces":                            (801, "FAST-NUCES"),
    "nu fast":                               (801, "FAST-NUCES"),
    "islamia university of bahawalpur":      (801, "Islamia University Bahawalpur"),
    "university of peshawar":                (801, "University of Peshawar"),
}

_NOISE_WORDS = re.compile(r'\b(the|of|and|at|in|for|&)\b', re.IGNORECASE)


def _normalize_institution(name: str) -> str:
    n = name.lower().strip()
    n = _NOISE_WORDS.sub(' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n


def _lookup_qs(institution: Optional[str]) -> Optional[Dict[str, Any]]:
    if not institution:
        return None
    norm = _normalize_institution(institution)
    # Exact match
    if norm in _QS_DB:
        rank, official = _QS_DB[norm]
        return _format_ranking(official, rank)
    # Substring match: any key that appears in the normalized name
    for key, (rank, official) in _QS_DB.items():
        if key in norm or norm in key:
            return _format_ranking(official, rank)
    return None


def _format_ranking(official: str, rank: int) -> Dict[str, Any]:
    if rank <= 100:
        tier = "Top 100"
    elif rank <= 300:
        tier = "Top 300"
    elif rank <= 500:
        tier = "Top 500"
    elif rank <= 700:
        tier = "Top 700"
    else:
        tier = "Top 1000+"
    return {
        "official_name": official,
        "rank_number":   rank,
        "source":        "QS World University Rankings 2024",
        "tier":          tier,
    }


# ── Year extraction helper ────────────────────────────────────────────────────

def _extract_year(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    m = re.search(r'\b(19|20)\d{2}\b', str(date_str))
    return int(m.group()) if m else None


# ── Main analyzer ─────────────────────────────────────────────────────────────

class EducationalAnalyzer:

    def analyze(self, cv: ExtractedCV) -> Dict[str, Any]:
        records = cv.education
        if not records:
            return self._empty_result()

        # Highest degree by rank
        ranked = sorted(records, key=lambda e: DEGREE_RANK.get(e.degree_level, 0), reverse=True)
        highest = ranked[0]

        # Degree progression (chronological)
        progression = sorted(
            records,
            key=lambda e: (e.start_year or 0, DEGREE_RANK.get(e.degree_level, 0))
        )
        progression_labels = [DEGREE_LABELS.get(e.degree_level, "Other") for e in progression]

        # Normalized grade stats
        grades = [e.normalized_percentage for e in records if e.normalized_percentage is not None]

        # Foreign education
        foreign_records = [
            e for e in records
            if e.country and e.country.lower().strip() not in PAKISTAN_IDENTIFIERS
        ]
        has_foreign = len(foreign_records) > 0
        foreign_institutions = [f"{e.institution} ({e.country})" for e in foreign_records]

        # Education time span
        dated = [(e.start_year, e.end_year) for e in records if e.start_year and e.end_year]
        education_span = None
        if dated:
            earliest = min(s for s, _ in dated)
            latest   = max(e for _, e in dated)
            education_span = latest - earliest

        # ── Gap detection with employment justification (Req 3.1-viii) ───────
        sorted_by_time = sorted(records, key=lambda e: e.start_year or 0)
        gaps_detected: List[str] = []
        gaps_with_justification: List[Dict[str, Any]] = []

        # Build employment year ranges for justification lookup
        emp_ranges: List[Tuple[int, Optional[int], str, str]] = []  # (start, end, title, org)
        for job in (cv.experience or []):
            jstart = _extract_year(getattr(job, 'start_date', None))
            jend   = _extract_year(getattr(job, 'end_date', None))
            if job.is_current:
                jend = 9999
            if jstart:
                emp_ranges.append((jstart, jend, job.job_title or '', job.organization or ''))

        for i in range(len(sorted_by_time) - 1):
            curr_end   = sorted_by_time[i].end_year
            next_start = sorted_by_time[i + 1].start_year
            if curr_end and next_start and (next_start - curr_end) > 1:
                gap_years = next_start - curr_end
                a = DEGREE_LABELS.get(sorted_by_time[i].degree_level, "Degree")
                b = DEGREE_LABELS.get(sorted_by_time[i + 1].degree_level, "Degree")
                gaps_detected.append(f"{gap_years} year(s) between {a} and {b}")

                # Check if employed during gap
                jobs_in_gap = [
                    {"title": title, "organization": org}
                    for (jstart, jend, title, org) in emp_ranges
                    if jstart is not None and jstart <= next_start and (jend is None or jend >= curr_end)
                ]
                if jobs_in_gap:
                    justification = "Candidate was employed during this period: " + "; ".join(
                        f"{j['title']} at {j['organization']}" for j in jobs_in_gap if j['title'] or j['organization']
                    )
                    justified = True
                else:
                    justification = "No employment record found for this period."
                    justified = False

                gaps_with_justification.append({
                    "gap_years":              gap_years,
                    "from_degree":            a,
                    "to_degree":              b,
                    "gap_start_year":         curr_end,
                    "gap_end_year":           next_start,
                    "justified":              justified,
                    "justification":          justification,
                    "employment_during_gap":  jobs_in_gap,
                })

        # ── THE/QS institutional rankings (Req 3.1-v) ────────────────────────
        institutional_rankings: List[Dict[str, Any]] = []
        for inst in {e.institution for e in records if e.institution}:
            result = _lookup_qs(inst)
            if result:
                institutional_rankings.append({"institution": inst, **result})
        institutional_rankings.sort(key=lambda x: x["rank_number"])

        # Thesis records
        theses = [
            {"degree": e.degree_level.value, "title": e.thesis_title}
            for e in records if e.thesis_title
        ]

        # Unique institutions
        institutions = list({e.institution for e in records if e.institution})

        # Per-record detail
        education_detail = [
            {
                "degree_level":        DEGREE_LABELS.get(e.degree_level, "Other"),
                "degree_title":        e.degree_title,
                "institution":         e.institution,
                "country":             e.country,
                "start_year":          e.start_year,
                "end_year":            e.end_year,
                "grade_value":         e.grade_value,
                "grade_type":          e.grade_type.value if e.grade_type else None,
                "normalized_percentage": e.normalized_percentage,
                "thesis_title":        e.thesis_title,
            }
            for e in progression
        ]

        analysis = {
            "highest_degree":              DEGREE_LABELS.get(highest.degree_level, "Other"),
            "highest_degree_title":        highest.degree_title,
            "highest_degree_institution":  highest.institution,
            "highest_degree_year":         highest.end_year,
            "highest_degree_country":      highest.country,
            "highest_degree_rank":         DEGREE_RANK.get(highest.degree_level, 0),
            "total_degrees":               len(records),
            "has_phd":                     any(e.degree_level == DegreeLevel.PHD for e in records),
            "has_masters":                 any(
                e.degree_level in (DegreeLevel.MASTER_16, DegreeLevel.MASTER_18)
                for e in records
            ),
            "has_foreign_education":       has_foreign,
            "foreign_institutions":        foreign_institutions,
            "education_span_years":        education_span,
            "average_percentage":          round(sum(grades) / len(grades), 2) if grades else None,
            "highest_percentage":          max(grades) if grades else None,
            "lowest_percentage":           min(grades) if grades else None,
            "degree_progression":          progression_labels,
            "theses":                      theses,
            "institutions":                institutions,
            "gaps_detected":               gaps_detected,
            "gaps_with_justification":     gaps_with_justification,
            "institutional_rankings":      institutional_rankings,
            "education_detail":            education_detail,
        }

        # ── Educational strength interpretation (Req 3.1-ix) ─────────────────
        analysis["educational_strength_interpretation"] = _interpret_strength(analysis)
        return analysis

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "highest_degree": None,
            "highest_degree_title": None,
            "highest_degree_institution": None,
            "highest_degree_year": None,
            "highest_degree_country": None,
            "highest_degree_rank": 0,
            "total_degrees": 0,
            "has_phd": False,
            "has_masters": False,
            "has_foreign_education": False,
            "foreign_institutions": [],
            "education_span_years": None,
            "average_percentage": None,
            "highest_percentage": None,
            "lowest_percentage": None,
            "degree_progression": [],
            "theses": [],
            "institutions": [],
            "gaps_detected": [],
            "gaps_with_justification": [],
            "institutional_rankings": [],
            "education_detail": [],
            "educational_strength_interpretation": "No education records available.",
        }


# ── Educational strength interpretation (Req 3.1-ix) ─────────────────────────

def _interpret_strength(a: Dict[str, Any]) -> str:
    has_phd    = a.get("has_phd", False)
    has_masters = a.get("has_masters", False)
    avg_pct    = a.get("average_percentage")
    has_foreign = a.get("has_foreign_education", False)
    rankings   = a.get("institutional_rankings", [])
    gaps       = a.get("gaps_with_justification", [])
    unjustified_gaps = [g for g in gaps if not g.get("justified", True)]
    top_rank   = min((r["rank_number"] for r in rankings), default=None)

    # Grade descriptor
    if avg_pct is None:
        grade_desc = ""
    elif avg_pct >= 85:
        grade_desc = "with excellent academic grades"
    elif avg_pct >= 75:
        grade_desc = "with strong academic grades"
    elif avg_pct >= 65:
        grade_desc = "with above-average grades"
    else:
        grade_desc = "with satisfactory grades"

    # Institutional prestige
    if top_rank and top_rank <= 100:
        inst_desc = "from a globally top-100 institution"
    elif top_rank and top_rank <= 300:
        inst_desc = "from a top-300 ranked institution"
    elif top_rank and top_rank <= 500:
        inst_desc = "from a top-500 ranked institution"
    elif top_rank and top_rank <= 700:
        inst_desc = "from a recognized national institution"
    else:
        inst_desc = ""

    # Gap note
    gap_note = ""
    if unjustified_gaps:
        gap_note = f" Note: {len(unjustified_gaps)} unexplained gap(s) in the academic timeline."

    # Compose interpretation
    if has_phd:
        parts = ["Outstanding academic profile — holds a doctoral degree"]
        if grade_desc:
            parts.append(grade_desc)
        if inst_desc:
            parts.append(inst_desc)
        if has_foreign:
            parts.append("with international education experience")
        return " ".join(parts) + "." + gap_note

    if has_masters:
        parts = ["Strong academic background — graduate-level qualifications"]
        if grade_desc:
            parts.append(grade_desc)
        if inst_desc:
            parts.append(inst_desc)
        if has_foreign:
            parts.append("including international study")
        return " ".join(parts) + "." + gap_note

    parts = ["Adequate academic foundation — undergraduate-level qualification"]
    if grade_desc:
        parts.append(grade_desc)
    if inst_desc:
        parts.append(inst_desc)
    return " ".join(parts) + "." + gap_note
