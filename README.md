```markdown
# 🤖 Job Application Automation System

> **AI assists. System validates. Human approves.**

Automated job application system that converts job posting screenshots into Gmail drafts with attached CVs. Modular, secure, and human-in-the-loop.

---

## ✨ Features

- 📸 **Smart OCR** - Extract text from job posting screenshots (Tesseract + OpenCV)
- 🧠 **AI Parsing** - Convert OCR text to structured JSON (Google Gemini)
- 🎯 **CV Matcher** - Score and rank CVs based on job requirements
- ✍️ **Content Generation** - Create cover letters and emails (100% fact-based, no hallucination)
- 🛡️ **Validation** - 8-point safety check before draft creation
- 📧 **Gmail Integration** - Create drafts with CV attachments (no auto-send)

---

## 🏗️ Pipeline

```
Screenshot → OCR → Job Parser → CV Profiler → CV Matcher → 
Application Builder → Cover Letter Generator → Content Validator → 
Gmail Draft → 👤 Human Review & Send
```

---

## 📦 Requirements

- Python 3.10+
- Tesseract OCR ([Download](https://github.com/UB-Mannheim/tesseract/wiki))
- Google Gemini API Key ([Get here](https://aistudio.google.com/app/apikey))
- Google Cloud Project with Gmail API enabled

---

## ⚙️ Setup

```bash
# 1. Clone & install
git clone https://github.com/Azzuralized/job-application-automation.git
cd job-application-automation
pip install -r requirements.txt

# 2. Configure .env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=your_selected_gemini_model
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# 3. Setup Gmail OAuth
# Download credentials.json from Google Cloud Console
# Save to: credentials/credentials.json
```

---

## 🚀 Usage

```bash
# Place screenshots in screenshots/
# Place CVs (PDF/DOCX) in cv/
python main.py
```

Pipeline will create Gmail draft. Review in Gmail and send manually.

---

## 📂 Structure

```
├── cv/              # CV files (PDF/DOCX)
├── screenshots/     # Job posting images
├── credentials/     # OAuth credentials (gitignored)
├── token/           # OAuth token (auto-generated, gitignored)
├── src/             # Source code
│   ├── ocr.py
│   ├── job_parser.py
│   ├── cv_profiler.py
│   ├── cv_matcher.py
│   ├── application_builder.py
│   ├── cover_letter_generator.py
│   ├── content_validator.py
│   └── gmail_draft_creator.py
└── output/          # Generated files (auto-created, gitignored)
```

---

## 🛡️ Security

- **No auto-send** - Only creates drafts, human sends
- **Secrets protected** - `.env`, `credentials/`, `token/` in `.gitignore`
- **Local processing** - CVs processed locally, only structured data sent to API

---

## 📜 License

For educational and personal productivity use. Always review AI-generated content before sending.

**Built by Farhan Azzura**
```
