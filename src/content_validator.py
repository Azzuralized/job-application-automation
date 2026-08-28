#content_validator.py
from pathlib import Path
import json
import re
from typing import Any


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

OUTPUT_FILE = (
    BASE_DIR
    / "output"
    / "application"
    / "validation.json"
)


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"File tidak ditemukan:\n{path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"JSON tidak valid:\n{path}\n\n{error}"
        )


def save_json(
    data: dict,
    path: Path
) -> None:

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


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text: Any) -> str:
    """
    Normalize text for comparison.
    """

    if text is None:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def contains_text(
    text: str,
    value: str
) -> bool:

    text = normalize_text(text)
    value = normalize_text(value)

    if not text or not value:
        return False

    return value in text


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_application_structure(
    application: dict
) -> list[str]:

    errors = []

    required_sections = [
        "application_id",
        "job",
        "selected_cv",
        "match",
        "generated_content"
    ]

    for section in required_sections:

        if section not in application:
            errors.append(
                f"Missing application field: {section}"
            )

    return errors


def validate_identity(
    application: dict,
    cover_letter: str,
    email_subject: str,
    email_body: str
) -> tuple[str, list[str]]:

    errors = []

    job = application.get(
        "job",
        {}
    )

    company = job.get(
        "company"
    )

    position = job.get(
        "position"
    )

    combined_text = " ".join([
        cover_letter,
        email_subject,
        email_body
    ])

    if company and not contains_text(
        combined_text,
        company
    ):
        errors.append(
            f"Nama perusahaan '{company}' "
            "tidak ditemukan dalam generated content."
        )

    if position and not contains_text(
        combined_text,
        position
    ):
        errors.append(
            f"Posisi '{position}' "
            "tidak ditemukan dalam generated content."
        )

    if errors:
        return "failed", errors

    return "passed", []


def validate_placeholders(
    *texts: str
) -> tuple[str, list[str]]:

    errors = []

    placeholder_patterns = [
        r"\[[^\]]+\]",
        r"\{[^}]+\}",
        r"<[^>]+>",
    ]

    for text in texts:

        for pattern in placeholder_patterns:

            matches = re.findall(
                pattern,
                text
            )

            for match in matches:

                errors.append(
                    f"Placeholder ditemukan: {match}"
                )

    if errors:
        return "failed", errors

    return "passed", []


def validate_content_presence(
    cover_letter: str,
    email_subject: str,
    email_body: str
) -> tuple[str, list[str]]:

    errors = []

    if not cover_letter.strip():
        errors.append(
            "Cover letter kosong."
        )

    if not email_subject.strip():
        errors.append(
            "Email subject kosong."
        )

    if not email_body.strip():
        errors.append(
            "Email body kosong."
        )

    if errors:
        return "failed", errors

    return "passed", []


