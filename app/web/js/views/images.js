/**
 * Dedicated Image Tools Workspace.
 */

import { api } from "../api.js";
import { ICONS, showToast, formatBytes } from "../ui.js";

let loadedImage = null; // { file, path, url, meta }

export function initImagesView() {
  const container = document.getElementById("view-images");
  if (!container) return;

  renderImagesView(container);
  setupListeners(container);
}

function renderImagesView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); height: 100%;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h2>Image Processing & Optimization</h2>
          <p style="font-size: var(--font-size-xs); color: var(--text-muted);">
            High-precision image resizing, format encoding, color adjustments, and metadata stripping
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2);">
          <button id="img-btn-upload" class="btn btn-secondary btn-sm">
            <span style="width: 14px; height: 14px;">${ICONS.plus}</span> Open Image
          </button>
          <input type="file" id="img-file-input" accept="image/*" style="display: none;" />
        </div>
      </div>

      <div class="image-tools-grid">
        <!-- Left: Image Preview Canvas -->
        <div class="image-preview-panel">
          <div class="image-canvas-container" id="img-canvas-box">
            <div id="img-empty-prompt" style="text-align: center; color: var(--text-muted);">
              <span style="width: 48px; height: 48px; display: inline-block; margin-bottom: var(--space-2);">${ICONS.image}</span>
              <p>No image loaded. Click "Open Image" or drop an image file here.</p>
            </div>
            <img id="img-preview-elem" style="display: none;" alt="Preview" />
          </div>
          <div class="image-meta-bar" id="img-meta-bar">
            <span>Dimensions: <strong id="img-stat-dim">--</strong></span>
            <span>Color Mode: <strong id="img-stat-mode">--</strong></span>
            <span>Size: <strong id="img-stat-size">--</strong></span>
          </div>
        </div>

        <!-- Right: Settings Panel -->
        <div class="card" style="display: flex; flex-direction: column; gap: var(--space-3); overflow-y: auto;">
          <h3 style="font-size: var(--font-size-sm); border-bottom: 1px solid var(--border-subtle); padding-bottom: var(--space-2);">
            Output Configuration
          </h3>

          <div class="form-group">
            <label class="form-label">Target Format</label>
            <select id="img-target-fmt" class="input-select">
              <option value="webp" selected>WebP (Modern & Compact)</option>
              <option value="png">PNG (Lossless High Fidelity)</option>
              <option value="jpg">JPEG (Photo Standard)</option>
              <option value="bmp">BMP (Uncompressed Bitmap)</option>
              <option value="tiff">TIFF (Print Standard)</option>
              <option value="ico">ICO (Windows Icon)</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">
              <span>Quality</span>
              <span class="slider-val" id="img-quality-val">85%</span>
            </label>
            <div class="slider-wrapper">
              <input type="range" id="img-quality-slider" class="range-slider" min="1" max="100" value="85" />
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2);">
            <div class="form-group">
              <label class="form-label">Width (px)</label>
              <input type="number" id="img-width-input" class="input-number" placeholder="Original" />
            </div>
            <div class="form-group">
              <label class="form-label">Height (px)</label>
              <input type="number" id="img-height-input" class="input-number" placeholder="Original" />
            </div>
          </div>

          <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center;">
            <label class="form-label" style="margin-bottom: 0;">Preserve Aspect Ratio</label>
            <label class="switch">
              <input type="checkbox" id="img-preserve-aspect" checked />
              <span class="switch-slider"></span>
            </label>
          </div>

          <div class="form-group">
            <label class="form-label">Rotate</label>
            <select id="img-rotate-sel" class="input-select">
              <option value="0">0° (None)</option>
              <option value="90">90° Clockwise</option>
              <option value="180">180° Half-turn</option>
              <option value="270">270° Counter-clockwise</option>
            </select>
          </div>

          <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center;">
            <label class="form-label" style="margin-bottom: 0;">Grayscale</label>
            <label class="switch">
              <input type="checkbox" id="img-grayscale-toggle" />
              <span class="switch-slider"></span>
            </label>
          </div>

          <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center;">
            <label class="form-label" style="margin-bottom: 0;">Strip EXIF / Metadata</label>
            <label class="switch">
              <input type="checkbox" id="img-strip-meta" checked />
              <span class="switch-slider"></span>
            </label>
          </div>

          <div style="margin-top: auto; padding-top: var(--space-3);">
            <button id="img-btn-process" class="btn btn-primary" style="width: 100%;" disabled>
              <span style="width: 16px; height: 16px;">${ICONS.play || ICONS.convert}</span>
              Process & Save Image
            </button>
            <div id="img-result-actions" style="display: none; margin-top: var(--space-2); gap: var(--space-2);">
              <a id="img-download-link" class="btn btn-secondary btn-sm" style="flex: 1;" download>Download</a>
              <button id="img-folder-btn" class="btn btn-secondary btn-sm" style="flex: 1;">Show Folder</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const uploadBtn = container.querySelector("#img-btn-upload");
  const fileInput = container.querySelector("#img-file-input");
  const canvasBox = container.querySelector("#img-canvas-box");
  const processBtn = container.querySelector("#img-btn-process");
  const qualitySlider = container.querySelector("#img-quality-slider");
  const qualityVal = container.querySelector("#img-quality-val");

  uploadBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      loadImageFile(e.target.files[0]);
    }
  });

  // Canvas drag & drop
  canvasBox.addEventListener("dragover", (e) => { e.preventDefault(); });
  canvasBox.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length > 0) {
      loadImageFile(e.dataTransfer.files[0]);
    }
  });

  qualitySlider.addEventListener("input", (e) => {
    qualityVal.textContent = e.target.value + "%";
  });

  processBtn.addEventListener("click", processImage);
}

