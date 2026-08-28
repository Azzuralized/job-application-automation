#application_builder.py

from pathlib import Path
from datetime import datetime
import json
import re


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_FILE = (
    BASE_DIR
    / "output"
    / "job"
    / "latest.json"
)

SELECTED_CV_FILE = (
    BASE_DIR
    / "output"
    / "application"
    / "selected_cv.json"
)

# Metadata / CV index
CV_MANIFEST_FILE = (
    BASE_DIR
    / "output"
    / "cv"
    / "cv_manifest.json"
)

# Full CV profiles
CV_PROFILES_FILE = (
    BASE_DIR
    / "output"
    / "cv"
    / "profiles.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
    / "application"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "application.json"
)


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path: Path) -> dict:
    """Load JSON file safely."""

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
    """Save dictionary as formatted JSON."""

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
# STRING HELPERS
# ============================================================

def slugify(text: str) -> str:
    """
    Convert text into a safe identifier.

    Example:

    ETHOLOGY SYSTEM
    OPERATOR PEST CONTROL

    becomes:

    ethology-system-operator-pest-control
    """

    text = str(text).lower().strip()

    text = re.sub(
        r"[^a-z0-9\s-]",
        "",
        text
    )

    text = re.sub(
        r"[\s-]+",
        "-",
        text
    )

    return text.strip("-")


# ============================================================
# APPLICATION ID
# ============================================================

