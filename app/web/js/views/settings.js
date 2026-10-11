/**
 * Settings Workspace View.
 */

import { api } from "../api.js";
import { state } from "../state.js";
import { ICONS, showToast } from "../ui.js";

export function initSettingsView() {
  const container = document.getElementById("view-settings");
  if (!container) return;

  renderSettingsView(container);
  setupListeners(container);
}

function renderSettingsView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 800px; margin: 0 auto; width: 100%;">
      <div>
        <h2>Application Settings</h2>
        <p style="font-size: var(--font-size-xs); color: var(--text-muted);">
          Configure interface appearance, storage paths, default conversion policies, and performance tuning
        </p>
      </div>

      <!-- General Settings Card -->
      <div class="card">
        <h3 class="card-title" style="margin-bottom: var(--space-4);">General & Appearance</h3>

        <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center; margin-bottom: var(--space-4);">
          <div>
            <strong style="font-size: var(--font-size-sm);">Dark Interface Theme</strong>
            <p style="font-size: var(--font-size-xs); color: var(--text-muted);">Switch between sleek dark mode and light theme</p>
          </div>
          <label class="switch">
            <input type="checkbox" id="set-theme-toggle" ${state.theme === "dark" ? "checked" : ""} />
            <span class="switch-slider"></span>
          </label>
        </div>

        <div class="form-group">
          <label class="form-label">Default Output Directory</label>
          <input type="text" id="set-output-dir" class="input-text" placeholder="Leave blank to save alongside source files" />
          <span class="form-hint">Converted files will be written to this folder if specified.</span>
        </div>
      </div>

      <!-- Conversion & Performance Card -->
      <div class="card">
        <h3 class="card-title" style="margin-bottom: var(--space-4);">Conversion & Concurrency</h3>

        <div class="form-group">
          <label class="form-label">Default Collision Policy</label>
          <select id="set-overwrite-policy" class="input-select">
            <option value="rename" selected>Safe Auto-Rename (appends _1, _2 without overwriting)</option>
            <option value="overwrite">Overwrite Existing File</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">
            <span>Maximum Concurrent Worker Threads</span>
            <span class="slider-val" id="set-workers-val">4</span>
          </label>
          <div class="slider-wrapper">
            <input type="range" id="set-workers-slider" class="range-slider" min="1" max="16" value="4" />
          </div>
          <span class="form-hint">Controls how many background conversion processes run simultaneously.</span>
        </div>
      </div>

      <!-- Maintenance & Storage Card -->
      <div class="card">
        <h3 class="card-title" style="margin-bottom: var(--space-4);">Storage & Maintenance</h3>

        <div style="display: flex; align-items: center; justify-content: space-between; padding: var(--space-3) 0; border-bottom: 1px solid var(--border-subtle);">
          <div>
            <strong style="font-size: var(--font-size-sm);">Clean Temporary Conversion Files</strong>
            <p style="font-size: var(--font-size-xs); color: var(--text-muted);">Purges scratch files and temporary uploads from local disk</p>
          </div>
          <button id="set-btn-clean-temp" class="btn btn-secondary btn-sm">
            <span style="width: 14px; height: 14px;">${ICONS.trash}</span> Clean Temp Files
          </button>
        </div>

        <div style="display: flex; align-items: center; justify-content: space-between; padding-top: var(--space-3);">
          <div>
            <strong style="font-size: var(--font-size-sm);">Reset Conversion History</strong>
            <p style="font-size: var(--font-size-xs); color: var(--text-muted);">Permanently deletes all logged conversion records</p>
          </div>
          <button id="set-btn-clear-hist" class="btn btn-danger btn-sm">
            Clear History
          </button>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; margin-top: var(--space-2);">
        <button id="set-btn-save" class="btn btn-primary btn-lg">
          Save Settings
        </button>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const themeToggle = container.querySelector("#set-theme-toggle");
  const workersSlider = container.querySelector("#set-workers-slider");
  const workersVal = container.querySelector("#set-workers-val");
  const cleanTempBtn = container.querySelector("#set-btn-clean-temp");
  const clearHistBtn = container.querySelector("#set-btn-clear-hist");
  const saveBtn = container.querySelector("#set-btn-save");

  themeToggle.addEventListener("change", (e) => {
    state.setTheme(e.target.checked ? "dark" : "light");
  });

  workersSlider.addEventListener("input", (e) => {
    workersVal.textContent = e.target.value;
  });

  cleanTempBtn.addEventListener("click", async () => {
    const res = await api.cleanTemp();
    showToast(`Cleaned ${res.cleaned_files_count} temporary files.`, "success");
  });

  clearHistBtn.addEventListener("click", async () => {
    if (confirm("Are you sure you want to clear your local history?")) {
      await api.clearHistory();
      showToast("Conversion history cleared.", "info");
    }
  });

  saveBtn.addEventListener("click", async () => {
    const outputDir = document.getElementById("set-output-dir").value.trim() || null;
    const overwrite = document.getElementById("set-overwrite-policy").value;
    const maxWorkers = Number(document.getElementById("set-workers-slider").value);

    try {
      await api.updateSettings({
        default_output_dir: outputDir,
        overwrite_policy: overwrite,
        max_workers: maxWorkers,
        theme: state.theme
      });
      showToast("Settings saved successfully.", "success");
    } catch (err) {
      showToast(`Failed to save settings: ${err.message}`, "error");
    }
  });

  loadSettingsData();
}

async function loadSettingsData() {
  try {
    const s = await api.getSettings();
    const outDirInput = document.getElementById("set-output-dir");
    const overwriteSel = document.getElementById("set-overwrite-policy");
    const workersSlider = document.getElementById("set-workers-slider");
    const workersVal = document.getElementById("set-workers-val");

    if (outDirInput && s.default_output_dir) outDirInput.value = s.default_output_dir;
    if (overwriteSel && s.overwrite_policy) overwriteSel.value = s.overwrite_policy;
    if (workersSlider && s.max_workers) {
      workersSlider.value = s.max_workers;
      workersVal.textContent = s.max_workers;
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}
