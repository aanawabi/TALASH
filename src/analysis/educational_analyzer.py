from typing import Optional, List, Dict, Any
from ..models.cv_models import ExtractedCV, DegreeLevel

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
        foreign_institutions = [
            f"{e.institution} ({e.country})" for e in foreign_records
        ]

        # Education time span
        dated = [(e.start_year, e.end_year) for e in records if e.start_year and e.end_year]
        education_span = None
        if dated:
            earliest = min(s for s, _ in dated)
            latest = max(e for _, e in dated)
            education_span = latest - earliest

        # Gap detection between consecutive degrees
        sorted_by_time = sorted(records, key=lambda e: e.start_year or 0)
        gaps: List[str] = []
        for i in range(len(sorted_by_time) - 1):
            curr_end = sorted_by_time[i].end_year
            next_start = sorted_by_time[i + 1].start_year
            if curr_end and next_start and (next_start - curr_end) > 1:
                a = DEGREE_LABELS.get(sorted_by_time[i].degree_level, "Degree")
                b = DEGREE_LABELS.get(sorted_by_time[i + 1].degree_level, "Degree")
                gaps.append(f"{next_start - curr_end} year(s) between {a} and {b}")

        # Thesis records
        theses = [
            {"degree": e.degree_level.value, "title": e.thesis_title}
            for e in records if e.thesis_title
        ]

        # Unique institutions
        institutions = list({e.institution for e in records if e.institution})

        # Per-record detail (used by charts and exports)
        education_detail = [
            {
                "degree_level": DEGREE_LABELS.get(e.degree_level, "Other"),
                "degree_title": e.degree_title,
                "institution": e.institution,
                "country": e.country,
                "start_year": e.start_year,
                "end_year": e.end_year,
                "grade_value": e.grade_value,
                "grade_type": e.grade_type.value if e.grade_type else None,
                "normalized_percentage": e.normalized_percentage,
                "thesis_title": e.thesis_title,
            }
            for e in progression
        ]

        return {
            "highest_degree": DEGREE_LABELS.get(highest.degree_level, "Other"),
            "highest_degree_title": highest.degree_title,
            "highest_degree_institution": highest.institution,
            "highest_degree_year": highest.end_year,
            "highest_degree_country": highest.country,
            "highest_degree_rank": DEGREE_RANK.get(highest.degree_level, 0),
            "total_degrees": len(records),
            "has_phd": any(e.degree_level == DegreeLevel.PHD for e in records),
            "has_masters": any(
                e.degree_level in (DegreeLevel.MASTER_16, DegreeLevel.MASTER_18)
                for e in records
            ),
            "has_foreign_education": has_foreign,
            "foreign_institutions": foreign_institutions,
            "education_span_years": education_span,
            "average_percentage": round(sum(grades) / len(grades), 2) if grades else None,
            "highest_percentage": max(grades) if grades else None,
            "lowest_percentage": min(grades) if grades else None,
            "degree_progression": progression_labels,
            "theses": theses,
            "institutions": institutions,
            "gaps_detected": gaps,
            "education_detail": education_detail,
        }

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
            "education_detail": [],
        }