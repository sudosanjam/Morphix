/**
 * Documents and Office Processing Workspace.
 */

import { api } from "../api.js";
import { ICONS, showToast, formatBytes } from "../ui.js";

let loadedDoc = null;

export function initDocumentsView() {
  const container = document.getElementById("view-documents");
  if (!container) return;

  renderDocumentsView(container);
  setupListeners(container);
}

function renderDocumentsView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 900px; margin: 0 auto; width: 100%;">
      <div>
        <h2>Documents & Spreadsheets Processing</h2>
        <p style="font-size: var(--font-size-xs); color: var(--text-muted);">
          PDF page extraction & rotation, Markdown-to-PDF rendering, XLSX spreadsheet data conversion
        </p>
      </div>

      <!-- File Upload Box -->
      <div class="card" style="display: flex; align-items: center; justify-content: space-between; padding: var(--space-4);">
        <div style="display: flex; align-items: center; gap: var(--space-3);">
          <span style="width: 28px; height: 28px; color: var(--color-primary);">${ICONS.document}</span>
          <div>
            <strong id="doc-active-name" style="font-size: var(--font-size-sm);">No document loaded</strong>
            <div id="doc-active-sub" style="font-size: var(--font-size-xs); color: var(--text-muted);">Supports PDF, Markdown, TXT, XLSX, CSV</div>
          </div>
        </div>
        <button id="doc-btn-upload" class="btn btn-primary btn-sm">
          <span style="width: 14px; height: 14px;">${ICONS.plus}</span> Load Document
        </button>
        <input type="file" id="doc-file-input" accept=".pdf,.md,.txt,.html,.xlsx,.csv,.tsv" style="display: none;" />
      </div>

      <!-- Processing Form Card -->
      <div class="card" id="doc-processing-card" style="display: none;">
        <div class="card-header">
          <h3 class="card-title">Document Operations</h3>
          <span id="doc-detected-badge" class="badge badge-primary">PDF</span>
        </div>
        <div class="card-body" style="display: flex; flex-direction: column; gap: var(--space-4);">
          <!-- Dynamic Form Section based on format -->
          <div id="doc-dynamic-fields">
            <!-- Populated via JS -->
          </div>

          <div style="display: flex; justify-content: flex-end; margin-top: var(--space-3);">
            <button id="doc-btn-execute" class="btn btn-primary btn-lg">
              <span style="width: 18px; height: 18px;">${ICONS.play || ICONS.convert}</span> Process Document
            </button>
          </div>

          <!-- Result box -->
          <div id="doc-result-box" style="display: none; padding: var(--space-4); background: var(--color-success-bg); border-radius: var(--radius-md); align-items: center; justify-content: space-between;">
            <div>
              <strong style="color: var(--color-success);">Processing Completed</strong>
              <div style="font-size: 12px; color: var(--text-secondary);" id="doc-result-msg">Target generated successfully.</div>
            </div>
            <div style="display: flex; gap: var(--space-2);">
              <a id="doc-download-btn" class="btn btn-primary btn-sm" download>Download</a>
              <button id="doc-folder-btn" class="btn btn-secondary btn-sm">Show in Folder</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const uploadBtn = container.querySelector("#doc-btn-upload");
  const fileInput = container.querySelector("#doc-file-input");
  const execBtn = container.querySelector("#doc-btn-execute");

  uploadBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      loadDocumentFile(e.target.files[0]);
    }
  });

  execBtn.addEventListener("click", executeDocOperation);
}

async function loadDocumentFile(file) {
  showToast(`Loading ${file.name}...`, "info", 1500);
  try {
    const res = await api.uploadFile(file);
    const meta = res.metadata;

    loadedDoc = {
      file: file,
      path: res.path,
      meta: meta
    };

    document.getElementById("doc-active-name").textContent = file.name;
    document.getElementById("doc-active-sub").textContent = `${formatBytes(meta.size_bytes)} · Detected ${meta.format.toUpperCase()}`;
    document.getElementById("doc-processing-card").style.display = "block";
    document.getElementById("doc-detected-badge").textContent = meta.format.toUpperCase();

    renderDynamicDocFields(meta.format);
    showToast(`Loaded ${file.name}`, "success", 1500);
  } catch (err) {
    showToast(`Failed to load document: ${err.message}`, "error");
  }
}

