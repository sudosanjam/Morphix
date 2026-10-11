/**
 * Dedicated Audio Tools Workspace.
 */

import { api } from "../api.js";
import { ICONS, showToast, formatBytes } from "../ui.js";

let loadedAudio = null;

export function initAudioView() {
  const container = document.getElementById("view-audio");
  if (!container) return;

  renderAudioView(container);
  setupListeners(container);
}

function renderAudioView(container) {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: var(--space-4); max-width: 900px; margin: 0 auto; width: 100%;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <h2>Audio Encoding & Loudness Processing</h2>
          <p style="font-size: var(--font-size-xs); color: var(--text-muted);">
            FFmpeg-powered broadcast loudness normalization (LUFS), codec resampling, bitrate tuning, and trimming
          </p>
        </div>
        <div>
          <button id="aud-btn-upload" class="btn btn-primary btn-sm">
            <span style="width: 14px; height: 14px;">${ICONS.plus}</span> Open Audio File
          </button>
          <input type="file" id="aud-file-input" accept="audio/*" style="display: none;" />
        </div>
      </div>

      <!-- Audio Inspection Stats Card -->
      <div class="card" id="aud-stats-card">
        <div class="card-header">
          <h3 class="card-title">Stream Inspection</h3>
          <span id="aud-stat-badge" class="badge badge-neutral">No file loaded</span>
        </div>
        <div class="card-body">
          <div class="audio-meta-card">
            <div class="audio-stat-block">
              <span class="audio-stat-label">Codec</span>
              <span class="audio-stat-value" id="aud-val-codec">--</span>
            </div>
            <div class="audio-stat-block">
              <span class="audio-stat-label">Duration</span>
              <span class="audio-stat-value" id="aud-val-dur">--</span>
            </div>
            <div class="audio-stat-block">
              <span class="audio-stat-label">Sample Rate</span>
              <span class="audio-stat-value" id="aud-val-rate">--</span>
            </div>
            <div class="audio-stat-block">
              <span class="audio-stat-label">Channels</span>
              <span class="audio-stat-value" id="aud-val-ch">--</span>
            </div>
            <div class="audio-stat-block">
              <span class="audio-stat-label">Bitrate</span>
              <span class="audio-stat-value" id="aud-val-br">--</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Audio Configuration Settings Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Encoding & Filters</h3>
          <div style="display: flex; gap: var(--space-2);">
            <button class="btn btn-secondary btn-sm aud-preset-btn" data-preset="podcast">Podcast Preset</button>
            <button class="btn btn-secondary btn-sm aud-preset-btn" data-preset="voice">Voice Preset</button>
            <button class="btn btn-secondary btn-sm aud-preset-btn" data-preset="lossless">Lossless Preset</button>
          </div>
        </div>
        <div class="card-body" style="display: flex; flex-direction: column; gap: var(--space-4);">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
            <div class="form-group">
              <label class="form-label">Output Format</label>
              <select id="aud-target-fmt" class="input-select">
                <option value="mp3" selected>MP3 (MPEG Audio Layer III)</option>
                <option value="wav">WAV (Uncompressed PCM)</option>
                <option value="flac">FLAC (Lossless Audio)</option>
                <option value="aac">AAC (Advanced Audio Coding)</option>
                <option value="ogg">OGG (Vorbis Audio)</option>
                <option value="opus">Opus (Interactive Speech & Music)</option>
                <option value="aiff">AIFF (Apple Audio)</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Target Bitrate</label>
              <select id="aud-bitrate-sel" class="input-select">
                <option value="64k">64 kbps (Voice / Low)</option>
                <option value="96k">96 kbps</option>
                <option value="128k">128 kbps (Standard Speech)</option>
                <option value="192k" selected>192 kbps (Standard Music)</option>
                <option value="256k">256 kbps (High Quality)</option>
                <option value="320k">320 kbps (Maximum MP3 Fidelity)</option>
              </select>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
            <div class="form-group">
              <label class="form-label">Sample Rate</label>
              <select id="aud-rate-sel" class="input-select">
                <option value="">Keep Original</option>
                <option value="22050">22,050 Hz</option>
                <option value="44100" selected>44,100 Hz (CD Standard)</option>
                <option value="48000">48,000 Hz (Video / Studio Standard)</option>
                <option value="96000">96,000 Hz (Hi-Res Audio)</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Channels</label>
              <select id="aud-channels-sel" class="input-select">
                <option value="preserve" selected>Preserve Original</option>
                <option value="stereo">Stereo (2 Channels)</option>
                <option value="mono">Mono (1 Channel)</option>
              </select>
            </div>
          </div>

          <!-- Loudness Normalization -->
          <div style="padding: var(--space-4); background: var(--bg-surface-elevated); border-radius: var(--radius-md); display: flex; flex-direction: column; gap: var(--space-3);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <strong style="font-size: var(--font-size-sm);">EBU R128 Loudness Normalization (LUFS)</strong>
                <p style="font-size: var(--font-size-xs); color: var(--text-muted);">
                  Normalizes integrated loudness to target broadcast standard with true-peak limiting
                </p>
              </div>
              <label class="switch">
                <input type="checkbox" id="aud-lufs-toggle" />
                <span class="switch-slider"></span>
              </label>
            </div>
            <div id="aud-lufs-controls" style="display: none; grid-template-columns: 1fr 1fr; gap: var(--space-3);">
              <div class="form-group">
                <label class="form-label">
                  <span>Target Integrated LUFS</span>
                  <span class="slider-val" id="aud-lufs-val">-16.0 LUFS</span>
                </label>
                <input type="range" id="aud-lufs-slider" class="range-slider" min="-24.0" max="-12.0" step="0.5" value="-16.0" />
              </div>
              <div class="form-group">
                <label class="form-label">
                  <span>True Peak Ceiling (dBTP)</span>
                  <span class="slider-val" id="aud-peak-val">-1.0 dBTP</span>
                </label>
                <input type="range" id="aud-peak-slider" class="range-slider" min="-3.0" max="0.0" step="0.5" value="-1.0" />
              </div>
            </div>
          </div>

          <div style="display: flex; justify-content: flex-end; gap: var(--space-3); margin-top: var(--space-2);">
            <button id="aud-btn-convert" class="btn btn-primary btn-lg" disabled>
              <span style="width: 18px; height: 18px;">${ICONS.play || ICONS.convert}</span> Convert Audio
            </button>
          </div>

          <div id="aud-result-box" style="display: none; padding: var(--space-4); background: var(--color-success-bg); border-radius: var(--radius-md); align-items: center; justify-content: space-between;">
            <div>
              <strong style="color: var(--color-success);">Audio Conversion Completed</strong>
              <div style="font-size: 12px; color: var(--text-secondary);" id="aud-result-msg">Output validated and saved.</div>
            </div>
            <div style="display: flex; gap: var(--space-2);">
              <a id="aud-download-btn" class="btn btn-primary btn-sm" download>Download</a>
              <button id="aud-open-folder-btn" class="btn btn-secondary btn-sm">Show in Folder</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function setupListeners(container) {
  const uploadBtn = container.querySelector("#aud-btn-upload");
  const fileInput = container.querySelector("#aud-file-input");
  const convertBtn = container.querySelector("#aud-btn-convert");
  const lufsToggle = container.querySelector("#aud-lufs-toggle");
  const lufsControls = container.querySelector("#aud-lufs-controls");
  const lufsSlider = container.querySelector("#aud-lufs-slider");
  const lufsVal = container.querySelector("#aud-lufs-val");
  const peakSlider = container.querySelector("#aud-peak-slider");
  const peakVal = container.querySelector("#aud-peak-val");

  uploadBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      loadAudioFile(e.target.files[0]);
    }
  });

  lufsToggle.addEventListener("change", (e) => {
    lufsControls.style.display = e.target.checked ? "grid" : "none";
  });

  lufsSlider.addEventListener("input", (e) => {
    lufsVal.textContent = e.target.value + " LUFS";
  });

  peakSlider.addEventListener("input", (e) => {
    peakVal.textContent = e.target.value + " dBTP";
  });

  // Presets
  container.querySelectorAll(".aud-preset-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const type = btn.getAttribute("data-preset");
      if (type === "podcast") {
        document.getElementById("aud-target-fmt").value = "mp3";
        document.getElementById("aud-bitrate-sel").value = "128k";
        lufsToggle.checked = true;
        lufsControls.style.display = "grid";
        lufsSlider.value = "-16.0";
        lufsVal.textContent = "-16.0 LUFS";
        showToast("Applied Podcast Preset: MP3 128k, -16 LUFS", "info");
      } else if (type === "voice") {
        document.getElementById("aud-target-fmt").value = "opus";
        document.getElementById("aud-bitrate-sel").value = "64k";
        document.getElementById("aud-channels-sel").value = "mono";
        lufsToggle.checked = true;
        lufsControls.style.display = "grid";
        showToast("Applied Voice Preset: Opus Mono 64k, -16 LUFS", "info");
      } else if (type === "lossless") {
        document.getElementById("aud-target-fmt").value = "flac";
        lufsToggle.checked = false;
        lufsControls.style.display = "none";
        showToast("Applied Lossless Archive Preset: FLAC bit-perfect", "info");
      }
    });
  });

  convertBtn.addEventListener("click", convertAudio);
}

