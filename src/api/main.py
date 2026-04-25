"""
FastAPI Application for TALASH CV Processing System
Provides REST API endpoints for CV upload, processing, and analysis.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import shutil
import uuid
import logging
from datetime import datetime

# Import pipeline components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.preprocessing.pdf_parser import PDFParser
from src.preprocessing.text_cleaner import TextCleaner
from src.extraction.llm_extractor import CVExtractor
from src.utils.exporter import CVExporter
from src.utils.config import Config
from src.models.cv_models import ExtractedCV

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json, os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TALASH - Smart HR Recruitment System",
    description="AI-powered CV screening and candidate analysis using LLMs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CHARTS_DIR = Path("data/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config = Config()
pdf_parser = PDFParser()
text_cleaner = TextCleaner()
exporter = CVExporter(output_dir=config.output_folder)

# Store for processing jobs
processing_jobs: Dict[str, Dict[str, Any]] = {}


class ProcessingStatus(BaseModel):
    job_id: str
    status: str
    message: str
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None


class CVSummary(BaseModel):
    candidate_name: str
    email: Optional[str]
    education_count: int
    experience_count: int
    publication_count: int
    skills_count: int


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "TALASH CV Processing System",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "pdf_parser": "ready",
            "llm_extractor": "ready" if config.gemini_api_key else "missing_api_key",
            "exporter": "ready"
        },
        "config": {
            "input_folder": str(config.input_folder),
            "output_folder": str(config.output_folder),
            "model": config.gemini_model
        }
    }


@app.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload a single CV for processing.
    Returns the extracted text and a processing ID.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save uploaded file
    file_id = str(uuid.uuid4())[:8]
    upload_path = Path(config.input_folder) / f"{file_id}_{file.filename}"
    upload_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text
        extraction_result = pdf_parser.extract_text(str(upload_path))

        return {
            "file_id": file_id,
            "filename": file.filename,
            "status": "uploaded",
            "extraction_success": extraction_result["success"],
            "page_count": extraction_result.get("page_count", 0),
            "text_length": len(extraction_result.get("text", "")),
            "file_path": str(upload_path)
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/{file_id}")
async def process_cv(file_id: str, background_tasks: BackgroundTasks):
    """
    Process an uploaded CV using LLM extraction.
    """
    # Find the uploaded file
    input_path = Path(config.input_folder)
    matching_files = list(input_path.glob(f"{file_id}_*.pdf"))

    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = matching_files[0]

    if not config.gemini_api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Set GEMINI_API_KEY in .env file."
        )

    try:
        # Extract text
        extraction_result = pdf_parser.extract_text(str(file_path))
        if not extraction_result["success"]:
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")

        # Clean text
        cleaned_text = text_cleaner.prepare_for_llm(
            extraction_result["text"],
            max_length=config.max_cv_length
        )

        # Extract using LLM
        extractor = CVExtractor(
            api_key=config.gemini_api_key,
            model_name=config.gemini_model
        )
        extracted_cv = extractor.extract(cleaned_text, source_file=file_path.name)

        # Export to JSON
        json_path = exporter.export_single_cv_to_json(extracted_cv)

        # Prepare summary
        summary = CVSummary(
            candidate_name=extracted_cv.personal_info.full_name,
            email=extracted_cv.personal_info.email,
            education_count=len(extracted_cv.education),
            experience_count=len(extracted_cv.experience),
            publication_count=len(extracted_cv.journal_publications) + len(extracted_cv.conference_publications),
            skills_count=len(extracted_cv.skills)
        )

        return {
            "file_id": file_id,
            "status": "completed",
            "summary": summary.model_dump(),
            "output_file": json_path,
            "extracted_data": extracted_cv.model_dump()
        }

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-folder")
async def process_folder(folder_path: Optional[str] = None):
    """
    Process all CVs in a folder.
    """
    target_folder = folder_path or config.input_folder

    if not Path(target_folder).exists():
        raise HTTPException(status_code=404, detail="Folder not found")

    if not config.gemini_api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured"
        )

    try:
        from src.pipeline import CVProcessingPipeline

        pipeline = CVProcessingPipeline(config)
        results = pipeline.process_and_export(
            folder_path=target_folder,
            export_format="both"
        )

        return results

    except Exception as e:
        logger.error(f"Folder processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list-cvs")
async def list_cvs():
    """List all CVs in the input folder."""
    input_path = Path(config.input_folder)

    if not input_path.exists():
        return {"cvs": [], "count": 0}

    pdf_files = list(input_path.glob("*.pdf")) + list(input_path.glob("*.PDF"))

    cvs = []
    for pdf in pdf_files:
        cvs.append({
            "filename": pdf.name,
            "size_kb": pdf.stat().st_size / 1024,
            "modified": datetime.fromtimestamp(pdf.stat().st_mtime).isoformat()
        })

    return {
        "cvs": cvs,
        "count": len(cvs),
        "folder": str(input_path)
    }


@app.get("/outputs")
async def list_outputs():
    """List all output files."""
    output_path = Path(config.output_folder)

    if not output_path.exists():
        return {"files": [], "count": 0}

    files = []
    for f in output_path.iterdir():
        if f.is_file():
            files.append({
                "filename": f.name,
                "size_kb": f.stat().st_size / 1024,
                "type": f.suffix,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })

    return {
        "files": files,
        "count": len(files),
        "folder": str(output_path)
    }


@app.get("/download/{filename}")
async def download_output(filename: str):
    """Download an output file."""
    file_path = Path(config.output_folder) / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/candidates")
async def list_candidates():
    output_dir = Path("data/output")
    candidates = []
    for json_file in sorted(output_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            pi = data.get("personal_info", {})
            candidates.append({
                "candidate_id":            json_file.stem,
                "full_name":               pi.get("full_name"),
                "email":                   pi.get("email"),
                "phone":                   pi.get("phone"),
                "linkedin":                pi.get("linkedin"),
                "website":                 pi.get("website"),
                "source_file":             data.get("source_file"),
                "extraction_timestamp":    data.get("extraction_timestamp"),
                "education":               data.get("education", []),
                "experience":              data.get("experience", []),
                "skills":                  data.get("skills", []),
                "journal_publications":    data.get("journal_publications", []),
                "conference_publications": data.get("conference_publications", []),
                "supervisions":            data.get("supervisions", []),
                "patents":                 data.get("patents", []),
                "books":                   data.get("books", []),
            })
        except Exception:
            pass
    return candidates


@app.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: str):
    from fastapi import HTTPException
    json_file = Path("data/output") / f"{candidate_id}.json"
    if not json_file.exists():
        raise HTTPException(status_code=404, detail="Candidate not found")
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
    pi = data.get("personal_info", {})
    return {
        "candidate_id": json_file.stem,
        "full_name":    pi.get("full_name"),
        "email":        pi.get("email"),
        "phone":        pi.get("phone"),
        **data,
    }


@app.post("/process/{filename}")
async def process_file(filename: str):
    from fastapi import HTTPException
    import subprocess, sys
    pdf_path = Path("data/input_cvs") / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="File not found in input folder")

    result = subprocess.run(
        [sys.executable, "run.py", "single", str(pdf_path)],
        capture_output=True, text=True
    )

    output_dir = Path("data/output")
    json_files = sorted(output_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
    candidate = None
    if json_files:
        with open(json_files[0], encoding="utf-8") as f:
            raw = json.load(f)
        pi = raw.get("personal_info", {})
        candidate = {
            "candidate_id": json_files[0].stem,
            "full_name":    pi.get("full_name"),
            "email":        pi.get("email"),
            **raw,
        }

    return {
        "success":   result.returncode == 0,
        "candidate": candidate,
        "stdout":    result.stdout[-500:] if result.stdout else "",
        "stderr":    result.stderr[-200:] if result.stderr else "",
    }


@app.post("/upload-and-process")
async def upload_and_process(file: UploadFile = File(...)):
    import subprocess, sys

    # Save to input folder
    input_dir = Path("data/input_cvs")
    input_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = input_dir / file.filename

    with open(pdf_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Run pipeline — force UTF-8 encoding on Windows
    result = subprocess.run(
        [sys.executable, "run.py", "single", str(pdf_path)],
        capture_output=True,
        encoding='utf-8',  # ← force UTF-8
        errors='replace',  # ← replace unencodable chars instead of crashing
        env={**os.environ, "PYTHONIOENCODING": "utf-8"}  # ← tell subprocess to use UTF-8
    )

    # Find newest JSON output
    output_dir = Path("data/output")
    json_files = sorted(output_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
    candidate = None
    if json_files:
        with open(json_files[0], encoding="utf-8") as f:
            raw = json.load(f)
        pi = raw.get("personal_info", {})
        candidate = {
            "candidate_id": json_files[0].stem,
            "full_name": pi.get("full_name"),
            "email": pi.get("email"),
            "phone": pi.get("phone"),
            **raw,
        }

    return {
        "success": result.returncode == 0,
        "candidate": candidate,
        "stdout": result.stdout[-500:] if result.stdout else "",
        "stderr": result.stderr[-200:] if result.stderr else "",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api_host, port=config.api_port)
