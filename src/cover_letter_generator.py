#cover_letter_generator.py
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

APPLICATION_FILE = (
    BASE_DIR
    / "output"
    / "application"
    / "application.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
    / "application"
)

COVER_LETTER_FILE = (
    OUTPUT_DIR
    / "cover_letter.txt"
)

EMAIL_SUBJECT_FILE = (
    OUTPUT_DIR
    / "email_subject.txt"
)

EMAIL_BODY_FILE = (
    OUTPUT_DIR
    / "email_body.txt"
)

# Gemini model
MODEL_NAME = "gemini-3.6-flash"


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(
    BASE_DIR / ".env"
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


# ============================================================
# HELPERS
# ============================================================

def load_json(path: Path) -> dict:
    """Load JSON file."""

    if not path.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_json(
    data: dict,
    path: Path
) -> None:
    """Save JSON safely."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


def save_text(
    text: str,
    path: Path
) -> None:
    """Save generated text."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        text.strip(),
        encoding="utf-8"
    )


def clean_response(
    text: str
) -> str:
    """
    Remove accidental markdown code fences.
    """

    text = text.strip()

    text = re.sub(
        r"^```(?:json|text|markdown)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


def extract_json_response(
    text: str
) -> dict:
    """
    Convert Gemini JSON response into a Python dict.

    Handles accidental markdown code fences.
    """

    cleaned = clean_response(
        text
    )

    try:
        return json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        raise RuntimeError(
            "Gemini tidak mengembalikan "
            "JSON yang valid.\n\n"
            f"Response:\n{cleaned}\n\n"
            f"Error: {error}"
        )


# ============================================================
# VALIDATION
# ============================================================

def validate_environment() -> None:

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY tidak ditemukan.\n"
            "Pastikan file .env memiliki:\n\n"
            "GEMINI_API_KEY=your_api_key"
        )


def validate_application(
    application: dict
) -> None:

    required_sections = [
        "application_id",
        "job",
        "selected_cv"
    ]

    missing = [
        section
        for section in required_sections
        if section not in application
    ]

    if missing:
        raise ValueError(
            "application.json tidak lengkap.\n"
            f"Section yang hilang: "
            f"{', '.join(missing)}"
        )

    job = application["job"]

    if not job.get("company"):
        raise ValueError(
            "Nama perusahaan tidak tersedia."
        )

    if not job.get("position"):
        raise ValueError(
            "Posisi pekerjaan tidak tersedia."
        )

    selected_cv = application[
        "selected_cv"
    ]

    if not selected_cv.get("file"):
        raise ValueError(
            "File CV terpilih tidak tersedia."
        )

    if not selected_cv.get("profile"):
        raise ValueError(
            "Profile CV terpilih tidak tersedia."
        )


# ============================================================
# LANGUAGE
# ============================================================

def determine_language(
    application: dict
) -> str:
    """
    Determine application language.

    Priority:
    1. Explicit job language requirement
    2. Selected CV language
    3. Indonesian fallback
    """

    job = application["job"]

    selected_cv = application[
        "selected_cv"
    ]

    requirement = (
        job.get(
            "language_requirement"
        )
        or "unknown"
    ).lower()

    cv_language = (
        selected_cv.get(
            "language"
        )
        or "indonesian"
    ).lower()

    if requirement in {
        "english",
        "en"
    }:
        return "english"

    if requirement in {
        "indonesian",
        "bahasa indonesia",
        "id"
    }:
        return "indonesian"

    return cv_language


# ============================================================
# PROMPT
# ============================================================

