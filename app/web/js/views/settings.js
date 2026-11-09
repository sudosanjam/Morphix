/**
 * Settings Workspace View - Apple macOS Settings Style.
 * Includes Theme Palette Selector, Dynamic Background Controls & Concurrency Preferences.
 */

import { api } from "../api.js";
import { state } from "../state.js";
import { ICONS, showToast } from "../ui.js";
import { toggleHyperspace, hyperspacePulse } from "../components/hyperspace.js";

export function initSettingsView() {
  const container = document.getElementById("view-settings");
  if (!container) return;

  renderSettingsView(container);
  setupListeners(container);
}

function renderSettingsView(container) {
  const isHyperspaceOn = localStorage.getItem("morphix_hyperspace") !== "false";

  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 840px; margin: 0 auto; width: 100%;">
      <!-- Header -->
      <div>
        <h2>Preferences & Configuration</h2>
        <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
          Configure color palettes, dynamic ambient background, storage paths, and local concurrency
        </p>
      </div>

      <!-- Theme & Appearance Card -->
      <div class="card">
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <span style="width: 15px; height: 15px; color: var(--color-primary);">${ICONS.sun}</span>
            <h3 class="card-title">Color Palette & Atmosphere</h3>
          </div>
          <span class="badge badge-primary" style="font-size: 10px;">Dark Pastel Suite</span>
        </div>

        <!-- Palette Swatches Grid -->
        <div class="form-group" style="margin-bottom: var(--space-4);">
          <label class="form-label">
            <span>Theme Color Palette</span>
            <span style="font-size: 11px; color: var(--text-muted);">Select your preferred dark pastel aesthetic</span>
          </label>
          <div class="palette-swatches-grid">
            <!-- 1. Obsidian -->
            <div class="palette-swatch-card ${state.palette === 'obsidian' ? 'active' : ''}" data-palette-val="obsidian">
              <div class="palette-swatch-preview" style="background: #0e0f15; border: 1px solid rgba(255,255,255,0.08);">
                <div class="palette-swatch-circle" style="background: #89b4fa;"></div>
                <div class="palette-swatch-circle" style="background: #cba6f7;"></div>
              </div>
              <div class="palette-swatch-title">Obsidian</div>
              <div class="palette-swatch-sub">Slate Blue</div>
            </div>

            <!-- 2. Coffee -->
            <div class="palette-swatch-card ${state.palette === 'coffee' ? 'active' : ''}" data-palette-val="coffee">
              <div class="palette-swatch-preview" style="background: #120e0c; border: 1px solid rgba(212,163,115,0.18);">
                <div class="palette-swatch-circle" style="background: #d4a373;"></div>
                <div class="palette-swatch-circle" style="background: #e0a96d;"></div>
              </div>
              <div class="palette-swatch-title">Coffee</div>
              <div class="palette-swatch-sub">Mocha Espresso</div>
            </div>

            <!-- 3. Ruby -->
            <div class="palette-swatch-card ${state.palette === 'ruby' ? 'active' : ''}" data-palette-val="ruby">
              <div class="palette-swatch-preview" style="background: #13080b; border: 1px solid rgba(243,139,168,0.18);">
                <div class="palette-swatch-circle" style="background: #f38ba8;"></div>
                <div class="palette-swatch-circle" style="background: #f2cdcd;"></div>
              </div>
              <div class="palette-swatch-title">Ruby</div>
              <div class="palette-swatch-sub">Crimson Rose</div>
            </div>

            <!-- 4. Sapphire -->
            <div class="palette-swatch-card ${state.palette === 'sapphire' ? 'active' : ''}" data-palette-val="sapphire">
              <div class="palette-swatch-preview" style="background: #080d16; border: 1px solid rgba(56,189,248,0.18);">
                <div class="palette-swatch-circle" style="background: #38bdf8;"></div>
                <div class="palette-swatch-circle" style="background: #818cf8;"></div>
              </div>
              <div class="palette-swatch-title">Sapphire</div>
              <div class="palette-swatch-sub">Ocean Azure</div>
            </div>

            <!-- 5. Emerald -->
            <div class="palette-swatch-card ${state.palette === 'emerald' ? 'active' : ''}" data-palette-val="emerald">
              <div class="palette-swatch-preview" style="background: #07120d; border: 1px solid rgba(94,234,212,0.18);">
                <div class="palette-swatch-circle" style="background: #5eead4;"></div>
                <div class="palette-swatch-circle" style="background: #a6e3a1;"></div>
              </div>
              <div class="palette-swatch-title">Emerald</div>
              <div class="palette-swatch-sub">Pine Mint</div>
            </div>

            <!-- 6. Amethyst -->
            <div class="palette-swatch-card ${state.palette === 'amethyst' ? 'active' : ''}" data-palette-val="amethyst">
              <div class="palette-swatch-preview" style="background: #0e0817; border: 1px solid rgba(192,132,252,0.18);">
                <div class="palette-swatch-circle" style="background: #c084fc;"></div>
                <div class="palette-swatch-circle" style="background: #f5c2e7;"></div>
              </div>
              <div class="palette-swatch-title">Amethyst</div>
              <div class="palette-swatch-sub">Cosmic Violet</div>
            </div>
          </div>
        </div>

        <!-- Hyperspace Dynamic Background Switch -->
        <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center; margin-bottom: var(--space-3); padding: var(--space-3) 0; border-top: 1px solid var(--border-subtle); border-bottom: 1px solid var(--border-subtle);">
          <div>
            <strong style="font-size: var(--font-size-sm); color: var(--text-primary);">✦ Hyperspace Ambient Background</strong>
            <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
              Ultra-subtle cosmic stardust drift that harmonizes with your active palette (zero distraction)
            </p>
          </div>
          <label class="switch">
            <input type="checkbox" id="set-hyperspace-toggle" ${isHyperspaceOn ? "checked" : ""} />
            <span class="switch-slider"></span>
          </label>
        </div>

        <!-- Dark / Light Mode Switch -->
        <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center; margin-bottom: var(--space-3); padding-bottom: var(--space-3); border-bottom: 1px solid var(--border-subtle);">
          <div>
            <strong style="font-size: var(--font-size-sm); color: var(--text-primary);">Dark Interface Mode</strong>
            <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
              Toggle between deep dark and warm daylight latte tones
            </p>
          </div>
          <label class="switch">
            <input type="checkbox" id="set-theme-toggle" ${state.theme === "dark" ? "checked" : ""} />
            <span class="switch-slider"></span>
          </label>
        </div>

        <!-- Default Output Directory -->
        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">Default Converted Output Folder</label>
          <input type="text" id="set-output-dir" class="input-text" placeholder="Leave blank to save alongside original source file" />
          <span class="form-hint">When left empty, outputs are placed directly in the source file's directory.</span>
        </div>
      </div>

      <!-- Conversion & Concurrency Card -->
      <div class="card">
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <span style="width: 15px; height: 15px; color: var(--color-mocha);">${ICONS.convert}</span>
            <h3 class="card-title">Processing & Concurrency</h3>
          </div>
          <span class="badge badge-mocha" style="font-size: 10px;">High Performance</span>
        </div>

        <div class="form-group" style="margin-bottom: var(--space-4);">
          <label class="form-label">Default Collision Policy</label>
          <select id="set-overwrite-policy" class="input-select">
            <option value="rename" selected>Safe Auto-Rename (appends _1, _2 without overwriting)</option>
            <option value="overwrite">Overwrite Existing File</option>
          </select>
        </div>

        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">
            <span>Maximum Background Worker Threads</span>
            <span class="slider-val" id="set-workers-val">4</span>
          </label>
          <div class="slider-wrapper">
            <input type="range" id="set-workers-slider" class="range-slider" min="1" max="16" value="4" />
          </div>
          <span class="form-hint">Controls how many background conversion worker processes run simultaneously.</span>
        </div>
      </div>

      <!-- Storage & Maintenance Card -->
      <div class="card">
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <span style="width: 15px; height: 15px; color: var(--color-caramel);">${ICONS.trash}</span>
            <h3 class="card-title">Storage & Maintenance</h3>
          </div>
          <span class="badge badge-caramel" style="font-size: 10px;">Zero Cloud</span>
        </div>

        <div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: var(--space-3); border-bottom: 1px solid var(--border-subtle);">
          <div>
            <strong style="font-size: var(--font-size-sm); color: var(--text-primary);">Clean Temporary Upload Cache</strong>
            <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
              Purges staged files, scratch directories, and temporary intermediate assets
            </p>
          </div>
          <button id="set-btn-clean-temp" class="btn btn-secondary btn-sm">
            <span style="width: 13px; height: 13px;">${ICONS.trash}</span> Clean Cache
          </button>
        </div>

        <div style="display: flex; align-items: center; justify-content: space-between; padding-top: var(--space-3);">
          <div>
            <strong style="font-size: var(--font-size-sm); color: var(--text-primary);">Clear Conversion History</strong>
            <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
              Deletes past conversion log records from your local SQLite database
            </p>
          </div>
          <button id="set-btn-clear-hist" class="btn btn-danger btn-sm">
            Clear Logs
          </button>
        </div>
      </div>

      <div style="display: flex; justify-content: flex-end; margin-top: var(--space-2);">
        <button id="set-btn-save" class="btn btn-primary btn-lg" style="min-width: 160px;">
          Save Preferences
        </button>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const themeToggle = container.querySelector("#set-theme-toggle");
  const hyperspaceToggle = container.querySelector("#set-hyperspace-toggle");
  const workersSlider = container.querySelector("#set-workers-slider");
  const workersVal = container.querySelector("#set-workers-val");
  const cleanTempBtn = container.querySelector("#set-btn-clean-temp");
  const clearHistBtn = container.querySelector("#set-btn-clear-hist");
  const saveBtn = container.querySelector("#set-btn-save");

  // Palette swatch selection
  container.querySelectorAll(".palette-swatch-card").forEach(card => {
    card.addEventListener("click", () => {
      const pal = card.getAttribute("data-palette-val");
      container.querySelectorAll(".palette-swatch-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");

      state.setPalette(pal);
      hyperspacePulse(2.4);

      // Sync topbar select
      const topSelect = document.getElementById("theme-palette-select");
      if (topSelect) topSelect.value = pal;

      showToast(`Applied ${card.querySelector(".palette-swatch-title").textContent} theme`, "info", 1800);
    });
  });

  if (hyperspaceToggle) {
    hyperspaceToggle.addEventListener("change", (e) => {
      const enabled = toggleHyperspace(e.target.checked);
      showToast(enabled ? "✦ Dynamic Background Enabled" : "Dynamic Background Disabled", "info", 1800);
    });
  }

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