def generate_application_id(
    job: dict
) -> str:
    """Generate human-readable application ID."""

    company = job.get(
        "company",
        "unknown-company"
    )

    position = job.get(
        "position",
        "unknown-position"
    )

    date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    return (
        f"{date}-"
        f"{slugify(company)}-"
        f"{slugify(position)}"
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_job(
    job: dict
) -> None:

    required_fields = [
        "company",
        "position"
    ]

    missing = [
        field
        for field in required_fields
        if not job.get(field)
    ]

    if missing:
        raise ValueError(
            "Data job tidak lengkap.\n"
            f"Field yang hilang: "
            f"{', '.join(missing)}"
        )


def validate_matcher_output(
    matcher_data: dict
) -> None:

    if not matcher_data.get(
        "selected_cv"
    ):
        raise ValueError(
            "selected_cv.json tidak memiliki "
            "selected_cv."
        )

    selected_cv = matcher_data[
        "selected_cv"
    ]

    required_fields = [
        "id",
        "file",
        "language",
        "total_score"
    ]

    missing = [
        field
        for field in required_fields
        if field not in selected_cv
    ]

    if missing:
        raise ValueError(
            "Data selected CV tidak lengkap.\n"
            f"Field yang hilang: "
            f"{', '.join(missing)}"
        )


def validate_cv_manifest(
    manifest: dict
) -> None:
    """Validate CV manifest structure."""

    cvs = manifest.get("cvs")

    if not isinstance(cvs, list):
        raise ValueError(
            "cv_manifest.json harus memiliki "
            "field 'cvs' berupa list."
        )


def validate_cv_profiles(
    profiles_data: dict
) -> None:
    """Validate CV profiles structure."""

    cvs = profiles_data.get("cvs")

    if not isinstance(cvs, list):
        raise ValueError(
            "profiles.json harus memiliki "
            "field 'cvs' berupa list."
        )


# ============================================================
# CV PROFILE LOOKUP
# ============================================================

def find_cv_profile(
    profiles_data: dict,
    cv_id: str
) -> dict:
    """
    Find complete CV profile from profiles.json.

    profiles.json structure:

    {
        "cvs": [
            {
                "id": "...",
                "file": "...",
                "profile": {
                    ...
                }
            }
        ]
    }
    """

    cvs = profiles_data.get(
        "cvs",
        []
    )

    for cv in cvs:

        if cv.get("id") == cv_id:

            profile = cv.get(
                "profile"
            )

            if not isinstance(
                profile,
                dict
            ) or not profile:

                raise ValueError(
                    f"Profile untuk CV "
                    f"'{cv_id}' ditemukan "
                    "tetapi kosong."
                )

            return profile

    raise ValueError(
        f"CV dengan ID '{cv_id}' "
        "tidak ditemukan di profiles.json."
    )


# ============================================================
# CV CONSISTENCY CHECK
# ============================================================

def validate_cv_consistency(
    manifest: dict,
    profiles_data: dict,
    selected_cv: dict
) -> None:
    """
    Make sure selected CV exists in both
    manifest and profiles.

    This prevents mismatched CV data.
    """

    cv_id = selected_cv.get("id")

    if not cv_id:
        raise ValueError(
            "Selected CV tidak memiliki ID."
        )

    # --------------------------------------------------------
    # Check manifest
    # --------------------------------------------------------

    manifest_match = None

    for cv in manifest.get(
        "cvs",
        []
    ):

        if cv.get("id") == cv_id:
            manifest_match = cv
            break

    if manifest_match is None:

        raise ValueError(
            f"CV '{cv_id}' tidak ditemukan "
            "di cv_manifest.json."
        )

    # --------------------------------------------------------
    # Check profile
    # --------------------------------------------------------

    profile_match = None

    for cv in profiles_data.get(
        "cvs",
        []
    ):

        if cv.get("id") == cv_id:
            profile_match = cv
            break

    if profile_match is None:

        raise ValueError(
            f"CV '{cv_id}' tidak ditemukan "
            "di profiles.json."
        )

    # --------------------------------------------------------
    # Check file consistency
    # --------------------------------------------------------

    manifest_file = manifest_match.get(
        "file"
    )

    profile_file = profile_match.get(
        "file"
    )

    selected_file = selected_cv.get(
        "file"
    )

    if (
        manifest_file
        and selected_file
        and manifest_file != selected_file
    ):

        raise ValueError(
            "File CV tidak konsisten.\n"
            f"Manifest : {manifest_file}\n"
            f"Selected : {selected_file}"
        )

    if (
        profile_file
        and selected_file
        and profile_file != selected_file
    ):

        raise ValueError(
            "File CV pada profiles.json "
            "tidak konsisten dengan selected_cv.\n"
            f"Profile  : {profile_file}\n"
            f"Selected : {selected_file}"
        )


# ============================================================
# BUILD APPLICATION
# ============================================================

def build_application(
    job: dict,
    matcher_data: dict,
    cv_profile: dict
) -> dict:

    validate_job(
        job
    )

    validate_matcher_output(
        matcher_data
    )

    selected_cv = matcher_data[
        "selected_cv"
    ]

    application_id = (
        generate_application_id(
            job
        )
    )

    application = {

        # ----------------------------------------------------
        # IDENTIFICATION
        # ----------------------------------------------------

        "application_id": application_id,

        "created_at": datetime.now().isoformat(
            timespec="seconds"
        ),

        "status": "pending_review",

        # ----------------------------------------------------
        # JOB
        # ----------------------------------------------------

        "job": {

            "company": job.get(
                "company"
            ),

            "position": job.get(
                "position"
            ),

            "location": job.get(
                "location"
            ),

            "recipient_email": job.get(
                "recipient_email"
            ),

            "language_requirement": job.get(
                "language_requirement",
                "unknown"
            ),

            "requirements": job.get(
                "requirements",
                []
            ),

            "job_description": job.get(
                "job_description",
                []
            )
        },

        # ----------------------------------------------------
        # SELECTED CV
        # ----------------------------------------------------

        "selected_cv": {

            "id": selected_cv.get(
                "id"
            ),

            "file": selected_cv.get(
                "file"
            ),

            "language": selected_cv.get(
                "language"
            ),

            "profile": cv_profile
        },

        # ----------------------------------------------------
        # MATCH RESULT
        # ----------------------------------------------------

        "match": {

            "score": selected_cv.get(
                "total_score"
            ),

            "breakdown": selected_cv.get(
                "scores",
                {}
            ),

            "ranking": matcher_data.get(
                "ranking",
                []
            )
        },

        # ----------------------------------------------------
        # GENERATED CONTENT
        # ----------------------------------------------------

        "generated_content": {

            "cover_letter": None,

            "email_subject": None,

            "email_body": None
        },

        # ----------------------------------------------------
        # GMAIL
        # ----------------------------------------------------

        "gmail": {

            "draft_created": False,

            "draft_id": None
        }
    }

    return application


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print(
        "JOB APPLICATION AUTOMATION"
    )
    print(
        "STEP 6 - APPLICATION BUILDER"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # LOAD JOB
    # --------------------------------------------------------

    print(
        "\n📄 Loading job..."
    )

    job = load_json(
        JOB_FILE
    )

    validate_job(
        job
    )

    print(
        f"✅ {job.get('position')} "
        f"at {job.get('company')}"
    )

    # --------------------------------------------------------
    # LOAD MATCHER OUTPUT
    # --------------------------------------------------------

    print(
        "\n🎯 Loading CV match result..."
    )

    matcher_data = load_json(
        SELECTED_CV_FILE
    )

    validate_matcher_output(
        matcher_data
    )

    selected_cv = matcher_data[
        "selected_cv"
    ]

    print(
        f"✅ Selected CV: "
        f"{selected_cv.get('file')}"
    )

    print(
        f"🌐 Language: "
        f"{selected_cv.get('language')}"
    )

    print(
        f"🎯 Score: "
        f"{selected_cv.get('total_score')}"
    )

    # --------------------------------------------------------
    # LOAD CV MANIFEST
    # --------------------------------------------------------

    print(
        "\n📋 Loading CV manifest..."
    )

    manifest = load_json(
        CV_MANIFEST_FILE
    )

    validate_cv_manifest(
        manifest
    )

    print(
        f"✅ Manifest loaded: "
        f"{len(manifest['cvs'])} CV(s)"
    )

    # --------------------------------------------------------
    # LOAD FULL CV PROFILES
    # --------------------------------------------------------

    print(
        "\n📚 Loading CV profiles..."
    )

    profiles_data = load_json(
        CV_PROFILES_FILE
    )

    validate_cv_profiles(
        profiles_data
    )

    print(
        f"✅ Profiles loaded: "
        f"{len(profiles_data['cvs'])} CV(s)"
    )

    # --------------------------------------------------------
    # CONSISTENCY CHECK
    # --------------------------------------------------------

    print(
        "\n🔎 Checking CV consistency..."
    )

    validate_cv_consistency(
        manifest,
        profiles_data,
        selected_cv
    )

    print(
        "✅ CV metadata and profile "
        "are consistent."
    )

    # --------------------------------------------------------
    # FIND PROFILE
    # --------------------------------------------------------

    print(
        "\n🧠 Finding full CV profile..."
    )

    cv_profile = find_cv_profile(
        profiles_data,
        selected_cv.get("id")
    )

    print(
        "✅ Full CV profile loaded."
    )

    # --------------------------------------------------------
    # BUILD APPLICATION
    # --------------------------------------------------------

    print(
        "\n🔨 Building application context..."
    )

    application = build_application(
        job,
        matcher_data,
        cv_profile
    )

    print(
        "✅ Application context created."
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_json(
        application,
        OUTPUT_FILE
    )

    print(
        "\n📄 Saved application data:"
    )

    print(
        f"   {OUTPUT_FILE}"
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "APPLICATION SUMMARY"
    )

    print(
        "=" * 60
    )

    print(
        f"Application ID : "
        f"{application['application_id']}"
    )

    print(
        f"Company        : "
        f"{application['job']['company']}"
    )

    print(
        f"Position       : "
        f"{application['job']['position']}"
    )

    print(
        f"Location       : "
        f"{application['job']['location']}"
    )

    print(
        f"Recipient      : "
        f"{application['job']['recipient_email']}"
    )

    print(
        f"Selected CV    : "
        f"{application['selected_cv']['file']}"
    )

    print(
        f"CV Language    : "
        f"{application['selected_cv']['language']}"
    )

    print(
        f"Match Score    : "
        f"{application['match']['score']}"
    )

    print(
        f"Profile Fields : "
        f"{len(application['selected_cv']['profile'])}"
    )

    print(
        "=" * 60
    )

    print(
        "✅ STEP 6 COMPLETE"
    )

    print(
        "=" * 60
    )


if __name__ == "__main__":
    main()