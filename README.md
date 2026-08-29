# 🤖 Job Application Automation System
> **AI drafts. The system checks. You approve.**

I got tired of manually retyping job postings and matching CVs by hand, so I built this. Give it a screenshot of a job listing and it'll pull out the details, pick your best-matching CV, write a cover letter, and leave a Gmail draft waiting for you — you still hit send.

---

## ✨ What it does
- 📸 **Reads the screenshot** — OCR (Tesseract + OpenCV) pulls the text out of a job posting image
- 🧠 **Makes sense of it** — Gemini turns that raw text into structured job data
- 🎯 **Picks a CV** — scores and ranks the CVs you have on hand against what the job actually asks for
- ✍️ **Writes the email and cover letter** — sticks strictly to facts, doesn't invent anything about you
- 🛡️ **Double-checks itself** — an 8-point validation pass runs before anything gets drafted
- 📧 **Leaves it in Gmail as a draft** — never sends on its own

---

## 🏗️ How it flows
```
Screenshot → OCR → Job Parser → CV Profiler → CV Matcher → 
Application Builder → Cover Letter Generator → Content Validator → 
Gmail Draft → 👤 You review and send
```

---

## 📦 Before you start, you'll need
- Python 3.10+
- Tesseract OCR installed ([grab it here](https://github.com/UB-Mannheim/tesseract/wiki))
- A Gemini API key ([get one here](https://aistudio.google.com/app/apikey))
- A Google Cloud project with the Gmail API turned on

---

## ⚙️ Getting it running
```bash
# Clone it and install what it needs
git clone https://github.com/Azzuralized/job-application-automation.git
cd job-application-automation
pip install -r requirements.txt

# Fill in your .env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=your_selected_gemini_model
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Then set up Gmail OAuth:
# grab credentials.json from the Google Cloud Console
# and drop it in credentials/credentials.json
```

---

## 🚀 Running it
```bash
# Drop screenshots into screenshots/
# Drop your CVs (PDF/DOCX) into cv/
python main.py
```
It'll build a Gmail draft for you. Open Gmail, give it a read, hit send yourself.

---

## 📂 What's in here
```
├── cv/              # Your CVs (PDF/DOCX)
├── screenshots/     # Job posting screenshots
├── credentials/     # OAuth credentials (gitignored)
├── token/           # OAuth token, auto-generated (gitignored)
├── src/             # The actual code
│   ├── ocr.py
│   ├── job_parser.py
│   ├── cv_profiler.py
│   ├── cv_matcher.py
│   ├── application_builder.py
│   ├── cover_letter_generator.py
│   ├── content_validator.py
│   └── gmail_draft_creator.py
└── output/          # Generated files, auto-created (gitignored)
```

---

## 🛡️ On security
- It never sends anything by itself — drafts only, you're always the one who presses send
- `.env`, `credentials/`, and `token/` are all gitignored, so your secrets stay off GitHub
- CVs stay on your machine — only the structured job data goes out to the API

---

## 📜 License
Built for personal use and learning. Always read over what it writes before you send it.

**Built by Farhan Azzura**
