# api.py
import json
import sys
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Add src to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "src"))

# Import pipeline modules (logic yang SUDAH ADA)
from src import ocr
from src import job_parser
from src import cv_profiler
from src import cv_matcher
from src import application_builder
from src import cover_letter_generator
from src import content_validator
from src import gmail_draft_creator

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(
    title="Job Application Automation API",
    description="API for job application automation pipeline",
    version="1.0.0"
)

# Serve static files (HTML/CSS/JS)
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Directories
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
CV_DIR = BASE_DIR / "cv"
OUTPUT_DIR = BASE_DIR / "output"

SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
CV_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# HELPER
# ============================================================
def load_json_safe(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# FRONTEND ROUTES
# ============================================================
@app.get("/")
def serve_index():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Job Application Automation API is running. Frontend not ready yet."}

# ============================================================
# API: SYSTEM STATUS
# ============================================================
@app.get("/api/status")
def get_status():
    profiles_file = OUTPUT_DIR / "cv" / "profiles.json"
    app_file = OUTPUT_DIR / "application" / "application.json"

    cv_files = list(CV_DIR.glob("*.pdf")) + list(CV_DIR.glob("*.docx"))
    screenshots = list(SCREENSHOTS_DIR.glob("*.png")) + list(SCREENSHOTS_DIR.glob("*.jpg"))

    return {
        "cv_profiles_ready": profiles_file.exists(),
        "cv_count": len(cv_files),
        "screenshot_count": len(screenshots),
        "application_ready": app_file.exists()
    }

# ============================================================
# API: UPLOAD SCREENSHOT
# ============================================================
@app.post("/api/upload-screenshot")
async def upload_screenshot(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(400, "Only PNG/JPG/JPEG allowed")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = Path(file.filename).suffix
    save_path = SCREENSHOTS_DIR / f"screenshot_{timestamp}{ext}"

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "success", "filename": save_path.name}

# ============================================================
# API: UPLOAD CV
# ============================================================
@app.post("/api/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(400, "Only PDF/DOCX allowed")

    save_path = CV_DIR / file.filename

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"status": "success", "filename": file.filename}

# ============================================================
# API: LIST CVs
# ============================================================
@app.get("/api/cvs")
def list_cvs():
    cv_files = list(CV_DIR.glob("*.pdf")) + list(CV_DIR.glob("*.docx"))
    return {
        "count": len(cv_files),
        "files": [cv.name for cv in cv_files]
    }

# ============================================================
# API: PROFILE CVs
# ============================================================
@app.post("/api/profile")
def profile_cvs():
    try:
        cv_profiler.main()
        return {"status": "success", "message": "CVs profiled successfully"}
    except Exception as e:
        raise HTTPException(500, str(e))

# ============================================================
# API: RUN PIPELINE (APPLY)
# ============================================================
@app.post("/api/apply")
def run_apply():
    profiles_file = OUTPUT_DIR / "cv" / "profiles.json"
    if not profiles_file.exists():
        raise HTTPException(400, "CV profiles not found. Run /api/profile first.")

    try:
        ocr.run()
        job_parser.main()
        cv_matcher.main()
        application_builder.main()
        cover_letter_generator.main()
        content_validator.main()
        gmail_draft_creator.main()
        return {"status": "success", "message": "Pipeline completed"}
    except Exception as e:
        raise HTTPException(500, str(e))

# ============================================================
# API: GET RESULTS
# ============================================================
@app.get("/api/results")
def get_results():
    app_file = OUTPUT_DIR / "application" / "application.json"
    data = load_json_safe(app_file)
    if not data:
        raise HTTPException(404, "No application data found")
    return data

# ============================================================
# API: GET VALIDATION
# ============================================================
@app.get("/api/validation")
def get_validation():
    val_file = OUTPUT_DIR / "application" / "validation.json"
    data = load_json_safe(val_file)
    if not data:
        raise HTTPException(404, "No validation data found")
    return data

# ============================================================
# API: CREATE GMAIL DRAFT
# ============================================================
@app.post("/api/create-draft")
def create_draft():
    try:
        gmail_draft_creator.main()
        return {"status": "success", "message": "Gmail draft created"}
    except Exception as e:
        raise HTTPException(500, str(e))

# ============================================================
# RUN SERVER
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)