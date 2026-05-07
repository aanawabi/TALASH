"""
Module 3.6 – Topic Variability Analyzer
========================================
Measures the breadth vs. focus of a candidate's research by clustering
publications into thematic groups.

Per requirement 3.6, the system should:
- extract keywords, titles, abstracts, venues, and research domains
- group into thematic clusters (ML, CV, Networks, SE, Cybersecurity, HR analytics, etc.)
- measure concentration/dispersion across clusters
- identify core specialization
- estimate degree of topical diversity
- output: themes, percentages, dominant topic, diversity score, topic trend over time
"""

from __future__ import annotations
from typing import Dict, Any, List
from collections import defaultdict
import math

from ..models.cv_models import ExtractedCV, JournalPublication, ConferencePublication

# ── Theme keyword mapping (per requirement: includes HR analytics explicitly) ─
# Source themes explicitly listed in requirement 3.6:
# "machine learning, computer vision, networks, software engineering,
#  cybersecurity, HR analytics, etc."
_THEME_KEYWORDS: Dict[str, List[str]] = {
    "Machine Learning & AI": [
        "machine learning", "deep learning", "neural network", "artificial intelligence",
        "reinforcement learning", "transfer learning", "generative", "large language model",
        "llm", "transformer", "bert", "gpt", "classification", "regression", "ensemble",
        "federated learning", "few-shot", "zero-shot", "self-supervised", "meta-learning",
        "hyperparameter", "automl", "explainability", "interpretability", "xai",
        "bayesian", "probabilistic model", "gaussian process", "active learning",
        "multi-task learning", "continual learning", "knowledge distillation",
    ],
    "Computer Vision": [
        "image", "object detection", "segmentation", "face recognition", "visual",
        "convolutional", "cnn", "optical flow", "3d reconstruction", "medical imaging",
        "remote sensing", "pose estimation", "video understanding", "action recognition",
        "image classification", "instance segmentation", "depth estimation",
        "stereo vision", "point cloud", "lidar", "thermal imaging", "hyperspectral",
        "gan", "image generation", "style transfer", "super resolution",
    ],
    "Natural Language Processing": [
        "natural language", "nlp", "text classification", "sentiment analysis",
        "named entity", "machine translation", "question answering", "summarization",
        "chatbot", "information extraction", "word embedding", "language model",
        "dialogue", "coreference", "text mining", "topic modeling", "text generation",
        "reading comprehension", "relation extraction", "dependency parsing",
        "semantic similarity", "cross-lingual", "multilingual", "spell checking",
    ],
    "Cybersecurity": [
        "security", "intrusion detection", "malware", "cryptograph", "privacy",
        "authentication", "vulnerability", "forensic", "cyber", "threat detection",
        "anomaly detection", "blockchain", "access control", "encryption",
        "ransomware", "phishing", "zero-day", "penetration testing", "ids", "ips",
        "ddos", "botnet", "steganography", "digital watermark", "secure protocol",
        "privacy-preserving", "differential privacy", "trusted execution",
    ],
    "Networks & Systems": [
        "network", "wireless", "iot", "internet of things", "cloud computing",
        "fog computing", "edge computing", "protocol", "routing", "bandwidth",
        "latency", "5g", "mobile computing", "distributed system", "sensor network",
        "vehicular", "cognitive radio", "software defined network", "sdn", "nfv",
        "network slicing", "qos", "traffic engineering", "peer-to-peer",
        "ad hoc", "mesh network", "lpwan", "zigbee", "lora",
    ],
    "Data Science & Analytics": [
        "data mining", "big data", "analytics", "prediction", "clustering",
        "visualization", "knowledge graph", "recommendation system", "time series",
        "feature selection", "dimensionality reduction", "data warehouse", "etl",
        "stream processing", "data integration", "data quality", "data preprocessing",
        "outlier detection", "association rule", "frequent pattern", "dashboarding",
        "business intelligence", "descriptive analytics", "predictive analytics",
    ],
    "Software Engineering": [
        "software", "testing", "agile", "devops", "microservice", "software architecture",
        "code quality", "refactoring", "requirements engineering", "uml", "model-driven",
        "continuous integration", "technical debt", "software maintenance",
        "software testing", "unit testing", "regression testing", "test automation",
        "static analysis", "code smell", "design pattern", "api design",
        "service-oriented", "software metrics", "mutation testing", "fuzzing",
    ],
    "Healthcare & Bioinformatics": [
        "health", "medical", "clinical", "bioinformatics", "genomic", "drug discovery",
        "diagnosis", "patient", "eeg", "ecg", "cancer", "covid", "electronic health",
        "telemedicine", "wearable", "brain-computer", "radiology", "pathology",
        "disease prediction", "protein structure", "gene expression", "dna sequencing",
        "medical record", "clinical trial", "epidemiology", "pandemic", "mri", "ct scan",
        "retinal", "surgical", "rehabilitation",
    ],
    "Biological Sciences": [
        "biology", "molecular biology", "cell biology", "microbiology", "genetics",
        "evolution", "ecology", "zoology", "botany", "physiology", "biochemistry",
        "neuroscience", "neurobiology", "immunology", "virology", "bacteriology",
        "proteomics", "metabolomics", "systems biology", "synthetic biology",
        "computational biology", "biodiversity", "phylogenetic", "genome", "rna",
        "crispr", "stem cell", "developmental biology", "marine biology",
    ],
    "Environmental & Earth Sciences": [
        "environment", "climate change", "global warming", "carbon emission",
        "renewable energy", "sustainability", "ecology", "remote sensing satellite",
        "geospatial", "gis", "hydrology", "atmospheric", "oceanography",
        "soil science", "land use", "deforestation", "pollution", "water quality",
        "energy efficiency", "smart grid", "solar energy", "wind energy",
        "environmental monitoring", "natural disaster", "flood prediction",
    ],
    "Physics & Mathematics": [
        "physics", "quantum", "thermodynamics", "mechanics", "optics", "acoustics",
        "electromagnetism", "plasma", "condensed matter", "particle physics",
        "mathematics", "algebra", "calculus", "topology", "graph theory",
        "number theory", "optimization", "numerical method", "simulation",
        "differential equation", "stochastic", "probability", "statistics",
        "computational mathematics", "linear programming", "integer programming",
    ],
    "Chemistry & Materials Science": [
        "chemistry", "organic chemistry", "inorganic chemistry", "polymer",
        "nanomaterial", "composite material", "semiconductor", "catalyst",
        "electrochemistry", "spectroscopy", "chromatography", "synthesis",
        "material science", "corrosion", "thin film", "graphene", "nanoparticle",
        "superconductor", "alloy", "biomaterial", "photovoltaic",
    ],
    "HR Analytics & Recruitment": [
        # Explicitly required by project spec (TALASH is HR-focused)
        "hr analytics", "human resource", "recruitment", "talent acquisition",
        "employee", "workforce", "job matching", "resume", "cv screening",
        "performance appraisal", "attrition", "turnover", "hiring", "organizational",
        "people analytics", "competency",
    ],
    "Education & E-Learning": [
        "education", "e-learning", "learning management", "student performance",
        "pedagogy", "curriculum", "blended learning", "mooc", "online education",
        "intelligent tutoring", "learning analytics", "gamification", "flipped classroom",
        "higher education", "academic performance", "dropout prediction",
        "adaptive learning", "collaborative learning", "knowledge assessment",
    ],
    "Robotics & Control": [
        "robot", "autonomous", "control system", "pid controller", "motion planning",
        "drone", "uav", "unmanned", "simulation", "embedded system", "actuator",
        "manipulator", "humanoid", "swarm robot", "path planning", "slam",
        "localization", "navigation", "human robot interaction", "teleoperation",
        "model predictive control", "fuzzy control", "adaptive control",
    ],
    "Signal Processing": [
        "signal processing", "speech recognition", "audio", "image processing",
        "filter", "fourier", "wavelet", "compression", "noise reduction",
        "feature extraction", "emd", "short-time fourier", "beamforming",
        "source separation", "channel estimation", "modulation", "mimo",
        "ofdm", "radar signal", "ecg signal", "eeg signal processing",
    ],
    "Economics & Social Sciences": [
        "economics", "econometrics", "finance", "stock market", "financial market",
        "social network", "sentiment", "public policy", "political science",
        "sociology", "psychology", "behavioral", "cognitive", "survey",
        "game theory", "mechanism design", "welfare", "poverty", "inequality",
        "social media analysis", "opinion mining", "fake news", "misinformation",
    ],
    "Agriculture & Food Science": [
        "agriculture", "crop", "precision farming", "irrigation", "soil",
        "plant disease", "yield prediction", "smart farming", "food science",
        "food quality", "food safety", "supply chain", "postharvest",
        "livestock", "aquaculture", "remote sensing crop", "agricultural drone",
    ],
    "Transportation & Smart Cities": [
        "transportation", "traffic", "autonomous vehicle", "self-driving",
        "urban computing", "smart city", "ride sharing", "logistics", "supply chain",
        "public transit", "pedestrian", "accident detection", "road network",
        "parking", "congestion", "mobility", "geolocation", "navigation system",
    ],
}


