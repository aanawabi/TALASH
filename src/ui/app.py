import streamlit as st
import pandas as pd
from datetime import datetime
import time
import json
import glob
import os
from pathlib import Path

# ─── Path to your pipeline's output folder ────────────────────────────────────
OUTPUT_DIR = Path("data/output")


def load_candidate_from_json(json_path: str) -> dict:
    """Convert a pipeline JSON file into the UI candidate dict format."""
    with open(json_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    pi = d.get("personal_info", {})

    # ── Personal info ──
    personal = {
        "Full name":  pi.get("full_name")  or "—",
        "Email":      pi.get("email")      or "—",
        "Phone":      pi.get("phone")      or "—",
        "Address":    pi.get("address")    or "—",
        "LinkedIn":   pi.get("linkedin")   or "—",
        "GitHub":     pi.get("website")    or "—",
        "ORCID":      pi.get("orcid")      or "—",
    }
    # Remove rows that are all dashes to keep it clean
    personal = {k: v for k, v in personal.items() if v != "—" or k in ("Email", "Phone")}

    # ── Education ──
    education = []
    for e in d.get("education", []):
        education.append({
            "Degree":        e.get("degree_title") or "—",
            "Level":         e.get("degree_level") or "—",
            "Specialization":e.get("specialization") or "—",
            "Institution":   e.get("institution") or "—",
            "Country":       e.get("country") or "—",
            "From":          str(e.get("start_year") or "—"),
            "To":            str(e.get("end_year")   or "—"),
            "Grade":         e.get("grade_value")  or "—",
            "Grade Type":    e.get("grade_type")   or "—",
        })

    # ── Experience ──
    experience = []
    for e in d.get("experience", []):
        experience.append({
            "Title":        e.get("job_title")      or "—",
            "Organization": e.get("organization")   or "—",
            "Location":     e.get("location")       or "—",
            "From":         e.get("start_date")     or "—",
            "To":           "Present" if e.get("is_current") else (e.get("end_date") or "—"),
            "Type":         e.get("employment_type") or "—",
        })

    # ── Skills ──
    skills_raw = d.get("skills", [])
    skills = [s.get("skill_name", "") for s in skills_raw if s.get("skill_name")]

    # ── Publications ──
    journals = []
    for p in d.get("journal_publications", []):
        journals.append({
            "Title":   p.get("title")   or "—",
            "Journal": p.get("journal") or "—",
            "Year":    str(p.get("year") or "—"),
            "Role":    p.get("author_role") or "—",
            "Type":    "Journal",
        })
    conferences = []
    for p in d.get("conference_publications", []):
        conferences.append({
            "Title":      p.get("title")      or "—",
            "Conference": p.get("conference") or "—",
            "Year":       str(p.get("year")   or "—"),
            "Role":       p.get("author_role") or "—",
            "Type":       "Conference",
        })
    publications = journals + conferences

    # ── Missing field detection ──
    missing = []
    if not pi.get("email"):   missing.append("Email missing")
    if not pi.get("phone"):   missing.append("Phone missing")
    if education:
        for e in education:
            if e["Grade"] == "—":
                missing.append(f"Grade missing ({e['Degree']})")

    name = pi.get("full_name") or Path(json_path).stem.replace("_", " ")

    return {
        "id":           Path(json_path).stem,
        "name":         name,
        "file":         d.get("source_file", Path(json_path).name),
        "uploaded":     datetime.fromisoformat(d["extraction_timestamp"]).strftime("%d %b %Y, %H:%M")
                        if d.get("extraction_timestamp") else "Unknown",
        "status":       "Processed",
        "missing":      missing,
        "personal":     personal,
        "education":    education,
        "experience":   experience,
        "skills":       skills,
        "publications": publications,
        "_json_path":   json_path,
    }


def scan_output_folder():
    """Load all JSON files from the output folder, skipping already loaded or cleared ones."""
    if not OUTPUT_DIR.exists():
        return
    loaded_ids  = {c["id"] for c in st.session_state.candidates}
    cleared_ids = st.session_state.get("cleared_ids", set())
    for json_file in sorted(OUTPUT_DIR.glob("*.json")):
        candidate_id = json_file.stem
        if candidate_id in loaded_ids or candidate_id in cleared_ids:
            continue
        try:
            candidate = load_candidate_from_json(str(json_file))
            st.session_state.candidates.append(candidate)
            loaded_ids.add(candidate_id)
        except Exception as e:
            st.session_state.logs.insert(0, {
                "time": datetime.now().strftime("%H:%M:%S"),
                "file": json_file.name,
                "level": "error",
                "msg": f"Failed to load {json_file.name}",
                "detail": str(e),
            })

st.set_page_config(
    page_title="TALASH — Smart HR Recruitment",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background-color: #1a1a1a; color: #e8e8e8; }

[data-testid="stSidebar"] {
    background-color: #222222 !important;
    border-right: 1px solid #333 !important;
}
[data-testid="stSidebar"] * { color: #c0c0c0 !important; }

/* Hide sidebar collapse button — covers all Streamlit versions */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[kind="header"],
section[data-testid="stSidebar"] > div > div > div > button,
.st-emotion-cache-zq5wmm,
.st-emotion-cache-1dp5vir { display: none !important; }

.block-container {
    padding: 2rem 2.5rem 2rem 2.5rem !important;
    max-width: 100% !important;
}

h1, h2, h3 {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    color: #f0f0f0 !important;
}

[data-testid="metric-container"] {
    background: #2a2a2a;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
}
[data-testid="metric-container"] label {
    color: #888 !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 600 !important;
    color: #f0f0f0 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] { display: none; }

[data-testid="stDataFrame"] {
    background: #2a2a2a !important;
    border-radius: 10px !important;
    border: 1px solid #333 !important;
}

.stButton > button {
    background: #2e2e2e;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #383838;
    border-color: #555;
    color: #fff;
}

[data-testid="stFileUploader"] {
    background: #2a2a2a;
    border: 1.5px dashed #444;
    border-radius: 12px;
    padding: 1rem;
}
[data-testid="stFileUploader"] * { color: #aaa !important; }

.stSelectbox > div > div,
.stTextInput > div > div {
    background: #2a2a2a !important;
    border: 1px solid #3a3a3a !important;
    border-radius: 8px !important;
    color: #e0e0e0 !important;
}

[data-testid="stExpander"] {
    background: #252525;
    border: 1px solid #333;
    border-radius: 10px;
}
[data-testid="stExpander"] summary { color: #ddd !important; font-weight: 500; }

hr { border-color: #333 !important; }

[data-testid="stTabs"] [role="tab"] {
    color: #888 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #fff !important;
    border-bottom: 2px solid #4f8ef7 !important;
}
[data-testid="stTabs"] [role="tabpanel"] {
    background: transparent !important;
    padding-top: 1rem;
}

.stAlert { border-radius: 8px !important; border: none !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1a1a1a; }
::-webkit-scrollbar-thumb { background: #3a3a3a; border-radius: 3px; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Session state init ───────────────────────────────────────────────────────
if "candidates" not in st.session_state:
    st.session_state.candidates = []

if "logs" not in st.session_state:
    st.session_state.logs = []

if "selected_candidate" not in st.session_state:
    st.session_state.selected_candidate = None

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "cleared_ids" not in st.session_state:
    st.session_state.cleared_ids = set()

# Auto-load any existing JSONs from the output folder on every page load
scan_output_folder()


# ─── Helper: render HTML safely ───────────────────────────────────────────────
def html(content: str):
    """Always renders with unsafe_allow_html=True."""
    st.markdown(content, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    cls = {
        "Processed": "badge-processed",
        "Pending":   "badge-pending",
        "Error":     "badge-error",
    }.get(status, "badge-info")
    return (
        f'<span style="display:inline-block;padding:3px 12px;border-radius:20px;'
        f'font-size:0.78rem;font-weight:500;'
        + {
            "badge-processed": "background:#1a3a2a;color:#4caf7d;border:1px solid #2d5a3d;",
            "badge-pending":   "background:#3a2e1a;color:#d4a044;border:1px solid #5a4520;",
            "badge-error":     "background:#3a1a1a;color:#e07070;border:1px solid #5a2a2a;",
            "badge-info":      "background:#1a2a3a;color:#4a9fd4;border:1px solid #2a4a6a;",
        }[cls]
        + f'">{status}</span>'
    )


def log_dot_color(level: str) -> str:
    return {"success": "#4caf7d", "warning": "#d4a044", "error": "#e07070", "info": "#4a9fd4"}.get(level, "#888")


def candidates_table(candidates: list):
    """Render the candidates table as clean HTML."""
    rows = ""
    for c in candidates:
        if c["missing"]:
            missing_html = " ".join([
                f'<span style="background:#3a2e1a;color:#d4a044;font-size:0.75rem;'
                f'padding:2px 8px;border-radius:8px;border:1px solid #5a4520;">{m}</span>'
                for m in c["missing"]
            ])
        else:
            missing_html = "<span style='color:#444'>—</span>"

        rows += f"""
        <tr style="border-bottom:1px solid #2a2a2a;">
            <td style="padding:12px 8px 12px 0;color:#ddd;font-weight:500;">{c['name']}</td>
            <td style="padding:12px 8px;color:#666;font-family:'DM Mono',monospace;font-size:0.78rem;">{c['file']}</td>
            <td style="padding:12px 8px;color:#777;">{c['uploaded']}</td>
            <td style="padding:12px 8px;">{missing_html}</td>
            <td style="padding:12px 0;">{status_badge(c['status'])}</td>
        </tr>"""

    html(f"""
    <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
      <thead>
        <tr style="border-bottom:1px solid #333;">
          <th style="text-align:left;padding:8px 8px 10px 0;color:#666;font-weight:400;width:22%">Candidate</th>
          <th style="text-align:left;padding:8px 8px 10px;color:#666;font-weight:400;width:22%">File</th>
          <th style="text-align:left;padding:8px 8px 10px;color:#666;font-weight:400;width:16%">Uploaded</th>
          <th style="text-align:left;padding:8px 8px 10px;color:#666;font-weight:400;width:22%">Missing info</th>
          <th style="text-align:left;padding:8px 0 10px;color:#666;font-weight:400;width:18%">Status</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    html("""
    <div style="padding:1.2rem 1rem 1rem;border-bottom:1px solid #333;margin-bottom:0.5rem;">
        <div style="font-size:1.2rem;font-weight:600;color:#f0f0f0;letter-spacing:0.03em;">TALASH</div>
        <div style="font-size:0.75rem;color:#555;margin-top:2px;">Smart HR Recruitment</div>
    </div>
    """)

    nav_pages = ["Dashboard", "Upload CVs", "Candidates", "Logs"]
    nav_icons = ["◉", "◎", "◈", "◍"]

    for icon, pg in zip(nav_icons, nav_pages):
        if st.button(f"{icon}  {pg}", key=f"nav_{pg}", use_container_width=True):
            st.session_state.page = pg
            st.rerun()

    st.markdown("---")
    total_c    = len(st.session_state.candidates)
    processed_c = sum(1 for c in st.session_state.candidates if c["status"] == "Processed")
    html(f"<div style='font-size:0.75rem;color:#555;padding:0 0.5rem'>{processed_c}/{total_c} CVs processed</div>")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Dashboard":
    st.markdown("# Dashboard")
    html('<div style="color:#777;font-size:0.9rem;margin-top:-0.8rem;margin-bottom:1.5rem;">Overview of all uploaded candidates and processing status</div>')

    candidates = st.session_state.candidates
    total     = len(candidates)
    processed = sum(1 for c in candidates if c["status"] == "Processed")
    pending   = sum(1 for c in candidates if c["status"] == "Pending")
    errors    = sum(1 for c in candidates if c["status"] == "Error")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total CVs",  total)
    c2.metric("Processed",  processed)
    c3.metric("Pending",    pending)
    c4.metric("Errors",     errors)

    # Colour the metric values
    html("""<style>
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetricValue"] { color: #4caf7d !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetricValue"] { color: #d4a044 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stMetricValue"] { color: #e07070 !important; }
    </style>""")

    html("<br>")
    dash_col1, dash_col2 = st.columns([5, 1])
    with dash_col1:
        st.markdown("### Recent candidates")
    with dash_col2:
        if candidates:
            if st.button("🗑 Clear", key="dash_clear"):
                st.session_state.cleared_ids.update(c["id"] for c in st.session_state.candidates)
                st.session_state.candidates = []
                st.session_state.selected_candidate = None
                st.rerun()

    if not candidates:
        html("""
        <div style="background:#242424;border:1px solid #2d2d2d;border-radius:10px;
                    padding:2.5rem;text-align:center;color:#555;font-size:0.9rem;">
            No CVs uploaded yet. Click <b style="color:#888">+ Upload new CVs</b> to get started.
        </div>
        """)
    else:
        rows = ""
        for c in candidates:
            rows += f"""
            <tr style="border-bottom:1px solid #2a2a2a;">
                <td style="padding:11px 12px 11px 0;color:#ddd;font-weight:500;">{c['name']}</td>
                <td style="padding:11px 12px;color:#777;">{c['uploaded']}</td>
                <td style="padding:11px 0;">{status_badge(c['status'])}</td>
            </tr>"""
        html(f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
          <thead>
            <tr style="border-bottom:1px solid #333;">
              <th style="text-align:left;padding:8px 12px 10px 0;color:#666;font-weight:400;">Name</th>
              <th style="text-align:left;padding:8px 12px 10px;color:#666;font-weight:400;">Uploaded</th>
              <th style="text-align:left;padding:8px 0 10px;color:#666;font-weight:400;">Status</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        """)

    html("<br>")
    if st.button("+ Upload new CVs"):
        st.session_state.page = "Upload CVs"
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — UPLOAD CVs
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Upload CVs":
    st.markdown("# Upload CVs")
    html('<div style="color:#777;font-size:0.9rem;margin-top:-0.8rem;margin-bottom:1.5rem;">Upload one or multiple PDF files to begin extraction</div>')

    # Show success feedback from previous extraction
    if st.session_state.get("upload_success"):
        n = st.session_state.pop("upload_success")
        st.success(f"✓ {n} file(s) extracted and loaded successfully.")
        st.balloons()

    uploaded_files = st.file_uploader(
        "Drag and drop CV files here — PDF format only",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        html("<br>")
        st.markdown("### Queued files")

        valid, invalid = [], []
        for f in uploaded_files:
            (valid if f.type == "application/pdf" else invalid).append(f)

        for f in valid:
            size_kb = round(f.size / 1024)
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                html(f"<div style='color:#ddd;font-size:0.88rem;padding:6px 0;'>📄 {f.name}</div>")
            with col2:
                html(f"<div style='color:#666;font-size:0.82rem;padding:8px 0;'>{size_kb} KB</div>")
            with col3:
                html('<span style="display:inline-block;padding:3px 12px;border-radius:20px;font-size:0.78rem;font-weight:500;background:#1a3a2a;color:#4caf7d;border:1px solid #2d5a3d;">Ready</span>')

        for f in invalid:
            html(f'<span style="display:inline-block;padding:3px 12px;border-radius:20px;font-size:0.78rem;background:#3a1a1a;color:#e07070;border:1px solid #5a2a2a;">✗ {f.name} — not a PDF</span>')

        html("<br>")

        if st.button(f"▶  Start extraction on {len(valid)} file(s)"):
            progress = st.progress(0, text="Starting extraction...")

            # Save uploaded files to data/input_cvs so the pipeline can read them
            input_dir = Path("data/input_cvs")
            input_dir.mkdir(parents=True, exist_ok=True)

            saved_paths = []
            for f in valid:
                save_path = input_dir / f.name
                with open(save_path, "wb") as out:
                    out.write(f.getbuffer())
                saved_paths.append(save_path)

            # Run the pipeline for each file
            import subprocess, sys
            for i, (f, pdf_path) in enumerate(zip(valid, saved_paths)):
                progress.progress((i + 1) / len(valid), text=f"Extracting {f.name}...")

                result = subprocess.run(
                    [sys.executable, "run.py", "single", str(pdf_path)],
                    capture_output=True, text=True
                )

                # Find the JSON that was just created
                if OUTPUT_DIR.exists():
                    json_files = sorted(OUTPUT_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)
                    already_loaded = {c["id"] for c in st.session_state.candidates}
                    for jf in json_files:
                        if jf.stem not in already_loaded:
                            try:
                                candidate = load_candidate_from_json(str(jf))
                                st.session_state.candidates.append(candidate)
                                st.session_state.logs.insert(0, {
                                    "time": datetime.now().strftime("%H:%M:%S"),
                                    "file": f.name, "level": "success",
                                    "msg": f"Extracted: {candidate['name']}",
                                    "detail": f"{len(candidate['education'])} education, "
                                              f"{len(candidate['experience'])} experience, "
                                              f"{len(candidate['skills'])} skills",
                                })
                            except Exception as e:
                                st.session_state.logs.insert(0, {
                                    "time": datetime.now().strftime("%H:%M:%S"),
                                    "file": f.name, "level": "error",
                                    "msg": "JSON load failed after extraction",
                                    "detail": str(e),
                                })
                            break

                if result.returncode != 0:
                    st.session_state.logs.insert(0, {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "file": f.name, "level": "error",
                        "msg": f"Pipeline error on {f.name}",
                        "detail": result.stderr[:200] if result.stderr else "Unknown error",
                    })

            progress.empty()
            st.session_state["upload_success"] = len(valid)
            st.rerun()

    else:
        html("""
        <div style="background:#242424;border:1px solid #333;border-radius:10px;
                    padding:1.5rem;margin-top:1rem;color:#666;font-size:0.85rem;">
            <b style="color:#888">Supported format:</b> PDF only &nbsp;·&nbsp;
            <b style="color:#888">Multiple files:</b> Yes &nbsp;·&nbsp;
            <b style="color:#888">Max size:</b> 10 MB per file
        </div>
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — CANDIDATE LIST
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Candidates":
    st.markdown("# Candidates")
    html('<div style="color:#777;font-size:0.9rem;margin-top:-0.8rem;margin-bottom:1.5rem;">All uploaded candidates and their extraction results</div>')

    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search = st.text_input("Search", placeholder="Search by name or file...", label_visibility="collapsed")
    with col_filter:
        status_filter = st.selectbox("Status", ["All", "Processed", "Pending", "Error"], label_visibility="collapsed")

    filtered = st.session_state.candidates
    if search:
        filtered = [c for c in filtered if search.lower() in c["name"].lower() or search.lower() in c["file"].lower()]
    if status_filter != "All":
        filtered = [c for c in filtered if c["status"] == status_filter]

    html("<br>")
    if not filtered:
        html("""
        <div style="background:#242424;border:1px solid #2d2d2d;border-radius:10px;
                    padding:2.5rem;text-align:center;color:#555;font-size:0.9rem;">
            No candidates found. Try adjusting your filters or upload some CVs first.
        </div>
        """)
    else:
        candidates_table(filtered)

    if st.session_state.candidates:
        html("<br>")
        col_prof, col_clear = st.columns([3, 1])
        with col_prof:
            st.markdown("**Open a candidate profile:**")
            # Show "Name — filename.pdf" so duplicates are distinguishable
            options = [
                f"{c['name']}  —  {c['file']}"
                for c in st.session_state.candidates
            ]
            selected_idx = st.selectbox(
                "Candidate", range(len(options)),
                format_func=lambda i: options[i],
                label_visibility="collapsed"
            )
            if st.button("View profile →"):
                st.session_state.selected_candidate = st.session_state.candidates[selected_idx]
                st.session_state.page = "Candidate Profile"
                st.rerun()
        with col_clear:
            st.markdown("**Clear all:**")
            if st.button("🗑  Clear candidates"):
                # Remember which IDs were cleared so scan_output_folder won't reload them
                st.session_state.cleared_ids.update(c["id"] for c in st.session_state.candidates)
                st.session_state.candidates = []
                st.session_state.selected_candidate = None
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — CANDIDATE PROFILE
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Candidate Profile":
    if st.session_state.selected_candidate is None:
        st.warning("No candidate selected. Go to Candidates and click 'View profile'.")
        if st.button("← Back to Candidates"):
            st.session_state.page = "Candidates"
            st.rerun()
    else:
        c = st.session_state.selected_candidate

        if st.button("← Back to Candidates"):
            st.session_state.page = "Candidates"
            st.rerun()

        # Initials avatar
        name_parts = c["name"].replace("Dr. ", "").replace("Prof. ", "").split()
        initials = "".join([p[0] for p in name_parts[:2]]).upper()

        html(f"""
        <div style="display:flex;align-items:center;gap:16px;
                    padding:1rem 0 1.2rem;border-bottom:1px solid #2d2d2d;margin-bottom:1.5rem;">
            <div style="width:52px;height:52px;border-radius:50%;background:#1a2a3a;
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.1rem;font-weight:600;color:#4a9fd4;flex-shrink:0;">
                {initials}
            </div>
            <div>
                <div style="font-size:1.25rem;font-weight:500;color:#f0f0f0;">
                    {c['name']} &nbsp; {status_badge(c['status'])}
                </div>
                <div style="font-size:0.82rem;color:#666;margin-top:3px;">{c['file']}</div>
            </div>
        </div>
        """)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Personal", "Education", "Experience", "Skills", "Publications"])

        with tab1:
            html('<div style="font-size:0.8rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#555;margin-bottom:0.8rem;">Personal information</div>')
            if c["personal"]:
                for k, v in c["personal"].items():
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        html(f"<div style='color:#555;font-size:0.85rem;padding:4px 0;'>{k}</div>")
                    with col2:
                        html(f"<div style='color:#ddd;font-size:0.85rem;padding:4px 0;'>{v}</div>")
            else:
                html("<div style='color:#555;font-size:0.85rem;'>No personal information extracted.</div>")

        with tab2:
            html('<div style="font-size:0.8rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#555;margin-bottom:0.8rem;">Education history</div>')
            if c["education"]:
                st.dataframe(pd.DataFrame(c["education"]), use_container_width=True, hide_index=True)
            else:
                html("<div style='color:#555;font-size:0.85rem;'>No education records extracted.</div>")

        with tab3:
            html('<div style="font-size:0.8rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#555;margin-bottom:0.8rem;">Professional experience</div>')
            if c["experience"]:
                st.dataframe(pd.DataFrame(c["experience"]), use_container_width=True, hide_index=True)
            else:
                html("<div style='color:#555;font-size:0.85rem;'>No experience records extracted.</div>")

        with tab4:
            html('<div style="font-size:0.8rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#555;margin-bottom:0.8rem;">Skills</div>')
            if c["skills"]:
                pills = " ".join([
                    f'<span style="display:inline-block;background:#2a2a2a;border:1px solid #3a3a3a;'
                    f'color:#bbb;font-size:0.8rem;padding:3px 10px;border-radius:20px;margin:3px 3px 0 0;">'
                    f'{s}</span>'
                    for s in c["skills"]
                ])
                html(pills)
            else:
                html("<div style='color:#555;font-size:0.85rem;'>No skills extracted.</div>")

        with tab5:
            html('<div style="font-size:0.8rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#555;margin-bottom:0.8rem;">Publications</div>')
            if c["publications"]:
                st.dataframe(pd.DataFrame(c["publications"]), use_container_width=True, hide_index=True)
            else:
                html("<div style='color:#555;font-size:0.85rem;'>No publications found.</div>")

        # Missing info + draft email
        if c["missing"]:
            html("<br>")
            missing_list = "\n".join([f"- {m}" for m in c["missing"]])
            st.warning(f"**Missing information detected:**\n{missing_list}")

            if st.button("📧 Draft email to candidate"):
                last_name = c["name"].split()[-1]
                missing_bullets = "\n".join([f"  • {m}" for m in c["missing"]])
                body = (
                    f"Subject: Additional Information Required — {c['name']}\n\n"
                    f"Dear {last_name},\n\n"
                    f"Thank you for applying. To complete your profile assessment, "
                    f"we require the following additional information:\n\n"
                    f"{missing_bullets}\n\n"
                    f"Kindly provide an updated CV at your earliest convenience.\n\n"
                    f"Best regards,\nTALASH Recruitment Team"
                )
                st.text_area("Draft email:", value=body, height=240)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — LOGS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Logs":
    st.markdown("# Extraction logs")
    html('<div style="color:#777;font-size:0.9rem;margin-top:-0.8rem;margin-bottom:1.5rem;">Step-by-step record of what was extracted, flagged, or failed</div>')

    col_f1, col_f2, _ = st.columns([1, 1, 2])
    with col_f1:
        level_filter = st.selectbox("Level", ["All", "Success", "Warning", "Error", "Info"])
    with col_f2:
        file_options = ["All"] + sorted(set(l["file"] for l in st.session_state.logs))
        file_filter = st.selectbox("File", file_options)

    logs = st.session_state.logs
    if level_filter != "All":
        logs = [l for l in logs if l["level"] == level_filter.lower()]
    if file_filter != "All":
        logs = [l for l in logs if l["file"] == file_filter]

    html("<br>")

    rows = ""
    for l in logs:
        dot_color  = log_dot_color(l["level"])
        detail_div = f'<div style="color:#666;font-size:0.78rem;margin-top:2px;">{l["detail"]}</div>' if l["detail"] else ""
        rows += f"""
        <div style="display:flex;align-items:flex-start;gap:12px;padding:10px 0;
                    border-bottom:1px solid #2a2a2a;font-size:0.85rem;">
            <div style="width:8px;height:8px;border-radius:50%;background:{dot_color};
                        margin-top:5px;flex-shrink:0;"></div>
            <div style="color:#555;width:80px;flex-shrink:0;">{l['time']}</div>
            <div style="color:#777;width:160px;flex-shrink:0;
                        font-family:'DM Mono',monospace;font-size:0.78rem;">{l['file']}</div>
            <div style="color:#ccc;flex:1;">{l['msg']}{detail_div}</div>
        </div>"""

    if not rows:
        rows = '<div style="color:#555;font-size:0.85rem;padding:1rem 0;">No log entries match your filters.</div>'

    html(f'<div style="background:#222;border:1px solid #2d2d2d;border-radius:10px;padding:0.8rem 1.2rem;">{rows}</div>')

    html("<br>")
    if st.button("🗑  Clear logs"):
        st.session_state.logs = []
        st.rerun()