def build_prompt(
    application: dict,
    language: str
) -> str:

    job = application["job"]

    selected_cv = application[
        "selected_cv"
    ]

    profile = selected_cv[
        "profile"
    ]

    if language == "english":

        language_instruction = """
Write all generated content in professional,
natural English.
"""

    else:

        language_instruction = """
Tulis semua konten dalam Bahasa Indonesia
yang profesional, natural, dan tidak kaku.
"""

    prompt = f"""
You are an expert job application writer.

Your task is to prepare application content
for a real job application.

IMPORTANT TRUTHFULNESS RULES:

1. Use ONLY facts explicitly present in the CV profile
   and job information below.
2. NEVER invent work experience.
3. NEVER invent skills.
4. NEVER invent certifications.
5. NEVER invent achievements.
6. NEVER invent responsibilities.
7. NEVER claim experience in a field that is not
   supported by the CV.
8. Do not exaggerate qualifications.
9. If the candidate does not directly match the job,
   emphasize transferable skills honestly.
10. Do not mention the matching score.
11. Do not mention that AI was used.
12. Do not apologize for missing qualifications.
13. Do not invent recruiter names.
14. Do not invent contact information.
15. Do not invent company information.

LANGUAGE:

{language_instruction}

============================================================
1. COVER LETTER
============================================================

Create a professional and concise cover letter.

Style:

- Human-sounding
- Professional
- Natural
- Specific to the position
- Approximately 180-300 words
- No markdown
- No bullet points
- No subject line
- No email address
- No placeholder text
- Do not repeat the entire CV

============================================================
2. EMAIL SUBJECT
============================================================

Create a concise professional email subject.

The subject should clearly communicate:

- Job application
- Position
- Applicant name when appropriate

Do not use emojis.

============================================================
3. EMAIL BODY
============================================================

Create a professional email body for sending the
application and CV as an attachment.

The email should:

- Address the recruitment team naturally.
- State the position being applied for.
- Briefly introduce the applicant.
- Mention that the CV is attached.
- Invite further discussion/interview.
- End professionally.
- Not duplicate the entire cover letter.
- Not invent information.

Do NOT include:

- Fake attachments
- Fake phone numbers
- Fake recruiter names
- Fake company information
- Markdown
- Placeholder text

============================================================
JOB INFORMATION
============================================================

Company:
{job.get("company")}

Position:
{job.get("position")}

Location:
{job.get("location")}

Language Requirement:
{job.get("language_requirement")}

Recipient Email:
{job.get("recipient_email")}

Requirements:
{json.dumps(
    job.get("requirements", []),
    ensure_ascii=False,
    indent=2
)}

Job Description:
{json.dumps(
    job.get("job_description", []),
    ensure_ascii=False,
    indent=2
)}

============================================================
SELECTED CV
============================================================

CV File:
{selected_cv.get("file")}

CV Language:
{selected_cv.get("language")}

Professional Summary:
{profile.get("professional_summary")}

Target Roles:
{json.dumps(
    profile.get("target_roles", []),
    ensure_ascii=False,
    indent=2
)}

Skills:
{json.dumps(
    profile.get("skills", []),
    ensure_ascii=False,
    indent=2
)}

Experience:
{json.dumps(
    profile.get("experience", []),
    ensure_ascii=False,
    indent=2
)}

Education:
{json.dumps(
    profile.get("education", []),
    ensure_ascii=False,
    indent=2
)}

Certifications:
{json.dumps(
    profile.get("certifications", []),
    ensure_ascii=False,
    indent=2
)}

============================================================

RETURN FORMAT

Return ONLY valid JSON.

Use exactly this structure:

{{
  "cover_letter": "...",
  "email_subject": "...",
  "email_body": "..."
}}

Do not wrap the JSON in markdown code fences.
"""

    return prompt.strip()


# ============================================================
# GEMINI
# ============================================================

def generate_application_content(
    prompt: str
) -> dict:

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise RuntimeError(
            "Gemini mengembalikan response kosong."
        )

    result = extract_json_response(
        response.text
    )

    required_fields = [
        "cover_letter",
        "email_subject",
        "email_body"
    ]

    missing = [
        field
        for field in required_fields
        if not result.get(field)
    ]

    if missing:

        raise RuntimeError(
            "Gemini tidak menghasilkan "
            "field berikut:\n"
            + ", ".join(missing)
        )

    return {
        "cover_letter": str(
            result["cover_letter"]
        ).strip(),

        "email_subject": str(
            result["email_subject"]
        ).strip(),

        "email_body": str(
            result["email_body"]
        ).strip()
    }


# ============================================================
# UPDATE APPLICATION
# ============================================================

