#gmail_draft_creator.py

from pathlib import Path
from email.message import EmailMessage
import base64
import json
import os

from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


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

VALIDATION_FILE = (
    BASE_DIR
    / "output"
    / "application"
    / "validation.json"
)

CREDENTIALS_FILE = (
    BASE_DIR
    / "credentials"
    / "credentials.json"
)

TOKEN_DIR = (
    BASE_DIR
    / "token"
)

TOKEN_FILE = (
    TOKEN_DIR
    / "token.json"
)


# Gmail scope.
#
# This allows the application to create/manage drafts.
# The program intentionally does NOT implement sending.
#
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose"
]


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path: Path) -> dict:
    """Load JSON file."""

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


# ============================================================
# VALIDATION
# ============================================================

def validate_files() -> None:
    """Validate required files."""

    required_files = [
        APPLICATION_FILE,
        VALIDATION_FILE,
        CREDENTIALS_FILE
    ]

    for path in required_files:

        if not path.exists():

            raise FileNotFoundError(
                f"File yang dibutuhkan tidak ditemukan:\n{path}"
            )


def validate_application(
    application: dict
) -> None:
    """Validate application data."""

    required_sections = [
        "application_id",
        "job",
        "selected_cv",
        "generated_content"
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

    if not job.get("recipient_email"):

        raise ValueError(
            "Email penerima tidak tersedia."
        )


    selected_cv = application["selected_cv"]

    if not selected_cv.get("file"):

        raise ValueError(
            "File CV terpilih tidak tersedia."
        )


    generated = application["generated_content"]

    if not generated.get("email_subject"):

        raise ValueError(
            "Email subject belum tersedia."
        )


    if not generated.get("email_body"):

        raise ValueError(
            "Email body belum tersedia."
        )


# ============================================================
# VALIDATION RESULT
# ============================================================

def validate_content(
    validation: dict
) -> None:
    """Require Step 7.5 to pass."""

    status = str(
        validation.get("status", "")
    ).lower()

    score = validation.get(
        "score"
    )

    print(
        f"Validation status : {status}"
    )

    print(
        f"Validation score  : {score}/100"
    )

    if status != "passed":

        raise RuntimeError(
            "Content validation belum PASSED.\n"
            "Gmail Draft tidak akan dibuat."
        )


# ============================================================
# CV PATH
# ============================================================

def resolve_cv_path(
    cv_file: str
) -> Path:
    """
    Resolve CV path from application data.

    Example:

        cv\\CV_Farhan_Azzura_ID.pdf

    becomes:

        F:\\000\\Job\\cv\\CV_Farhan_Azzura_ID.pdf
    """

    normalized = str(
        cv_file
    ).replace(
        "\\",
        os.sep
    )

    relative_path = Path(
        normalized
    )

    if relative_path.is_absolute():

        cv_path = relative_path

    elif relative_path.parts and (
        relative_path.parts[0].lower() == "cv"
    ):

        cv_path = (
            BASE_DIR
            / relative_path
        )

    else:

        cv_path = (
            BASE_DIR
            / "cv"
            / relative_path.name
        )


    if not cv_path.exists():

        raise FileNotFoundError(
            "File CV tidak ditemukan:\n"
            f"{cv_path}"
        )


    return cv_path


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================

def authenticate_gmail():
    """
    Authenticate the user's Gmail account.

    First run:
        Opens browser for Google OAuth.

    Later runs:
        Reuses token.json.
    """

    TOKEN_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    credentials = None


    # --------------------------------------------------------
    # Existing token
    # --------------------------------------------------------

    if TOKEN_FILE.exists():

        print(
            "🔑 Existing Gmail token found."
        )

        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES
        )


    # --------------------------------------------------------
    # Refresh expired token
    # --------------------------------------------------------

    if credentials and credentials.expired:

        if credentials.refresh_token:

            print(
                "🔄 Refreshing Gmail authorization..."
            )

            credentials.refresh(
                Request()
            )

        else:

            credentials = None


    # --------------------------------------------------------
    # First-time OAuth
    # --------------------------------------------------------

    if not credentials:

        print(
            "\n🌐 Gmail authorization required."
        )

        print(
            "A browser window will open."
        )

        print(
            "Please sign in using the Gmail account "
            "you want to use for job applications."
        )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES
        )

        credentials = flow.run_local_server(
            port=0
        )


    # --------------------------------------------------------
    # Save token
    # --------------------------------------------------------

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8"
    )

    print(
        f"✅ Gmail authorization ready."
    )

    print(
        f"🔐 Token saved to: {TOKEN_FILE}"
    )

    return credentials


# ============================================================
# MIME MESSAGE
# ============================================================

def build_message(
    application: dict,
    cv_path: Path
) -> EmailMessage:
    """
    Build a MIME email with CV attachment.
    """

    job = application["job"]

    generated = application[
        "generated_content"
    ]


    recipient = job[
        "recipient_email"
    ]

    subject = generated[
        "email_subject"
    ]

    body = generated[
        "email_body"
    ]


    message = EmailMessage()


    # --------------------------------------------------------
    # Headers
    # --------------------------------------------------------

    message["To"] = recipient

    message["Subject"] = subject


    # --------------------------------------------------------
    # Body
    # --------------------------------------------------------

    message.set_content(
        body
    )


    # --------------------------------------------------------
    # CV attachment
    # --------------------------------------------------------

    cv_data = cv_path.read_bytes()

    message.add_attachment(
        cv_data,
        maintype="application",
        subtype="pdf",
        filename=cv_path.name
    )


    return message


