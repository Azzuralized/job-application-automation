// ============================================================
// API HELPERS
// ============================================================
async function apiGet(endpoint) {
    const response = await fetch(endpoint);
    if (!response.ok) throw new Error(`API error: ${response.statusText}`);
    return response.json();
}

async function apiPost(endpoint, data = null, isFormData = false) {
    const options = { method: 'POST' };
    if (isFormData) {
        options.body = data;
    } else {
        options.headers = { 'Content-Type': 'application/json' };
        if (data) options.body = JSON.stringify(data);
    }
    const response = await fetch(endpoint, options);
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `API error: ${response.statusText}`);
    }
    return response.json();
}

// ============================================================
// UX: TOAST NOTIFICATION
// ============================================================
function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<span>✅</span> <span>${message}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardStatus();
    setupCVUploadAndProfile(); // LOGIKA BARU: Upload + Profile
    setupScreenshotUpload();
    setupRunPipeline();
    setupCreateDraft();
});

// ============================================================
// DASHBOARD STATUS & CV CHECK
// ============================================================
async function loadDashboardStatus() {
    try {
        const status = await apiGet('/api/status');
        const cvs = await apiGet('/api/cvs');

        document.getElementById('cv-count').textContent = status.cv_count;
        document.getElementById('screenshot-count').textContent = status.screenshot_count;

        const profileStatus = document.getElementById('cv-profiles-status');
        profileStatus.textContent = status.cv_profiles_ready ? 'YES' : 'NO';
        profileStatus.className = status.cv_profiles_ready ? 'text-2xl text-[var(--sage)]' : 'text-2xl text-[var(--amber)]';

        const appStatus = document.getElementById('application-status');
        appStatus.textContent = status.application_ready ? 'READY' : 'PENDING';
        appStatus.className = status.application_ready ? 'text-2xl text-[var(--sage)]' : 'text-2xl text-[var(--fog)]';

        const cvListContainer = document.getElementById('cv-list-container');
        if (cvs.count === 0) {
            cvListContainer.innerHTML = `<span class="text-[var(--amber)]">⚠️ NO CVs DETECTED. Please upload and profile a CV to begin.</span>`;
        } else {
            let html = `<span class="text-[var(--sage)]">✅ ${cvs.count} CV(s) profiled and ready:</span><ul class="mt-2 space-y-1">`;
            cvs.files.forEach(file => {
                html += `<li class="text-[var(--paper)]">  ↳ ${file}</li>`;
            });
            html += `</ul>`;
            cvListContainer.innerHTML = html;

            // Reveal Step 2 if CVs exist
            document.getElementById('step-process').classList.remove('hidden-section');
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

// ============================================================
// STEP 1: CV UPLOAD & PROFILE (MODE_PROFILE)
// ============================================================
function setupCVUploadAndProfile() {
    const form = document.getElementById('cv-upload-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('cv-file');
        const file = fileInput.files[0];
        if (!file) return;

        const btn = form.querySelector('button');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<span class="status-dot"></span> SAVING & PROFILING...`;

        try {
            // 1. Upload file
            const formData = new FormData();
            formData.append('file', file);
            await apiPost('/api/upload-cv', formData, true);

            // 2. Trigger PROFILING ONLY (mode_profile)
            await apiPost('/api/profile');

            // 3. Success UX
            showToast(`CV "${file.name}" successfully saved and profiled!`);
            fileInput.value = ''; // Reset input
            await loadDashboardStatus(); // Refresh list and stats

        } catch (error) {
            alert('❌ Failed to save/profile CV: ' + error.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    });
}

// ============================================================
// STEP 2: SCREENSHOT UPLOAD
// ============================================================
function setupScreenshotUpload() {
    const fileInput = document.getElementById('screenshot-file');
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const url = URL.createObjectURL(file);
            document.getElementById('preview-img').src = url;
            document.getElementById('screenshot-preview').classList.remove('hidden');
            document.getElementById('run-pipeline-container').classList.remove('hidden');
        }
    });

    document.getElementById('screenshot-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            await apiPost('/api/upload-screenshot', formData, true);
            showToast('Screenshot uploaded and ready for pipeline.');
        } catch (error) {
            alert('❌ Screenshot upload failed: ' + error.message);
        }
    });
}

// ============================================================
// STEP 2: SCREENSHOT UPLOAD (AUTO-UPLOAD)
// ============================================================
function setupScreenshotUpload() {
    const fileInput = document.getElementById('screenshot-file');
    const previewDiv = document.getElementById('screenshot-preview');
    const runContainer = document.getElementById('run-pipeline-container');

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Tampilkan preview dulu
        const url = URL.createObjectURL(file);
        document.getElementById('preview-img').src = url;
        previewDiv.classList.remove('hidden');

        // AUTO-UPLOAD ke server
        const formData = new FormData();
        formData.append('file', file);

        try {
            await apiPost('/api/upload-screenshot', formData, true);
            showToast('Screenshot uploaded and ready!');

            // Tampilkan tombol "Create Draft" setelah upload sukses
            runContainer.classList.remove('hidden');
        } catch (error) {
            alert('❌ Screenshot upload failed: ' + error.message);
            previewDiv.classList.add('hidden');
            runContainer.classList.add('hidden');
        }
    });
}

// ============================================================
// STEP 2: RUN PIPELINE (ONE CLICK - CREATE DRAFT)
// ============================================================
function setupRunPipeline() {
    const btn = document.getElementById('run-pipeline-btn');
    const fileInput = document.getElementById('screenshot-file');
    const previewDiv = document.getElementById('screenshot-preview');
    const runContainer = document.getElementById('run-pipeline-container');

    btn.addEventListener('click', async () => {
        btn.disabled = true;
        btn.innerHTML = `<span class="status-dot"></span> CREATING DRAFT...`;
        document.getElementById('pipeline-loading').classList.remove('hidden');

        try {
            // Jalankan pipeline (screenshot sudah ter-upload otomatis)
            await apiPost('/api/apply');

            // Tunggu 1.5 detik biar file application.json ter-update
            await new Promise(resolve => setTimeout(resolve, 1500));

            // RESET UI untuk screenshot berikutnya
            fileInput.value = '';
            previewDiv.classList.add('hidden');
            runContainer.classList.add('hidden');

            document.getElementById('pipeline-loading').classList.add('hidden');
            document.getElementById('step-results').classList.remove('hidden');
            document.getElementById('step-results').scrollIntoView({ behavior: 'smooth' });

            await loadResults();

            // Tampilkan toast notifikasi jika draft berhasil dibuat
            const appData = await apiGet('/api/results');
            if (appData.gmail?.draft_created) {
                showToast('✅ Gmail Draft created successfully! Check your Gmail Drafts folder.');
            }

            // Reset button state
            btn.disabled = false;
            btn.innerHTML = `<span>Create Draft</span> <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;

        } catch (error) {
            alert('❌ Pipeline failed: ' + error.message);
            btn.disabled = false;
            btn.innerHTML = `<span>Create Draft</span> <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
        }
    });
}
// ============================================================
// STEP 3: LOAD & DISPLAY RESULTS
// ============================================================
async function loadResults() {
    try {
        const appData = await apiGet('/api/results');
        const valData = await apiGet('/api/validation');

        document.getElementById('res-company').textContent = appData.job?.company || 'N/A';
        document.getElementById('res-position').textContent = appData.job?.position || 'N/A';
        document.getElementById('res-email').textContent = appData.job?.recipient_email || 'N/A';
        document.getElementById('res-score').textContent = `${(appData.match?.score || 0).toFixed(1)}%`;

        document.getElementById('val-status').textContent = valData.status.toUpperCase();
        document.getElementById('val-status').className = valData.status === 'passed' ? 'text-[var(--sage)]' : 'text-[var(--amber)]';
        document.getElementById('val-score').textContent = `${valData.score}/100`;

        const warningsDiv = document.getElementById('val-warnings');
        if (valData.checks?.known_facts?.warnings) {
            warningsDiv.innerHTML = valData.checks.known_facts.warnings.map(w => `⚠️ ${w}`).join('<br>');
        }

        document.getElementById('res-cover-letter').textContent = appData.generated_content?.cover_letter || 'No cover letter generated.';

        // Auto-detect if draft was already created by the pipeline
        const draftCreated = appData.gmail?.draft_created || false;
        const draftBtn = document.getElementById('create-draft-btn');
        const draftSuccess = document.getElementById('draft-success');

        if (draftCreated) {
            draftBtn.classList.add('hidden');
            draftSuccess.classList.remove('hidden');
            draftSuccess.classList.add('flex');
        } else {
            draftBtn.classList.remove('hidden');
            draftSuccess.classList.add('hidden');
        }

    } catch (error) {
        console.error('Failed to load results:', error);
    }
}

// ============================================================
// STEP 3: CREATE DRAFT (Manual fallback)
// ============================================================
function setupCreateDraft() {
    const btn = document.getElementById('create-draft-btn');
    btn.addEventListener('click', async () => {
        btn.disabled = true;
        btn.textContent = 'CREATING DRAFT...';
        try {
            await apiPost('/api/create-draft');
            btn.classList.add('hidden');
            const draftSuccess = document.getElementById('draft-success');
            draftSuccess.classList.remove('hidden');
            draftSuccess.classList.add('flex');
            showToast('Gmail Draft created successfully!');
        } catch (error) {
            alert('❌ Failed to create draft: ' + error.message);
            btn.disabled = false;
            btn.textContent = 'CREATE GMAIL DRAFT';
        }
    });
}

// ============================================================
// UTILS
// ============================================================
function copyToClipboard(elementId) {
    const text = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!');
    });
}