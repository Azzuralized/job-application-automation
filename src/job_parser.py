# job_parser.py
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OCR_FILE = BASE_DIR / "output" / "ocr" / "latest.txt"
OUTPUT_DIR = BASE_DIR / "output" / "job"
OUTPUT_FILE = OUTPUT_DIR / "latest.json"

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ============================================================
# JOB SCHEMA
# ============================================================

class JobPosting(BaseModel):
    company: str = Field(
        description="Company or organization offering the job."
    )

    position: str = Field(
        description="Job position or title."
    )

    location: str | None = Field(
        default=None,
        description="Job location if mentioned."
    )

    recipient_email: str | None = Field(
        default=None,
        description="Application recipient email address."
    )

    language_requirement: str = Field(
        description=(
            "Required application language. "
            "Use 'english', 'indonesian', or 'unknown'."
        )
    )

    requirements: list[str] = Field(
        default_factory=list,
        description="Job requirements."
    )

    job_description: list[str] = Field(
        default_factory=list,
        description="Job responsibilities."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

def create_gemini_client() -> genai.Client:

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY tidak ditemukan.\n"
            "Pastikan file .env berisi:\n"
            "GEMINI_API_KEY=..."
        )

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# READ OCR
# ============================================================

def read_ocr_text() -> str:

    if not OCR_FILE.exists():
        raise FileNotFoundError(
            f"OCR file tidak ditemukan:\n{OCR_FILE}"
        )

    text = OCR_FILE.read_text(
        encoding="utf-8"
    ).strip()

    if not text:
        raise ValueError(
            "OCR file kosong."
        )

    return text


# ============================================================
# PARSE JOB WITH GEMINI
# ============================================================

def parse_job(text: str) -> JobPosting:

    client = create_gemini_client()

    prompt = f"""
You are a job posting information extraction system.

Extract structured information from the OCR text below.

The OCR may contain:
- spelling mistakes
- broken words
- duplicated characters
- random visual noise
- incorrect character recognition

Your job is to reconstruct the intended meaning when it is obvious.

IMPORTANT RULES:

1. Do not invent information.

2. Correct obvious OCR mistakes when the intended meaning
   is clear from context.

3. Extract the company name.

4. Extract the exact job position.

5. Extract the job location if mentioned.

6. Extract the application email address if present.

7. For language_requirement:

   Use "english" ONLY if the job explicitly requires
   English for the CV, application, documents, or communication.

   Use "indonesian" ONLY if the job explicitly requires
   Indonesian.

   Otherwise use "unknown".

8. Extract requirements as individual items.

9. Extract job responsibilities separately.

10. Ignore social media handles, decorative text,
    watermarks, and unrelated OCR noise.

11. If information is unavailable, use null where allowed.

OCR TEXT:

---------------- START OCR ----------------

{text}

----------------- END OCR -----------------
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": JobPosting,
        },
    )

    if not response.text:
        raise RuntimeError(
            "Gemini mengembalikan response kosong."
        )

    return JobPosting.model_validate_json(
        response.text
    )


# ============================================================
# SAVE JOB JSON
# ============================================================

def save_job(job: JobPosting) -> Path:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        job.model_dump_json(indent=2),
        encoding="utf-8"
    )

    return OUTPUT_FILE


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("JOB APPLICATION AUTOMATION")
    print("STEP 3 - AI JOB PARSER")
    print("=" * 60)

    # --------------------------------------------------------
    # READ OCR
    # --------------------------------------------------------

    print("\n📄 Reading OCR...")

    try:
        ocr_text = read_ocr_text()

    except Exception as error:
        print(f"❌ Failed to read OCR:")
        print(f"   {error}")
        return

    print("✅ OCR loaded.")

    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    print("\n🧠 Sending OCR to Gemini...")
    print(f"🤖 Model: {GEMINI_MODEL}")

    try:
        job = parse_job(ocr_text)

    except Exception as error:
        print(f"❌ Gemini parsing failed:")
        print(f"   {error}")
        return

    print("✅ Job parsed successfully.")

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output_file = save_job(job)

    print("\n📄 Saved structured job data:")
    print(f"   {output_file}")

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("JOB DATA")
    print("=" * 60)

    print(
        json.dumps(
            job.model_dump(),
            indent=2,
            ensure_ascii=False
        )
    )

    print("=" * 60)
    print("✅ STEP 3 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()