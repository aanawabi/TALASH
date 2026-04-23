import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.cv_models import ExtractedCV

sns.set_theme(style="whitegrid", palette="muted")
_FIG_DPI = 150


def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


class ChartGenerator:

    def __init__(self, output_dir: str = "data/charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _candidate_dir(self, name: str) -> Path:
        d = self.output_dir / _safe_name(name)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _aggregate_dir(self) -> Path:
        d = self.output_dir / "aggregate"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _save(self, fig: plt.Figure, path: Path) -> str:
        fig.savefig(path, dpi=_FIG_DPI, bbox_inches="tight")
        plt.close(fig)
        return str(path)

    # ══════════════════════════════════════════════════════════════════════════
    # PER-CANDIDATE CHARTS
    # ══════════════════════════════════════════════════════════════════════════

    def education_timeline(self, cv: ExtractedCV, edu_analysis: Dict[str, Any]) -> str:
        """Horizontal Gantt-style bar chart showing each degree over time."""
        detail = edu_analysis.get("education_detail", [])
        records = [d for d in detail if d["start_year"] and d["end_year"]]
        if not records:
            return ""

        fig, ax = plt.subplots(figsize=(10, max(3, len(records) * 1.0)))
        colors = sns.color_palette("Blues_d", len(records))

        for i, rec in enumerate(records):
            start = rec["start_year"]
            end = rec["end_year"]
            ax.barh(i, end - start, left=start, height=0.5,
                    color=colors[i], edgecolor="white")
            label = f"{rec['degree_level']}\n{rec['institution']}"
            ax.text(start + 0.1, i, label, va="center", ha="left",
                    fontsize=8, color="white", fontweight="bold")

        ax.set_yticks(range(len(records)))
        ax.set_yticklabels([r["degree_title"] or r["degree_level"] for r in records], fontsize=9)
        ax.set_xlabel("Year")
        ax.set_title(f"Education Timeline — {cv.personal_info.full_name}", fontweight="bold")
        fig.tight_layout()
        return self._save(fig, self._candidate_dir(cv.personal_info.full_name) / "education_timeline.png")

    def experience_timeline(self, cv: ExtractedCV, exp_analysis: Dict[str, Any]) -> str:
        """Horizontal Gantt chart of work history."""
        roles = [r for r in exp_analysis.get("role_details", [])
                 if r["start_date"] or r["end_date"]]
        if not roles:
            return ""

        now_year = datetime.now().year

        def _year(s: Optional[str], fallback: int) -> float:
            if not s:
                return fallback
            import re
            m = re.match(r"(\d{4})", s)
            return float(m.group(1)) if m else fallback

        parsed = []
        for r in roles:
            start = _year(r["start_date"], now_year - 1)
            end = now_year if r["is_current"] else _year(r["end_date"], start + 1)
            parsed.append((r["job_title"], r["organization"], start, end))

        parsed.sort(key=lambda x: x[2])
        fig, ax = plt.subplots(figsize=(10, max(3, len(parsed) * 0.9)))
        colors = sns.color_palette("Greens_d", len(parsed))

        for i, (title, org, start, end) in enumerate(parsed):
            ax.barh(i, end - start, left=start, height=0.5,
                    color=colors[i], edgecolor="white")
            ax.text(start + 0.05, i, f"{title}\n{org}", va="center", ha="left",
                    fontsize=8, color="white", fontweight="bold")

        ax.set_yticks(range(len(parsed)))
        ax.set_yticklabels([p[0] for p in parsed], fontsize=9)
        ax.set_xlabel("Year")
        ax.set_title(f"Experience Timeline — {cv.personal_info.full_name}", fontweight="bold")
        fig.tight_layout()
        return self._save(fig, self._candidate_dir(cv.personal_info.full_name) / "experience_timeline.png")

    def skills_chart(self, cv: ExtractedCV) -> str:
        """Horizontal bar chart of skills grouped by category."""
        if not cv.skills:
            return ""

        from collections import Counter
        cat_counts = Counter(s.skill_category or "Other" for s in cv.skills)
        cats = sorted(cat_counts.keys())
        counts = [cat_counts[c] for c in cats]

        fig, ax = plt.subplots(figsize=(8, max(3, len(cats) * 0.7)))
        bars = ax.barh(cats, counts, color=sns.color_palette("Purples_d", len(cats)))
        ax.bar_label(bars, padding=3, fontsize=9)
        ax.set_xlabel("Number of Skills")
        ax.set_title(f"Skills by Category — {cv.personal_info.full_name}", fontweight="bold")
        ax.set_xlim(0, max(counts) * 1.2)
        fig.tight_layout()
        return self._save(fig, self._candidate_dir(cv.personal_info.full_name) / "skills.png")

    def publications_by_year(self, cv: ExtractedCV, research_analysis: Dict[str, Any]) -> str:
        """Bar chart of publications per year."""
        by_year = research_analysis.get("publications_by_year", {})
        if not by_year:
            return ""

        years = sorted(by_year.keys())
        counts = [by_year[y] for y in years]

        fig, ax = plt.subplots(figsize=(max(6, len(years) * 0.8), 4))
        bars = ax.bar(years, counts, color=sns.color_palette("Oranges_d", len(years)))
        ax.bar_label(bars, padding=2, fontsize=9)
        ax.set_xlabel("Year")
        ax.set_ylabel("Publications")
        ax.set_title(f"Publications by Year — {cv.personal_info.full_name}", fontweight="bold")
        ax.set_xticks(years)
        ax.set_xticklabels(years, rotation=45)
        fig.tight_layout()
        return self._save(fig, self._candidate_dir(cv.personal_info.full_name) / "publications_by_year.png")

    def research_summary_radar(self, cv: ExtractedCV, research_analysis: Dict[str, Any]) -> str:
        """Radar chart showing key research dimensions."""
        q = research_analysis["quartile_distribution"]
        dims = ["Total Pubs", "Q1/Q2 Pubs", "Indexed Conf", "Supervisions", "Patents/Books"]
        raw = [
            research_analysis["total_publications"],
            q["Q1"] + q["Q2"],
            research_analysis["indexed_conference_count"],
            research_analysis["total_supervisions"],
            research_analysis["total_patents"] + research_analysis["total_books"],
        ]
        # Normalize each dimension to 0-10
        caps = [30, 10, 10, 10, 5]
        values = [min(v / c * 10, 10) for v, c in zip(raw, caps)]
        values += values[:1]

        angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.plot(angles, values, "o-", linewidth=2, color="#2196F3")
        ax.fill(angles, values, alpha=0.25, color="#2196F3")
        ax.set_thetagrids(np.degrees(angles[:-1]), dims, fontsize=10)
        ax.set_ylim(0, 10)
        ax.set_title(f"Research Profile — {cv.personal_info.full_name}",
                     fontweight="bold", pad=20)
        fig.tight_layout()
        return self._save(fig, self._candidate_dir(cv.personal_info.full_name) / "research_radar.png")

    def candidate_overview(
        self,
        cv: ExtractedCV,
        edu_analysis: Dict[str, Any],
        exp_analysis: Dict[str, Any],
        research_analysis: Dict[str, Any],
    ) -> str:
        """2×2 summary dashboard for a single candidate."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"Candidate Overview — {cv.personal_info.full_name}",
                     fontsize=14, fontweight="bold")

        # ── Top-left: Education progression ──────────────────────────────────
        ax = axes[0, 0]
        prog = edu_analysis.get("degree_progression", [])
        if prog:
            ax.barh(range(len(prog)), [1] * len(prog),
                    color=sns.color_palette("Blues", len(prog)))
            ax.set_yticks(range(len(prog)))
            ax.set_yticklabels(prog, fontsize=9)
            ax.set_xticks([])
            ax.set_title("Degree Progression", fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No education data", ha="center", va="center")
            ax.set_title("Degree Progression", fontweight="bold")

        # ── Top-right: Experience timeline ────────────────────────────────────
        ax = axes[0, 1]
        roles = exp_analysis.get("role_details", [])
        if roles:
            labels = [f"{r['job_title']}\n({r['organization']})" for r in roles]
            durations = [r["duration_years"] or 0 for r in roles]
            bars = ax.barh(range(len(roles)), durations,
                           color=sns.color_palette("Greens_d", len(roles)))
            ax.set_yticks(range(len(roles)))
            ax.set_yticklabels(labels, fontsize=8)
            ax.set_xlabel("Years")
            ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)
            ax.set_title("Experience Duration per Role", fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No experience data", ha="center", va="center")
            ax.set_title("Experience Duration per Role", fontweight="bold")

        # ── Bottom-left: Quartile distribution ───────────────────────────────
        ax = axes[1, 0]
        q = research_analysis["quartile_distribution"]
        q_labels = [k for k, v in q.items() if v > 0]
        q_vals = [v for v in q.values() if v > 0]
        if q_vals:
            ax.pie(q_vals, labels=q_labels, autopct="%1.0f%%",
                   colors=sns.color_palette("Set2", len(q_vals)))
            ax.set_title("Journal Quartile Distribution", fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No publications", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_title("Journal Quartile Distribution", fontweight="bold")

        # ── Bottom-right: Skills by category ─────────────────────────────────
        ax = axes[1, 1]
        if cv.skills:
            from collections import Counter
            cat_counts = Counter(s.skill_category or "Other" for s in cv.skills)
            cats = list(cat_counts.keys())
            counts = list(cat_counts.values())
            bars = ax.barh(cats, counts, color=sns.color_palette("Purples_d", len(cats)))
            ax.bar_label(bars, padding=2, fontsize=9)
            ax.set_xlabel("Count")
            ax.set_title("Skills by Category", fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No skills data", ha="center", va="center",
                    transform=ax.transAxes)
            ax.set_title("Skills by Category", fontweight="bold")

        fig.tight_layout()
        return self._save(fig, self._candidate_dir(cv.personal_info.full_name) / "overview.png")

    # ══════════════════════════════════════════════════════════════════════════
    # AGGREGATE CHARTS (multiple candidates)
    # ══════════════════════════════════════════════════════════════════════════

    def education_level_distribution(
        self, cvs: List[ExtractedCV], edu_analyses: List[Dict[str, Any]]
    ) -> str:
        """Bar chart of highest degree distribution across all candidates."""
        from collections import Counter
        counts = Counter(a["highest_degree"] or "Unknown" for a in edu_analyses)
        labels = list(counts.keys())
        values = list(counts.values())

        fig, ax = plt.subplots(figsize=(max(6, len(labels)), 5))
        x = range(len(labels))
        bars = ax.bar(x, values, color=sns.color_palette("Blues_d", len(labels)))
        ax.bar_label(bars, padding=3)
        ax.set_ylabel("Number of Candidates")
        ax.set_title("Highest Degree Distribution", fontweight="bold")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=30, ha="right")
        fig.tight_layout()
        return self._save(fig, self._aggregate_dir() / "education_distribution.png")

    def experience_distribution(
        self, cvs: List[ExtractedCV], exp_analyses: List[Dict[str, Any]]
    ) -> str:
        """Histogram of total years of experience across candidates."""
        years = [a["total_years_experience"] for a in exp_analyses
                 if a["total_years_experience"] is not None]
        if not years:
            return ""

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(years, bins=min(10, len(years)), color="#42A5F5", edgecolor="white")
        ax.set_xlabel("Years of Experience")
        ax.set_ylabel("Number of Candidates")
        ax.set_title("Experience Distribution Across Candidates", fontweight="bold")
        fig.tight_layout()
        return self._save(fig, self._aggregate_dir() / "experience_distribution.png")

    def top_skills_frequency(
        self, cvs: List[ExtractedCV], top_n: int = 20
    ) -> str:
        """Horizontal bar chart of the most common skills across all candidates."""
        from collections import Counter
        all_skills = [s.skill_name for cv in cvs for s in cv.skills]
        if not all_skills:
            return ""

        counts = Counter(all_skills).most_common(top_n)
        labels = [c[0] for c in counts]
        values = [c[1] for c in counts]

        fig, ax = plt.subplots(figsize=(10, max(5, top_n * 0.4)))
        bars = ax.barh(labels[::-1], values[::-1],
                       color=sns.color_palette("Purples_d", len(labels)))
        ax.bar_label(bars, padding=3, fontsize=8)
        ax.set_xlabel("Frequency")
        ax.set_title(f"Top {top_n} Skills Across All Candidates", fontweight="bold")
        fig.tight_layout()
        return self._save(fig, self._aggregate_dir() / "top_skills.png")

    def research_impact_comparison(
        self,
        cvs: List[ExtractedCV],
        research_analyses: List[Dict[str, Any]],
    ) -> str:
        """Horizontal bar chart comparing research impact scores."""
        names = [cv.personal_info.full_name for cv in cvs]
        scores = [a["research_impact_score"] for a in research_analyses]
        paired = sorted(zip(scores, names), reverse=True)
        scores, names = zip(*paired) if paired else ([], [])

        fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.6)))
        bars = ax.barh(names, scores, color=sns.color_palette("Oranges_d", len(names)))
        ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)
        ax.set_xlabel("Research Impact Score")
        ax.set_title("Research Impact Score Comparison", fontweight="bold")
        fig.tight_layout()
        return self._save(fig, self._aggregate_dir() / "research_impact.png")

    def publications_comparison(
        self,
        cvs: List[ExtractedCV],
        research_analyses: List[Dict[str, Any]],
    ) -> str:
        """Stacked bar chart: journal vs conference publications per candidate."""
        names = [cv.personal_info.full_name for cv in cvs]
        journals = [a["total_journal_publications"] for a in research_analyses]
        conferences = [a["total_conference_publications"] for a in research_analyses]

        x = np.arange(len(names))
        fig, ax = plt.subplots(figsize=(max(8, len(names) * 1.5), 5))
        b1 = ax.bar(x, journals, label="Journal", color="#1565C0")
        b2 = ax.bar(x, conferences, bottom=journals, label="Conference", color="#42A5F5")
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("Publications")
        ax.set_title("Publications per Candidate (Journal vs Conference)", fontweight="bold")
        ax.legend()
        fig.tight_layout()
        return self._save(fig, self._aggregate_dir() / "publications_comparison.png")

    def quartile_distribution_aggregate(
        self,
        cvs: List[ExtractedCV],
        research_analyses: List[Dict[str, Any]],
    ) -> str:
        """Stacked bar chart of Q1/Q2/Q3/Q4/Unranked per candidate."""
        names = [cv.personal_info.full_name for cv in cvs]
        qs = ["Q1", "Q2", "Q3", "Q4", "Unranked"]
        colors = ["#1A237E", "#1565C0", "#1E88E5", "#64B5F6", "#BBDEFB"]

        data = {q: [a["quartile_distribution"][q] for a in research_analyses] for q in qs}
        x = np.arange(len(names))
        bottom = np.zeros(len(names))

        fig, ax = plt.subplots(figsize=(max(8, len(names) * 1.5), 5))
        for q, color in zip(qs, colors):
            vals = np.array(data[q])
            ax.bar(x, vals, bottom=bottom, label=q, color=color)
            bottom += vals

        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("Journal Publications")
        ax.set_title("Quartile Distribution per Candidate", fontweight="bold")
        ax.legend(title="Quartile")
        fig.tight_layout()
        return self._save(fig, self._aggregate_dir() / "quartile_distribution.png")

    # ── Convenience: generate all charts for one candidate ────────────────────

    def generate_all_candidate_charts(
        self,
        cv: ExtractedCV,
        edu_analysis: Dict[str, Any],
        exp_analysis: Dict[str, Any],
        research_analysis: Dict[str, Any],
    ) -> Dict[str, str]:
        paths = {}
        p = self.education_timeline(cv, edu_analysis)
        if p: paths["education_timeline"] = p
        p = self.experience_timeline(cv, exp_analysis)
        if p: paths["experience_timeline"] = p
        p = self.skills_chart(cv)
        if p: paths["skills"] = p
        p = self.publications_by_year(cv, research_analysis)
        if p: paths["publications_by_year"] = p
        if research_analysis["total_publications"] > 0:
            p = self.research_summary_radar(cv, research_analysis)
            if p: paths["research_radar"] = p
        p = self.candidate_overview(cv, edu_analysis, exp_analysis, research_analysis)
        if p: paths["overview"] = p
        return paths

    # ── Convenience: generate all aggregate charts ────────────────────────────

    def generate_all_aggregate_charts(
        self,
        cvs: List[ExtractedCV],
        edu_analyses: List[Dict[str, Any]],
        exp_analyses: List[Dict[str, Any]],
        research_analyses: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        if len(cvs) < 2:
            return {}
        paths = {}
        p = self.education_level_distribution(cvs, edu_analyses)
        if p: paths["education_distribution"] = p
        p = self.experience_distribution(cvs, exp_analyses)
        if p: paths["experience_distribution"] = p
        p = self.top_skills_frequency(cvs)
        if p: paths["top_skills"] = p
        p = self.research_impact_comparison(cvs, research_analyses)
        if p: paths["research_impact"] = p
        p = self.publications_comparison(cvs, research_analyses)
        if p: paths["publications_comparison"] = p
        p = self.quartile_distribution_aggregate(cvs, research_analyses)
        if p: paths["quartile_distribution"] = p
        return paths