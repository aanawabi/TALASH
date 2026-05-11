# Module 3 – Integration Progress Log

Branch: `feature/module3-integration`

---

## What Was Missing (Starting State)

All backend analysis classes were implemented but **disconnected** from the web application:

- FastAPI had no endpoints that called any analyzer — it only extracted and stored raw CV data.
- The React frontend displayed raw extracted fields; it never received analyzer output.
- Analysis results were printed to the CLI (`run.py single`) but never saved to JSON or served via API.
- `CandidateSummarizer`, `CandidateRanker`, email drafts, and aggregate charts were inaccessible from the UI.
- `EducationalAnalyzer` was missing: THE/QS institutional ranking lookup, gap justification against employment, and an overall educational strength interpretation.

---

## Changes Made

---

### 1. New API Endpoints — `src/api/main.py`

#### `GET /candidates/{candidate_id}/analyze`

Runs all analysis modules on an already-extracted candidate JSON and returns the full analysis payload.

**Query params:**
- `include_summary=false` (default) — skips the LLM narrative to keep the endpoint fast
- `include_summary=true` — also calls `CandidateSummarizer` for the Gemini-generated narrative

**Returns:**
```json
{
  "candidate_id": "...",
  "edu_analysis":       { ... },   // EducationalAnalyzer
  "exp_analysis":       { ... },   // ExperienceAnalyzer
  "res_analysis":       { ... },   // ResearchProfileAnalyzer (journals, conf, supervision, books, patents)
  "missing_info":       { ... },   // MissingInfoDetector
  "topic_analysis":     { ... },   // TopicVariabilityAnalyzer (Module 3.6)
  "coauthor_analysis":  { ... },   // CoAuthorAnalyzer (Module 3.7)
  "skill_analysis":     { ... },   // SkillAlignmentAnalyzer (Module 3.9)
  "rank_result":        { ... },   // CandidateRanker (extra credit)
  "summary":            null        // CandidateSummarizer, only when include_summary=true
}
```

**How it works:**
1. Loads the candidate's JSON from `data/output/{candidate_id}.json`
2. Reconstructs an `ExtractedCV` Pydantic object via `ExtractedCV.model_validate(data)`
3. Passes the CV through every analyzer in sequence
4. Returns all results in a single response

---

#### `GET /candidates/{candidate_id}/emails`

Returns missing-information detection results and draft emails for a candidate.

**Returns:**
```json
{
  "candidate_id": "...",
  "has_missing_info": true,
  "total_missing_fields": 3,
  "draft_emails": { "contact": "...", "academic": "..." },
  "all_missing": ["...", "..."]
}
```

---

### 2. React API Client — `src/ui/react/src/api/index.js`

Added two new exported functions:

- `analyzeCandidate(candidateId, includeSummary = false)` → calls `GET /candidates/{id}/analyze`
- `getCandidateEmails(candidateId)` → calls `GET /candidates/{id}/emails`

---

---

### 3. MissingInfo Page Rewrite — `src/ui/react/src/pages/MissingInfo.js`

Full rewrite to consume `getCandidateEmails()` instead of doing client-side field detection.

**What changed:**
- Calls `getCandidateEmails(candidate_id)` on mount / candidate change; shows a spinner while loading
- **Stats row**: Missing Fields count, Draft Emails count, Status pill
- **Missing fields panel**: flat list of `all_missing` strings returned by `MissingInfoDetector`
- **Draft email panel**: renders `draft_emails.contact` and `draft_emails.academic` (or any keys returned) with a tab switcher when multiple email types are present; Copy button copies the active email to clipboard
- Shows a green "Profile appears complete" banner when `has_missing_info` is false

---

### 4. Research Page Rewrite — `src/ui/react/src/pages/Research.js`

Full rewrite of the Research page to consume `analyzeCandidate()` instead of doing client-side computation on raw CV data.

**What changed:**
- Calls `analyzeCandidate(candidate_id)` on mount / candidate change; shows a spinner while loading
- **Stats row** now shows: Total Publications, Research Impact Score, Q1/Q2 count, Profile Tier — all from `res_analysis`
- **Overview charts**: Publications-by-year bar chart + Quartile distribution pie chart (both from verified analyzer data)
- **Summary pill row**: WoS indexed count, Scopus count, Avg IF, A* conferences, PhD/MS supervised, patents, books
- **6-tab layout**:
  | Tab | Data source | Key info shown |
  |-----|-------------|----------------|
  | Journal Papers | `res_analysis.journal_analyses` | Verified IF, quartile, WoS/Scopus, authorship role, quality label |
  | Conference Papers | `res_analysis.conference_analyses` | CORE rank, A* flag, maturity label, indexing, quality label |
  | Supervision | `res_analysis.supervision` | MS/PhD main vs co-supervisor counts, papers with students |
  | Books & Patents | `res_analysis.books`, `res_analysis.patents` | Full book/patent details with credibility notes |
  | Topic Variability (3.6) | `topic_analysis` | Diversity score, theme distribution progress bars, topic trend chart |
  | Co-Author Network (3.7) | `coauthor_analysis` | Unique co-authors, recurring collaborators, avg team size, top collaborators bars |

