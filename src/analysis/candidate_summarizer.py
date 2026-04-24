from typing import Dict, Any, Optional
from ..models.cv_models import ExtractedCV


class CandidateSummarizer:

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key
        self.model_name = model_name

    # ── Stats summary ─────────────────────────────────────────────────────────

    def compute_stats(
        self,
        cv: ExtractedCV,
        edu_analysis: Dict[str, Any],
        exp_analysis: Dict[str, Any],
        research_analysis: Dict[str, Any],
        missing_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        pi = cv.personal_info
        return {
            # Identity
            "name":            pi.full_name,
            "email":           pi.email,
            "phone":           pi.phone,
            "linkedin":        pi.linkedin,
            # Education headline
            "highest_degree":       edu_analysis["highest_degree"],
            "highest_institution":  edu_analysis["highest_degree_institution"],
            "highest_degree_year":  edu_analysis["highest_degree_year"],
            "has_phd":              edu_analysis["has_phd"],
            "has_foreign_education":edu_analysis["has_foreign_education"],
            "avg_grade_pct":        edu_analysis["average_percentage"],
            # Experience headline
            "total_experience_years": exp_analysis["total_years_experience"],
            "current_position":       exp_analysis["current_position"],
            "current_organization":   exp_analysis["current_organization"],
            "career_trajectory":      exp_analysis["career_trajectory"],
            "num_positions":          exp_analysis["number_of_positions"],
            # Research headline
            "profile_tier":           research_analysis["profile_tier"],
            "total_publications":     research_analysis["total_publications"],
            "q1_q2_publications":     research_analysis["high_impact_count"],
            "research_impact_score":  research_analysis["research_impact_score"],
            "phd_supervised":         research_analysis["phd_supervised"],
            "ms_supervised":          research_analysis["ms_supervised"],
            "granted_patents":        research_analysis["granted_patents"],
            # Skills
            "total_skills":           len(cv.skills),
            # Completeness
            "has_missing_info":       missing_info["has_missing_info"],
            "missing_fields_count":   missing_info["total_missing_fields"],
        }

    # ── LLM narrative ─────────────────────────────────────────────────────────

    def generate_narrative(
        self,
        cv: ExtractedCV,
        edu_analysis: Dict[str, Any],
        exp_analysis: Dict[str, Any],
        research_analysis: Dict[str, Any],
    ) -> str:
        from google import genai

        pi = cv.personal_info
        skills_sample = ", ".join(s.skill_name for s in cv.skills[:10])
        pub_line = (
            f"{research_analysis['total_publications']} publications "
            f"({research_analysis['high_impact_count']} in Q1/Q2 journals)"
            if research_analysis["total_publications"] > 0
            else "no publications listed"
        )
        exp_line = (
            f"{exp_analysis['total_years_experience']} years of experience "
            f"with a {exp_analysis['career_trajectory']} trajectory"
            if exp_analysis["total_years_experience"]
            else "experience details partially available"
        )

        prompt = f"""You are a senior HR analyst writing a professional candidate summary for an internal recruitment report.

Candidate: {pi.full_name}
Highest qualification: {edu_analysis['highest_degree']} from {edu_analysis['highest_degree_institution']} ({edu_analysis['highest_degree_year']})
Foreign education: {'Yes' if edu_analysis['has_foreign_education'] else 'No'}
Experience: {exp_line}
Current role: {exp_analysis['current_position']} at {exp_analysis['current_organization']}
Research: {pub_line}
Research impact score: {research_analysis['research_impact_score']}
Profile tier: {research_analysis['profile_tier']}
Key skills: {skills_sample}
PhD supervisions: {research_analysis['phd_supervised']}, MS supervisions: {research_analysis['ms_supervised']}
Patents granted: {research_analysis['granted_patents']}

Write a concise 2–3 paragraph professional summary suitable for a recruitment shortlisting report.
Cover: academic background, professional experience, and research/technical strengths.
Be factual and objective. Do not add information not provided above.
Return only the summary text."""

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(model=self.model_name, contents=prompt)
        return response.text.strip()

    # ── Combined entry point ──────────────────────────────────────────────────

    def summarize(
        self,
        cv: ExtractedCV,
        edu_analysis: Dict[str, Any],
        exp_analysis: Dict[str, Any],
        research_analysis: Dict[str, Any],
        missing_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        stats = self.compute_stats(cv, edu_analysis, exp_analysis, research_analysis, missing_info)
        narrative = self.generate_narrative(cv, edu_analysis, exp_analysis, research_analysis)
        return {"stats": stats, "narrative": narrative}