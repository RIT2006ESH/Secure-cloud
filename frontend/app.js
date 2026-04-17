/* ═══════════════════════════════════════════════════
   Secure Cloud File Storage System — app.js
   ═══════════════════════════════════════════════════ */

const API_BASE = "http://127.0.0.1:8000";

// ── DOM refs ──────────────────────────────────────────
const dropZone      = document.getElementById("drop-zone");
const fileInput     = document.getElementById("file-input");
const filePreview   = document.getElementById("file-preview");
const previewName   = document.getElementById("preview-name");
const previewSize   = document.getElementById("preview-size");
const previewIcon   = document.getElementById("preview-icon");
const removeFileBtn = document.getElementById("remove-file");
const uploadBtn     = document.getElementById("upload-btn");
const progressWrap  = document.getElementById("progress-wrap");
const progressFill  = document.getElementById("progress-fill");
const progressPct   = document.getElementById("progress-pct");
const toast         = document.getElementById("toast");
const toastTitle    = document.getElementById("toast-title");
const toastMsg      = document.getElementById("toast-msg");
const toastIcon     = document.getElementById("toast-icon");
const filesList     = document.getElementById("files-list");
const refreshBtn    = document.getElementById("refresh-btn");

let selectedFile = null;

// ── File type → emoji ─────────────────────────────────
function fileEmoji(name) {
  const ext = name.split(".").pop().toLowerCase();
  const map = {
    pdf: "📄", doc: "📝", docx: "📝", txt: "📋",
    xls: "📊", xlsx: "📊", csv: "📊",
    ppt: "📑", pptx: "📑",
    jpg: "🖼️", jpeg: "🖼️", png: "🖼️", gif: "🖼️", svg: "🎨", webp: "🖼️",
    mp4: "🎬", mov: "🎬", avi: "🎬", mkv: "🎬",
    mp3: "🎵", wav: "🎵", flac: "🎵",
    zip: "🗜️", rar: "🗜️", "7z": "🗜️", tar: "🗜️",
    py: "🐍", js: "📜", ts: "📜", html: "🌐", css: "🎨",
    json: "🗂️", xml: "🗂️", yaml: "🗂️", yml: "🗂️",
  };
  return map[ext] || "📁";
}

// ── Human-readable file size ──────────────────────────
function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

// ── Show toast notification ───────────────────────────
function showToast(type, title, message) {
  toast.className = `visible ${type}`;
  toastIcon.textContent = type === "success" ? "✅" : "❌";
  toastTitle.textContent = title;
  toastMsg.textContent = message;

  // Auto-dismiss after 6 s
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => { toast.className = ""; }, 6000);
}

// ── Select / preview file ─────────────────────────────
function selectFile(file) {
  if (!file) return;
  selectedFile = file;
  previewName.textContent = file.name;
  previewSize.textContent = formatBytes(file.size);
  previewIcon.textContent = fileEmoji(file.name);
  filePreview.classList.add("visible");
  uploadBtn.disabled = false;
  toast.className = ""; // clear old toast
}

function clearFile() {
  selectedFile = null;
  fileInput.value = "";
  filePreview.classList.remove("visible");
  uploadBtn.disabled = true;
  progressWrap.classList.remove("visible");
  progressFill.style.width = "0%";
}

// ── Drag & drop ───────────────────────────────────────
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file) selectFile(file);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) selectFile(fileInput.files[0]);
});

removeFileBtn.addEventListener("click", clearFile);