# ============================================================
# CREATE GMAIL DRAFT
# ============================================================

def create_gmail_draft(
    service,
    message: EmailMessage
) -> dict:
    """
    Create a real Gmail Draft.

    IMPORTANT:
    This function ONLY calls drafts.create.
    It does NOT send the email.
    """

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode(
        "utf-8"
    )


    draft_body = {
        "message": {
            "raw": encoded_message
        }
    }


    draft = (
        service
        .users()
        .drafts()
        .create(
            userId="me",
            body=draft_body
        )
        .execute()
    )


    return draft


# ============================================================
# UPDATE APPLICATION
# ============================================================

def update_application(
    application: dict,
    draft: dict,
    cv_path: Path
) -> dict:
    """
    Store Gmail draft information
    inside application.json.
    """

    updated = json.loads(
        json.dumps(
            application
        )
    )


    if "gmail" not in updated:

        updated["gmail"] = {}


    updated["gmail"].update({

        "draft_created": True,

        "draft_id": draft.get(
            "id"
        ),

        "status": "draft_created",

        "recipient": application[
            "job"
        ].get(
            "recipient_email"
        ),

        "subject": application[
            "generated_content"
        ].get(
            "email_subject"
        ),

        "attachment": {

            "file": str(
                cv_path.relative_to(
                    BASE_DIR
                )
            ),

            "filename": cv_path.name
        }
    })


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
        "STEP 8 - GMAIL DRAFT CREATOR"
    )

    print("=" * 60)


    # --------------------------------------------------------
    # FILES
    # --------------------------------------------------------

    print(
        "\n📋 Checking required files..."
    )

    validate_files()

    print(
        "✅ Required files available."
    )


    # --------------------------------------------------------
    # APPLICATION
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
        f"✅ {application['application_id']}"
    )


    job = application[
        "job"
    ]

    selected_cv = application[
        "selected_cv"
    ]

    generated = application[
        "generated_content"
    ]


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    print(
        "\n🔍 Loading content validation..."
    )

    validation = load_json(
        VALIDATION_FILE
    )

    validate_content(
        validation
    )

    print(
        "✅ Content validation passed."
    )


    # --------------------------------------------------------
    # DISPLAY APPLICATION
    # --------------------------------------------------------

    print(
        "\n" + "-" * 60
    )

    print(
        "APPLICATION"
    )

    print(
        "-" * 60
    )

    print(
        f"Company    : "
        f"{job.get('company')}"
    )

    print(
        f"Position   : "
        f"{job.get('position')}"
    )

    print(
        f"Recipient  : "
        f"{job.get('recipient_email')}"
    )

    print(
        f"Subject    : "
        f"{generated.get('email_subject')}"
    )

    print(
        f"CV         : "
        f"{selected_cv.get('file')}"
    )


    # --------------------------------------------------------
    # CV
    # --------------------------------------------------------

    print(
        "\n📎 Resolving selected CV..."
    )

    cv_path = resolve_cv_path(
        selected_cv.get("file")
    )

    print(
        f"✅ {cv_path}"
    )


    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

    print(
        "\n🔐 Authenticating Gmail..."
    )

    credentials = authenticate_gmail()


    # --------------------------------------------------------
    # GMAIL SERVICE
    # --------------------------------------------------------

    print(
        "\n📡 Connecting to Gmail API..."
    )

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    print(
        "✅ Gmail API connected."
    )


    # --------------------------------------------------------
    # BUILD MESSAGE
    # --------------------------------------------------------

    print(
        "\n✉️ Building email..."
    )

    message = build_message(
        application,
        cv_path
    )

    print(
        "✅ Email prepared."
    )


    # --------------------------------------------------------
    # CREATE DRAFT
    # --------------------------------------------------------

    print(
        "\n📝 Creating Gmail Draft..."
    )

    draft = create_gmail_draft(
        service,
        message
    )


    draft_id = draft.get(
        "id"
    )


    if not draft_id:

        raise RuntimeError(
            "Gmail tidak mengembalikan Draft ID."
        )


    print(
        "✅ Gmail Draft created."
    )

    print(
        f"🆔 Draft ID: {draft_id}"
    )


    # --------------------------------------------------------
    # UPDATE APPLICATION
    # --------------------------------------------------------

    updated_application = (
        update_application(
            application,
            draft,
            cv_path
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
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "STEP 8 RESULT"
    )

    print(
        "=" * 60
    )

    print(
        "✅ REAL GMAIL DRAFT CREATED"
    )

    print(
        f"Recipient : "
        f"{job.get('recipient_email')}"
    )

    print(
        f"Subject   : "
        f"{generated.get('email_subject')}"
    )

    print(
        f"CV        : "
        f"{cv_path.name}"
    )

    print(
        f"Draft ID  : "
        f"{draft_id}"
    )

    print(
        "\n⚠️ Email BELUM dikirim."
    )

    print(
        "👤 Review dan klik Send secara manual "
        "di Gmail."
    )

    print(
        "=" * 60
    )

    print(
        "✅ STEP 8 COMPLETE"
    )

    print(
        "=" * 60
    )


if __name__ == "__main__":
    main()