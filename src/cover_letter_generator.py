# src/cover_letter_generator.py
from pathlib import Path
import json
import os
import re
from dotenv import load_dotenv
from google import genai

# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
APPLICATION_FILE = BASE_DIR / "output" / "application" / "application.json"
OUTPUT_DIR = BASE_DIR / "output" / "application"
COVER_LETTER_FILE = OUTPUT_DIR / "cover_letter.txt"
EMAIL_SUBJECT_FILE = OUTPUT_DIR / "email_subject.txt"
EMAIL_BODY_FILE = OUTPUT_DIR / "email_body.txt"

load_dotenv(BASE_DIR / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


# ============================================================
# HELPERS
# ============================================================
def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File tidak ditemukan:\n{path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def save_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip(), encoding="utf-8")


def clean_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json|text|markdown)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_json_response(text: str) -> dict:
    cleaned = clean_response(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Gemini tidak mengembalikan JSON yang valid.\n\n"
            f"Response:\n{cleaned}\n\nError: {error}"
        )


# ============================================================
# VALIDATION
# ============================================================
def validate_environment() -> None:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan di .env")


def validate_application(application: dict) -> None:
    required = ["application_id", "job", "selected_cv"]
    missing = [s for s in required if s not in application]
    if missing:
        raise ValueError(f"application.json tidak lengkap. Section hilang: {', '.join(missing)}")

    job = application["job"]
    if not job.get("company") or not job.get("position"):
        raise ValueError("Nama perusahaan atau posisi pekerjaan tidak tersedia.")

    selected_cv = application["selected_cv"]
    if not selected_cv.get("file") or not selected_cv.get("profile"):
        raise ValueError("File atau Profile CV terpilih tidak tersedia.")


# ============================================================
# LANGUAGE & PROMPT
# ============================================================
def determine_language(application: dict) -> str:
    job = application["job"]
    selected_cv = application["selected_cv"]
    req = (job.get("language_requirement") or "unknown").lower()
    cv_lang = (selected_cv.get("language") or "indonesian").lower()

    if req in {"english", "en"}:
        return "english"
    if req in {"indonesian", "bahasa indonesia", "id"}:
        return "indonesian"
    return cv_lang


def build_prompt(application: dict, language: str) -> str:
    job = application["job"]
    selected_cv = application["selected_cv"]
    profile = selected_cv["profile"]

    lang_instr = (
        "Write all generated content in professional, natural English."
        if language == "english"
        else "Tulis semua konten dalam Bahasa Indonesia yang profesional, natural, dan tidak kaku."
    )

    return f"""You are an expert job application writer. Prepare application content for a real job application.

IMPORTANT TRUTHFULNESS RULES:
Use ONLY facts explicitly present in the CV profile and job info.
NEVER invent work experience, skills, certifications, or achievements.
Do not mention matching score or AI usage.

LANGUAGE:
{lang_instr}

============================================================
JOB INFORMATION
Company: {job.get("company")}
Position: {job.get("position")}
Location: {job.get("location")}
Recipient Email: {job.get("recipient_email")}
Requirements: {json.dumps(job.get("requirements", []), ensure_ascii=False, indent=2)}
Job Description: {json.dumps(job.get("job_description", []), ensure_ascii=False, indent=2)}

============================================================
SELECTED CV
CV File: {selected_cv.get("file")}
Professional Summary: {profile.get("professional_summary")}
Target Roles: {json.dumps(profile.get("target_roles", []), ensure_ascii=False, indent=2)}
Skills: {json.dumps(profile.get("skills", []), ensure_ascii=False, indent=2)}
Experience: {json.dumps(profile.get("experience", []), ensure_ascii=False, indent=2)}
Education: {json.dumps(profile.get("education", []), ensure_ascii=False, indent=2)}
Certifications: {json.dumps(profile.get("certifications", []), ensure_ascii=False, indent=2)}

============================================================
RETURN FORMAT
Return ONLY valid JSON. Use exactly this structure. Do not wrap in markdown code fences.
{{
  "cover_letter": "...",
  "email_subject": "...",
  "email_body": "..."
}}
"""


# ============================================================
# GENERATE CONTENT
# ============================================================
def generate_application_content(prompt: str) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)

    # GANTI INI: Gunakan Chat API untuk menghindari warning AFC
    chat = client.chats.create(model=GEMINI_MODEL)
    response = chat.send_message(prompt)

    if not response.text:
        raise RuntimeError("Gemini mengembalikan response kosong.")

    result = extract_json_response(response.text)

    missing = [f for f in ["cover_letter", "email_subject", "email_body"] if not result.get(f)]
    if missing:
        raise RuntimeError(f"Gemini tidak menghasilkan field berikut:\n" + ", ".join(missing))

    return {
        "cover_letter": str(result["cover_letter"]).strip(),
        "email_subject": str(result["email_subject"]).strip(),
        "email_body": str(result["email_body"]).strip(),
    }


def update_application(application: dict, generated_content: dict) -> dict:
    updated = json.loads(json.dumps(application))
    updated.setdefault("generated_content", {})
    updated["generated_content"] = {
        "cover_letter": generated_content["cover_letter"],
        "cover_letter_language": determine_language(application),
        "email_subject": generated_content["email_subject"],
        "email_body": generated_content["email_body"]
    }
    return updated


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("JOB APPLICATION AUTOMATION")
    print("STEP 7 - APPLICATION CONTENT GENERATOR")
    print("=" * 60)
    print(f"\n🤖 Model: {GEMINI_MODEL}")

    print("\n🔐 Checking Gemini configuration...")
    validate_environment()
    print("✅ Gemini API key loaded.")

    print("\n📄 Loading application...")
    application = load_json(APPLICATION_FILE)
    validate_application(application)
    print(f"✅ Application loaded: {application['application_id']}")

    job = application["job"]
    selected_cv = application["selected_cv"]
    print(f"\n🏢 Company  : {job.get('company')}")
    print(f"💼 Position : {job.get('position')}")
    print(f"📄 CV       : {selected_cv.get('file')}")

    language = determine_language(application)
    print(f"🌐 Language  : {language}")

    print("\n🧠 Building AI prompt...")
    prompt = build_prompt(application, language)
    print("✅ Prompt prepared.")

    print(f"\n🤖 Sending application context to Gemini...")
    try:
        generated_content = generate_application_content(prompt)
    except Exception as error:
        print(f"\n❌ Application content generation failed.\nReason: {error}")
        print("\n⚠️ application.json tidak diubah.")
        raise

    print("✅ Cover letter generated.")
    print("✅ Email subject generated.")
    print("✅ Email body generated.")

    save_text(generated_content["cover_letter"], COVER_LETTER_FILE)
    save_text(generated_content["email_subject"], EMAIL_SUBJECT_FILE)
    save_text(generated_content["email_body"], EMAIL_BODY_FILE)
    print(f"\n📄 Standalone files saved to: {OUTPUT_DIR}")

    updated_application = update_application(application, generated_content)
    save_json(updated_application, APPLICATION_FILE)
    print("\n💾 application.json updated.")

    print("\n" + "=" * 60)
    print("GENERATED COVER LETTER")
    print("=" * 60)
    print(generated_content["cover_letter"])
    print("\n" + "=" * 60)
    print("GENERATED EMAIL")
    print("=" * 60)
    print(f"Subject:\n{generated_content['email_subject']}")
    print(f"\nBody:\n{generated_content['email_body']}")
    print("=" * 60)
    print("✅ STEP 7 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()