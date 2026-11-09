/**
 * Primary Convert Workspace View - Redesigned Apple Pro Experience & Studio Deck.
 */

import { state } from "../state.js";
import { api } from "../api.js";
import { ICONS, showToast, formatBytes } from "../ui.js";

let pollInterval = null;
let currentViewMode = localStorage.getItem("morphix_convert_view_mode") || "cards"; // 'cards' or 'list'

export function initConvertView() {
  const container = document.getElementById("view-convert");
  if (!container) return;

  // Expose global hook for universal drag & drop
  window.morphixConvertDrop = (files) => handleFiles(files);

  renderConvertView(container);
  setupListeners(container);

  state.on("queueChange", () => renderQueue());
  state.on("selectedItemChange", () => renderSettingsPanel());
  state.on("prototypeChange", (proto) => {
    if (proto === "table") {
      currentViewMode = "list";
    } else {
      currentViewMode = "cards";
    }
    renderQueue();
  });
}

function renderConvertView(container) {
  const isEmpty = state.queue.length === 0;
  container.innerHTML = `
    <div class="convert-layout ${isEmpty ? 'empty-queue' : ''}">
      <!-- Main Workspace Column -->
      <div class="convert-main">
        <!-- 1. Creative Morphing Studio Hero (When queue is empty) -->
        <div id="convert-dropzone" class="studio-hero-card">
          <div class="studio-hero-icon-ring">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="16 3 21 3 21 8"></polyline>
              <line x1="4" y1="20" x2="21" y2="3"></line>
              <polyline points="21 16 21 21 16 21"></polyline>
              <line x1="15" y1="15" x2="21" y2="21"></line>
              <line x1="4" y1="4" x2="9" y2="9"></line>
            </svg>
          </div>
          <div class="studio-hero-title">Drop Any File to Morph</div>
          <div class="studio-hero-sub">
            Drag images, audio, documents, or spreadsheets anywhere onto the screen. Everything processes 100% locally on your machine with zero cloud telemetry.
          </div>

          <div style="display: flex; gap: var(--space-3); margin-top: var(--space-1);">
            <button id="btn-browse-files" class="btn btn-primary btn-lg" style="min-width: 170px;">
              <span style="width: 16px; height: 16px;">${ICONS.plus}</span>
              Browse Local Files
            </button>
            <input type="file" id="file-input-files" multiple style="display: none;" />
          </div>

          <!-- Quick Starter Feature Tiles -->
          <div class="studio-starter-grid">
            <div class="starter-item" data-starter="webp">
              <div class="starter-item-icon" style="background: var(--color-primary-light); color: var(--color-primary);">${ICONS.image}</div>
              <div>
                <div class="starter-item-title">Image Optimizer</div>
                <div class="starter-item-desc">WebP & AVIF transcoding (-80% size)</div>
              </div>
            </div>

            <div class="starter-item" data-starter="audio">
              <div class="starter-item-icon" style="background: var(--color-mocha-light); color: var(--color-mocha);">${ICONS.audio}</div>
              <div>
                <div class="starter-item-title">Audio Studio</div>
                <div class="starter-item-desc">Broadcast EBU R128 LUFS & MP3/Opus</div>
              </div>
            </div>

            <div class="starter-item" data-starter="pdf">
              <div class="starter-item-icon" style="background: var(--color-caramel-light); color: var(--color-caramel);">${ICONS.document}</div>
              <div>
                <div class="starter-item-title">Document & PDF Lab</div>
                <div class="starter-item-desc">Word to PDF, Page rotation, Extraction</div>
              </div>
            </div>

            <div class="starter-item" data-starter="sheet">
              <div class="starter-item-icon" style="background: var(--color-success-bg); color: var(--color-success);">${ICONS.spreadsheet}</div>
              <div>
                <div class="starter-item-title">Spreadsheet Engine</div>
                <div class="starter-item-desc">Excel XLSX to CSV, TSV, or JSON</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Active Queue Deck (When files are added) -->
        <div id="queue-container" style="display: none; flex-direction: column; gap: var(--space-3-5);">
          <!-- Compact Drop Strip -->
          <div id="convert-drop-strip" class="drop-strip" title="Click or drag files here to add more">
            <div style="display: flex; align-items: center; gap: var(--space-2-5);">
              <span style="width: 18px; height: 18px; color: var(--color-primary);">${ICONS.plus}</span>
              <span style="font-size: var(--font-size-xs); font-weight: 500; color: var(--text-secondary);">
                Drop more files anywhere on screen or click here to add...
              </span>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-2);">
              <span id="queue-count-badge" class="badge badge-primary">0 files</span>
              <span id="queue-size-summary" class="badge badge-neutral">0 B</span>
            </div>
          </div>

          <!-- Queue Control Bar -->
          <div class="queue-header-actions">
            <div class="queue-title-wrap">
              <h2>Media Deck</h2>
              <span style="font-size: var(--font-size-xs); color: var(--text-muted);">Adjust individual target formats or use batch presets below</span>
            </div>

            <div style="display: flex; align-items: center; gap: var(--space-2);">
              <!-- Segmented View Mode Toggle -->
              <div class="segmented-control" id="queue-view-toggle">
                <button class="segmented-btn ${currentViewMode === 'cards' ? 'active' : ''}" data-mode="cards" title="Studio Cards View">
                  <span style="width: 13px; height: 13px; display: inline-flex;">${ICONS.grid}</span>
                  <span>Cards</span>
                </button>
                <button class="segmented-btn ${currentViewMode === 'list' ? 'active' : ''}" data-mode="list" title="Power Table View">
                  <span style="width: 13px; height: 13px; display: inline-flex;">${ICONS.list}</span>
                  <span>Table</span>
                </button>
              </div>

              <button id="btn-merge-images-pdf" class="btn btn-mocha btn-sm" style="display: none;">
                <span style="width: 13px; height: 13px;">${ICONS.document}</span>
                <span id="btn-merge-images-label">Combine to PDF</span>
              </button>

              <button id="btn-toggle-inspector" class="btn btn-secondary btn-sm" title="Toggle Inspector Sidebar">
                <span style="width: 13px; height: 13px;">${ICONS.sliders}</span> Inspector
              </button>

              <button id="btn-clear-queue" class="btn btn-ghost btn-sm" title="Clear Queue">
                <span style="width: 13px; height: 13px;">${ICONS.trash}</span> Clear
              </button>
            </div>
          </div>

          <!-- Cards Grid View -->
          <div id="queue-cards-wrapper" class="queue-cards-grid" style="${currentViewMode === 'cards' ? '' : 'display: none;'}">
            <!-- Dynamically populated cards -->
          </div>

          <!-- Table View -->
          <div class="table-container" id="queue-table-wrapper" style="${currentViewMode === 'list' ? '' : 'display: none;'}">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Source File</th>
                  <th>Source</th>
                  <th>Target Format</th>
                  <th>Size</th>
                  <th>Status</th>
                  <th style="text-align: right;">Actions</th>
                </tr>
              </thead>
              <tbody id="queue-table-body">
                <!-- Dynamically populated rows -->
              </tbody>
            </table>
          </div>
        </div>

        <!-- 3. Floating Smart Action Dock (Fixed at bottom) -->
        <div id="floating-action-dock" class="floating-action-dock" style="display: none;">
          <div class="dock-left">
            <span class="dock-quick-label">Batch Convert:</span>
            <div class="dock-chips-group">
              <button class="format-chip" data-batch-fmt="webp">WebP</button>
              <button class="format-chip" data-batch-fmt="png">PNG</button>
              <button class="format-chip" data-batch-fmt="jpg">JPG</button>
              <button class="format-chip" data-batch-fmt="pdf">PDF</button>
              <button class="format-chip" data-batch-fmt="mp3">MP3</button>
              <button class="format-chip" data-batch-fmt="wav">WAV</button>
              <button class="format-chip" data-batch-fmt="csv">CSV</button>
            </div>
          </div>

          <div class="dock-right">
            <span id="dock-summary-text" class="dock-summary">0 files</span>
            <button id="btn-start-convert" class="btn btn-primary btn-convert-dock">
              <span style="width: 14px; height: 14px;">${ICONS.play}</span>
              Convert Queue
            </button>
          </div>
        </div>
      </div>

      <!-- Right Column: Inspector Sidebar -->
      <aside id="convert-settings-sidebar" class="convert-sidebar">
        <div class="card" id="settings-card" style="box-shadow: var(--shadow-md);">
          <div class="card-header">
            <div style="display: flex; align-items: center; gap: var(--space-2);">
              <span style="width: 15px; height: 15px; color: var(--color-primary);">${ICONS.sliders}</span>
              <h3 class="card-title">Inspector</h3>
            </div>
            <span id="settings-format-badge" class="badge badge-neutral">Auto</span>
          </div>
          <div id="settings-card-body" class="card-body">
            <p style="color: var(--text-muted); font-size: var(--font-size-sm); text-align: center; padding: var(--space-6) 0;">
              Select any file in the deck to configure fine-grained format settings.
            </p>
          </div>
        </div>
      </aside>
    </div>
  `;
}

