/**
 * Diagnostics Workspace View - Apple System Profiler Aesthetic.
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
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 1040px; margin: 0 auto; width: 100%;">
      <!-- Header -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h2>System Diagnostics & Hardware Engines</h2>
          <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
            Real-time inspection of local conversion runtimes, memory, sandbox permissions, and runtime logs
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2);">
          <button id="diag-btn-copy" class="btn btn-secondary btn-sm">
            <span style="width: 13px; height: 13px;">${ICONS.copy}</span> Copy Report
          </button>
          <button id="diag-btn-run" class="btn btn-primary btn-sm">
            <span style="width: 13px; height: 13px;">${ICONS.refresh}</span> Run Diagnostics
          </button>
        </div>
      </div>

      <!-- System Summary Cards Grid -->
      <div class="diag-grid">
        <div class="card">
          <div style="font-size: 11px; text-transform: uppercase; letter-spacing: var(--letter-spacing-wide); color: var(--text-muted); margin-bottom: 4px;">Host Environment</div>
          <strong id="diag-val-os" style="font-size: var(--font-size-md); color: var(--text-primary);">--</strong>
          <div id="diag-val-python" style="font-size: var(--font-size-xs); color: var(--text-secondary); margin-top: 4px;">--</div>
        </div>

        <div class="card">
          <div style="font-size: 11px; text-transform: uppercase; letter-spacing: var(--letter-spacing-wide); color: var(--text-muted); margin-bottom: 4px;">Local Storage</div>
          <strong id="diag-val-disk" style="font-size: var(--font-size-md); color: var(--text-primary);">--</strong>
          <div id="diag-val-perms" style="font-size: var(--font-size-xs); color: var(--color-success); margin-top: 4px; display: flex; align-items: center; gap: 4px;">
            <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--color-success); display: inline-block;"></span>
            Local Storage Writable
          </div>
        </div>

        <div class="card">
          <div style="font-size: 11px; text-transform: uppercase; letter-spacing: var(--letter-spacing-wide); color: var(--text-muted); margin-bottom: 4px;">Offline Routing Pipeline</div>
          <strong id="diag-val-routes" style="font-size: var(--font-size-md); color: var(--color-primary);">--</strong>
          <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 4px;">Zero cloud dependencies</div>
        </div>
      </div>

      <!-- Engine Detection Cards -->
      <div>
        <h3 style="margin-bottom: var(--space-3); font-size: var(--font-size-sm); color: var(--text-primary);">Detected Local Processing Engines</h3>
        <div class="diag-grid" id="diag-engines-grid">
          <!-- Engine Cards dynamically injected -->
        </div>
      </div>

      <!-- Log Stream -->
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-2);">
          <h3 style="font-size: var(--font-size-sm); color: var(--text-primary);">Active Server Logs</h3>
          <span class="badge badge-neutral" style="font-size: 10px;">Local Session</span>
        </div>
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
    document.getElementById("diag-val-disk").textContent = `${data.storage.disk_free_formatted} Available`;

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
        <div class="engine-path" title="${eng.path || 'Not detected'}">${eng.path || 'Built-in library'}</div>
        <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Version: ${eng.version || 'System Active'}</div>
      `;
      enginesGrid.appendChild(card);
    });

    // Logs
    const logBox = document.getElementById("diag-log-viewer");
    if (data.recent_logs && data.recent_logs.length > 0) {
      logBox.innerHTML = data.recent_logs.map(l => `<div style="padding: 1px 0;">${escapeHtml(l)}</div>`).join("");
    } else {
      logBox.innerHTML = `<div>No log entries found. All systems operating normally.</div>`;
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
