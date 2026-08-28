
# ocr.py

import os
from pathlib import Path

import cv2
import pytesseract
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SCREENSHOT_DIR = (
    BASE_DIR
    / "screenshots"
)

OCR_OUTPUT_DIR = (
    BASE_DIR
    / "output"
    / "ocr"
)

OCR_OUTPUT_FILE = (
    OCR_OUTPUT_DIR
    / "latest.txt"
)

SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
}


# ============================================================
# TESSERACT CONFIG
# ============================================================

TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD"
)

if not TESSERACT_CMD:
    raise RuntimeError(
        "TESSERACT_CMD tidak ditemukan di .env.\n"
        "Contoh:\n"
        "TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    )

pytesseract.pytesseract.tesseract_cmd = (
    TESSERACT_CMD
)


# ============================================================
# SCREENSHOT
# ============================================================

def get_latest_screenshot() -> Path | None:
    """
    Find the most recently modified screenshot.
    """

    if not SCREENSHOT_DIR.exists():

        raise FileNotFoundError(
            f"Screenshot directory tidak ditemukan:\n"
            f"{SCREENSHOT_DIR}"
        )

    screenshots = [
        file
        for file in SCREENSHOT_DIR.iterdir()
        if (
            file.is_file()
            and file.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    ]

    if not screenshots:
        return None

    return max(
        screenshots,
        key=lambda file: file.stat().st_mtime
    )


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(
    image_path: Path
):
    """
    Prepare screenshot before OCR.
    """

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        raise ValueError(
            f"Could not read image:\n"
            f"{image_path}"
        )

    # --------------------------------------------------------
    # 1. Grayscale
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # 2. Enlarge image
    # --------------------------------------------------------

    scale = 2

    resized = cv2.resize(
        gray,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    # --------------------------------------------------------
    # 3. Reduce noise
    # --------------------------------------------------------

    denoised = cv2.GaussianBlur(
        resized,
        (3, 3),
        0
    )

    # --------------------------------------------------------
    # 4. Otsu threshold
    # --------------------------------------------------------

    processed = cv2.threshold(
        denoised,
        0,
        255,
        cv2.THRESH_BINARY
        + cv2.THRESH_OTSU
    )[1]

    return processed


# ============================================================
# OCR
# ============================================================

def extract_text(
    image_path: Path
) -> str:
    """
    Preprocess screenshot and extract
    Indonesian + English text.
    """

    processed_image = preprocess_image(
        image_path
    )

    text = pytesseract.image_to_string(
        processed_image,
        lang="eng+ind",
        config="--psm 6"
    )

    return text.strip()


# ============================================================
# SAVE OCR RESULT
# ============================================================

def save_ocr_result(
    text: str
) -> Path:
    """
    Save OCR result to output/ocr/latest.txt.
    """

    OCR_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OCR_OUTPUT_FILE.write_text(
        text,
        encoding="utf-8"
    )

    return OCR_OUTPUT_FILE


# ============================================================
# RUN OCR PIPELINE
# ============================================================

def run() -> Path:
    """
    Execute OCR process.

    Returns:
        Path to generated OCR text file.
    """

    print("\n" + "=" * 60)
    print("STEP 2 - OCR")
    print("=" * 60)

    print(
        f"\n📂 Looking for screenshots:\n"
        f"{SCREENSHOT_DIR}"
    )

    latest = get_latest_screenshot()

    if latest is None:

        raise RuntimeError(
            "Tidak ada screenshot ditemukan."
        )

    print(
        f"✅ Latest screenshot: {latest.name}"
    )

    print(
        "\n🔍 Preprocessing image..."
    )

    text = extract_text(
        latest
    )

    print(
        "🔍 Running OCR..."
    )

    if not text:

        raise RuntimeError(
            "OCR tidak menghasilkan text."
        )

    output_file = save_ocr_result(
        text
    )

    print(
        "✅ OCR completed."
    )

    print(
        f"📄 Saved to:\n"
        f"{output_file}"
    )

    print(
        "\n" + "-" * 60
    )

    print("OCR RESULT")

    print("-" * 60)

    print(text)

    print("-" * 60)

    return output_file


# ============================================================
# STANDALONE ENTRY POINT
# ============================================================

def main():
    """
    Allow ocr.py to still be executed independently.
    """

    try:

        run()

    except Exception as error:

        print(
            "\n❌ OCR failed:"
        )

        print(
            f"   {error}"
        )


if __name__ == "__main__":
    main()