function setupListeners(container) {
  const browseBtn = container.querySelector("#btn-browse-files");
  const fileInput = container.querySelector("#file-input-files");
  const dropStrip = container.querySelector("#convert-drop-strip");
  const clearBtn = container.querySelector("#btn-clear-queue");
  const startBtn = container.querySelector("#btn-start-convert");
  const mergePdfBtn = container.querySelector("#btn-merge-images-pdf");
  const inspectorToggle = container.querySelector("#btn-toggle-inspector");

  browseBtn.addEventListener("click", () => fileInput.click());
  if (dropStrip) dropStrip.addEventListener("click", () => fileInput.click());

  // Starter tiles click
  container.querySelectorAll("[data-starter]").forEach(tile => {
    tile.addEventListener("click", () => fileInput.click());
  });

  // Toggle Inspector Sidebar
  if (inspectorToggle) {
    inspectorToggle.addEventListener("click", () => {
      const sidebar = container.querySelector("#convert-settings-sidebar");
      if (sidebar) {
        sidebar.classList.toggle("collapsed");
      }
    });
  }

  // View Mode Switcher (Cards vs Table)
  const viewToggle = container.querySelector("#queue-view-toggle");
  if (viewToggle) {
    viewToggle.querySelectorAll(".segmented-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const mode = btn.getAttribute("data-mode");
        currentViewMode = mode;
        localStorage.setItem("morphix_convert_view_mode", mode);
        viewToggle.querySelectorAll(".segmented-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        const tableWrapper = container.querySelector("#queue-table-wrapper");
        const cardsWrapper = container.querySelector("#queue-cards-wrapper");
        if (tableWrapper && cardsWrapper) {
          if (mode === "list") {
            tableWrapper.style.display = "";
            cardsWrapper.style.display = "none";
          } else {
            tableWrapper.style.display = "none";
            cardsWrapper.style.display = "grid";
          }
        }
      });
    });
  }

  // Quick Format Switcher Chips (Apply to all eligible)
  container.querySelectorAll("[data-batch-fmt]").forEach(chip => {
    chip.addEventListener("click", () => {
      const targetFmt = chip.getAttribute("data-batch-fmt");
      applyFormatToAll(targetFmt);
    });
  });

  if (mergePdfBtn) {
    mergePdfBtn.addEventListener("click", async () => {
      const imageItems = state.queue.filter(i => 
        i.family === "image" || ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "ico", "gif"].includes(i.format)
      );
      if (imageItems.length < 2) {
        showToast("Select at least 2 images to combine into a PDF", "warning");
        return;
      }
      showToast(`Combining ${imageItems.length} images into a single PDF...`, "info", 3000);
      try {
        const imagePaths = imageItems.map(i => i.path);
        const firstStem = imageItems[0].name.split(".")[0];
        const job = await api.imagesToPdf(imagePaths, { title: `${firstStem}_merged` });

        for (let i = 0; i < 40; i++) {
          await new Promise(r => setTimeout(r, 600));
          const status = await api.getJob(job.id);
          if (status.status === "completed") {
            showToast(`Successfully combined ${imageItems.length} images into PDF!`, "success", 4000);
            const a = document.createElement("a");
            a.href = `/api/jobs/${status.id}/download`;
            a.download = `${firstStem}_merged.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            break;
          } else if (status.status === "failed") {
            throw new Error(status.error_message || "Merge failed");
          }
        }
      } catch (err) {
        showToast(`PDF merge failed: ${err.message}`, "error");
      }
    });
  }

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
      fileInput.value = "";
    }
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => state.clearQueue());
  }

  if (startBtn) {
    startBtn.addEventListener("click", startConversionQueue);
  }
}

function applyFormatToAll(targetFmt) {
  if (state.queue.length === 0) {
    showToast("Add files to queue first", "info");
    return;
  }

  let updatedCount = 0;
  state.queue.forEach(item => {
    const hasTarget = item.targets.some(t => t.format === targetFmt);
    if (hasTarget) {
      item.selectedTarget = targetFmt;
      updatedCount++;
    }
  });

  if (updatedCount > 0) {
    showToast(`Updated ${updatedCount} file(s) target to ${targetFmt.toUpperCase()}`, "success");
    renderQueue();
  } else {
    showToast(`Target ${targetFmt.toUpperCase()} is not available for current files`, "warning");
  }
}

async function handleFiles(files) {
  showToast(`Inspecting ${files.length} file(s)...`, "info", 1800);

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
  const convertLayout = document.querySelector(".convert-layout");
  const dropzone = document.getElementById("convert-dropzone");
  const queueContainer = document.getElementById("queue-container");
  const floatingDock = document.getElementById("floating-action-dock");
  const tbody = document.getElementById("queue-table-body");
  const cardsWrapper = document.getElementById("queue-cards-wrapper");
  const badge = document.getElementById("queue-count-badge");
  const sizeSummary = document.getElementById("queue-size-summary");
  const dockSummary = document.getElementById("dock-summary-text");

  if (!dropzone || !queueContainer) return;

  if (state.queue.length === 0) {
    if (convertLayout) convertLayout.classList.add("empty-queue");
    dropzone.style.display = "flex";
    queueContainer.style.display = "none";
    if (floatingDock) floatingDock.style.display = "none";
    renderSettingsPanel();
    return;
  }

  if (convertLayout) convertLayout.classList.remove("empty-queue");
  dropzone.style.display = "none";
  queueContainer.style.display = "flex";
  if (floatingDock) floatingDock.style.display = "flex";

  const totalBytes = state.queue.reduce((acc, i) => acc + (i.size || 0), 0);
  const countStr = `${state.queue.length} file${state.queue.length > 1 ? "s" : ""}`;
  const sizeStr = formatBytes(totalBytes);

  if (badge) badge.textContent = countStr;
  if (sizeSummary) sizeSummary.textContent = sizeStr;
  if (dockSummary) dockSummary.textContent = `${countStr} · ${sizeStr}`;

  // Multi-image merge button
  const mergeBtn = document.getElementById("btn-merge-images-pdf");
  const mergeLabel = document.getElementById("btn-merge-images-label");
  const imageCount = state.queue.filter(i => 
    i.family === "image" || ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "ico", "gif"].includes(i.format)
  ).length;

  if (mergeBtn) {
    if (imageCount >= 2) {
      mergeBtn.style.display = "inline-flex";
      if (mergeLabel) mergeLabel.textContent = `Combine ${imageCount} Images to PDF`;
    } else {
      mergeBtn.style.display = "none";
    }
  }

  // Clear wrappers
  if (tbody) tbody.innerHTML = "";
  if (cardsWrapper) cardsWrapper.innerHTML = "";

  state.queue.forEach(item => {
    const isSelected = item.id === state.selectedQueueItemId;
    const targetOptions = item.targets.map(t => 
      `<option value="${t.format}" ${t.format === item.selectedTarget ? "selected" : ""}>${t.format.toUpperCase()} (${t.name})</option>`
    ).join("");

    // Status HTML
    let statusHtml = "";
    if (item.status === "ready") {
      statusHtml = `<span class="badge badge-neutral">Ready</span>`;
    } else if (item.status === "converting") {
      statusHtml = `
        <div style="min-width: 110px;">
          <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 3px;">
            <span style="color: var(--text-secondary);">${item.progressMessage || "Converting"}</span>
            <span style="color: var(--color-primary); font-family: var(--font-family-mono); font-weight: 600;">${item.progress}%</span>
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

    // Savings estimate
    let savingsHtml = "";
    if (item.selectedTarget === "webp" || item.selectedTarget === "avif") {
      savingsHtml = `<span class="savings-chip">~ -70% size</span>`;
    } else if (item.selectedTarget === "mp3" && item.format === "wav") {
      savingsHtml = `<span class="savings-chip">~ -85% size</span>`;
    } else if (item.selectedTarget === "pdf") {
      savingsHtml = `<span class="savings-chip">Doc Bundle</span>`;
    }

    // Actions block
    let actionsHtml = `<div style="display: flex; justify-content: flex-end; align-items: center; gap: var(--space-1-5);">`;

    if (item.status === "completed" && item.jobId) {
      if (item.outputFiles && item.outputFiles.length > 1) {
        actionsHtml += `
          <button class="btn btn-primary btn-sm btn-view-pages" data-id="${item.id}" title="View & Download ${item.outputFiles.length} Individual Pages">
            <span style="width: 13px; height: 13px;">${ICONS.document}</span>
            <span>${item.outputFiles.length} Pages</span>
          </button>
          <a href="/api/jobs/${item.jobId}/download" class="btn btn-secondary btn-sm" download title="Download All (${item.outputFiles.length} Pages ZIP)">
            <span style="width: 13px; height: 13px;">${ICONS.download}</span>
          </a>
        `;
      } else {
        actionsHtml += `
          <a href="/api/jobs/${item.jobId}/download" class="btn btn-secondary btn-sm" download title="Download Converted File">
            <span style="width: 13px; height: 13px;">${ICONS.download}</span>
          </a>
        `;
      }
      actionsHtml += `
        <button class="btn btn-secondary btn-sm btn-open-folder" data-path="${item.outputPath}" title="Reveal in Folder">
          <span style="width: 13px; height: 13px;">${ICONS.folder}</span>
        </button>
      `;
    }

    actionsHtml += `
      <button class="btn btn-ghost btn-sm btn-remove-item" data-id="${item.id}" title="Remove file">
        <span style="width: 14px; height: 14px;">${ICONS.close}</span>
      </button>
    </div>`;

    // 1. CARDS VIEW (Studio Deck)
    if (cardsWrapper) {
      const card = document.createElement("div");
      card.className = `morph-card ${isSelected ? 'selected-card' : ''}`;
      card.innerHTML = `
        <div class="morph-card-top">
          <div class="morph-card-file-info">
            <div class="morph-card-icon" style="background: ${getFamilyBg(item.family)}; color: ${getFamilyColor(item.family)};">
              ${ICONS[item.family] || ICONS.document}
            </div>
            <div style="min-width: 0;">
              <div class="morph-card-name" title="${item.name}">${item.name}</div>
              <div class="morph-card-meta">
                <span>${formatBytes(item.size)}</span>
                <span>·</span>
                <span style="text-transform: uppercase;">${item.family}</span>
                ${savingsHtml}
              </div>
            </div>
          </div>
          <button class="btn btn-ghost btn-xs btn-remove-item" data-id="${item.id}" title="Remove file">
            <span style="width: 12px; height: 12px;">${ICONS.close}</span>
          </button>
        </div>

        <!-- Morph Flow Row -->
        <div class="morph-flow-pill">
          <span class="morph-tag">${item.format.toUpperCase()}</span>
          <span class="morph-arrow">${ICONS.arrowRight}</span>
          <select class="morph-target-select format-selector" data-id="${item.id}">
            ${targetOptions || `<option value="">No targets</option>`}
          </select>
        </div>

        <!-- Status & Actions Bottom Row -->
        <div style="display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); margin-top: 2px;">
          <div style="flex: 1;">${statusHtml}</div>
          ${actionsHtml}
        </div>
      `;

      bindItemEvents(card, item);
      cardsWrapper.appendChild(card);
    }

    // 2. TABLE VIEW (Power Table)
    if (tbody) {
      const tr = document.createElement("tr");
      tr.className = isSelected ? "selected-row" : "";
      tr.style.cursor = "pointer";

      tr.innerHTML = `
        <td>
          <div style="display: flex; align-items: center; gap: var(--space-2-5);">
            <span style="width: 20px; height: 20px; color: ${getFamilyColor(item.family)};">${ICONS[item.family] || ICONS.document}</span>
            <span style="font-weight: 500; max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.name}">${item.name}</span>
          </div>
        </td>
        <td><span class="badge badge-neutral">${item.format.toUpperCase()}</span></td>
        <td>
          <select class="input-select format-selector" data-id="${item.id}" style="height: 28px; font-size: 11.5px; padding-left: 8px;">
            ${targetOptions || `<option value="">No targets</option>`}
          </select>
        </td>
        <td style="color: var(--text-muted); font-size: 12px; font-family: var(--font-family-mono);">${formatBytes(item.size)}</td>
        <td>${statusHtml}</td>
        <td>${actionsHtml}</td>
      `;

      bindItemEvents(tr, item);
      tbody.appendChild(tr);
    }
  });

  renderSettingsPanel();
}

function bindItemEvents(element, item) {
  element.addEventListener("click", (e) => {
    if (!e.target.closest("select") && !e.target.closest("button") && !e.target.closest("a")) {
      state.selectQueueItem(item.id);
    }
  });

  const sel = element.querySelector(".format-selector");
  if (sel) {
    sel.addEventListener("change", (e) => {
      state.updateQueueItem(item.id, { selectedTarget: e.target.value });
      renderSettingsPanel();
    });
  }

  const pagesBtn = element.querySelector(".btn-view-pages");
  if (pagesBtn) {
    pagesBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openPagesModal(item);
    });
  }

  const removeBtn = element.querySelector(".btn-remove-item");
  if (removeBtn) {
    removeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      state.removeFromQueue(item.id);
    });
  }

  const folderBtn = element.querySelector(".btn-open-folder");
  if (folderBtn) {
    folderBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      api.openFolder(folderBtn.getAttribute("data-path")).catch(err => {
        showToast(`Could not open folder: ${err.message}`, "error");
      });
    });
  }
}