def _extract_pub_text(pub) -> str:
    """
    Per requirement 3.6: extract keywords, titles, abstracts, venues, research domains.
    Combines all available text fields from a publication.
    """
    parts = []
    # Title
    if hasattr(pub, "title") and pub.title:
        parts.append(pub.title.lower())
    # Venue (journal name or conference name)
    if hasattr(pub, "journal_name") and pub.journal_name:
        parts.append(pub.journal_name.lower())
    if hasattr(pub, "conference_name") and pub.conference_name:
        parts.append(pub.conference_name.lower())
    # Authors can hint at research group/domain
    # (not used for theme, but kept for completeness)
    return " ".join(parts)


def _assign_theme(pub) -> str:
    """Return the best-matching theme label or 'Other'."""
    text = _extract_pub_text(pub)
    scores: Dict[str, int] = {}
    for theme, keywords in _THEME_KEYWORDS.items():
        hit = sum(1 for kw in keywords if kw in text)
        if hit:
            scores[theme] = hit
    if not scores:
        return "Other"
    return max(scores, key=lambda t: scores[t])


def _shannon_entropy_normalized(counts: List[int]) -> float:
    """
    Normalized Shannon entropy H = -Σ p*log2(p) / log2(n_themes)
    Returns value in [0, 1]:
      0 = all publications in one theme (highly focused)
      1 = perfectly uniform across all themes (highly diverse)
    """
    total = sum(counts)
    n = len(counts)
    if total == 0 or n <= 1:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return round(h / math.log2(n), 3)


