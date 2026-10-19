/**
 * Primary Convert Workspace View.
 */

import { state } from "../state.js";
import { api } from "../api.js";
import { ICONS, showToast, formatBytes } from "../ui.js";

let pollInterval = null;

export function initConvertView() {
  const container = document.getElementById("view-convert");
  if (!container) return;

  renderConvertView(container);
  setupListeners(container);

  state.on("queueChange", () => renderQueue());
  state.on("selectedItemChange", () => renderSettingsPanel());
}

function renderConvertView(container) {
  container.innerHTML = `
    <div class="convert-layout">
      <!-- Left Main Column: Dropzone & Queue Table -->
      <div class="convert-main">
        <div id="convert-dropzone" class="dropzone">
          <div class="dropzone-icon">${ICONS.convert}</div>
          <div class="dropzone-title">Drop files here to convert</div>
          <div class="dropzone-subtitle">All processing occurs 100% locally on your machine · Zero data uploaded</div>
          <div style="display: flex; gap: var(--space-3); margin-top: var(--space-2);">
            <button id="btn-browse-files" class="btn btn-primary">
              <span style="width: 16px; height: 16px;">${ICONS.plus}</span>
              Browse Files
            </button>
            <input type="file" id="file-input-files" multiple style="display: none;" />
          </div>
        </div>

        <div id="queue-container" style="display: none; flex-direction: column; gap: var(--space-3);">
          <div class="queue-header-actions">
            <div style="display: flex; align-items: center; gap: var(--space-3);">
              <h2>Conversion Queue</h2>
              <span id="queue-count-badge" class="badge badge-primary">0 files</span>
            </div>
            <div style="display: flex; gap: var(--space-2);">
              <button id="btn-add-more" class="btn btn-secondary btn-sm">
                <span style="width: 14px; height: 14px;">${ICONS.plus}</span> Add More
              </button>
              <button id="btn-clear-queue" class="btn btn-ghost btn-sm">
                <span style="width: 14px; height: 14px;">${ICONS.trash}</span> Clear
              </button>
            </div>
          </div>

          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Source</th>
                  <th>Target Format</th>
                  <th>Size</th>
                  <th>Status</th>
                  <th style="text-align: right;">Actions</th>
                </tr>
              </thead>
              <tbody id="queue-table-body">
                <!-- Dynamically generated rows -->
              </tbody>
            </table>
          </div>

          <div style="display: flex; justify-content: flex-end; gap: var(--space-3); margin-top: var(--space-3);">
            <button id="btn-start-convert" class="btn btn-primary btn-lg" style="min-width: 180px;">
              <span style="width: 20px; height: 20px;">${ICONS.play || ICONS.convert}</span>
              Convert Files
            </button>
          </div>
        </div>
      </div>

      <!-- Right Column: Contextual Settings Panel -->
      <div id="convert-settings-sidebar" class="convert-sidebar">
        <div class="card" id="settings-card">
          <div class="card-header">
            <h3 class="card-title">Conversion Settings</h3>
            <span id="settings-format-badge" class="badge badge-neutral">Auto</span>
          </div>
          <div id="settings-card-body" class="card-body">
            <p style="color: var(--text-muted); font-size: var(--font-size-sm); text-align: center; padding: var(--space-6) 0;">
              Select a file in the queue to adjust format-specific options.
            </p>
          </div>
        </div>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const dropzone = container.querySelector("#convert-dropzone");
  const browseBtn = container.querySelector("#btn-browse-files");
  const fileInput = container.querySelector("#file-input-files");
  const addMoreBtn = container.querySelector("#btn-add-more");
  const clearBtn = container.querySelector("#btn-clear-queue");
  const startBtn = container.querySelector("#btn-start-convert");

  browseBtn.addEventListener("click", () => fileInput.click());
  if (addMoreBtn) addMoreBtn.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
      fileInput.value = "";
    }
  });

  // Drag and drop handlers
  ["dragenter", "dragover"].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("drag-active");
    });
  });

  ["dragleave", "drop"].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("drag-active");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFiles(files);
    }
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => state.clearQueue());
  }

  if (startBtn) {
    startBtn.addEventListener("click", startConversionQueue);
  }
}

async function handleFiles(files) {
  showToast(`Uploading and inspecting ${files.length} file(s)...`, "info", 2000);

  for (const file of files) {
    try {
      const res = await api.uploadFile(file);
      const meta = res.metadata;
      const targets = meta.available_targets || [];
      const defaultTarget = targets.length > 0 ? targets[0].format : "";

      state.addToQueue({
        id: "item_" + Math.random().toString(36).substr(2, 9),
        name: res.filename,
        path: res.path,
        format: meta.format || "unknown",
        family: meta.family || "other",
        size: meta.size_bytes || file.size,
        targets: targets,
        selectedTarget: defaultTarget,
        settings: {},
        status: "ready", // 'ready', 'converting', 'completed', 'failed', 'cancelled'
        progress: 0,
        progressMessage: "Ready",
        jobId: null,
        outputPath: null,
        error: null,
        metadata: meta
      });
    } catch (err) {
      showToast(`Failed to load ${file.name}: ${err.message}`, "error");
    }
  }
}

function renderQueue() {
  const dropzone = document.getElementById("convert-dropzone");
  const queueContainer = document.getElementById("queue-container");
  const tbody = document.getElementById("queue-table-body");
  const badge = document.getElementById("queue-count-badge");

  if (!dropzone || !queueContainer || !tbody) return;

  if (state.queue.length === 0) {
    dropzone.style.display = "flex";
    queueContainer.style.display = "none";
    renderSettingsPanel();
    return;
  }

  dropzone.style.display = "none";
  queueContainer.style.display = "flex";
  badge.textContent = `${state.queue.length} file${state.queue.length > 1 ? "s" : ""}`;

  tbody.innerHTML = "";

  state.queue.forEach(item => {
    const tr = document.createElement("tr");
    tr.className = item.id === state.selectedQueueItemId ? "selected-row" : "";
    tr.style.cursor = "pointer";

    // Format options for dropdown
    const targetOptions = item.targets.map(t => 
      `<option value="${t.format}" ${t.format === item.selectedTarget ? "selected" : ""}>${t.format.toUpperCase()} (${t.name})</option>`
    ).join("");

    let statusHtml = "";
    if (item.status === "ready") {
      statusHtml = `<span class="badge badge-neutral">Ready</span>`;
    } else if (item.status === "converting") {
      statusHtml = `
        <div style="min-width: 120px;">
          <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 2px;">
            <span>${item.progressMessage || "Converting"}</span>
            <span>${item.progress}%</span>
          </div>
          <div class="progress-container">
            <div class="progress-fill" style="width: ${item.progress}%;"></div>
          </div>
        </div>
      `;
    } else if (item.status === "completed") {
      statusHtml = `<span class="badge badge-success">Done</span>`;
    } else if (item.status === "failed") {
      statusHtml = `<span class="badge badge-danger" title="${item.error || 'Error'}">Failed</span>`;
    }

    let actionsHtml = `
      <div style="display: flex; justify-content: flex-end; gap: var(--space-2);">
    `;

    if (item.status === "completed" && item.jobId) {
      if (item.outputFiles && item.outputFiles.length > 1) {
        actionsHtml += `
          <button class="btn btn-primary btn-sm btn-view-pages" data-id="${item.id}" title="View & Download ${item.outputFiles.length} Individual Pages">
            <span style="width: 14px; height: 14px;">${ICONS.document || ICONS.convert}</span>
            <span>${item.outputFiles.length} Pages</span>
          </button>
          <a href="/api/jobs/${item.jobId}/download" class="btn btn-secondary btn-sm" download title="Download All (${item.outputFiles.length} Pages ZIP)">
            <span style="width: 14px; height: 14px;">${ICONS.download}</span>
          </a>
        `;
      } else {
        actionsHtml += `
          <a href="/api/jobs/${item.jobId}/download" class="btn btn-secondary btn-sm" download title="Download Output">
            <span style="width: 14px; height: 14px;">${ICONS.download}</span>
          </a>
        `;
      }
      actionsHtml += `
        <button class="btn btn-secondary btn-sm btn-open-folder" data-path="${item.outputPath}" title="Reveal in Folder">
          <span style="width: 14px; height: 14px;">${ICONS.folder}</span>
        </button>
      `;
    }

    actionsHtml += `
      <button class="btn btn-ghost btn-sm btn-remove-item" data-id="${item.id}" title="Remove file">
        <span style="width: 14px; height: 14px;">${ICONS.close}</span>
      </button>
    </div>`;

    tr.innerHTML = `
      <td>
        <div style="display: flex; align-items: center; gap: var(--space-2);">
          <span style="width: 20px; height: 20px; color: var(--color-primary);">${ICONS[item.family] || ICONS.document}</span>
          <span style="font-weight: 500; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.name}">${item.name}</span>
        </div>
      </td>
      <td><span class="badge badge-neutral">${item.format.toUpperCase()}</span></td>
      <td>
        <select class="input-select format-selector" data-id="${item.id}" style="height: 28px; font-size: 12px;">
          ${targetOptions || `<option value="">No targets</option>`}
        </select>
      </td>
      <td style="color: var(--text-muted); font-size: 12px;">${formatBytes(item.size)}</td>
      <td>${statusHtml}</td>
      <td>${actionsHtml}</td>
    `;

    // Row selection on click
    tr.addEventListener("click", (e) => {
      if (!e.target.closest("select") && !e.target.closest("button") && !e.target.closest("a")) {
        state.selectQueueItem(item.id);
      }
    });

    // Format selector change
    const sel = tr.querySelector(".format-selector");
    if (sel) {
      sel.addEventListener("change", (e) => {
        state.updateQueueItem(item.id, { selectedTarget: e.target.value });
        renderSettingsPanel();
      });
    }

    // View individual pages button
    const pagesBtn = tr.querySelector(".btn-view-pages");
    if (pagesBtn) {
      pagesBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        openPagesModal(item);
      });
    }

    // Remove button
    const removeBtn = tr.querySelector(".btn-remove-item");
    if (removeBtn) {
      removeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        state.removeFromQueue(item.id);
      });
    }

    // Open folder button
    const folderBtn = tr.querySelector(".btn-open-folder");
    if (folderBtn) {
      folderBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        api.openFolder(folderBtn.getAttribute("data-path")).catch(err => {
          showToast(`Could not open folder: ${err.message}`, "error");
        });
      });
    }

    tbody.appendChild(tr);
  });

  renderSettingsPanel();
}

function renderSettingsPanel() {
  const panelBody = document.getElementById("settings-card-body");
  const badge = document.getElementById("settings-format-badge");
  if (!panelBody) return;

  const item = state.getSelectedItem();
  if (!item) {
    badge.textContent = "Auto";
    panelBody.innerHTML = `
      <p style="color: var(--text-muted); font-size: var(--font-size-sm); text-align: center; padding: var(--space-6) 0;">
        Select a file in the queue to adjust format-specific options.
      </p>
    `;
    return;
  }

  badge.textContent = `${item.format.toUpperCase()} → ${item.selectedTarget.toUpperCase()}`;

  // Find target capability route for settings schema
  let route = null;
  for (const r of state.capabilities.routes || []) {
    if (r.source_formats.includes(item.format) && r.target_formats.includes(item.selectedTarget) && r.available) {
      route = r;
      break;
    }
  }

  let html = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4);">
      <div>
        <div style="font-weight: 600; font-size: var(--font-size-sm);">${item.name}</div>
        <div style="font-size: var(--font-size-xs); color: var(--text-muted);">${formatBytes(item.size)} · ${item.family.toUpperCase()}</div>
      </div>
  `;

  if (route && route.potential_info_loss) {
    html += `
      <div style="padding: var(--space-3); background: var(--color-warning-bg); border-left: 3px solid var(--color-warning); border-radius: 4px; font-size: 12px; color: var(--color-warning);">
        <strong>Note:</strong> ${route.potential_info_loss}
      </div>
    `;
  }

  // Common quick controls based on target family
  const targetFmt = item.selectedTarget;

  if (["jpg", "jpeg", "webp"].includes(targetFmt)) {
    const qVal = item.settings.quality !== undefined ? item.settings.quality : 85;
    html += `
      <div class="form-group">
        <label class="form-label">
          <span>Quality</span>
          <span class="slider-val" id="val-quality">${qVal}%</span>
        </label>
        <div class="slider-wrapper">
          <input type="range" class="range-slider setting-input" data-key="quality" min="1" max="100" value="${qVal}" />
        </div>
      </div>
    `;
  }

  if (["png", "jpg", "webp", "bmp"].includes(targetFmt)) {
    html += `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2);">
        <div class="form-group">
          <label class="form-label">Width (px)</label>
          <input type="number" class="input-number setting-input" data-key="width" placeholder="Original" value="${item.settings.width || ''}" />
        </div>
        <div class="form-group">
          <label class="form-label">Height (px)</label>
          <input type="number" class="input-number setting-input" data-key="height" placeholder="Original" value="${item.settings.height || ''}" />
        </div>
      </div>
      <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center;">
        <label class="form-label" style="margin-bottom: 0;">Preserve Aspect Ratio</label>
        <label class="switch">
          <input type="checkbox" class="setting-input" data-key="preserve_aspect" ${item.settings.preserve_aspect !== false ? "checked" : ""} />
          <span class="switch-slider"></span>
        </label>
      </div>
    `;
  }

  if (["mp3", "aac", "ogg", "opus", "m4a"].includes(targetFmt)) {
    const bitrates = ["64k", "96k", "128k", "192k", "256k", "320k"];
    html += `
      <div class="form-group">
        <label class="form-label">Audio Bitrate</label>
        <select class="input-select setting-input" data-key="bitrate">
          ${bitrates.map(b => `<option value="${b}" ${item.settings.bitrate === b || (!item.settings.bitrate && b === "192k") ? "selected" : ""}>${b}</option>`).join("")}
        </select>
      </div>
      <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center;">
        <label class="form-label" style="margin-bottom: 0;">Loudness Normalization (LUFS)</label>
        <label class="switch">
          <input type="checkbox" class="setting-input" data-key="loudness_norm" ${item.settings.loudness_norm ? "checked" : ""} />
          <span class="switch-slider"></span>
        </label>
      </div>
    `;
  }

  if (targetFmt === "pdf" && item.format === "pdf") {
    html += `
      <div class="form-group">
        <label class="form-label">Page Range</label>
        <input type="text" class="input-text setting-input" data-key="page_range" placeholder="e.g. 1-3, 5" value="${item.settings.page_range || ''}" />
      </div>
      <div class="form-group">
        <label class="form-label">Rotate Pages</label>
        <select class="input-select setting-input" data-key="rotate_pages">
          <option value="0" ${item.settings.rotate_pages === 0 ? "selected" : ""}>0° (No rotation)</option>
          <option value="90" ${item.settings.rotate_pages === 90 ? "selected" : ""}>90° Clockwise</option>
          <option value="180" ${item.settings.rotate_pages === 180 ? "selected" : ""}>180° Flip</option>
          <option value="270" ${item.settings.rotate_pages === 270 ? "selected" : ""}>270° Counter-clockwise</option>
        </select>
      </div>
    `;
  }

  if (item.format === "pdf" && ["png", "jpg", "jpeg", "webp", "bmp", "tiff"].includes(targetFmt)) {
    const dpiVal = item.settings.dpi || 150;
    html += `
      <div class="form-group">
        <label class="form-label">Page Range Filter</label>
        <input type="text" class="input-text setting-input" data-key="page_range" placeholder="e.g. 1-3, 5 (blank for all)" value="${item.settings.page_range || ''}" />
      </div>
      <div class="form-group">
        <label class="form-label">Resolution (DPI)</label>
        <select class="input-select setting-input" data-key="dpi">
          <option value="72" ${dpiVal === 72 ? "selected" : ""}>72 DPI (Standard Web)</option>
          <option value="150" ${dpiVal === 150 ? "selected" : ""}>150 DPI (Crisp / Recommended)</option>
          <option value="200" ${dpiVal === 200 ? "selected" : ""}>200 DPI (High Clarity)</option>
          <option value="300" ${dpiVal === 300 ? "selected" : ""}>300 DPI (Ultra / Print Quality)</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Rotate Pages</label>
        <select class="input-select setting-input" data-key="rotate_pages">
          <option value="0" ${item.settings.rotate_pages === 0 ? "selected" : ""}>0° (No rotation)</option>
          <option value="90" ${item.settings.rotate_pages === 90 ? "selected" : ""}>90° Clockwise</option>
          <option value="180" ${item.settings.rotate_pages === 180 ? "selected" : ""}>180° Flip</option>
          <option value="270" ${item.settings.rotate_pages === 270 ? "selected" : ""}>270° Counter-clockwise</option>
        </select>
      </div>
    `;
  }

  if (["csv", "tsv"].includes(targetFmt)) {
    html += `
      <div class="form-group">
        <label class="form-label">Delimiter</label>
        <select class="input-select setting-input" data-key="delimiter">
          <option value="comma" ${item.settings.delimiter === "comma" ? "selected" : ""}>Comma (,)</option>
          <option value="tab" ${item.settings.delimiter === "tab" ? "selected" : ""}>Tab (\\t)</option>
          <option value="semicolon" ${item.settings.delimiter === "semicolon" ? "selected" : ""}>Semicolon (;)</option>
        </select>
      </div>
    `;
  }

  // Display completed page breakdown in sidebar if multi-file
  if (item.status === "completed" && item.outputFiles && item.outputFiles.length > 1) {
    html += `
      <div style="border-top: 1px solid var(--border-subtle); padding-top: var(--space-3); margin-top: var(--space-3);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
          <strong style="font-size: var(--font-size-xs); color: var(--text-primary);">
            Converted Pages (${item.outputFiles.length})
          </strong>
          <button class="btn btn-primary btn-sm" id="btn-sidebar-view-pages" style="height: 24px; padding: 0 var(--space-2); font-size: 11px;">
            Open Gallery
          </button>
        </div>
        <div style="display: flex; flex-direction: column; gap: var(--space-2); max-height: 220px; overflow-y: auto;">
          ${item.outputFiles.map((f, i) => {
            const fname = f.split(/[/\\\\]/).pop();
            return `
              <div style="display: flex; align-items: center; justify-content: space-between; padding: var(--space-1) var(--space-2); background: var(--bg-surface-elevated); border-radius: var(--radius-sm); font-size: 11px; border: 1px solid var(--border-subtle);">
                <div style="display: flex; align-items: center; gap: var(--space-2); overflow: hidden;">
                  <span class="badge badge-primary" style="font-size: 10px; padding: 1px 4px;">P${i + 1}</span>
                  <span style="max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${fname}">
                    ${fname}
                  </span>
                </div>
                <div style="display: flex; gap: 4px;">
                  <a href="/api/jobs/${item.jobId}/download/${i + 1}" class="btn btn-secondary btn-sm" style="height: 22px; padding: 0 var(--space-2); font-size: 10px;" download="${fname}" title="Download Page ${i + 1}">
                    ${ICONS.download}
                  </a>
                  <a href="/api/jobs/${item.jobId}/preview/${i + 1}" target="_blank" class="btn btn-ghost btn-sm" style="height: 22px; padding: 0 4px; font-size: 10px;" title="Preview">
                    ↗
                  </a>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    `;
  }

  html += `</div>`;
  panelBody.innerHTML = html;

  // Listen to input changes in panel
  panelBody.querySelectorAll(".setting-input").forEach(input => {
    const key = input.getAttribute("data-key");
    const updateHandler = () => {
      let val;
      if (input.type === "checkbox") {
        val = input.checked;
      } else if (input.type === "number") {
        val = input.value ? Number(input.value) : undefined;
      } else if (input.type === "range") {
        val = Number(input.value);
        const display = document.getElementById(`val-${key}`);
        if (display) display.textContent = val + (key === "quality" ? "%" : "");
      } else {
        val = input.value;
      }
      item.settings[key] = val;
    };
    input.addEventListener("input", updateHandler);
    input.addEventListener("change", updateHandler);
  });

  const sidebarGalleryBtn = panelBody.querySelector("#btn-sidebar-view-pages");
  if (sidebarGalleryBtn) {
    sidebarGalleryBtn.addEventListener("click", () => openPagesModal(item));
  }
}

async function startConversionQueue() {
  const readyItems = state.queue.filter(i => i.status === "ready" || i.status === "failed");
  if (readyItems.length === 0) {
    showToast("No files ready to convert.", "info");
    return;
  }

  showToast(`Starting conversion of ${readyItems.length} file(s)...`, "info");

  for (const item of readyItems) {
    item.status = "converting";
    item.progress = 5;
    item.progressMessage = "Starting...";
    renderQueue();

    try {
      const job = await api.convert({
        source_path: item.path,
        target_format: item.selectedTarget,
        settings: item.settings,
        overwrite_policy: "rename"
      });
      item.jobId = job.id;
    } catch (err) {
      item.status = "failed";
      item.error = err.message;
      item.progressMessage = `Failed: ${err.message}`;
      renderQueue();
    }
  }

  // Start polling
  if (!pollInterval) {
    pollInterval = setInterval(pollActiveJobs, 1000);
  }
}

async function pollActiveJobs() {
  const convertingItems = state.queue.filter(i => i.status === "converting");
  if (convertingItems.length === 0) {
    clearInterval(pollInterval);
    pollInterval = null;
    return;
  }

  try {
    for (const item of convertingItems) {
      if (!item.jobId) continue;
      const job = await api.getJob(item.jobId);
      item.progress = job.progress || 0;
      item.progressMessage = job.progress_message || "";
      item.outputPath = job.target_path;

      if (job.status === "completed") {
        item.status = "completed";
        item.progress = 100;
        item.outputFiles = job.output_files || [];
        showToast(`Converted: ${item.name}`, "success");
      } else if (job.status === "failed") {
        item.status = "failed";
        item.error = job.error_message || "Conversion failed";
        showToast(`Failed: ${item.name} (${item.error})`, "error");
      }
    }
    renderQueue();
  } catch (err) {
    console.error("Poll error:", err);
  }
}

async function openPagesModal(item) {
  try {
    const filesData = await api.getJobFiles(item.jobId);
    if (!filesData.files || filesData.files.length === 0) {
      showToast("No individual page files found.", "info");
      return;
    }

    const modalId = "pages-modal-dialog";
    let modal = document.getElementById(modalId);
    if (!modal) {
      modal = document.createElement("div");
      modal.id = modalId;
      modal.className = "modal-backdrop";
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="modal-container" style="max-width: 820px; width: 92%;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <h3 class="modal-title" style="margin: 0; font-size: var(--font-size-md);">
              ${item.name} · Converted Pages
            </h3>
            <span class="badge badge-primary">${filesData.total_files} Pages (${item.selectedTarget.toUpperCase()})</span>
          </div>
          <button class="btn btn-ghost btn-sm btn-close-modal" title="Close">
            <span style="width: 16px; height: 16px;">${ICONS.close}</span>
          </button>
        </div>
        <div class="modal-body" style="max-height: 65vh; overflow-y: auto;">
          <p style="color: var(--text-muted); font-size: var(--font-size-xs); margin-top: 0; margin-bottom: var(--space-3);">
            Preview or download any individual page below, or download all pages together in a single ZIP file.
          </p>
          <div class="pdf-pages-grid">
            ${filesData.files.map(f => `
              <div class="pdf-page-card">
                <div class="pdf-page-thumb-wrapper">
                  <img src="${f.preview_url}" class="pdf-page-thumb" alt="${f.filename}" loading="lazy" />
                </div>
                <div class="pdf-page-meta">
                  <span class="pdf-page-name">Page ${f.index}</span>
                  <span class="pdf-page-size">${formatBytes(f.size_bytes)}</span>
                </div>
                <div style="display: flex; gap: var(--space-2); width: 100%; margin-top: var(--space-1);">
                  <a href="${f.download_url}" class="btn btn-primary btn-sm" style="flex: 1;" download="${f.filename}">
                    <span style="width: 14px; height: 14px;">${ICONS.download}</span> Download
                  </a>
                  <a href="${f.preview_url}" target="_blank" class="btn btn-secondary btn-sm" title="View Fullscreen">
                    <span style="width: 14px; height: 14px;">↗</span>
                  </a>
                </div>
              </div>
            `).join("")}
          </div>
        </div>
        <div class="modal-footer" style="display: flex; justify-content: space-between;">
          <button class="btn btn-secondary btn-sm btn-modal-folder">
            <span style="width: 14px; height: 14px;">${ICONS.folder}</span> Reveal in Folder
          </button>
          <div style="display: flex; gap: var(--space-2);">
            <a href="/api/jobs/${item.jobId}/download" class="btn btn-primary btn-sm" download>
              <span style="width: 14px; height: 14px;">${ICONS.download}</span> Download All (ZIP)
            </a>
            <button class="btn btn-secondary btn-sm btn-close-modal">Close</button>
          </div>
        </div>
      </div>
    `;

    modal.classList.add("open");

    const closeBtns = modal.querySelectorAll(".btn-close-modal");
    closeBtns.forEach(b => b.addEventListener("click", () => modal.classList.remove("open")));

    const folderBtn = modal.querySelector(".btn-modal-folder");
    if (folderBtn) {
      folderBtn.addEventListener("click", () => {
        api.openFolder(item.outputPath).catch(err => {
          showToast(`Could not open folder: ${err.message}`, "error");
        });
      });
    }

    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("open");
      }
    });

  } catch (err) {
    showToast(`Failed to load page list: ${err.message}`, "error");
  }
}