async function loadAudioFile(file) {
  showToast(`Uploading and inspecting audio ${file.name}...`, "info", 1500);
  try {
    const res = await api.uploadFile(file);
    const meta = res.metadata;
    const props = meta.properties || {};

    loadedAudio = {
      file: file,
      path: res.path,
      meta: meta
    };

    document.getElementById("aud-stat-badge").textContent = file.name;
    document.getElementById("aud-stat-badge").className = "badge badge-primary";

    document.getElementById("aud-val-codec").textContent = props.codec ? props.codec.toUpperCase() : meta.format.toUpperCase();
    document.getElementById("aud-val-dur").textContent = props.duration_str || (props.duration_seconds ? props.duration_seconds + "s" : "--");
    document.getElementById("aud-val-rate").textContent = props.sample_rate ? `${props.sample_rate} Hz` : "--";
    document.getElementById("aud-val-ch").textContent = props.channel_layout || (props.channels ? `${props.channels} ch` : "--");
    document.getElementById("aud-val-br").textContent = props.bitrate_kbps ? `${props.bitrate_kbps} kbps` : "--";

    document.getElementById("aud-btn-convert").disabled = false;
    showToast(`Loaded: ${file.name}`, "success", 2000);
  } catch (err) {
    showToast(`Failed to load audio: ${err.message}`, "error");
  }
}

