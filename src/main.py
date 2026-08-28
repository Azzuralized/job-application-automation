
"""
JOB APPLICATION AUTOMATION
Main Pipeline Orchestrator

Pipeline:

1. OCR
2. Job Parser
3. CV Profiler
4. CV Matcher
5. Application Builder
6. Cover Letter Generator
7. Content Validator
8. Gmail Draft Creator

This file intentionally contains orchestration logic only.
Each processing step remains responsible for its own logic.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PATH
# ============================================================

SRC_DIR = Path(__file__).resolve().parent


# ============================================================
# IMPORT PIPELINE STEPS
# ============================================================

from ocr import main as run_ocr
from job_parser import main as run_job_parser
from cv_profiler import main as run_cv_profiler
from cv_matcher import main as run_cv_matcher
from application_builder import main as run_application_builder
from cover_letter_generator import main as run_cover_letter_generator
from content_validator import main as run_content_validator
from gmail_draft_creator import main as run_gmail_draft_creator


# ============================================================
# PIPELINE
# ============================================================

STEPS = [
    (
        1,
        "OCR",
        run_ocr,
    ),
    (
        2,
        "JOB PARSER",
        run_job_parser,
    ),
    (
        3,
        "CV PROFILER",
        run_cv_profiler,
    ),
    (
        4,
        "CV MATCHER",
        run_cv_matcher,
    ),
    (
        5,
        "APPLICATION BUILDER",
        run_application_builder,
    ),
    (
        6,
        "COVER LETTER GENERATOR",
        run_cover_letter_generator,
    ),
    (
        7,
        "CONTENT VALIDATOR",
        run_content_validator,
    ),
    (
        8,
        "GMAIL DRAFT CREATOR",
        run_gmail_draft_creator,
    ),
]


# ============================================================
# DISPLAY
# ============================================================

def print_header() -> None:

    print()
    print("=" * 70)
    print("JOB APPLICATION AUTOMATION")
    print("=" * 70)
    print()
    print("FULL PIPELINE")
    print()
    print("  1. OCR")
    print("  2. Job Parser")
    print("  3. CV Profiler")
    print("  4. CV Matcher")
    print("  5. Application Builder")
    print("  6. Cover Letter Generator")
    print("  7. Content Validator")
    print("  8. Gmail Draft Creator")
    print()
    print("=" * 70)


def print_step_start(
    number: int,
    name: str
) -> None:

    print()
    print()
    print("#" * 70)
    print(f"STEP {number} - {name}")
    print("#" * 70)


def print_step_complete(
    number: int,
    name: str
) -> None:

    print()
    print("-" * 70)
    print(f"✅ STEP {number} COMPLETE - {name}")
    print("-" * 70)


def print_step_failed(
    number: int,
    name: str,
    error: Exception
) -> None:

    print()
    print("!" * 70)
    print(f"❌ STEP {number} FAILED - {name}")
    print("!" * 70)
    print()
    print(f"Error: {error}")
    print()


# ============================================================
# RUN SINGLE STEP
# ============================================================

def run_step(
    number: int,
    name: str,
    function
) -> bool:

    print_step_start(
        number,
        name
    )

    try:

        result = function()

        print_step_complete(
            number,
            name
        )

        return True

    except KeyboardInterrupt:

        print()
        print(
            "⚠️ Pipeline dihentikan oleh user."
        )

        return False

    except Exception as error:

        print_step_failed(
            number,
            name,
            error
        )

        return False


# ============================================================
# MAIN PIPELINE
# ============================================================

def main() -> int:

    print_header()

    print(
        f"📂 Source directory:\n{SRC_DIR}"
    )

    print()
    print(
        "🚀 Starting application automation pipeline..."
    )

    for number, name, function in STEPS:

        success = run_step(
            number,
            name,
            function
        )

        if not success:

            print()
            print("=" * 70)
            print("❌ PIPELINE STOPPED")
            print("=" * 70)
            print()
            print(
                f"Pipeline berhenti pada STEP {number} - {name}."
            )
            print()

            return 1

    print()
    print()
    print("=" * 70)
    print("🎉 FULL PIPELINE COMPLETE")
    print("=" * 70)
    print()
    print("Semua proses berhasil dijalankan:")
    print()
    print("  ✅ 1. OCR")
    print("  ✅ 2. Job Parser")
    print("  ✅ 3. CV Profiler")
    print("  ✅ 4. CV Matcher")
    print("  ✅ 5. Application Builder")
    print("  ✅ 6. Cover Letter Generator")
    print("  ✅ 7. Content Validator")
    print("  ✅ 8. Gmail Draft Creator")
    print()
    print(
        "⚠️ Email belum dikirim."
    )
    print(
        "👤 Review Gmail Draft dan kirim secara manual."
    )
    print()
    print("=" * 70)

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )

