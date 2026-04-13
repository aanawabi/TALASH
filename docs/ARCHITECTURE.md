# TALASH System Architecture

## Overview

TALASH (Talent Acquisition & Learning Automation for Smart Hiring) is an AI-powered recruitment support system built using Large Language Models (LLMs). The system automates CV screening, candidate-job matching, academic and publication analysis.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TALASH SYSTEM ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   User/HR    │
                              │  Interface   │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │    Web    │    │    API    │    │    CLI    │
            │    App    │    │  Client   │    │  Script   │
            └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
                  │                │                │
                  └────────────────┼────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Upload    │  │   Process   │  │   Export    │  │   Query     │        │
│  │  Endpoint   │  │  Endpoint   │  │  Endpoint   │  │  Endpoint   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Processing Pipeline                                  │
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   PDF Parser    │───▶│  Text Cleaner   │───▶│  LLM Extractor  │         │
│  │   (PyMuPDF)     │    │                 │    │  (Gemini API)   │         │
│  └─────────────────┘    └─────────────────┘    └────────┬────────┘         │
│                                                          │                   │
│                                                          ▼                   │
│                                              ┌─────────────────┐            │
│                                              │  Structured CV  │            │
│                                              │     Models      │            │
│                                              └────────┬────────┘            │
│                                                       │                      │
│                                                       ▼                      │
│                                              ┌─────────────────┐            │
│                                              │    Exporter     │            │
│                                              │ (CSV/Excel/JSON)│            │
│                                              └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Data Layer                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Input CVs   │  │  Extracted  │  │   Output    │  │   Config    │        │
│  │  (PDF)      │  │    JSON     │  │ CSV/Excel   │  │   (.env)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Interaction and Data Flow

### 1. Input Processing Flow

```
PDF File → PDFParser → Raw Text → TextCleaner → Cleaned Text → LLM Extractor → Structured Data
```

### 2. Component Descriptions

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| PDF Parser | Extract text from PDF CVs | PyMuPDF, pdfplumber |
| Text Cleaner | Normalize and clean text | Python regex |
| LLM Extractor | Parse CV into structured fields | Google Gemini API |
| Exporter | Convert to relational format | Pandas, openpyxl |
| API Layer | REST endpoints for processing | FastAPI |

### 3. Data Flow Sequence

```
1. User uploads CV (PDF)
       ↓
2. PDF Parser extracts raw text
       ↓
3. Text Cleaner normalizes content
       ↓
4. LLM Extractor sends to Gemini
       ↓
5. Gemini returns JSON structure
       ↓
6. Parser validates & maps to models
       ↓
7. Exporter creates CSV/Excel output
       ↓
8. User downloads structured data
```

## Folder-Based CV Ingestion Design

```
data/
├── input_cvs/           # Drop PDFs here for processing
│   ├── candidate1.pdf
│   ├── candidate2.pdf
│   └── ...
│
└── output/              # Processed results appear here
    ├── cv_extraction_YYYYMMDD.xlsx
    ├── cv_extraction_YYYYMMDD_candidates.csv
    ├── cv_extraction_YYYYMMDD_education.csv
    ├── cv_extraction_YYYYMMDD_experience.csv
    └── individual_jsons/
        ├── candidate1.json
        └── candidate2.json
```

### Ingestion Process

1. **Folder Monitoring**: System watches `data/input_cvs/` for new PDFs
2. **Batch Processing**: CVs processed in configurable batches
3. **Output Generation**: Creates relational tables with foreign keys

## LLM/NLP Pipeline Design

### Gemini Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     LLM Extraction Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│   │   Cleaned    │     │   Prompt     │     │   Gemini     │   │
│   │   CV Text    │────▶│  Engineering │────▶│    API       │   │
│   └──────────────┘     └──────────────┘     └──────┬───────┘   │
│                                                     │            │
│                                                     ▼            │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│   │  Validated   │◀────│    JSON      │◀────│   Response   │   │
│   │  Pydantic    │     │   Parser     │     │    Text      │   │
│   │   Models     │     │              │     │              │   │
│   └──────────────┘     └──────────────┘     └──────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Prompt Engineering Strategy

1. **Structured Output**: Request JSON with exact schema
2. **Field Definitions**: Clear descriptions for each field
3. **Enum Mappings**: Predefined options for categorical fields
4. **Null Handling**: Explicit instructions for missing data

## Database/Storage Design

### Relational Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                    RELATIONAL DATA MODEL                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│    candidates    │  (Main Table)
├──────────────────┤
│ candidate_id PK  │────┐
│ full_name        │    │
│ email            │    │
│ phone            │    │
│ linkedin         │    │
│ source_file      │    │
│ extraction_time  │    │
└──────────────────┘    │
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  education   │  │  experience  │  │    skills    │
├──────────────┤  ├──────────────┤  ├──────────────┤
│candidate_id FK│ │candidate_id FK│ │candidate_id FK│
│degree_level  │  │job_title     │  │skill_name    │
│degree_title  │  │organization  │  │skill_category│
│institution   │  │start_date    │  │proficiency   │
│grade_value   │  │end_date      │  └──────────────┘
│normalized_%  │  │is_current    │
└──────────────┘  └──────────────┘

     ┌──────────────────┴──────────────────┐
     ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│journal_publications│            │conference_publications│
├──────────────────┤              ├──────────────────┤
│candidate_id FK   │              │candidate_id FK   │
│title             │              │title             │
│journal_name      │              │conference_name   │
│issn              │              │conference_rank   │
│impact_factor     │              │publisher         │
│quartile          │              │is_indexed        │
│author_role       │              │author_role       │
│is_wos_indexed    │              └──────────────────┘
│is_scopus_indexed │
└──────────────────┘

     ┌──────────────────┬──────────────────┐
     ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ supervisions │  │   patents    │  │    books     │
├──────────────┤  ├──────────────┤  ├──────────────┤
│candidate_id FK│ │candidate_id FK│ │candidate_id FK│
│student_name  │  │patent_number │  │book_title    │
│degree_level  │  │patent_title  │  │isbn          │
│thesis_title  │  │inventors     │  │publisher     │
│role          │  │filing_date   │  │publication_yr│
│status        │  │country       │  │role          │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Storage Format Options

| Format | Use Case | Pros | Cons |
|--------|----------|------|------|
| Excel (.xlsx) | Single file, multiple sheets | Human-readable, familiar | File size limits |
| CSV | Individual tables | Universal, lightweight | Multiple files |
| JSON | Individual CVs | Nested data, API-friendly | Not tabular |

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3.10+ | Core processing |
| API | FastAPI | REST endpoints |
| PDF Processing | PyMuPDF, pdfplumber | Text extraction |
| LLM | Google Gemini | Information extraction |
| Data Models | Pydantic | Validation & serialization |
| Data Export | Pandas | CSV/Excel generation |
| Configuration | python-dotenv | Environment management |

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

## Security Considerations

1. **API Key Management**: Gemini API key stored in .env (not committed)
2. **Input Validation**: File type checking, size limits
3. **CORS**: Configurable allowed origins
4. **No PII Logging**: Sensitive data not logged

## Scalability Design

1. **Batch Processing**: Process multiple CVs in parallel
2. **Async API**: Non-blocking request handling
3. **Configurable Limits**: Adjustable batch sizes and timeouts
4. **Stateless Processing**: Each CV processed independently