async function convertAudio() {
  if (!loadedAudio) return;

  const btn = document.getElementById("aud-btn-convert");
  const targetFmt = document.getElementById("aud-target-fmt").value;
  const bitrate = document.getElementById("aud-bitrate-sel").value;
  const sampleRate = document.getElementById("aud-rate-sel").value;
  const channels = document.getElementById("aud-channels-sel").value;
  const lufsNorm = document.getElementById("aud-lufs-toggle").checked;
  const targetLufs = Number(document.getElementById("aud-lufs-slider").value);
  const truePeak = Number(document.getElementById("aud-peak-slider").value);

  const settings = {
    bitrate: bitrate,
    channels: channels,
    loudness_norm: lufsNorm
  };

  if (sampleRate) settings.sample_rate = Number(sampleRate);
  if (lufsNorm) {
    settings.target_lufs = targetLufs;
    settings.true_peak = truePeak;
  }

  btn.disabled = true;
  btn.textContent = "Encoding Audio...";

  try {
    const job = await api.convert({
      source_path: loadedAudio.path,
      target_format: targetFmt,
      settings: settings,
      overwrite_policy: "rename"
    });

    let finished = null;
    for (let i = 0; i < 40; i++) {
      await new Promise(r => setTimeout(r, 600));
      const status = await api.getJob(job.id);
      if (status.status === "completed") {
        finished = status;
        break;
      } else if (status.status === "failed") {
        throw new Error(status.error_message || "Conversion failed");
      }
    }

    if (finished) {
      showToast("Audio converted successfully!", "success");
      const resultBox = document.getElementById("aud-result-box");
      const downloadBtn = document.getElementById("aud-download-btn");
      const folderBtn = document.getElementById("aud-open-folder-btn");
      const resultMsg = document.getElementById("aud-result-msg");

      resultBox.style.display = "flex";
      resultMsg.textContent = `Duration: ${finished.duration_seconds}s | Output: ${formatBytes(finished.output_size_bytes)}`;
      downloadBtn.href = `/api/jobs/${finished.id}/download`;
      downloadBtn.download = `${loadedAudio.file.name.split('.')[0]}_converted.${targetFmt}`;
      folderBtn.onclick = () => api.openFolder(finished.target_path);
    }
  } catch (err) {
    showToast(`Audio conversion failed: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span style="width: 18px; height: 18px;">${ICONS.play || ICONS.convert}</span> Convert Audio`;
  }
}
