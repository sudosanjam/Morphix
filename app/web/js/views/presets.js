/**
 * Presets Workspace View - Apple Pro Preset Library.
 */

import { api } from "../api.js";
import { ICONS, showToast, openModal, closeModal } from "../ui.js";

export function initPresetsView() {
  const container = document.getElementById("view-presets");
  if (!container) return;

  renderPresetsView(container);
  setupListeners(container);
}

function renderPresetsView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 1040px; margin: 0 auto; width: 100%;">
      <!-- Header -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h2>Preset Templates</h2>
          <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
            Pre-configured conversion recipes for one-click re-use across the app and CLI
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2);">
          <button id="preset-btn-create" class="btn btn-primary btn-sm">
            <span style="width: 13px; height: 13px;">${ICONS.plus}</span> New Custom Preset
          </button>
        </div>
      </div>

      <div class="presets-grid" id="presets-grid-container">
        <!-- Preset Cards -->
      </div>
    </div>

    <!-- Create Preset Modal -->
    <div id="modal-create-preset" class="modal-backdrop">
      <div class="modal-container">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <span style="width: 16px; height: 16px; color: var(--color-primary);">${ICONS.preset}</span>
            <h3 class="modal-title">Create Custom Preset</h3>
          </div>
          <button class="btn-icon modal-close-btn">
            <span style="width: 16px; height: 16px;">${ICONS.close}</span>
          </button>
        </div>
        <div class="modal-body" style="display: flex; flex-direction: column; gap: var(--space-3-5);">
          <div class="form-group">
            <label class="form-label">Preset Name</label>
            <input type="text" id="preset-new-name" class="input-text" placeholder="e.g. Web-Optimized Avatars" />
          </div>
          <div class="form-group">
            <label class="form-label">Media Category</label>
            <select id="preset-new-cat" class="input-select">
              <option value="image">Image (WebP, PNG, JPG)</option>
              <option value="audio">Audio (MP3, WAV, Opus)</option>
              <option value="document">Document (PDF, Word)</option>
              <option value="spreadsheet">Spreadsheet (XLSX, CSV)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Target Format</label>
            <input type="text" id="preset-new-fmt" class="input-text" placeholder="e.g. webp, mp3, pdf" />
          </div>
          <div class="form-group">
            <label class="form-label">Description / Intended Use</label>
            <input type="text" id="preset-new-desc" class="input-text" placeholder="Brief summary of resolution, bitrate, or quality" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary modal-close-btn">Cancel</button>
          <button id="preset-save-btn" class="btn btn-primary">Save Preset</button>
        </div>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const createBtn = container.querySelector("#preset-btn-create");
  const saveBtn = container.querySelector("#preset-save-btn");
  const closeBtns = container.querySelectorAll(".modal-close-btn");

  createBtn.addEventListener("click", () => openModal("modal-create-preset"));
  closeBtns.forEach(btn => btn.addEventListener("click", () => closeModal("modal-create-preset")));

  saveBtn.addEventListener("click", async () => {
    const name = document.getElementById("preset-new-name").value.trim();
    const cat = document.getElementById("preset-new-cat").value;
    const fmt = document.getElementById("preset-new-fmt").value.trim();
    const desc = document.getElementById("preset-new-desc").value.trim();

    if (!name || !fmt) {
      showToast("Please provide preset name and target format.", "error");
      return;
    }

    try {
      await api.createPreset({
        name: name,
        category: cat,
        target_format: fmt,
        description: desc,
        settings: {}
      });
      showToast(`Created preset "${name}"`, "success");
      closeModal("modal-create-preset");
      loadPresetsData();
    } catch (err) {
      showToast(`Failed to save preset: ${err.message}`, "error");
    }
  });

  loadPresetsData();
}

export async function loadPresetsData() {
  const grid = document.getElementById("presets-grid-container");
  if (!grid) return;

  try {
    const presetList = await api.getPresets();
    grid.innerHTML = "";

    presetList.forEach(p => {
      const card = document.createElement("div");
      card.className = "preset-card";

      const badgeType = p.is_builtin
        ? `<span class="badge badge-neutral">Built-in</span>`
        : `<span class="badge badge-primary">Custom</span>`;

      card.innerHTML = `
        <div>
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-2);">
            <strong style="font-size: var(--font-size-md); color: var(--text-primary);">${p.name}</strong>
            ${badgeType}
          </div>
          <p style="font-size: var(--font-size-xs); color: var(--text-secondary); margin-bottom: var(--space-3); line-height: 1.45;">
            ${p.description || 'Pre-configured workflow setting'}
          </p>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid var(--border-subtle); padding-top: var(--space-3);">
          <span class="badge badge-neutral">${p.target_format.toUpperCase()}</span>
          <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-primary); font-weight: 600;">
            ${p.category || 'general'}
          </span>
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load presets:", err);
  }
}
