import streamlit as st
import subprocess
from pathlib import Path
from datetime import datetime
import os
# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = Path(__file__).parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
CV_DIR = BASE_DIR / "cv"

# Create directories if not exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
CV_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Job Application Automation",
    page_icon="🤖",
    layout="wide"
)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    st.title("🤖 Job Automation")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["🏠 Home", "📸 Process Job", "📊 View Results", "📧 Gmail Draft"]
    )
    
    st.markdown("---")
    st.markdown("### System Status")
    
    # Check if profiles.json exists
    profiles_file = BASE_DIR / "output" / "cv" / "profiles.json"
    if profiles_file.exists():
        st.success("✅ CV profiles ready")
    else:
        st.warning("⚠️ No CV profiles yet")
        st.info("Run 'python main.py profile' first")
    
    # Count screenshots
    screenshots = list(SCREENSHOTS_DIR.glob("*.png")) + list(SCREENSHOTS_DIR.glob("*.jpg")) + list(SCREENSHOTS_DIR.glob("*.jpeg"))
    st.metric("Screenshots", len(screenshots))
    
    # Count CVs
    cvs = list(CV_DIR.glob("*.pdf")) + list(CV_DIR.glob("*.docx"))
    st.metric("CVs", len(cvs))

# ============================================================
# HOME PAGE
# ============================================================
if page == "🏠 Home":
    st.title("🤖 Job Application Automation")
    st.markdown("### Transform job screenshots into professional applications")
    
    st.markdown("---")
    
    # Pipeline Overview
    st.subheader("🔄 How It Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Step 1-2:** OCR & Job Parser")
        st.markdown("**Step 3:** CV Matcher")
        st.markdown("**Step 4:** Application Builder")
        st.markdown("**Step 5:** Cover Letter Generator")
    
    with col2:
        st.markdown("**Step 6:** Content Validator")
        st.markdown("**Step 7:** Gmail Draft Creator")
        st.markdown("**Step 8:** Human Review & Send")
    
    st.markdown("---")
    
    # Quick Start
    st.subheader("🚀 Quick Start")
    st.write("1. **First time?** Run `python main.py profile` to profile your CVs")
    st.write("2. Go to **Process Job** to upload screenshot")
    st.write("3. Run the pipeline")
    st.write("4. Review results in **View Results**")
    st.write("5. Create Gmail draft")