def validate_recipient(
    application: dict
) -> tuple[str, list[str]]:

    errors = []

    recipient = (
        application
        .get("job", {})
        .get("recipient_email")
    )

    if not recipient:

        errors.append(
            "Recipient email tidak tersedia."
        )

    else:

        email_pattern = (
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        if not re.match(
            email_pattern,
            recipient
        ):

            errors.append(
                f"Format email tidak valid: {recipient}"
            )

    if errors:
        return "failed", errors

    return "passed", []


def validate_cv(
    application: dict
) -> tuple[str, list[str]]:

    errors = []

    selected_cv = application.get(
        "selected_cv",
        {}
    )

    cv_file = selected_cv.get(
        "file"
    )

    cv_language = selected_cv.get(
        "language"
    )

    cv_profile = selected_cv.get(
        "profile",
        {}
    )

    if not cv_file:
        errors.append(
            "File CV tidak tersedia."
        )

    if not cv_language:
        errors.append(
            "Bahasa CV tidak tersedia."
        )

    if not cv_profile:
        errors.append(
            "CV profile kosong."
        )

    if errors:
        return "failed", errors

    return "passed", []


def validate_language(
    application: dict,
    cover_letter: str,
    email_body: str
) -> tuple[str, list[str]]:

    warnings = []

    selected_cv = application.get(
        "selected_cv",
        {}
    )

    language = normalize_text(
        selected_cv.get(
            "language",
            ""
        )
    )

    combined_text = normalize_text(
        cover_letter + " " + email_body
    )

    if language == "indonesian":

        english_markers = [
            "dear ",
            "i am writing",
            "i would like to apply",
            "thank you for your consideration",
            "sincerely"
        ]

        found = [
            marker
            for marker in english_markers
            if marker in combined_text
        ]

        if found:

            warnings.append(
                "CV berbahasa Indonesia tetapi "
                "generated content mengandung "
                "indikasi bahasa Inggris."
            )

    elif language == "english":

        indonesian_markers = [
            "yang terhormat",
            "melalui surat ini",
            "saya menyampaikan",
            "hormat saya",
            "terima kasih"
        ]

        found = [
            marker
            for marker in indonesian_markers
            if marker in combined_text
        ]

        if found:

            warnings.append(
                "CV berbahasa Inggris tetapi "
                "generated content mengandung "
                "indikasi bahasa Indonesia."
            )

    if warnings:
        return "warning", warnings

    return "passed", []


# ============================================================
# BASIC FACTUAL VALIDATION
# ============================================================

def validate_known_facts(
    application: dict,
    cover_letter: str
) -> tuple[str, list[str]]:

    warnings = []

    selected_cv = application.get(
        "selected_cv",
        {}
    )

    profile = selected_cv.get(
        "profile",
        {}
    )

    # --------------------------------------------------------
    # Candidate name
    # --------------------------------------------------------

    candidate_name = profile.get(
        "name"
    )

    if candidate_name:

        if not contains_text(
            cover_letter,
            candidate_name
        ):

            warnings.append(
                "Nama kandidat tidak ditemukan "
                "dalam cover letter."
            )

    # --------------------------------------------------------
    # Known experience
    # --------------------------------------------------------

    experiences = profile.get(
        "experience",
        []
    )

    experience_text = " ".join(
        str(item)
        for item in experiences
    )

    # --------------------------------------------------------
    # Detect obvious unsupported claims
    # --------------------------------------------------------

    risky_patterns = [
        r"\b\d+\s+tahun pengalaman\b",
        r"\b\d+\s+years of experience\b",
        r"\bberpengalaman sebagai\b",
        r"\bexperienced as\b",
        r"\bmemiliki pengalaman di bidang pest control\b",
        r"\bhave experience in pest control\b"
    ]

    for pattern in risky_patterns:

        matches = re.findall(
            pattern,
            normalize_text(cover_letter)
        )

        for match in matches:

            # We intentionally mark these as warnings
            # rather than automatic failures because
            # semantic interpretation requires AI.
            warnings.append(
                "Potensi klaim pengalaman yang "
                f"perlu direview: '{match}'."
            )

    if warnings:
        return "warning", warnings

    return "passed", []


# ============================================================
# SCORING
# ============================================================

def calculate_score(
    checks: dict
) -> int:

    score = 100

    for check in checks.values():

        status = check.get(
            "status"
        )

        if status == "failed":
            score -= 25

        elif status == "warning":
            score -= 10

    return max(
        0,
        score
    )


def determine_status(
    checks: dict
) -> str:

    statuses = [
        check.get("status")
        for check in checks.values()
    ]

    if "failed" in statuses:
        return "failed"

    if "warning" in statuses:
        return "needs_review"

    return "passed"


# ============================================================
# MAIN VALIDATION
# ============================================================

def validate_application(
    application: dict
) -> dict:

    generated = application.get(
        "generated_content",
        {}
    )

    cover_letter = generated.get(
        "cover_letter"
    ) or ""

    email_subject = generated.get(
        "email_subject"
    ) or ""

    email_body = generated.get(
        "email_body"
    ) or ""

    checks = {}

    # --------------------------------------------------------
    # Application structure
    # --------------------------------------------------------

    errors = validate_application_structure(
        application
    )

    checks["application_structure"] = {
        "status": (
            "failed"
            if errors
            else "passed"
        ),
        "errors": errors
    }

    # --------------------------------------------------------
    # Content presence
    # --------------------------------------------------------

    status, errors = validate_content_presence(
        cover_letter,
        email_subject,
        email_body
    )

    checks["content_presence"] = {
        "status": status,
        "errors": errors
    }

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    status, errors = validate_identity(
        application,
        cover_letter,
        email_subject,
        email_body
    )

    checks["identity"] = {
        "status": status,
        "errors": errors
    }

    # --------------------------------------------------------
    # Placeholders
    # --------------------------------------------------------

    status, errors = validate_placeholders(
        cover_letter,
        email_subject,
        email_body
    )

    checks["placeholders"] = {
        "status": status,
        "errors": errors
    }

    # --------------------------------------------------------
    # Recipient
    # --------------------------------------------------------

    status, errors = validate_recipient(
        application
    )

    checks["recipient"] = {
        "status": status,
        "errors": errors
    }

    # --------------------------------------------------------
    # CV
    # --------------------------------------------------------

    status, errors = validate_cv(
        application
    )

    checks["cv"] = {
        "status": status,
        "errors": errors
    }

    # --------------------------------------------------------
    # Language
    # --------------------------------------------------------

    status, messages = validate_language(
        application,
        cover_letter,
        email_body
    )

    checks["language"] = {
        "status": status,
        "warnings": messages
    }

    # --------------------------------------------------------
    # Known facts
    # --------------------------------------------------------

    status, messages = validate_known_facts(
        application,
        cover_letter
    )

    checks["known_facts"] = {
        "status": status,
        "warnings": messages
    }

    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    score = calculate_score(
        checks
    )

    status = determine_status(
        checks
    )

    return {

        "application_id": application.get(
            "application_id"
        ),

        "validated_at": __import__(
            "datetime"
        ).datetime.now().isoformat(
            timespec="seconds"
        ),

        "status": status,

        "score": score,

        "checks": checks,

        "summary": {

            "ready_for_draft": (
                status == "passed"
            ),

            "requires_human_review": (
                status == "needs_review"
                or status == "failed"
            )
        }
    }


# ============================================================
# DISPLAY
# ============================================================

def print_summary(
    validation: dict
) -> None:

    print("\n" + "=" * 60)
    print("CONTENT VALIDATION RESULT")
    print("=" * 60)

    print(
        f"Status : {validation['status']}"
    )

    print(
        f"Score  : {validation['score']}/100"
    )

    print()

    for name, result in validation[
        "checks"
    ].items():

        status = result.get(
            "status"
        )

        if status == "passed":
            icon = "✅"

        elif status == "warning":
            icon = "⚠️"

        else:
            icon = "❌"

        print(
            f"{icon} {name}: {status}"
        )

        for error in result.get(
            "errors",
            []
        ):

            print(
                f"   └─ {error}"
            )

        for warning in result.get(
            "warnings",
            []
        ):

            print(
                f"   └─ {warning}"
            )

    print("\n" + "-" * 60)

    if validation[
        "summary"
    ]["ready_for_draft"]:

        print(
            "✅ Content aman untuk masuk "
            "ke tahap Gmail Draft."
        )

    else:

        print(
            "⚠️ Human review diperlukan "
            "sebelum membuat Gmail Draft."
        )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "JOB APPLICATION AUTOMATION"
    )
    print(
        "STEP 7.5 - CONTENT VALIDATOR"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # LOAD APPLICATION
    # --------------------------------------------------------

    print("\n📄 Loading application...")

    application = load_json(
        APPLICATION_FILE
    )

    print(
        f"✅ {application.get('application_id')}"
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    print(
        "\n🔍 Validating generated content..."
    )

    validation = validate_application(
        application
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_json(
        validation,
        OUTPUT_FILE
    )

    print(
        f"\n📄 Saved validation result:"
    )

    print(
        f"   {OUTPUT_FILE}"
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print_summary(
        validation
    )

    print(
        "\n✅ STEP 7.5 COMPLETE"
    )


if __name__ == "__main__":
    main()