async function loadImageFile(file) {
  showToast(`Loading ${file.name}...`, "info", 1500);
  try {
    const uploadRes = await api.uploadFile(file);
    const meta = uploadRes.metadata;
    const props = meta.properties || {};

    loadedImage = {
      file: file,
      path: uploadRes.path,
      url: URL.createObjectURL(file),
      meta: meta
    };

    const emptyPrompt = document.getElementById("img-empty-prompt");
    const previewImg = document.getElementById("img-preview-elem");
    const dimStat = document.getElementById("img-stat-dim");
    const modeStat = document.getElementById("img-stat-mode");
    const sizeStat = document.getElementById("img-stat-size");
    const processBtn = document.getElementById("img-btn-process");

    emptyPrompt.style.display = "none";
    previewImg.src = loadedImage.url;
    previewImg.style.display = "block";

    dimStat.textContent = `${props.width || '--'} × ${props.height || '--'} px`;
    modeStat.textContent = props.mode || "RGB";
    sizeStat.textContent = formatBytes(meta.size_bytes);

    processBtn.disabled = false;
    showToast(`Image loaded: ${props.width}×${props.height} px`, "success", 2000);
  } catch (err) {
    showToast(`Failed to inspect image: ${err.message}`, "error");
  }
}

async function processImage() {
  if (!loadedImage) return;

  const processBtn = document.getElementById("img-btn-process");
  const targetFmt = document.getElementById("img-target-fmt").value;
  const quality = Number(document.getElementById("img-quality-slider").value);
  const widthVal = document.getElementById("img-width-input").value;
  const heightVal = document.getElementById("img-height-input").value;
  const preserveAspect = document.getElementById("img-preserve-aspect").checked;
  const rotateVal = Number(document.getElementById("img-rotate-sel").value);
  const grayscale = document.getElementById("img-grayscale-toggle").checked;
  const stripMeta = document.getElementById("img-strip-meta").checked;

  const settings = {
    quality: quality,
    preserve_aspect: preserveAspect,
    rotate: rotateVal,
    grayscale: grayscale,
    strip_metadata: stripMeta
  };

  if (widthVal) settings.width = Number(widthVal);
  if (heightVal) settings.height = Number(heightVal);

  processBtn.disabled = true;
  processBtn.textContent = "Processing...";

  try {
    const job = await api.convert({
      source_path: loadedImage.path,
      target_format: targetFmt,
      settings: settings,
      overwrite_policy: "rename"
    });

    // Poll until finished
    let finishedJob = null;
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 600));
      const status = await api.getJob(job.id);
      if (status.status === "completed") {
        finishedJob = status;
        break;
      } else if (status.status === "failed") {
        throw new Error(status.error_message || "Conversion failed");
      }
    }

    if (finishedJob) {
      showToast("Image processed successfully!", "success");
      const resultActions = document.getElementById("img-result-actions");
      const downloadLink = document.getElementById("img-download-link");
      const folderBtn = document.getElementById("img-folder-btn");

      resultActions.style.display = "flex";
      downloadLink.href = `/api/jobs/${finishedJob.id}/download`;
      downloadLink.download = `${loadedImage.file.name.split('.')[0]}_converted.${targetFmt}`;

      folderBtn.onclick = () => {
        api.openFolder(finishedJob.target_path);
      };
    }
  } catch (err) {
    showToast(`Processing failed: ${err.message}`, "error");
  } finally {
    processBtn.disabled = false;
    processBtn.innerHTML = `<span style="width: 16px; height: 16px;">${ICONS.play || ICONS.convert}</span> Process & Save Image`;
  }
}
