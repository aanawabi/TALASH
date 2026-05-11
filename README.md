# TALASH — AI-Powered CV Screening & Analysis System

**Talent Acquisition & Learning Automation for Smart Hiring**

An LLM-powered recruitment support system for university faculty hiring, built for the Large Language Models course at NUST SEECS.

---

## Features

- PDF ingestion and text extraction (PyMuPDF)
- Structured CV extraction via Google Gemini 2.5 Flash with Pydantic v2 validation
- Educational profile analysis — degree standardisation, QS rankings, CGPA normalisation, gap detection
- Professional experience analysis — career trajectory, seniority scoring, overlap/gap detection
- Research profile analysis — Research Impact Score, quartile distribution, publication trends
- Publication verification — offline ISSN/conference databases + live fallback (WoS, CORE)
- Topic variability analysis — Shannon entropy over 9 research theme clusters
- Co-author network analysis — collaboration frequency, team size, national vs. international
- Skill alignment analysis — evidence classification (strongly/partially/weakly/unsupported)
- Candidate ranking — composite score (education 25%, research 40%, experience 25%, skills 10%)
- Missing information detection with template and LLM-generated email drafting
- Candidate summary — statistical profile + on-demand Gemini narrative
- Per-candidate and aggregate PNG charts (12 chart types)
- Analysis Excel export (6 sheets)
- React 18 SPA with 10 pages, backed by FastAPI (19 endpoints)

---

## Project Structure

```
TALASH/
├── src/
│   ├── api/
│   │   └── main.py                      # FastAPI app — 19 endpoints
│   ├── analysis/
│   │   ├── educational_analyzer.py      # Degree analysis, QS rankings, CGPA normalisation
│   │   ├── experience_analyzer.py       # Career trajectory, seniority, gap detection
│   │   ├── research_profile_analyzer.py # Impact score, quartile distribution, publication trends
│   │   ├── publication_verifier.py      # Offline + live journal/conference verification
│   │   ├── topic_variability_analyzer.py# Shannon entropy topic diversity
│   │   ├── coauthor_analyzer.py         # Collaboration network analysis
│   │   ├── skill_alignment_analyzer.py  # Evidence-based skill verification
│   │   ├── candidate_ranker.py          # Composite score ranking
│   │   ├── missing_info_detector.py     # Missing field detection + email drafting
│   │   └── candidate_summarizer.py      # Stats summary + LLM narrative
│   ├── extraction/                      # Gemini extraction logic
│   ├── models/                          # Pydantic v2 CV schema
│   ├── preprocessing/                   # PDF parsing & text cleaning
│   ├── utils/                           # Config, export utilities
│   ├── visualization/
│   │   └── chart_generator.py           # Matplotlib/Seaborn chart generation
│   └── pipeline.py                      # Main processing pipeline
├── src/ui/react/                        # React 18 SPA (10 pages)
├── data/
│   ├── input_cvs/                       # Place CVs here for batch processing
│   ├── output/                          # Extracted JSON, CSV, Excel
│   ├── charts/                          # PNG charts (per-candidate + aggregate/)
│   └── emails/                          # Auto-generated email drafts
├── tests/
├── requirements.txt
├── run.py
└── .env.example
```

---

## Quick Start

### 1. Backend setup

```bash
git clone https://github.com/aanawabi/TALASH
cd TALASH

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

```bash
copy .env.example .env
# Add your Gemini API key to .env:
# GEMINI_API_KEY=your_key_here
```

Get a key at: https://makersuite.google.com/app/apikey

### 3. Run the backend

```bash
python run.py api
# API at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### 4. Run the React frontend

```bash
cd src/ui/react
npm install
npm start
# UI at http://localhost:3000
```

### 5. Process CVs from CLI

```bash
# Single CV
python run.py single path/to/cv.pdf

# Batch folder
python run.py process -i data/input_cvs -f excel
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-and-process` | Upload PDF and run full pipeline in one call |
| POST | `/upload` | Upload PDF only, returns `file_id` |
| POST | `/process/{file_id}` | Run extraction + analysis on uploaded file |
| POST | `/process-folder` | Batch process all PDFs in `data/input_cvs/` |
| GET | `/candidates` | List all processed candidates |
| GET | `/candidates/{id}` | Full extracted CV object |
| GET | `/candidates/{id}/analyze` | Run all analysers, return full analysis dict |
| POST | `/candidates/{id}/skill-alignment` | Skill alignment against a target job description |
| GET | `/candidates/{id}/emails` | Missing info detection + draft email templates |
| GET | `/candidates/{id}/charts` | List available chart filenames |
| GET | `/candidates/rank` | Rank all candidates by composite score |
| GET | `/download/{filename}` | Download generated file |

---

## Web Interface (React)

| Page | Description |
|------|-------------|
| Dashboard | Summary stats cards |
| Upload | Drag-and-drop PDF upload |
| Candidates | Searchable candidate table |
| Education | Degree timeline, QS rankings, grade breakdown |
| Experience | Career timeline, trajectory, overlap/gap warnings |
| Research | Journals, conferences, books, patents, supervision |
| Skills | Evidence-classified skill list |
| Missing Info | Missing fields + draft email viewer |
| Summary | Composite score, dimension bars, LLM narrative |
| Ranking | Ranked composite-score table across all candidates |
| Charts | Embedded per-candidate and aggregate charts |

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| LLM | Google Gemini 2.5 Flash |
| PDF Parsing | PyMuPDF (fitz) |
| Data Validation | Pydantic v2 |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + React Router + Recharts |
| Static Charts | Matplotlib + Seaborn |
| Storage | JSON + CSV flat files |
| Export | OpenPyXL / Pandas |

---

## Deliverables

### Module 1
- [x] PDF preprocessing (parsing, cleaning, batch ingestion)
- [x] LLM extraction pipeline (Gemini, schema-injecting prompt, Pydantic validation)
- [x] Relational CSV/JSON storage (9 tables linked by `candidate_id`)
- [x] FastAPI skeleton + CLI runner

### Module 2
- [x] Educational profile analysis (degree standardisation, grades, gaps)
- [x] Professional experience analysis (career trajectory, seniority, overlaps)
- [x] Research profile analysis (impact score, quartile distribution, publication trends)
- [x] Missing information detection + template email drafting
- [x] Candidate summary (statistical + LLM narrative)
- [x] 12 chart types (6 per-candidate, 6 aggregate)
- [x] Analysis Excel export (6 sheets)

### Module 3
- [x] Publication verifier (offline ISSN/CORE dicts + live WoS/CORE fallback)
- [x] Topic variability analyser (Shannon entropy, 9 theme clusters)
- [x] Co-author network analyser (frequency, team size, collaboration diversity)
- [x] Skill alignment analyser (4-level evidence classification, JD matching)
- [x] Candidate ranker (composite score with configurable weights)
- [x] QS World University Rankings 2024 integration
- [x] CGPA normalisation (4.0 and 5.0 scales to percentage)
- [x] React 18 SPA (10 pages, Recharts visualisations)
- [x] Full FastAPI backend (19 endpoints)

---

## Team

| Member | Role |
|--------|------|
| Affan Ahmad Basra (476173) | Backend, analysis modules, React UI |
| Amna Akhtar Nawabi (462939) | Frontend, co-author & topic analysers |
| Fatima Ehsan Niazi (466093) | Pipeline, charts, skill alignment, testing |

NUST SEECS — Large Language Models, Spring 2026