// ── Upload ────────────────────────────────────────────
uploadBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  uploadBtn.disabled = true;
  uploadBtn.innerHTML = `<span>Uploading…</span>`;

  progressWrap.classList.add("visible");
  progressFill.style.width = "0%";
  progressPct.textContent = "0%";

  // Helper to reset button
  const resetUploadState = () => {
    uploadBtn.disabled = false;
    uploadBtn.innerHTML = `<span>☁️ Upload to S3</span>`;
    setTimeout(() => {
      progressWrap.classList.remove("visible");
      progressFill.style.width = "0%";
    }, 1200);
  };

  try {
    // [STEP 1] Get presigned POST URL and form fields from our FastAPI backend
    const presignRes = await fetch(`${API_BASE}/presigned-url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: selectedFile.name,
        // Fallback if browser doesn't know the exact mime type
        content_type: selectedFile.type || "application/octet-stream"
      })
    });
    
    const presignData = await presignRes.json();
    if (!presignRes.ok || !presignData.success) {
      throw new Error(presignData.detail || "Failed to generate presigned URL.");
    }
    
    const s3Data = presignData.data;
    const formData = new FormData();
    
    // [STEP 2] Append all AWS S3 required fields to FormData
    // Important: Fields must be appended before the file!
    Object.entries(s3Data.presigned_data.fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    // Finally, append the file
    formData.append("file", selectedFile);

    // [STEP 3] Upload directly to S3 using XMLHttpRequest for real progress events
    let uploadUrl = s3Data.presigned_data.url;
    // Force AWS Region injection to avoid 301 redirects which break CORS
    if (!uploadUrl.includes(s3Data.region)) {
        uploadUrl = uploadUrl.replace('.s3.amazonaws.com', `.s3.${s3Data.region}.amazonaws.com`);
    }

    const xhr = new XMLHttpRequest();
    xhr.open("POST", uploadUrl, true);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        progressFill.style.width = `${pct}%`;
        progressPct.textContent = `${pct}%`;
      }
    };

    xhr.onload = async () => {
      // 204 No Content is the default success response from S3 POST
      if (xhr.status >= 200 && xhr.status < 300) {
        progressFill.style.width = "100%";
        progressPct.textContent = "100%";
        
        try {
          // [STEP 4] Confirm upload to backend to store metadata in Firestore
          await fetch(`${API_BASE}/confirm-upload`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: "test_user", // hardcoded user for now
              s3_key: s3Data.s3_key,
              filename: s3Data.original_filename,
              size_bytes: selectedFile.size,
              url: `https://${s3Data.bucket}.s3.${s3Data.region}.amazonaws.com/${s3Data.s3_key}`
            })
          });
          
          showToast(
            "success",
            "Upload Successful 🎉",
            `${s3Data.original_filename} (${formatBytes(selectedFile.size)}) stored securely.`
          );
          clearFile();
          loadFiles();
        } catch (confirmErr) {
          showToast("error", "Metadata Error", "Uploaded to S3, but failed to save metadata.");
        }
      } else {
        // Parse S3 XML error message
        let errorMsg = "Direct S3 upload failed.";
        try {
          const parser = new DOMParser();
          const xmlDoc = parser.parseFromString(xhr.responseText, "text/xml");
          const code = xmlDoc.getElementsByTagName("Message")[0].textContent;
          errorMsg = `S3 Error: ${code}`;
        } catch(e) {}
        showToast("error", "Upload Failed", errorMsg);
      }
      resetUploadState();
    };

    xhr.onerror = () => {
      showToast("error", "Network Error", "Could not upload file directly to S3.");
      resetUploadState();
    };

    // Send the direct-to-S3 request
    xhr.send(formData);

  } catch (err) {
    showToast("error", "Upload Error", err.message || "Something went wrong.");
    resetUploadState();
  }
});

// ── Load file list ────────────────────────────────────
async function loadFiles() {
  refreshBtn.classList.add("spinning");
  filesList.innerHTML = '';

  try {
    const res = await fetch(`${API_BASE}/files`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "Failed to load files.");

    if (!data.files || data.files.length === 0) {
      filesList.innerHTML = `
        <li class="empty-state">
          <div class="empty-icon">☁️</div>
          No files uploaded yet. Upload your first file!
        </li>`;
      return;
    }

    data.files.forEach(f => {
      const li = document.createElement("li");
      li.className = "file-item";
      li.id = `file-${CSS.escape(f.s3_key)}`;

      const name = f.s3_key.split("/").pop();
      const modified = new Date(f.last_modified).toLocaleDateString("en-US", {
        year: "numeric", month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit",
      });

      li.innerHTML = `
        <div class="file-item-icon">${fileEmoji(name)}</div>
        <div class="file-item-info">
          <div class="file-item-name" title="${name}">${name}</div>
          <div class="file-item-meta">${formatBytes(f.size_bytes)} · ${modified}</div>
        </div>
        <div class="file-item-actions">
          <button class="btn-delete" data-key="${f.s3_key}" title="Delete from S3">
            🗑 Delete
          </button>
        </div>`;
      filesList.appendChild(li);
    });

    // Attach delete handlers
    document.querySelectorAll(".btn-delete").forEach(btn => {
      btn.addEventListener("click", () => deleteFile(btn.dataset.key, btn));
    });

  } catch (err) {
    filesList.innerHTML = `
      <li class="empty-state" style="color:var(--error-text)">
        <div class="empty-icon">⚠️</div>
        ${err.message}
      </li>`;
  } finally {
    refreshBtn.classList.remove("spinning");
  }
}

// ── Delete file ───────────────────────────────────────
async function deleteFile(s3Key, btn) {
  btn.disabled = true;
  btn.textContent = "Deleting…";

  try {
    const res = await fetch(`${API_BASE}/files/${encodeURIComponent(s3Key)}`, { method: "DELETE" });
    const data = await res.json();

    if (res.ok && data.success) {
      showToast("success", "File Deleted", `'${s3Key.split("/").pop()}' was removed from S3.`);
      loadFiles();
    } else {
      showToast("error", "Delete Failed", data.detail || "Could not delete the file.");
      btn.disabled = false;
      btn.innerHTML = "🗑 Delete";
    }
  } catch {
    showToast("error", "Network Error", "Could not reach the backend.");
    btn.disabled = false;
    btn.innerHTML = "🗑 Delete";
  }
}

// ── Refresh button ────────────────────────────────────
refreshBtn.addEventListener("click", loadFiles);

// ── Init ──────────────────────────────────────────────
uploadBtn.disabled = true;
loadFiles();
