/**
 * Batch Jobs Workspace - Redesigned Apple Pro Experience.
 */

import { api } from "../api.js";
import { ICONS, showToast, formatBytes } from "../ui.js";

let batchFiles = [];

export function initBatchView() {
  const container = document.getElementById("view-batch");
  if (!container) return;

  window.morphixBatchDrop = (files) => {
    if (files.length > 0) {
      loadBatchFiles(files);
    }
  };

  renderBatchView(container);
  setupListeners(container);
}

function renderBatchView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 1040px; margin: 0 auto; width: 100%;">
      <!-- Header -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h2>Batch Processing Studio</h2>
          <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
            High-throughput offline conversion pipeline with bounded concurrency and collision guard
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2);">
          <button id="batch-btn-select" class="btn btn-primary btn-sm">
            <span style="width: 13px; height: 13px;">${ICONS.plus}</span> Select Files
          </button>
          <button id="batch-btn-clear" class="btn btn-ghost btn-sm" title="Clear Batch List">
            <span style="width: 13px; height: 13px;">${ICONS.trash}</span> Clear
          </button>
          <input type="file" id="batch-file-input" multiple style="display: none;" />
        </div>
      </div>

      <!-- Batch Configuration Bar -->
      <div class="card" style="display: grid; grid-template-columns: 1fr 1fr 200px; gap: var(--space-4); padding: var(--space-4);">
        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">
            <span>Target Output Format</span>
            <span class="badge badge-primary" style="font-size: 10px;">Universal</span>
          </label>
          <select id="batch-target-fmt" class="input-select">
            <optgroup label="Modern Images">
              <option value="webp" selected>WebP (Lossy & Lossless)</option>
              <option value="png">PNG (Lossless)</option>
              <option value="jpg">JPEG (Photo Standard)</option>
            </optgroup>
            <optgroup label="Audio Formats">
              <option value="mp3">MP3 (High Compatibility)</option>
              <option value="wav">WAV (Uncompressed PCM)</option>
              <option value="flac">FLAC (Lossless)</option>
            </optgroup>
            <optgroup label="Documents & Spreadsheets">
              <option value="pdf">PDF (Document Format)</option>
              <option value="csv">CSV (Spreadsheet Data)</option>
            </optgroup>
          </select>
        </div>

        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">Collision Policy</label>
          <select id="batch-overwrite-policy" class="input-select">
            <option value="rename" selected>Safe Auto-Rename (_1, _2)</option>
            <option value="overwrite">Overwrite Existing Output</option>
          </select>
        </div>

        <div style="display: flex; align-items: flex-end;">
          <button id="batch-btn-start" class="btn btn-primary btn-lg" style="width: 100%; height: 32px;" disabled>
            <span style="width: 15px; height: 15px;">${ICONS.play}</span>
            Run Batch
          </button>
        </div>
      </div>

      <!-- Batch Progress Section -->
      <div id="batch-progress-card" class="card" style="display: none; border-color: var(--color-primary-border); background: var(--color-primary-light);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
          <span style="font-weight: 600; font-size: var(--font-size-sm); color: var(--color-primary);" id="batch-progress-title">Processing Batch...</span>
          <span style="font-size: var(--font-size-xs); font-family: var(--font-family-mono); color: var(--color-primary); font-weight: 600;" id="batch-progress-counts">0 / 0</span>
        </div>
        <div class="progress-container">
          <div id="batch-progress-bar" class="progress-fill" style="width: 0%;"></div>
        </div>
      </div>

      <!-- Drop strip for adding more batch files -->
      <div id="batch-drop-strip" class="drop-strip" title="Click or drop files here to add to batch">
        <div style="display: flex; align-items: center; gap: var(--space-2);">
          <span style="width: 16px; height: 16px; color: var(--color-primary);">${ICONS.plus}</span>
          <span style="font-size: var(--font-size-xs); color: var(--text-secondary);">
            Drag and drop additional files anywhere here to queue them for batch conversion...
          </span>
        </div>
        <span id="batch-file-count-badge" class="badge badge-neutral">0 files</span>
      </div>

      <!-- Files Queue Table -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>File Name</th>
              <th>Format</th>
              <th>Size</th>
              <th>Status</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody id="batch-table-body">
            <tr>
              <td colspan="5" style="text-align: center; color: var(--text-muted); padding: var(--space-8);">
                No files queued for batch. Drop files or click "Select Files" above to get started.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const selectBtn = container.querySelector("#batch-btn-select");
  const clearBtn = container.querySelector("#batch-btn-clear");
  const fileInput = container.querySelector("#batch-file-input");
  const startBtn = container.querySelector("#batch-btn-start");
  const dropStrip = container.querySelector("#batch-drop-strip");

  selectBtn.addEventListener("click", () => fileInput.click());
  if (dropStrip) dropStrip.addEventListener("click", () => fileInput.click());

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      batchFiles = [];
      renderBatchTable();
      showToast("Batch queue cleared", "info");
    });
  }

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      loadBatchFiles(Array.from(e.target.files));
      fileInput.value = "";
    }
  });

  if (dropStrip) {
    ["dragenter", "dragover"].forEach(name => {
      dropStrip.addEventListener(name, (e) => {
        e.preventDefault();
        dropStrip.classList.add("drag-active");
      });
    });
    ["dragleave", "drop"].forEach(name => {
      dropStrip.addEventListener(name, (e) => {
        e.preventDefault();
        dropStrip.classList.remove("drag-active");
      });
    });
    dropStrip.addEventListener("drop", (e) => {
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        loadBatchFiles(files);
      }
    });
  }

  startBtn.addEventListener("click", runBatchConversion);
}

