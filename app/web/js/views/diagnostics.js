/**
 * Diagnostics Workspace View.
 */

import { api } from "../api.js";
import { ICONS, showToast } from "../ui.js";

let lastDiagData = null;

export function initDiagnosticsView() {
  const container = document.getElementById("view-diagnostics");
  if (!container) return;

  renderDiagnosticsView(container);
  setupListeners(container);
}

function renderDiagnosticsView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 1000px; margin: 0 auto; width: 100%;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h2>System Diagnostics & Engine Status</h2>
          <p style="font-size: var(--font-size-xs); color: var(--text-muted);">
            Real-time inspection of local conversion runtimes, disk quotas, system permissions, and logs
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2);">
          <button id="diag-btn-copy" class="btn btn-secondary btn-sm">
            <span style="width: 14px; height: 14px;">${ICONS.copy}</span> Copy Report
          </button>
          <button id="diag-btn-run" class="btn btn-primary btn-sm">
            <span style="width: 14px; height: 14px;">${ICONS.refresh}</span> Run Diagnostics
          </button>
        </div>
      </div>

      <!-- System Summary Cards Grid -->
      <div class="diag-grid">
        <div class="card">
          <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: 4px;">Host Environment</div>
          <strong id="diag-val-os" style="font-size: var(--font-size-md);">--</strong>
          <div id="diag-val-python" style="font-size: var(--font-size-xs); color: var(--text-secondary); margin-top: 4px;">--</div>
        </div>

        <div class="card">
          <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: 4px;">Local Storage</div>
          <strong id="diag-val-disk" style="font-size: var(--font-size-md);">--</strong>
          <div id="diag-val-perms" style="font-size: var(--font-size-xs); color: var(--color-success); margin-top: 4px;">Storage Writable</div>
        </div>

        <div class="card">
          <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: 4px;">Conversion Pipeline</div>
          <strong id="diag-val-routes" style="font-size: var(--font-size-md);">--</strong>
          <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 4px;">Zero cloud dependencies</div>
        </div>
      </div>

      <!-- Engine Detection Cards -->
      <div>
        <h3 style="margin-bottom: var(--space-3); font-size: var(--font-size-sm);">Detected Engines & Runtimes</h3>
        <div class="diag-grid" id="diag-engines-grid">
          <!-- Engine Cards -->
        </div>
      </div>

      <!-- Log Stream -->
      <div>
        <h3 style="margin-bottom: var(--space-2); font-size: var(--font-size-sm);">Recent Local Logs</h3>
        <div class="log-stream-viewer" id="diag-log-viewer">
          Loading logs...
        </div>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const runBtn = container.querySelector("#diag-btn-run");
  const copyBtn = container.querySelector("#diag-btn-copy");

  runBtn.addEventListener("click", loadDiagnosticsData);
  copyBtn.addEventListener("click", copyReport);

  loadDiagnosticsData();
}

export async function loadDiagnosticsData() {
  try {
    const data = await api.getDiagnostics();
    lastDiagData = data;

    // Host
    document.getElementById("diag-val-os").textContent = `${data.system.os} (${data.system.architecture})`;
    document.getElementById("diag-val-python").textContent = `Python ${data.system.python_version} · ${data.system.cpu_count} CPU cores`;

    // Storage
    document.getElementById("diag-val-disk").textContent = `${data.storage.disk_free_formatted} Free`;

    // Routes
    document.getElementById("diag-val-routes").textContent = `${data.capabilities.active_routes} Active Routes`;

    // Engine cards
    const enginesGrid = document.getElementById("diag-engines-grid");
    enginesGrid.innerHTML = "";

    data.capabilities.engines.forEach(eng => {
      const card = document.createElement("div");
      card.className = "engine-card";

      const badge = eng.available
        ? `<span class="badge badge-success">Available</span>`
        : `<span class="badge badge-warning">Optional (Not installed)</span>`;

      card.innerHTML = `
        <div class="engine-card-header">
          <span class="engine-name">${eng.display_name}</span>
          ${badge}
        </div>
        <div class="engine-path" title="${eng.path || 'Not detected'}">${eng.path || 'Not detected'}</div>
        <div style="font-size: 11px; color: var(--text-muted);">Version: ${eng.version || 'N/A'}</div>
      `;
      enginesGrid.appendChild(card);
    });

    // Logs
    const logBox = document.getElementById("diag-log-viewer");
    if (data.recent_logs && data.recent_logs.length > 0) {
      logBox.innerHTML = data.recent_logs.map(l => `<div>${escapeHtml(l)}</div>`).join("");
    } else {
      logBox.innerHTML = `<div>No log entries found. All systems normal.</div>`;
    }

    showToast("Diagnostics updated.", "info", 1500);
  } catch (err) {
    console.error("Diagnostics load error:", err);
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function copyReport() {
  if (!lastDiagData) return;
  const report = JSON.stringify(lastDiagData, null, 2);
  navigator.clipboard.writeText(report).then(() => {
    showToast("Diagnostic report copied to clipboard!", "success");
  }).catch(() => {
    showToast("Failed to copy report to clipboard.", "error");
  });
}