class TopicVariabilityAnalyzer:

    def analyze(self, cv: ExtractedCV) -> Dict[str, Any]:
        """
        Per requirement 3.6 outputs:
        - major research themes of the candidate
        - percentage of publications in each theme
        - dominant topic area
        - diversity score / variability score
        - trend of topic changes over time
        """
        journals: List[JournalPublication]     = cv.journal_publications
        conferences: List[ConferencePublication] = cv.conference_publications
        all_pubs = list(journals) + list(conferences)

        if not all_pubs:
            return {
                "total_publications_analyzed": 0,
                "theme_distribution":          {},
                "dominant_theme":              None,
                "dominant_theme_percentage":   0,
                "theme_count":                 0,
                "diversity_score":             0.0,
                "variability_label":           "No publications",
                "topic_trend_by_year":         {},
                "per_publication_themes":      [],
                "interpretation":              "No publications found for topic analysis.",
            }

        # ── Assign theme to each publication ──────────────────────────────────
        theme_counts: Dict[str, int] = defaultdict(int)
        yearly_themes: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        per_pub: List[Dict[str, Any]] = []

        for pub in all_pubs:
            theme = _assign_theme(pub)
            theme_counts[theme] += 1
            year = getattr(pub, "publication_year", None)
            if year:
                yearly_themes[year][theme] += 1
            per_pub.append({
                "title": getattr(pub, "title", ""),
                "year":  year,
                "assigned_theme": theme,
            })

        total = len(all_pubs)

        # ── Diversity score ───────────────────────────────────────────────────
        counts_list = list(theme_counts.values())
        diversity_score = _shannon_entropy_normalized(counts_list)

        # ── Variability label ─────────────────────────────────────────────────
        n_themes = len([t for t in theme_counts if t != "Other"])
        if diversity_score < 0.20:
            label = "Highly Focused"
        elif diversity_score < 0.45:
            label = "Moderately Focused"
        elif diversity_score < 0.70:
            label = "Interdisciplinary"
        else:
            label = "Highly Diverse"

        # ── Dominant theme ────────────────────────────────────────────────────
        dominant = max(theme_counts, key=lambda t: theme_counts[t])
        dominant_pct = round(theme_counts[dominant] / total * 100, 1)

        # ── Theme distribution with percentages (Req 3.6 output) ─────────────
        theme_distribution = {
            theme: {
                "count":      cnt,
                "percentage": round(cnt / total * 100, 1),
            }
            for theme, cnt in sorted(theme_counts.items(), key=lambda x: -x[1])
        }

        # ── Year-wise trend (Req 3.6: "trend of topic changes over time") ─────
        topic_trend_by_year = {
            year: dict(themes)
            for year, themes in sorted(yearly_themes.items())
        }

        # ── Detect research focus shift over time ─────────────────────────────
        years_sorted = sorted(yearly_themes.keys())
        focus_shifted = False
        if len(years_sorted) >= 4:
            first_half = years_sorted[:len(years_sorted)//2]
            second_half = years_sorted[len(years_sorted)//2:]
            def dominant_in_period(period):
                combined: Dict[str, int] = defaultdict(int)
                for yr in period:
                    for theme, cnt in yearly_themes[yr].items():
                        combined[theme] += cnt
                return max(combined, key=lambda t: combined[t]) if combined else None

            d1 = dominant_in_period(first_half)
            d2 = dominant_in_period(second_half)
            focus_shifted = (d1 != d2)

        # ── Interpretation ────────────────────────────────────────────────────
        if label == "Highly Focused":
            interp = (
                f"The candidate is a specialist. {dominant_pct}% of publications fall under "
                f"'{dominant}', indicating deep expertise in a single domain."
            )
        elif label == "Moderately Focused":
            interp = (
                f"The candidate has a primary focus in '{dominant}' ({dominant_pct}%) "
                f"with exposure to {n_themes} additional theme(s). "
                + ("Research focus has shifted over time." if focus_shifted else "Focus has remained stable.")
            )
        elif label == "Interdisciplinary":
            interp = (
                f"The candidate demonstrates interdisciplinary research spanning {len(theme_counts)} "
                f"theme(s), led by '{dominant}' ({dominant_pct}%). "
                + ("A notable shift in research focus was detected over time." if focus_shifted else "")
            )
        else:
            interp = (
                f"The candidate publishes broadly across {len(theme_counts)} research areas "
                f"({label}), with '{dominant}' as the largest cluster ({dominant_pct}%). "
                f"This shows high adaptability and interdisciplinary engagement."
            )

        return {
            "total_publications_analyzed": total,
            "theme_distribution":          theme_distribution,
            "dominant_theme":              dominant,
            "dominant_theme_percentage":   dominant_pct,
            "theme_count":                 len(theme_counts),
            "diversity_score":             diversity_score,
            "variability_label":           label,
            "focus_shifted_over_time":     focus_shifted,
            "topic_trend_by_year":         topic_trend_by_year,
            "per_publication_themes":      per_pub,
            "interpretation":              interp,
        }