async function loadBatchFiles(files) {
  showToast(`Preparing ${files.length} file(s) for batch...`, "info", 2000);
  for (const file of files) {
    try {
      const res = await api.uploadFile(file);
      batchFiles.push({
        id: "batch_" + Math.random().toString(36).substr(2, 9),
        name: file.name,
        path: res.path,
        format: res.metadata.format || "unknown",
        size: file.size,
        status: "ready",
        jobId: null,
        outputPath: null
      });
    } catch (err) {
      console.error(err);
    }
  }

  renderBatchTable();
}

function renderBatchTable() {
  const tbody = document.getElementById("batch-table-body");
  const startBtn = document.getElementById("batch-btn-start");
  const countBadge = document.getElementById("batch-file-count-badge");
  if (!tbody) return;

  if (countBadge) {
    countBadge.textContent = `${batchFiles.length} file${batchFiles.length !== 1 ? 's' : ''}`;
  }

  if (batchFiles.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: var(--space-8);">
          No files queued for batch. Drop files or click "Select Files" above to get started.
        </td>
      </tr>
    `;
    startBtn.disabled = true;
    return;
  }

  startBtn.disabled = false;
  tbody.innerHTML = "";

  batchFiles.forEach(item => {
    const tr = document.createElement("tr");

    let statusBadge = `<span class="badge badge-neutral">Ready</span>`;
    if (item.status === "converting") {
      statusBadge = `<span class="badge badge-primary">Processing...</span>`;
    } else if (item.status === "completed") {
      statusBadge = `<span class="badge badge-success">Done</span>`;
    } else if (item.status === "failed") {
      statusBadge = `<span class="badge badge-danger">Failed</span>`;
    }

    let actionBtn = "";
    if (item.status === "completed" && item.jobId) {
      actionBtn = `
        <a href="/api/jobs/${item.jobId}/download" class="btn btn-secondary btn-sm" download title="Download Output">
          <span style="width: 13px; height: 13px;">${ICONS.download}</span>
        </a>
      `;
    }

    tr.innerHTML = `
      <td>
        <span style="font-weight: 500; color: var(--text-primary);">${item.name}</span>
      </td>
      <td><span class="badge badge-neutral">${item.format.toUpperCase()}</span></td>
      <td style="color: var(--text-muted); font-size: 12px; font-family: var(--font-family-mono);">${formatBytes(item.size)}</td>
      <td>${statusBadge}</td>
      <td style="text-align: right;">${actionBtn}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function runBatchConversion() {
  const targetFmt = document.getElementById("batch-target-fmt").value;
  const overwritePolicy = document.getElementById("batch-overwrite-policy").value;
  const progressCard = document.getElementById("batch-progress-card");
  const progressBar = document.getElementById("batch-progress-bar");
  const countsElem = document.getElementById("batch-progress-counts");
  const startBtn = document.getElementById("batch-btn-start");

  const pending = batchFiles.filter(f => f.status === "ready");
  if (pending.length === 0) return;

  startBtn.disabled = true;
  progressCard.style.display = "block";

  let doneCount = 0;
  countsElem.textContent = `${doneCount} / ${pending.length}`;

  for (const item of pending) {
    item.status = "converting";
    renderBatchTable();

    try {
      const job = await api.convert({
        source_path: item.path,
        target_format: targetFmt,
        overwrite_policy: overwritePolicy
      });
      item.jobId = job.id;

      // Poll until done
      for (let i = 0; i < 30; i++) {
        await new Promise(r => setTimeout(r, 600));
        const status = await api.getJob(job.id);
        if (status.status === "completed") {
          item.status = "completed";
          item.outputPath = status.target_path;
          break;
        } else if (status.status === "failed") {
          item.status = "failed";
          break;
        }
      }
    } catch (err) {
      item.status = "failed";
    }

    doneCount++;
    const pct = Math.round((doneCount / pending.length) * 100);
    progressBar.style.width = `${pct}%`;
    countsElem.textContent = `${doneCount} / ${pending.length}`;
    renderBatchTable();
  }

  showToast(`Batch completed: ${doneCount} files processed.`, "success");
  startBtn.disabled = false;
}