---

---

### 5. Ranking Page — `src/ui/react/src/pages/Ranking.js` + `GET /candidates/rank`

New backend endpoint and React page for multi-candidate ranking.

**Backend (`src/api/main.py`):**
- `GET /candidates/rank` — loads every JSON in `data/output/`, runs `EducationalAnalyzer`, `ExperienceAnalyzer`, `ResearchProfileAnalyzer`, `SkillAlignmentAnalyzer` on each, then passes all results to `CandidateRanker.rank_candidates()`. Returns a sorted list with rank positions, composite scores, dimension scores, and aggregate stats. Inserted before `GET /candidates/{candidate_id}` so FastAPI doesn't capture "rank" as a candidate_id path parameter.

**API client (`src/ui/react/src/api/index.js`):**
- Added `rankCandidates()` → `GET /candidates/rank`

**React page:**
- "Run Ranking" button triggers the expensive API call on demand
- Stats row: total candidates, average score, highest, lowest
- Dimension leaders row (4 cards: edu/res/exp/skills leader + score)
- Composite score bar chart (Recharts BarChart, Cell colored green/amber/red by score)
- Leaderboard table: rank badge (gold/silver/bronze for top 3), candidate name, tier badge, composite score, 4 mini progress bars per dimension

**Routing:**
- Route `/ranking` added to `App.js`
- "Ranking" nav item with `Trophy` icon added to Sidebar.js under Reports

---

### 6. Comparative Dashboard — `src/ui/react/src/pages/Dashboard.js`

Enhanced Dashboard with a live comparative analysis section that appears when ≥2 candidates are loaded (no extra API calls — uses raw data from AppContext).

**Charts added:**
- **Publications per candidate**: stacked bar chart (Journals + Conferences), sorted by total, top 12
- **Highest degree distribution**: pie chart (PhD / Masters-MPhil / Bachelor's / Other)
- **Skills count per candidate**: horizontal bar chart, top 12 by skills volume
- **Experience positions per candidate**: horizontal bar chart, top 12 by position count

All charts use Recharts and are colored with the global CSS palette variables.

---

### 7. EducationalAnalyzer completions — `src/analysis/educational_analyzer.py`

Three missing requirements from Req 3.1 now implemented:

**THE/QS Institutional Ranking Lookup (Req 3.1-v):**
- Static `_QS_DB` dictionary of ~150 universities with QS World 2024 rank numbers and official names
- Covers top 100 global universities + major Pakistani institutions (NUST, LUMS, Aga Khan, QAU, UET, COMSATS, FAST, etc.)
- `_lookup_qs(institution)` normalizes names (lowercasing, strips noise words) and does exact then substring matching
- Returns `{ official_name, rank_number, source, tier }` where tier is Top 100/300/500/700/1000+
- `edu_analysis.institutional_rankings` is a sorted list of matched institutions
- Education page now shows a table of matched QS rankings instead of the "coming soon" placeholder

**Gap Justification vs Employment (Req 3.1-viii):**
- `_extract_year()` helper parses year from any date string format using regex
- For each education gap, checks if any experience record spans the gap period
- `edu_analysis.gaps_with_justification` is a list of dicts with: `gap_years`, `from_degree`, `to_degree`, `gap_start_year`, `gap_end_year`, `justified` (bool), `justification` (text), `employment_during_gap` (list of matching jobs)
- Education page gap detection card now shows green "Justified" or amber "Unexplained" per gap, with justification text

**Educational Strength Interpretation (Req 3.1-ix):**
- `_interpret_strength()` generates a human-readable text from PhD/Masters/Bachelor status, average grade, foreign education flag, and top institutional rank
- `edu_analysis.educational_strength_interpretation` is a single descriptive string
- Shown as a blue banner near the top of the Education page

---

### 8. Chart API Endpoint + Charts Page Fix — `src/api/main.py` + `src/ui/react/src/pages/Charts.js`

**Problem:** The old `Charts.js` probed charts via HEAD requests using an uppercase folder name transformation, but chart folders are generated with mixed-case names by `ChartGenerator._safe_name()`. This caused mismatches (e.g., "Aamina_Akbar" vs "AAMINA_AKBAR").

**Fix:**
- New `GET /candidates/{candidate_id}/charts` endpoint — looks up the candidate's name from their JSON, applies `_safe_chart_name()` (mirrors ChartGenerator logic), then does a **case-insensitive** directory scan to find the actual folder, returns chart file list with proper URLs
- New `getCandidateCharts(candidateId)` API client function
- `Charts.js` rewritten to call the API endpoint on candidate change instead of manual HEAD probing — eliminates all naming mismatch issues

---