function getFamilyColor(family) {
  switch (family) {
    case "image": return "var(--family-image)";
    case "audio": return "var(--family-audio)";
    case "document": return "var(--family-document)";
    case "spreadsheet": return "var(--family-spreadsheet)";
    default: return "var(--color-primary)";
  }
}

function getFamilyBg(family) {
  switch (family) {
    case "image": return "var(--color-primary-light)";
    case "audio": return "var(--color-mocha-light)";
    case "document": return "var(--color-caramel-light)";
    case "spreadsheet": return "var(--color-success-bg)";
    default: return "var(--color-primary-light)";
  }
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
        Select any file in the deck to configure fine-grained format settings.
      </p>
    `;
    return;
  }

  badge.textContent = `${item.format.toUpperCase()} → ${item.selectedTarget.toUpperCase()}`;

  let route = null;
  for (const r of state.capabilities.routes || []) {
    if (r.source_formats.includes(item.format) && r.target_formats.includes(item.selectedTarget) && r.available) {
      route = r;
      break;
    }
  }

  let metaDetails = "";
  if (item.metadata && item.metadata.properties) {
    const props = item.metadata.properties;
    const parts = [];
    if (props.word_count) parts.push(`${props.word_count.toLocaleString()} words`);
    if (props.paragraphs_count) parts.push(`${props.paragraphs_count} paragraphs`);
    if (props.tables_count) parts.push(`${props.tables_count} tables`);
    if (props.page_count) parts.push(`${props.page_count} pages`);
    if (props.author && props.author !== "Unknown") parts.push(`by ${props.author}`);
    if (parts.length > 0) {
      metaDetails = `<div style="font-size: 11px; color: var(--color-primary); margin-top: 4px; font-weight: 500;">${parts.join(" · ")}</div>`;
    }
  }

  let html = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4);">
      <div class="inspector-section">
        <div class="inspector-section-title">Selected Asset</div>
        <div style="font-weight: 600; font-size: var(--font-size-sm); color: var(--text-primary); word-break: break-all;">
          ${item.name}
        </div>
        <div style="display: flex; align-items: center; gap: var(--space-2); margin-top: 2px;">
          <span class="badge badge-neutral">${formatBytes(item.size)}</span>
          <span class="badge" style="background: var(--color-primary-light); color: var(--color-primary);">${item.family.toUpperCase()}</span>
        </div>
        ${metaDetails}
      </div>
  `;

  if (route && route.potential_info_loss) {
    html += `
      <div style="padding: var(--space-3); background: var(--color-warning-bg); border-left: 3px solid var(--color-warning); border-radius: var(--radius-sm); font-size: 11.5px; color: var(--color-warning); line-height: 1.4;">
        <strong>Advisory:</strong> ${route.potential_info_loss}
      </div>
    `;
  }

  const targetFmt = item.selectedTarget;

  // 1. Image Quality & Compression
  if (["jpg", "jpeg", "webp"].includes(targetFmt)) {
    const qVal = item.settings.quality !== undefined ? item.settings.quality : 85;
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">
          <span>Compression Quality</span>
          <span class="slider-val" id="val-quality">${qVal}%</span>
        </div>
        <div class="slider-wrapper">
          <input type="range" class="range-slider setting-input" data-key="quality" min="1" max="100" value="${qVal}" />
        </div>
        <div class="quality-presets-wrap">
          <button type="button" class="quality-preset-btn ${qVal === 95 ? 'active' : ''}" data-set-quality="95">Max (95%)</button>
          <button type="button" class="quality-preset-btn ${qVal === 85 ? 'active' : ''}" data-set-quality="85">Balanced (85%)</button>
          <button type="button" class="quality-preset-btn ${qVal === 70 ? 'active' : ''}" data-set-quality="70">Web (70%)</button>
        </div>
      </div>
    `;
  }

  // 2. Geometry & Resizing
  if (["png", "jpg", "webp", "bmp"].includes(targetFmt)) {
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">Geometry & Resizing</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2);">
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Width (px)</label>
            <input type="number" class="input-number setting-input" data-key="width" placeholder="Original" value="${item.settings.width || ''}" />
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Height (px)</label>
            <input type="number" class="input-number setting-input" data-key="height" placeholder="Original" value="${item.settings.height || ''}" />
          </div>
        </div>
        <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center; margin-bottom: 0; margin-top: 4px;">
          <label class="form-label" style="margin-bottom: 0;">Preserve Aspect Ratio</label>
          <label class="switch">
            <input type="checkbox" class="setting-input" data-key="preserve_aspect" ${item.settings.preserve_aspect !== false ? "checked" : ""} />
            <span class="switch-slider"></span>
          </label>
        </div>
      </div>
    `;
  }

  // 3. Audio Encoding
  if (["mp3", "aac", "ogg", "opus", "m4a", "wav", "flac"].includes(targetFmt)) {
    const bitrates = ["64k", "96k", "128k", "192k", "256k", "320k"];
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">Audio Processing</div>
        ${targetFmt !== 'wav' && targetFmt !== 'flac' ? `
          <div class="form-group">
            <label class="form-label">Target Bitrate</label>
            <select class="input-select setting-input" data-key="bitrate">
              ${bitrates.map(b => `<option value="${b}" ${item.settings.bitrate === b || (!item.settings.bitrate && b === "192k") ? "selected" : ""}>${b}</option>`).join("")}
            </select>
          </div>
        ` : ''}
        <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center; margin-bottom: 0;">
          <div>
            <label class="form-label" style="margin-bottom: 0;">Broadcast Normalization</label>
            <span class="form-hint">EBU R128 (-16 LUFS)</span>
          </div>
          <label class="switch">
            <input type="checkbox" class="setting-input" data-key="loudness_norm" ${item.settings.loudness_norm ? "checked" : ""} />
            <span class="switch-slider"></span>
          </label>
        </div>
      </div>
    `;
  }

  // 4. PDF Page Range & Rotation
  if (targetFmt === "pdf" && item.format === "pdf") {
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">PDF Optimization</div>
        <div class="form-group">
          <label class="form-label">Page Range</label>
          <input type="text" class="input-text setting-input" data-key="page_range" placeholder="e.g. 1-3, 5" value="${item.settings.page_range || ''}" />
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">Rotate Orientation</label>
          <select class="input-select setting-input" data-key="rotate_pages">
            <option value="0" ${item.settings.rotate_pages === 0 ? "selected" : ""}>0° (Default)</option>
            <option value="90" ${item.settings.rotate_pages === 90 ? "selected" : ""}>90° Clockwise</option>
            <option value="180" ${item.settings.rotate_pages === 180 ? "selected" : ""}>180° Flip</option>
            <option value="270" ${item.settings.rotate_pages === 270 ? "selected" : ""}>270° Counter-clockwise</option>
          </select>
        </div>
      </div>
    `;
  }

  // 5. Document to Images / Rendering
  if (["pdf", "docx", "doc"].includes(item.format) && ["png", "jpg", "jpeg", "webp", "bmp", "tiff"].includes(targetFmt)) {
    const dpiVal = item.settings.dpi || 150;
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">Rendering Quality</div>
        <div class="form-group">
          <label class="form-label">Page Filter</label>
          <input type="text" class="input-text setting-input" data-key="page_range" placeholder="e.g. 1-3, 5 (blank = all)" value="${item.settings.page_range || ''}" />
        </div>
        <div class="form-group">
          <label class="form-label">Output DPI</label>
          <select class="input-select setting-input" data-key="dpi">
            <option value="72" ${dpiVal === 72 ? "selected" : ""}>72 DPI (Standard Web)</option>
            <option value="150" ${dpiVal === 150 ? "selected" : ""}>150 DPI (Crisp / Recommended)</option>
            <option value="200" ${dpiVal === 200 ? "selected" : ""}>200 DPI (High Clarity)</option>
            <option value="300" ${dpiVal === 300 ? "selected" : ""}>300 DPI (Ultra / Print Quality)</option>
          </select>
        </div>
        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">Rotate Pages</label>
          <select class="input-select setting-input" data-key="rotate_pages">
            <option value="0" ${item.settings.rotate_pages === 0 ? "selected" : ""}>0° (Default)</option>
            <option value="90" ${item.settings.rotate_pages === 90 ? "selected" : ""}>90° Clockwise</option>
            <option value="180" ${item.settings.rotate_pages === 180 ? "selected" : ""}>180° Flip</option>
            <option value="270" ${item.settings.rotate_pages === 270 ? "selected" : ""}>270° Counter-clockwise</option>
          </select>
        </div>
      </div>
    `;
  }

  // 6. Delimiters
  if (["csv", "tsv"].includes(targetFmt)) {
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">Delimiter Format</div>
        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">Separator</label>
          <select class="input-select setting-input" data-key="delimiter">
            <option value="comma" ${item.settings.delimiter === "comma" ? "selected" : ""}>Comma (,)</option>
            <option value="tab" ${item.settings.delimiter === "tab" ? "selected" : ""}>Tab (\\t)</option>
            <option value="semicolon" ${item.settings.delimiter === "semicolon" ? "selected" : ""}>Semicolon (;)</option>
          </select>
        </div>
      </div>
    `;
  }

  // Display completed page breakdown in sidebar if multi-file
  if (item.status === "completed" && item.outputFiles && item.outputFiles.length > 1) {
    html += `
      <div class="inspector-section">
        <div class="inspector-section-title">
          <span>Output Pages (${item.outputFiles.length})</span>
          <button class="btn btn-primary btn-xs" id="btn-sidebar-view-pages">
            Gallery
          </button>
        </div>
        <div style="display: flex; flex-direction: column; gap: var(--space-1-5); max-height: 220px; overflow-y: auto;">
          ${item.outputFiles.map((f, i) => {
            const fname = f.split(/[/\\\\]/).pop();
            return `
              <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 8px; background: var(--bg-surface-elevated); border-radius: var(--radius-sm); font-size: 11px; border: 1px solid var(--border-subtle);">
                <div style="display: flex; align-items: center; gap: var(--space-2); overflow: hidden;">
                  <span class="badge badge-primary" style="font-size: 10px; padding: 1px 4px;">P${i + 1}</span>
                  <span style="max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${fname}">
                    ${fname}
                  </span>
                </div>
                <div style="display: flex; gap: 4px;">
                  <a href="/api/jobs/${item.jobId}/download/${i + 1}" class="btn btn-secondary btn-xs" download="${fname}" title="Download Page ${i + 1}">
                    ${ICONS.download}
                  </a>
                  <a href="/api/jobs/${item.jobId}/preview/${i + 1}" target="_blank" class="btn btn-ghost btn-xs" title="Preview">
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

  panelBody.querySelectorAll("[data-set-quality]").forEach(btn => {
    btn.addEventListener("click", () => {
      const q = Number(btn.getAttribute("data-set-quality"));
      item.settings.quality = q;
      const rangeInput = panelBody.querySelector('[data-key="quality"]');
      if (rangeInput) rangeInput.value = q;
      const display = document.getElementById("val-quality");
      if (display) display.textContent = `${q}%`;

      panelBody.querySelectorAll("[data-set-quality]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
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

  window.hyperspacePulse?.(3.2);
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
      <div class="modal-container" style="max-width: 840px; width: 92%;">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: var(--space-2-5);">
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
                    <span style="width: 13px; height: 13px;">${ICONS.download}</span> Download
                  </a>
                  <a href="${f.preview_url}" target="_blank" class="btn btn-secondary btn-sm" title="View Fullscreen">
                    <span style="width: 13px; height: 13px;">↗</span>
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
