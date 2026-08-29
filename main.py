# main.py
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent

# Import pipeline steps
from src import ocr
from src import job_parser
from src import cv_profiler
from src import cv_matcher
from src import application_builder
from src import cover_letter_generator
from src import content_validator
from src import gmail_draft_creator

def run_ocr(): return ocr.run()
def run_job_parser(): job_parser.main()
def run_cv_profiler(): cv_profiler.main()
def run_cv_matcher(): cv_matcher.main()
def run_application_builder(): application_builder.main()
def run_cover_letter_generator(): cover_letter_generator.main()
def run_content_validator(): content_validator.main()
def run_gmail_draft_creator(): gmail_draft_creator.main()

STEPS = [
    (1, "OCR", run_ocr),
    (2, "JOB PARSER", run_job_parser),
    (3, "CV PROFILER", run_cv_profiler),
    (4, "CV MATCHER", run_cv_matcher),
    (5, "APPLICATION BUILDER", run_application_builder),
    (6, "COVER LETTER GENERATOR", run_cover_letter_generator),
    (7, "CONTENT VALIDATOR", run_content_validator),
    (8, "GMAIL DRAFT CREATOR", run_gmail_draft_creator),
]

def print_header():
    print("\n" + "=" * 70)
    print("JOB APPLICATION AUTOMATION")
    print("=" * 70 + "\nFULL PIPELINE\n")
    for num, name, _ in STEPS:
        print(f"  {num}. {name}")
    print("=" * 70)

def run_step(number: int, name: str, function) -> bool:
    print(f"\n{'#' * 70}\nSTEP {number} - {name}\n{'#' * 70}")
    try:
        function()
        print(f"\n{'-' * 70}\n✅ STEP {number} COMPLETE - {name}\n{'-' * 70}")
        return True
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline dihentikan oleh user.")
        return False
    except Exception as error:
        print(f"\n{'!' * 70}\n❌ STEP {number} FAILED - {name}\n{'!' * 70}\n\nError: {error}")
        return False

def main() -> int:
    print_header()
    print(f"📂 Source directory:\n{SRC_DIR}\n")
    print("🚀 Starting application automation pipeline...")
    
    for number, name, function in STEPS:
        if not run_step(number, name, function):
            print(f"\n{'=' * 70}\n❌ PIPELINE STOPPED\n{'=' * 70}")
            print(f"\nPipeline berhenti pada STEP {number} - {name}.\n")
            return 1
            
    print(f"\n{'=' * 70}\n🎉 FULL PIPELINE COMPLETE\n{'=' * 70}")
    print("\n⚠️ Email belum dikirim. 👤 Review Gmail Draft dan kirim secara manual.")
    return 0

if __name__ == "__main__":
    sys.exit(main())