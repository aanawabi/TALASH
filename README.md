# TALASH - Smart HR Recruitment System

**Talent Acquisition & Learning Automation for Smart Hiring**

An AI-powered recruitment support system built using Large Language Models (LLMs) for CS 417 - Large Language Models course.

## Features

- PDF CV parsing and text extraction
- LLM-based structured information extraction using Google Gemini
- Relational database-like output format (CSV/Excel)
- Interactive web UI for recruiters (Streamlit)
- REST API for programmatic access
- Batch processing of multiple CVs

## Project Structure

```
Talash/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── extraction/       # LLM extraction logic
│   ├── models/           # Pydantic data models
│   ├── preprocessing/    # PDF parsing & text cleaning
│   ├── ui/               # Streamlit web interface
│   │   └── app.py        # Main UI application
│   ├── utils/            # Config, export utilities
│   └── pipeline.py       # Main processing pipeline
├── data/
│   ├── input_cvs/        # Place CVs here for processing
│   └── output/           # Extracted data appears here (JSON + CSV)
├── docs/
│   └── ARCHITECTURE.md   # System architecture
├── tests/                # Unit tests
├── requirements.txt      # Python dependencies
├── run.py                # Main entry point
├── .env.example          # Environment template
└── README.md
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd Talash

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
copy .env.example .env

# Edit .env and add your Gemini API key
# Get your key from: https://makersuite.google.com/app/apikey
```

### 3. Usage

#### Launch the Web UI

```bash
python run.py ui

# UI will be available at http://localhost:8501
```

#### Process a Single CV (CLI)

```bash
python run.py single path/to/cv.pdf
```

#### Process Multiple CVs (CLI)

```bash
# Place CVs in data/input_cvs/ folder
python run.py process -i data/input_cvs -f excel
```

#### Start API Server

```bash
python run.py api

# API will be available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

## Web Interface

TALASH includes a dark-themed recruiter dashboard built with Streamlit. Launch it with `python run.py ui`.

### Screens

| Screen | Description |
|--------|-------------|
| **Dashboard** | Overview of all uploaded CVs with processing stats and status summary |
| **Upload CVs** | Drag-and-drop PDF upload with real-time extraction progress |
| **Candidates** | Searchable and filterable table of all candidates with missing-info flags |
| **Candidate Profile** | Tabbed view of extracted data — Personal, Education, Experience, Skills, Publications |
| **Extraction Logs** | Timestamped log of every extraction event, filterable by level and file |

### How It Works

1. Upload one or more CV PDFs via the Upload CVs screen
2. The UI saves them to `data/input_cvs/` and runs the extraction pipeline automatically
3. Extracted data is stored as JSON in `data/output/` and loaded into the UI
4. Any previously extracted JSONs are auto-loaded when the app starts
5. Missing fields are flagged inline — the system can draft a follow-up email to the candidate automatically

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/upload` | POST | Upload single CV |
| `/process/{file_id}` | POST | Process uploaded CV |
| `/process-folder` | POST | Process all CVs in folder |
| `/list-cvs` | GET | List input CVs |
| `/outputs` | GET | List output files |
| `/download/{filename}` | GET | Download output file |

## Output Format

The system generates relational tables with the following structure:

### Tables Generated

1. **candidates** - Personal information (primary table)
2. **education** - Educational records
3. **experience** - Work experience
4. **skills** - Technical and soft skills
5. **journal_publications** - Journal papers
6. **conference_publications** - Conference papers
7. **supervisions** - Student supervision records
8. **patents** - Patent records
9. **books** - Authored/co-authored books

All tables are linked via `candidate_id` foreign key.

## Technology Stack

- **Python 3.10+**
- **Streamlit** - Recruiter web interface
- **FastAPI** - REST API framework
- **Google Gemini** - LLM for extraction
- **PyMuPDF** - PDF processing
- **Pandas** - Data manipulation
- **Pydantic** - Data validation

## Milestone 1 Deliverables

- [x] Pre-Processing Module (PDF parsing, text extraction)
- [x] System Architecture Design
- [x] LLM/NLP Pipeline Design
- [x] Database/Storage Design (relational CSV schema linked by candidate_id)
- [x] Web UI with 5 screens (Dashboard, Upload, Candidates, Profile, Logs)
- [x] Early Prototype with upload/read flow
- [x] Folder-based CV ingestion
- [x] Preliminary extraction from sample CVs

![img.png](img.png)

## Team

Affan Basra
Amna Akhtar Nawabi
Fatima Ehsan Niazi
(SEECS, NUST)

## License

Academic Project - NUST SEECS
