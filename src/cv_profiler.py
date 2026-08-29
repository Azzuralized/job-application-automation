# src/cv_profiler.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from pypdf import PdfReader
from docx import Document

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
CV_DIR = BASE_DIR / "cv"
OUTPUT_DIR = BASE_DIR / "output" / "cv"
OUTPUT_FILE = OUTPUT_DIR / "profiles.json"
MANIFEST_FILE = OUTPUT_DIR / "cv_manifest.json"

load_dotenv(BASE_DIR / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


# ============================================================
# CV PROFILE SCHEMA
# ============================================================
class Experience(BaseModel):
    role: str = Field(description="Job title or role.")
    company: str | None = Field(default=None, description="Company name.")
    duration: str | None = Field(default=None, description="Employment duration if available.")
    responsibilities: list[str] = Field(default_factory=list, description="Important responsibilities.")
    skills: list[str] = Field(default_factory=list, description="Skills demonstrated in this experience.")


class Education(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    graduation_year: str | None = None


class CVProfile(BaseModel):
    language: str = Field(description="Language of the CV. Use 'english', 'indonesian', or 'unknown'.")
    name: str | None = Field(default=None, description="Candidate full name.")
    professional_summary: str | None = Field(default=None, description="Short summary of the candidate.")
    target_roles: list[str] = Field(default_factory=list, description="Roles this CV is suitable for.")
    skills: list[str] = Field(default_factory=list, description="Technical and professional skills.")
    experience: list[Experience] = Field(default_factory=list, description="Relevant work experience.")
    education: list[Education] = Field(default_factory=list, description="Education history.")
    certifications: list[str] = Field(default_factory=list, description="Certifications.")
    keywords: list[str] = Field(default_factory=list, description="Important searchable keywords from the CV.")


class CVRecord(BaseModel):
    id: str
    file: str
    profile: CVProfile


class CVProfiles(BaseModel):
    cvs: list[CVRecord]


# ============================================================
# GEMINI CLIENT
# ============================================================
def create_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan di .env")
    return genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# FILE DISCOVERY
# ============================================================
def get_cv_files() -> list[Path]:
    if not CV_DIR.exists():
        raise FileNotFoundError(f"CV folder tidak ditemukan:\n{CV_DIR}")
    files = [
        file for file in CV_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


# ============================================================
# TEXT EXTRACTION
# ============================================================
def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages).strip()


def extract_docx_text(path: Path) -> str:
    document = Document(str(path))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_cv_text(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".pdf":
        return extract_pdf_text(path)
    if extension == ".docx":
        return extract_docx_text(path)
    raise ValueError(f"Unsupported CV format: {extension}")


# ============================================================
# PROFILE CV WITH GEMINI
# ============================================================
def profile_cv(client: genai.Client, cv_text: str, filename: str) -> CVProfile:
    prompt = f"""
You are a CV profiling system.
Analyze the CV below and create a structured profile.

IMPORTANT RULES:
- Do not invent information.
- Only extract information that actually appears in the CV.
- Correct obvious extraction mistakes when the intended meaning is clear.

Determine the language of the CV: english, indonesian, or unknown.
Identify realistic target job roles based on the candidate's actual experience and skills.
Extract technical skills and professional skills.
Extract work experience.
Extract education.
Extract certifications.
Keywords should contain useful terms that can later be used to match this CV against job postings.

Do not inflate the candidate's experience.
Do not add skills simply because they are common for the candidate's target profession.

CV FILE: {filename}

CV TEXT:
---------------- START CV ----------------
{cv_text}
----------------- END CV -----------------
"""

    chat = client.chats.create(model=GEMINI_MODEL)
    response = chat.send_message(
        prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": CVProfile,
        },
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return CVProfile.model_validate_json(response.text)


# ============================================================
# BUILD ALL PROFILES
# ============================================================
def build_profiles() -> CVProfiles:
    client = create_gemini_client()
    cv_files = get_cv_files()

    if not cv_files:
        raise RuntimeError(f"Tidak ada CV ditemukan di:\n{CV_DIR}")

    records = []
    print(f"\n📁 Found {len(cv_files)} CV(s).")

    for index, cv_file in enumerate(cv_files, start=1):
        print(f"\n[{index}/{len(cv_files)}] Processing: {cv_file.name}")

        try:
            print("📄 Extracting text...")
            text = extract_cv_text(cv_file)

            if not text:
                print("⚠️ No text extracted. Skipping.")
                continue

            print("🧠 Profiling with Gemini...")
            profile = profile_cv(client, text, cv_file.name)

            record = CVRecord(
                id=cv_file.stem.lower().replace(" ", "_"),
                file=str(cv_file.relative_to(BASE_DIR)).replace("\\", "/"),
                profile=profile
            )

            records.append(record)
            print("✅ Profile created.")

        except Exception as error:
            print(f"❌ Failed to process {cv_file.name}: {error}")

    if not records:
        raise RuntimeError("Tidak ada CV yang berhasil diproses.")

    return CVProfiles(cvs=records)


# ============================================================
# SAVE PROFILES
# ============================================================
def save_profiles(profiles: CVProfiles) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(profiles.model_dump_json(indent=2), encoding="utf-8")
    return OUTPUT_FILE


# ============================================================
# 🐛 BUG FIX #3.1: AUTO-GENERATE CV MANIFEST
# ============================================================
def generate_cv_manifest(cv_files: list[Path]) -> dict:
    """
    Generate cv_manifest.json based on discovered CV files.
    This ensures cv_matcher.py always has a manifest to work with,
    even when moving to a new desktop/environment.
    """
    manifest = {"cvs": []}

    for cv_file in cv_files:
        cv_id = cv_file.stem.lower().replace(" ", "_")

        # Detect language from filename (simple heuristic)
        language = "unknown"
        filename_lower = cv_file.name.lower()
        if "eng" in filename_lower or "english" in filename_lower:
            language = "english"
        elif "id" in filename_lower or "indonesia" in filename_lower:
            language = "indonesian"

        manifest["cvs"].append({
            "id": cv_id,
            "file": str(cv_file.relative_to(BASE_DIR)).replace("\\", "/"),
            "enabled": True,
            "language": language,
            "target_roles": [],
            "tags": []
        })

    return manifest


def save_manifest(manifest: dict) -> Path:
    """Save cv_manifest.json"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return MANIFEST_FILE


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("JOB APPLICATION AUTOMATION")
    print("STEP 4 - CV PROFILER")
    print("=" * 60)
    print(f"\n🤖 Model: {GEMINI_MODEL}")
    print(f"\n📂 CV directory:\n{CV_DIR}")

    try:
        profiles = build_profiles()
    except Exception as error:
        print(f"\n❌ CV profiling failed:\n{error}")
        return

    output = save_profiles(profiles)
    print(f"\n📄 Profiles saved to:\n{output}")

    # ============================================================
    # 🐛 BUG FIX #3.1: Auto-generate manifest
    # ============================================================
    print("\n📋 Generating CV manifest...")
    cv_files = get_cv_files()
    manifest = generate_cv_manifest(cv_files)
    manifest_output = save_manifest(manifest)
    print(f"✅ Manifest saved to:\n{manifest_output}")

    print("\n" + "=" * 60)
    print("✅ STEP 4 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()