# ============================================================
# PROCESS JOB PAGE
# ============================================================
elif page == "📸 Process Job":
    st.title("📸 Process Job")
    st.markdown("Upload a job posting screenshot and run the automation pipeline")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    # ============================================================
    # LEFT COLUMN: Upload Screenshot
    # ============================================================
    with col1:
        st.subheader("📷 Upload Screenshot")
        
        uploaded_file = st.file_uploader(
            "Choose a job posting screenshot",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a screenshot of the job posting"
        )
        
        if uploaded_file is not None:
            # Save uploaded file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = Path(uploaded_file.name).suffix
            save_path = SCREENSHOTS_DIR / f"screenshot_{timestamp}{file_ext}"
            
            with open(save_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ Saved: {save_path.name}")
            st.image(save_path, caption="Uploaded Screenshot", use_container_width=True)
    
    # ============================================================
    # RIGHT COLUMN: Manage CVs
    # ============================================================
    with col2:
        st.subheader("📄 Manage CVs")
        
        # List existing CVs
        cv_files = list(CV_DIR.glob("*.pdf")) + list(CV_DIR.glob("*.docx"))
        
        if cv_files:
            st.write(f"**Found {len(cv_files)} CV(s):**")
            for cv in cv_files:
                st.write(f"📄 {cv.name}")
        else:
            st.warning("No CVs found in cv/ folder")
            st.info("Place your CV files (PDF/DOCX) in the cv/ folder")
        
        # Upload new CV
        uploaded_cv = st.file_uploader(
            "Upload new CV (optional)",
            type=['pdf', 'docx'],
            help="Upload additional CV to cv/ folder"
        )
        
        if uploaded_cv is not None:
            cv_save_path = CV_DIR / uploaded_cv.name
            with open(cv_save_path, 'wb') as f:
                f.write(uploaded_cv.getbuffer())
            st.success(f"✅ CV saved: {uploaded_cv.name}")
            st.rerun()
    
    st.markdown("---")
    
    # ============================================================
    # RUN PIPELINE
    # ============================================================
    st.subheader("🚀 Run Pipeline")
    
    # Check prerequisites
    profiles_file = BASE_DIR / "output" / "cv" / "profiles.json"
    if not profiles_file.exists():
        st.error("❌ CV profiles not found. Please run `python main.py profile` first.")
    else:
        st.success("✅ CV profiles ready")
        
        if st.button("▶️ Run Pipeline", type="primary", use_container_width=True):
            with st.spinner("Running pipeline... This may take a few minutes"):
                # Run python main.py apply
                env = os.environ.copy()
                env["PYTHONUTF8"] = "1"
                
                result = subprocess.run(
                    ["python", "main.py", "apply"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env=env,
                    cwd=BASE_DIR
                )
                
                if result.returncode == 0:
                    st.success("✅ Pipeline completed successfully!")
                    st.balloons()
                    
                    # Show output
                    with st.expander("📋 Pipeline Output"):
                        st.code(result.stdout, language="text")
                else:
                    st.error(f"❌ Pipeline failed")
                    with st.expander("📋 Error Output"):
                        st.code(result.stderr, language="text")

# ============================================================
# VIEW RESULTS PAGE (PLACEHOLDER)
# ============================================================
# ============================================================
# VIEW RESULTS PAGE
# ============================================================
elif page == "📊 View Results":
    st.title("📊 View Results")
    
    # Load application data
    app_file = BASE_DIR / "output" / "application" / "application.json"
    
    if not app_file.exists():
        st.warning("⚠️ No application data found. Run the pipeline first.")
        st.stop()
    
    import json
    with open(app_file, 'r', encoding='utf-8') as f:
        app_data = json.load(f)
    
    # ============================================================
    # JOB INFORMATION
    # ============================================================
    st.subheader("💼 Job Information")
    
    job = app_data.get('job', {})
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Company", job.get('company', 'N/A'))
        st.metric("Position", job.get('position', 'N/A'))
    
    with col2:
        st.metric("Location", job.get('location', 'N/A'))
        st.metric("Language", job.get('language_requirement', 'N/A'))
    
    if job.get('recipient_email'):
        st.info(f"📧 Recipient: {job['recipient_email']}")
    
    # Requirements
    if job.get('requirements'):
        with st.expander("📋 Job Requirements"):
            for req in job['requirements']:
                st.write(f"• {req}")
    
    st.markdown("---")
    
    # ============================================================
    # SELECTED CV
    # ============================================================
    st.subheader("📄 Selected CV")
    
    selected_cv = app_data.get('selected_cv', {})
    match_data = app_data.get('match', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("CV File", Path(selected_cv.get('file', 'N/A')).name)
    
    with col2:
        st.metric("Language", selected_cv.get('language', 'N/A'))
    
    with col3:
        score = match_data.get('score', 0)
        st.metric("Match Score", f"{score:.2f}")
    
    # Score Breakdown
    if match_data.get('breakdown'):
        with st.expander("📊 Score Breakdown"):
            breakdown = match_data['breakdown']
            for key, value in breakdown.items():
                st.write(f"**{key}**: {value:.2f}")
    
    st.markdown("---")
    
    # ============================================================
    # GENERATED CONTENT
    # ============================================================
    st.subheader("✍️ Generated Content")
    
    generated = app_data.get('generated_content', {})
    
    tab1, tab2, tab3 = st.tabs(["📝 Cover Letter", "📧 Email Subject", "📨 Email Body"])
    
    with tab1:
        if generated.get('cover_letter'):
            st.write(generated['cover_letter'])
            
            # Download button
            st.download_button(
                "📥 Download Cover Letter",
                generated['cover_letter'],
                file_name="cover_letter.txt",
                mime="text/plain"
            )
        else:
            st.warning("No cover letter generated")
    
    with tab2:
        if generated.get('email_subject'):
            st.write(generated['email_subject'])
        else:
            st.warning("No email subject generated")
    
    with tab3:
        if generated.get('email_body'):
            st.write(generated['email_body'])
            
            # Download button
            st.download_button(
                "📥 Download Email Body",
                generated['email_body'],
                file_name="email_body.txt",
                mime="text/plain"
            )
        else:
            st.warning("No email body generated")
    
    st.markdown("---")
    
    # ============================================================
    # VALIDATION RESULTS
    # ============================================================
    st.subheader("✅ Validation Results")
    
    validation_file = BASE_DIR / "output" / "application" / "validation.json"
    
    if validation_file.exists():
        with open(validation_file, 'r', encoding='utf-8') as f:
            validation = json.load(f)
        
        score = validation.get('score', 0)
        status = validation.get('status', 'unknown')
        
        if status == 'passed':
            st.success(f"✅ Validation PASSED - Score: {score}/100")
        elif status == 'needs_review':
            st.warning(f"⚠️ Validation NEEDS REVIEW - Score: {score}/100")
        else:
            st.error(f"❌ Validation FAILED - Score: {score}/100")
        
        # Show checks
        checks = validation.get('checks', {})
        with st.expander("🔍 Detailed Checks"):
            for check_name, check_data in checks.items():
                check_status = check_data.get('status', 'unknown')
                icon = "✅" if check_status == 'passed' else "⚠️" if check_status == 'warning' else "❌"
                st.write(f"{icon} **{check_name}**: {check_status}")
                
                if check_data.get('errors'):
                    for error in check_data['errors']:
                        st.write(f"   • {error}")
                
                if check_data.get('warnings'):
                    for warning in check_data['warnings']:
                        st.write(f"   • {warning}")
    else:
        st.warning("No validation data found")

# ============================================================
# GMAIL DRAFT PAGE (PLACEHOLDER)
# ============================================================
# ============================================================
# GMAIL DRAFT PAGE
# ============================================================
elif page == "📧 Gmail Draft":
    st.title("📧 Gmail Draft")
    
    # Load application data
    app_file = BASE_DIR / "output" / "application" / "application.json"
    
    if not app_file.exists():
        st.warning("⚠️ No application data found. Run the pipeline first.")
        st.stop()
    
    import json
    with open(app_file, 'r', encoding='utf-8') as f:
        app_data = json.load(f)
    
    # ============================================================
    # DRAFT STATUS
    # ============================================================
    st.subheader("📋 Draft Status")
    
    gmail_data = app_data.get('gmail', {})
    draft_created = gmail_data.get('draft_created', False)
    
    if draft_created:
        st.success("✅ Gmail Draft created successfully!")
        
        # Draft Details
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Draft ID", gmail_data.get('draft_id', 'N/A'))
            st.metric("Status", "Created")
        
        with col2:
            st.metric("Recipient", gmail_data.get('recipient', 'N/A'))
            st.metric("Subject", gmail_data.get('subject', 'N/A'))
        
        # Attachment info
        attachment = gmail_data.get('attachment', {})
        if attachment:
            st.info(f"📎 Attachment: {attachment.get('filename', 'N/A')}")
        
        st.markdown("---")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📧 Next Steps")
            st.write("1. Open Gmail")
            st.write("2. Go to **Drafts** folder")
            st.write("3. Review the draft")
            st.write("4. Click **Send**")
            
            # Link to Gmail
            st.markdown("[🔗 Open Gmail Drafts](https://mail.google.com/mail/u/0/#drafts)")
        
        with col2:
            st.markdown("### 🔄 Recreate Draft")
            st.write("If you want to recreate the draft (e.g., after editing content):")
            
            if st.button("🔄 Recreate Gmail Draft", type="secondary", use_container_width=True):
                with st.spinner("Recreating draft..."):
                    # Run Gmail Draft Creator only
                    env = os.environ.copy()
                    env["PYTHONUTF8"] = "1"
                    
                    result = subprocess.run(
                        ["python", "-c", 
                         "import sys; sys.path.insert(0, 'src'); "
                         "from src import gmail_draft_creator; "
                         "gmail_draft_creator.main()"],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        env=env,
                        cwd=BASE_DIR
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ Draft recreated successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Failed to recreate draft")
                        with st.expander("📋 Error Output"):
                            st.code(result.stderr, language="text")
    
    else:
        st.warning("⚠️ Gmail Draft not created yet")
        st.info("Run the pipeline to create a Gmail draft")
        
        if st.button("📧 Create Gmail Draft", type="primary", use_container_width=True):
            with st.spinner("Creating Gmail draft..."):
                # Run Gmail Draft Creator only
                env = os.environ.copy()
                env["PYTHONUTF8"] = "1"
                
                result = subprocess.run(
                    ["python", "-c", 
                     "import sys; sys.path.insert(0, 'src'); "
                     "from src import gmail_draft_creator; "
                     "gmail_draft_creator.main()"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env=env,
                    cwd=BASE_DIR
                )
                
                if result.returncode == 0:
                    st.success("✅ Gmail draft created successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to create draft")
                    with st.expander("📋 Error Output"):
                        st.code(result.stderr, language="text")
    
    st.markdown("---")
    
    # ============================================================
    # EMAIL PREVIEW
    # ============================================================
    st.subheader("📨 Email Preview")
    
    generated = app_data.get('generated_content', {})
    
    if generated:
        st.markdown(f"**Subject:** {generated.get('email_subject', 'N/A')}")
        st.markdown("---")
        st.markdown(generated.get('email_body', 'N/A'))
    else:
        st.warning("No email content generated")