function renderDynamicDocFields(format) {
  const fields = document.getElementById("doc-dynamic-fields");
  const fmt = format.toLowerCase();

  if (fmt === "pdf") {
    fields.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: var(--space-4);">
        <div class="form-group">
          <label class="form-label">Action / Target Format</label>
          <select id="doc-action-sel" class="input-select">
            <option value="pdf">Modify PDF (Page selection, Rotation, Metadata)</option>
            <option value="txt">Extract Plain Text (.txt)</option>
          </select>
        </div>
        <div id="pdf-extra-options" style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3);">
          <div class="form-group">
            <label class="form-label">Page Range Filter</label>
            <input type="text" id="pdf-page-range" class="input-text" placeholder="e.g. 1-3, 5 (blank for all)" />
          </div>
          <div class="form-group">
            <label class="form-label">Rotate Pages</label>
            <select id="pdf-rotate" class="input-select">
              <option value="0">0° (No rotation)</option>
              <option value="90">90° Clockwise</option>
              <option value="180">180° Flip</option>
              <option value="270">270° Counter-clockwise</option>
            </select>
          </div>
        </div>
      </div>
    `;

    document.getElementById("doc-action-sel").addEventListener("change", (e) => {
      document.getElementById("pdf-extra-options").style.display = e.target.value === "pdf" ? "grid" : "none";
    });

  } else if (["md", "markdown", "txt"].includes(fmt)) {
    fields.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: var(--space-3);">
        <div class="form-group">
          <label class="form-label">Target Format</label>
          <select id="doc-action-sel" class="input-select">
            <option value="pdf" selected>Render to Formatted PDF Document (.pdf)</option>
            <option value="html">Render to Clean HTML Webpage (.html)</option>
            <option value="txt">Export Plain Text (.txt)</option>
          </select>
        </div>
      </div>
    `;

  } else if (["xlsx", "csv", "tsv"].includes(fmt)) {
    fields.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
        <div class="form-group">
          <label class="form-label">Target Format</label>
          <select id="doc-action-sel" class="input-select">
            ${fmt === "xlsx" ? `
              <option value="csv" selected>CSV (Comma Separated)</option>
              <option value="tsv">TSV (Tab Separated)</option>
              <option value="json">JSON Array of Objects</option>
            ` : `
              <option value="xlsx" selected>Excel Workbook (.xlsx)</option>
              <option value="json">JSON Array of Objects</option>
            `}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Delimiter</label>
          <select id="sheet-delimiter" class="input-select">
            <option value="comma">Comma (,)</option>
            <option value="tab">Tab (\\t)</option>
            <option value="semicolon">Semicolon (;)</option>
          </select>
        </div>
      </div>
    `;
  } else {
    fields.innerHTML = `
      <div class="form-group">
        <label class="form-label">Target Format</label>
        <select id="doc-action-sel" class="input-select">
          <option value="pdf">PDF Document</option>
        </select>
      </div>
    `;
  }
}

async function executeDocOperation() {
  if (!loadedDoc) return;

  const execBtn = document.getElementById("doc-btn-execute");
  const targetFmt = document.getElementById("doc-action-sel").value;
  const settings = {};

  const rangeInput = document.getElementById("pdf-page-range");
  if (rangeInput && rangeInput.value.trim()) {
    settings.page_range = rangeInput.value.trim();
  }

  const rotateSelect = document.getElementById("pdf-rotate");
  if (rotateSelect) {
    settings.rotate_pages = Number(rotateSelect.value);
  }

  const delimSelect = document.getElementById("sheet-delimiter");
  if (delimSelect) {
    settings.delimiter = delimSelect.value;
  }

  execBtn.disabled = true;
  execBtn.textContent = "Processing...";

  try {
    const job = await api.convert({
      source_path: loadedDoc.path,
      target_format: targetFmt,
      settings: settings,
      overwrite_policy: "rename"
    });

    let finished = null;
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 600));
      const status = await api.getJob(job.id);
      if (status.status === "completed") {
        finished = status;
        break;
      } else if (status.status === "failed") {
        throw new Error(status.error_message || "Conversion failed");
      }
    }

    if (finished) {
      showToast("Document operation succeeded!", "success");
      const resultBox = document.getElementById("doc-result-box");
      const downloadBtn = document.getElementById("doc-download-btn");
      const folderBtn = document.getElementById("doc-folder-btn");
      const resultMsg = document.getElementById("doc-result-msg");

      resultBox.style.display = "flex";
      resultMsg.textContent = `Generated ${targetFmt.toUpperCase()} (${formatBytes(finished.output_size_bytes)})`;
      downloadBtn.href = `/api/jobs/${finished.id}/download`;
      downloadBtn.download = `${loadedDoc.file.name.split('.')[0]}_out.${targetFmt}`;
      folderBtn.onclick = () => api.openFolder(finished.target_path);
    }
  } catch (err) {
    showToast(`Document operation failed: ${err.message}`, "error");
  } finally {
    execBtn.disabled = false;
    execBtn.innerHTML = `<span style="width: 18px; height: 18px;">${ICONS.play || ICONS.convert}</span> Process Document`;
  }
}
