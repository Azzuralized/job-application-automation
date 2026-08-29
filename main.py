# main.py
import sys
import argparse
from pathlib import Path

SRC_DIR = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC_DIR))

from src import ocr
from src import job_parser
from src import cv_profiler
from src import cv_matcher
from src import application_builder
from src import cover_letter_generator
from src import content_validator
from src import gmail_draft_creator


def print_header():
    print("\n" + "=" * 70)
    print("JOB APPLICATION AUTOMATION")
    print("=" * 70)


def run_step(step_num, step_name, func):
    print(f"\n{'#' * 70}")
    print(f"STEP {step_num} - {step_name}")
    print(f"{'#' * 70}\n")
    try:
        func()
        print(f"\n{'-' * 70}")
        print(f"✅ STEP {step_num} COMPLETE - {step_name}")
        print(f"{'-' * 70}")
        return True
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline dihentikan oleh user.")
        return False
    except Exception as error:
        print(f"\n{'!' * 70}")
        print(f"❌ STEP {step_num} FAILED - {step_name}")
        print(f"{'!' * 70}\n\nError: {error}")
        return False


def mode_profile():
    print_header()
    print("\n📋 MODE: PROFILE CVs")
    print("=" * 70)
    print("\nProfiling all CVs in cv/ folder...")

    if run_step(1, "CV PROFILER", cv_profiler.main):
        print("\n" + "=" * 70)
        print("✅ CV PROFILING COMPLETE")
        print("=" * 70)
        print("\n📄 Saved to: output/cv/profiles.json")
        print("\n🎯 Next: Run 'python main.py apply' to process a job.")
    else:
        sys.exit(1)


def mode_apply():
    print_header()
    print("\n📋 MODE: APPLY TO JOB")
    print("=" * 70)

    profiles_file = Path("output/cv/profiles.json")
    if not profiles_file.exists():
        print("\n❌ profiles.json tidak ditemukan!")
        print("💡 Jalankan 'python main.py profile' dulu.")
        sys.exit(1)

    print("\nProcessing job application (using existing CV profiles)...")

    steps = [
        (1, "OCR", ocr.run),
        (2, "JOB PARSER", job_parser.main),
        (3, "CV MATCHER", cv_matcher.main),
        (4, "APPLICATION BUILDER", application_builder.main),
        (5, "COVER LETTER GENERATOR", cover_letter_generator.main),
        (6, "CONTENT VALIDATOR", content_validator.main),
        (7, "GMAIL DRAFT CREATOR", gmail_draft_creator.main),
    ]

    for num, name, func in steps:
        if not run_step(num, name, func):
            print(f"\n{'=' * 70}")
            print("❌ PIPELINE STOPPED")
            print(f"{'=' * 70}")
            sys.exit(1)

    print(f"\n{'=' * 70}")
    print("🎉 JOB APPLICATION COMPLETE")
    print(f"{'=' * 70}")
    print("\n⚠️ Email belum dikirim.")
    print("👤 Review Gmail Draft dan kirim secara manual.")


def mode_full():
    print_header()
    print("\n📋 MODE: FULL PIPELINE")
    print("=" * 70)
    print("\nRunning complete pipeline...")

    steps = [
        (1, "OCR", ocr.run),
        (2, "JOB PARSER", job_parser.main),
        (3, "CV PROFILER", cv_profiler.main),
        (4, "CV MATCHER", cv_matcher.main),
        (5, "APPLICATION BUILDER", application_builder.main),
        (6, "COVER LETTER GENERATOR", cover_letter_generator.main),
        (7, "CONTENT VALIDATOR", content_validator.main),
        (8, "GMAIL DRAFT CREATOR", gmail_draft_creator.main),
    ]

    for num, name, func in steps:
        if not run_step(num, name, func):
            print(f"\n{'=' * 70}")
            print("❌ PIPELINE STOPPED")
            print(f"{'=' * 70}")
            sys.exit(1)

    print(f"\n{'=' * 70}")
    print("🎉 FULL PIPELINE COMPLETE")
    print(f"{'=' * 70}")
    print("\n⚠️ Email belum dikirim.")
    print("👤 Review Gmail Draft dan kirim secara manual.")


def main():
    parser = argparse.ArgumentParser(
        description="Job Application Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py profile    Profile CVs only
  python main.py apply      Process job (skip CV profiling)
  python main.py full       Full pipeline (all steps)
        """
    )

    parser.add_argument(
        'mode',
        nargs='?',
        choices=['profile', 'apply', 'full'],
        help='Mode: profile, apply, or full'
    )

    args = parser.parse_args()

    if not args.mode:
        parser.print_help()
        print("\n💡 Quick Start:")
        print("  1. First time?     python main.py profile")
        print("  2. New screenshot? python main.py apply")
        print("  3. Everything?     python main.py full")
        sys.exit(0)

    if args.mode == 'profile':
        mode_profile()
    elif args.mode == 'apply':
        mode_apply()
    elif args.mode == 'full':
        mode_full()


if __name__ == "__main__":
    main()