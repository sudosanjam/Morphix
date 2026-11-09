/**
 * Dedicated Image Tools Workspace - Apple Pro Refined Experience.
 */

import { api } from "../api.js";
import { ICONS, showToast, formatBytes } from "../ui.js";

let loadedImage = null; // { file, path, url, meta }
let zoomLevel = 1.0;

export function initImagesView() {
  const container = document.getElementById("view-images");
  if (!container) return;

  window.morphixImagesDrop = (files) => {
    if (files.length === 1) {
      loadImageFile(files[0]);
    } else if (files.length > 1) {
      handleMultiImagePdf(files);
    }
  };

  renderImagesView(container);
  setupListeners(container);
}

function renderImagesView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); height: 100%;">
      <!-- Header -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h2>Image Processing & Optimization</h2>
          <p style="font-size: var(--font-size-xs); color: var(--text-muted); margin-top: 2px;">
            High-precision resampling, format transcoding, color transforms, and metadata stripping
          </p>
        </div>
        <div style="display: flex; gap: var(--space-2);">
          <button id="img-btn-multi-pdf" class="btn btn-mocha btn-sm" title="Combine multiple image files into a single multi-page PDF">
            <span style="width: 13px; height: 13px;">${ICONS.document}</span> Combine Images to PDF
          </button>
          <button id="img-btn-upload" class="btn btn-primary btn-sm">
            <span style="width: 13px; height: 13px;">${ICONS.plus}</span> Open Image
          </button>
          <input type="file" id="img-file-input" accept="image/*" style="display: none;" />
          <input type="file" id="img-multi-pdf-input" accept="image/*" multiple style="display: none;" />
        </div>
      </div>

      <div class="image-tools-grid">
        <!-- Left: Image Preview Canvas -->
        <div class="image-preview-panel">
          <div class="image-canvas-container" id="img-canvas-box">
            <div id="img-empty-prompt" style="text-align: center; color: var(--text-muted);">
              <span style="width: 44px; height: 44px; display: inline-block; margin-bottom: var(--space-2); color: var(--color-primary);">${ICONS.image}</span>
              <p style="font-size: var(--font-size-sm); font-weight: 500; color: var(--text-secondary);">No image loaded</p>
              <p style="font-size: var(--font-size-xs); margin-top: 4px;">Click "Open Image" or drop an image file directly onto this canvas.</p>
            </div>
            <img id="img-preview-elem" style="display: none; max-width: 100%; max-height: 100%; object-fit: contain; transform: scale(1);" alt="Preview" />
          </div>

          <div class="image-meta-bar" id="img-meta-bar">
            <span>Dimensions: <strong id="img-stat-dim">--</strong></span>
            <span>Color Space: <strong id="img-stat-mode">--</strong></span>
            <span>File Size: <strong id="img-stat-size">--</strong></span>
          </div>
        </div>

        <!-- Right: Settings Panel -->
        <div class="card" style="display: flex; flex-direction: column; gap: var(--space-3); overflow-y: auto;">
          <div class="card-header" style="margin-bottom: 0;">
            <div style="display: flex; align-items: center; gap: var(--space-2);">
              <span style="width: 15px; height: 15px; color: var(--color-primary);">${ICONS.sliders}</span>
              <h3 class="card-title">Image Options</h3>
            </div>
            <span class="badge badge-primary" style="font-size: 10px;">Pillow Engine</span>
          </div>

          <!-- Quick Presets -->
          <div class="form-group" style="margin-bottom: var(--space-2);">
            <label class="form-label">
              <span>Quick Presets</span>
            </label>
            <div class="quality-presets-wrap" style="flex-wrap: wrap;">
              <button type="button" class="quality-preset-btn active" id="preset-web">WebP 80%</button>
              <button type="button" class="quality-preset-btn" id="preset-lossless">PNG Lossless</button>
              <button type="button" class="quality-preset-btn" id="preset-photo">Photo JPG</button>
              <button type="button" class="quality-preset-btn" id="preset-pdf">PDF Doc</button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Target Format</label>
            <select id="img-target-fmt" class="input-select">
              <option value="webp" selected>WebP (Modern, Compact, Fast)</option>
              <option value="png">PNG (Lossless High Fidelity)</option>
              <option value="jpg">JPEG (Photo Standard)</option>
              <option value="pdf">PDF (Portable Document Format)</option>
              <option value="bmp">BMP (Uncompressed Bitmap)</option>
              <option value="tiff">TIFF (Print Standard)</option>
              <option value="ico">ICO (Windows Icon)</option>
            </select>
          </div>

          <div class="form-group" id="img-dpi-group" style="display: none;">
            <label class="form-label">PDF Resolution (DPI)</label>
            <select id="img-dpi-sel" class="input-select">
              <option value="72">72 DPI (Standard Web / Fast)</option>
              <option value="96">96 DPI (Screen)</option>
              <option value="150" selected>150 DPI (Crisp / Recommended)</option>
              <option value="200">200 DPI (High Clarity)</option>
              <option value="300">300 DPI (Print Quality)</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">
              <span>Quality Compression</span>
              <span class="slider-val" id="img-quality-val">85%</span>
            </label>
            <div class="slider-wrapper">
              <input type="range" id="img-quality-slider" class="range-slider" min="1" max="100" value="85" />
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2);">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label">Width (px)</label>
              <input type="number" id="img-width-input" class="input-number" placeholder="Original" />
            </div>
            <div class="form-group" style="margin-bottom: 0;">
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
            <label class="form-label">Rotate Orientation</label>
            <select id="img-rotate-sel" class="input-select">
              <option value="0">0° (No rotation)</option>
              <option value="90">90° Clockwise</option>
              <option value="180">180° Half-turn</option>
              <option value="270">270° Counter-clockwise</option>
            </select>
          </div>

          <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center;">
            <label class="form-label" style="margin-bottom: 0;">Grayscale Monochrome</label>
            <label class="switch">
              <input type="checkbox" id="img-grayscale-toggle" />
              <span class="switch-slider"></span>
            </label>
          </div>

          <div class="form-group" style="flex-direction: row; justify-content: space-between; align-items: center;">
            <div>
              <label class="form-label" style="margin-bottom: 0;">Strip EXIF / Privacy</label>
              <span class="form-hint">Removes camera, location, date tags</span>
            </div>
            <label class="switch">
              <input type="checkbox" id="img-strip-meta" checked />
              <span class="switch-slider"></span>
            </label>
          </div>

          <div style="margin-top: auto; padding-top: var(--space-3); border-top: 1px solid var(--border-subtle);">
            <button id="img-btn-process" class="btn btn-primary btn-lg" style="width: 100%;" disabled>
              <span style="width: 16px; height: 16px;">${ICONS.play}</span>
              Process & Save Image
            </button>
            <div id="img-result-actions" style="display: none; margin-top: var(--space-2); gap: var(--space-2);">
              <a id="img-download-link" class="btn btn-secondary btn-sm" style="flex: 1;" download>
                <span style="width: 13px; height: 13px;">${ICONS.download}</span> Download
              </a>
              <button id="img-folder-btn" class="btn btn-secondary btn-sm" style="flex: 1;">
                <span style="width: 13px; height: 13px;">${ICONS.folder}</span> Show Folder
              </button>
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

  const multiPdfBtn = container.querySelector("#img-btn-multi-pdf");
  const multiPdfInput = container.querySelector("#img-multi-pdf-input");
  const targetFmtSel = container.querySelector("#img-target-fmt");
  const dpiGroup = container.querySelector("#img-dpi-group");

  // Presets
  const presetWeb = container.querySelector("#preset-web");
  const presetLossless = container.querySelector("#preset-lossless");
  const presetPhoto = container.querySelector("#preset-photo");
  const presetPdf = container.querySelector("#preset-pdf");

  function setActivePreset(targetBtn) {
    [presetWeb, presetLossless, presetPhoto, presetPdf].forEach(b => b.classList.remove("active"));
    if (targetBtn) targetBtn.classList.add("active");
  }

  if (presetWeb) {
    presetWeb.addEventListener("click", () => {
      targetFmtSel.value = "webp";
      targetFmtSel.dispatchEvent(new Event("change"));
      qualitySlider.value = 80;
      qualityVal.textContent = "80%";
      setActivePreset(presetWeb);
    });
  }

  if (presetLossless) {
    presetLossless.addEventListener("click", () => {
      targetFmtSel.value = "png";
      targetFmtSel.dispatchEvent(new Event("change"));
      setActivePreset(presetLossless);
    });
  }

  if (presetPhoto) {
    presetPhoto.addEventListener("click", () => {
      targetFmtSel.value = "jpg";
      targetFmtSel.dispatchEvent(new Event("change"));
      qualitySlider.value = 85;
      qualityVal.textContent = "85%";
      setActivePreset(presetPhoto);
    });
  }

  if (presetPdf) {
    presetPdf.addEventListener("click", () => {
      targetFmtSel.value = "pdf";
      targetFmtSel.dispatchEvent(new Event("change"));
      setActivePreset(presetPdf);
    });
  }

  if (targetFmtSel && dpiGroup) {
    targetFmtSel.addEventListener("change", (e) => {
      dpiGroup.style.display = e.target.value === "pdf" ? "flex" : "none";
    });
  }

  if (multiPdfBtn && multiPdfInput) {
    multiPdfBtn.addEventListener("click", () => multiPdfInput.click());
    multiPdfInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        handleMultiImagePdf(Array.from(e.target.files));
      }
    });
  }

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

  if (targetFmt === "pdf") {
    const dpiVal = document.getElementById("img-dpi-sel");
    if (dpiVal) settings.dpi = Number(dpiVal.value);
  }

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
    processBtn.innerHTML = `<span style="width: 16px; height: 16px;">${ICONS.play}</span> Process & Save Image`;
  }
}

async function handleMultiImagePdf(files) {
  if (!files || files.length === 0) return;
  showToast(`Uploading ${files.length} images to merge into PDF...`, "info", 3000);

  try {
    const paths = [];
    for (const file of files) {
      const uploadRes = await api.uploadFile(file);
      paths.push(uploadRes.path);
    }

    showToast(`Assembling multi-page PDF from ${paths.length} images...`, "info", 3000);
    const job = await api.imagesToPdf(paths, {
      title: `${files[0].name.split('.')[0]}_combined`
    });

    // Poll until complete
    let finishedJob = null;
    for (let i = 0; i < 40; i++) {
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
      showToast(`Successfully created multi-page PDF from ${files.length} images!`, "success", 4000);
      const downloadUrl = `/api/jobs/${finishedJob.id}/download`;
      // Trigger instant download
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `${files[0].name.split('.')[0]}_combined.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  } catch (err) {
    showToast(`Failed to combine images to PDF: ${err.message}`, "error", 4000);
  }
}
