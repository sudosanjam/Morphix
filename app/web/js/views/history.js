/**
 * History Workspace View.
 */

import { api } from "../api.js";
import { ICONS, showToast, formatBytes } from "../ui.js";

export function initHistoryView() {
  const container = document.getElementById("view-history");
  if (!container) return;

  renderHistoryView(container);
  setupListeners(container);
}

function renderHistoryView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 1000px; margin: 0 auto; width: 100%;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h2>Conversion History</h2>
          <p style="font-size: var(--font-size-xs); color: var(--text-muted);">
            Local SQLite records of past conversions · Source files are never duplicated
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2);">
          <button id="hist-btn-refresh" class="btn btn-secondary btn-sm">
            <span style="width: 14px; height: 14px;">${ICONS.refresh}</span> Refresh
          </button>
          <button id="hist-btn-clear" class="btn btn-danger btn-sm">
            <span style="width: 14px; height: 14px;">${ICONS.trash}</span> Clear History
          </button>
        </div>
      </div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Source File</th>
              <th>Target Format</th>
              <th>Engine</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Output Size</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody id="hist-table-body">
            <tr>
              <td colspan="7" style="text-align: center; color: var(--text-muted); padding: var(--space-6);">
                Loading history...
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const refreshBtn = container.querySelector("#hist-btn-refresh");
  const clearBtn = container.querySelector("#hist-btn-clear");

  refreshBtn.addEventListener("click", loadHistoryData);
  clearBtn.addEventListener("click", async () => {
    if (confirm("Are you sure you want to clear your local conversion history?")) {
      await api.clearHistory();
      showToast("Conversion history cleared.", "info");
      loadHistoryData();
    }
  });

  loadHistoryData();
}

export async function loadHistoryData() {
  const tbody = document.getElementById("hist-table-body");
  if (!tbody) return;

  try {
    const entries = await api.getHistory(100);
    if (!entries || entries.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--text-muted); padding: var(--space-6);">
            No conversion history yet. Completed conversions will appear here.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = "";
    entries.forEach(item => {
      const tr = document.createElement("tr");
      const srcName = item.source_path.split(/[\\/]/).pop();
      const statusBadge = item.status === "completed"
        ? `<span class="badge badge-success">Completed</span>`
        : `<span class="badge badge-danger">Failed</span>`;

      const durStr = item.duration_seconds ? `${item.duration_seconds.toFixed(2)}s` : "--";
      const sizeStr = item.output_size_bytes ? formatBytes(item.output_size_bytes) : "--";

      let actionHtml = "";
      if (item.target_path) {
        actionHtml = `
          <button class="btn btn-secondary btn-sm hist-open-folder" data-path="${item.target_path}" title="Reveal in folder">
            <span style="width: 14px; height: 14px;">${ICONS.folder}</span>
          </button>
        `;
      }

      tr.innerHTML = `
        <td><strong title="${item.source_path}">${srcName}</strong></td>
        <td><span class="badge badge-primary">${item.target_format.toUpperCase()}</span></td>
        <td><span style="color: var(--text-muted); font-size: 12px;">${item.engine || '--'}</span></td>
        <td>${statusBadge}</td>
        <td><span style="font-family: var(--font-family-mono); font-size: 12px;">${durStr}</span></td>
        <td><span style="font-size: 12px;">${sizeStr}</span></td>
        <td style="text-align: right;">${actionHtml}</td>
      `;

      const folderBtn = tr.querySelector(".hist-open-folder");
      if (folderBtn) {
        folderBtn.addEventListener("click", () => {
          api.openFolder(folderBtn.getAttribute("data-path")).catch(err => {
            showToast(`Could not open folder: ${err.message}`, "error");
          });
        });
      }

      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}