def update_application(
    application: dict,
    generated_content: dict
) -> dict:
    """
    Add generated application content
    into application.json.
    """

    updated = json.loads(
        json.dumps(
            application
        )
    )

    updated.setdefault(
        "generated_content",
        {}
    )

    updated[
        "generated_content"
    ] = {

        "cover_letter":
            generated_content[
                "cover_letter"
            ],

        "cover_letter_language":
            determine_language(
                application
            ),

        "email_subject":
            generated_content[
                "email_subject"
            ],

        "email_body":
            generated_content[
                "email_body"
            ]
    }

    return updated


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print(
        "JOB APPLICATION AUTOMATION"
    )

    print(
        "STEP 7 - APPLICATION CONTENT GENERATOR"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------------

    print(
        "\n🔐 Checking Gemini configuration..."
    )

    validate_environment()

    print(
        "✅ Gemini API key loaded."
    )

    # --------------------------------------------------------
    # LOAD APPLICATION
    # --------------------------------------------------------

    print(
        "\n📄 Loading application..."
    )

    application = load_json(
        APPLICATION_FILE
    )

    validate_application(
        application
    )

    print(
        f"✅ Application loaded."
    )

    # --------------------------------------------------------
    # DISPLAY JOB
    # --------------------------------------------------------

    job = application[
        "job"
    ]

    selected_cv = application[
        "selected_cv"
    ]

    print(
        f"\n🏢 Company  : "
        f"{job.get('company')}"
    )

    print(
        f"💼 Position : "
        f"{job.get('position')}"
    )

    print(
        f"📄 CV       : "
        f"{selected_cv.get('file')}"
    )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    language = determine_language(
        application
    )

    print(
        f"🌐 Language  : "
        f"{language}"
    )

    # --------------------------------------------------------
    # BUILD PROMPT
    # --------------------------------------------------------

    print(
        "\n🧠 Building AI prompt..."
    )

    prompt = build_prompt(
        application,
        language
    )

    print(
        "✅ Prompt prepared."
    )

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    print(
        "\n🤖 Sending application context "
        "to Gemini..."
    )

    print(
        f"🤖 Model: {MODEL_NAME}"
    )

    try:

        generated_content = (
            generate_application_content(
                prompt
            )
        )

    except Exception as error:

        print(
            "\n❌ Application content "
            "generation failed."
        )

        print(
            f"Reason: {error}"
        )

        print(
            "\n⚠️ application.json "
            "tidak diubah."
        )

        raise

    print(
        "✅ Cover letter generated."
    )

    print(
        "✅ Email subject generated."
    )

    print(
        "✅ Email body generated."
    )

    # --------------------------------------------------------
    # SAVE STANDALONE FILES
    # --------------------------------------------------------

    save_text(
        generated_content[
            "cover_letter"
        ],
        COVER_LETTER_FILE
    )

    save_text(
        generated_content[
            "email_subject"
        ],
        EMAIL_SUBJECT_FILE
    )

    save_text(
        generated_content[
            "email_body"
        ],
        EMAIL_BODY_FILE
    )

    print(
        "\n📄 Standalone files saved:"
    )

    print(
        f"   Cover Letter : "
        f"{COVER_LETTER_FILE}"
    )

    print(
        f"   Email Subject: "
        f"{EMAIL_SUBJECT_FILE}"
    )

    print(
        f"   Email Body   : "
        f"{EMAIL_BODY_FILE}"
    )

    # --------------------------------------------------------
    # UPDATE APPLICATION
    # --------------------------------------------------------

    updated_application = (
        update_application(
            application,
            generated_content
        )
    )

    save_json(
        updated_application,
        APPLICATION_FILE
    )

    print(
        "\n💾 application.json updated."
    )

    # --------------------------------------------------------
    # DISPLAY COVER LETTER
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "GENERATED COVER LETTER"
    )

    print(
        "=" * 60
    )

    print(
        generated_content[
            "cover_letter"
        ]
    )

    # --------------------------------------------------------
    # DISPLAY EMAIL
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "GENERATED EMAIL"
    )

    print(
        "=" * 60
    )

    print(
        f"Subject:\n"
        f"{generated_content['email_subject']}"
    )

    print(
        "\nBody:\n"
    )

    print(
        generated_content[
            "email_body"
        ]
    )

    print(
        "=" * 60
    )

    print(
        "✅ STEP 7 COMPLETE"
    )

    print(
        "=" * 60
    )


if __name__ == "__main__":
    main()
