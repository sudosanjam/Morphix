/**
 * Morphix Application Bootstrap & Navigation Router.
 * Apple Pro Fluid Architecture with Universal Drag & Drop, Palette Themes & Dynamic Hyperspace.
 */

import { state } from "./state.js?v=1.4.1";
import { api } from "./api.js?v=1.4.1";
import { ICONS, showToast, formatBytes } from "./ui.js?v=1.4.1";

import { initConvertView } from "./views/convert.js?v=1.4.1";
import { initBatchView } from "./views/batch.js?v=1.4.1";
import { initImagesView } from "./views/images.js?v=1.4.1";
import { initAudioView } from "./views/audio.js?v=1.4.1";
import { initDocumentsView } from "./views/documents.js?v=1.4.1";
import { initHistoryView } from "./views/history.js?v=1.4.1";
import { initPresetsView } from "./views/presets.js?v=1.4.1";
import { initDiagnosticsView } from "./views/diagnostics.js?v=1.4.1";
import { initSettingsView } from "./views/settings.js?v=1.4.1";
import { initCommandPalette } from "./components/command_palette.js?v=1.4.1";
import { initHyperspace, toggleHyperspace, hyperspacePulse } from "./components/hyperspace.js?v=1.4.1";

const VIEW_TITLES = {
  convert: "All-in-One Studio",
  batch: "Batch Queue",
  images: "Image Optimizer",
  audio: "Audio Lab",
  documents: "Document Hub",
  history: "History & Logs",
  presets: "Presets",
  diagnostics: "Diagnostics",
  settings: "Settings"
};

document.addEventListener("DOMContentLoaded", async () => {
  // Apply saved theme & palette immediately
  document.documentElement.setAttribute("data-theme", state.theme);
  document.documentElement.setAttribute("data-palette", state.palette);

  // Initialize subtle ambient hyperspace background
  initHyperspace();

  // Initialize all view controllers
  initConvertView();
  initBatchView();
  initImagesView();
  initAudioView();
  initDocumentsView();
  initHistoryView();
  initPresetsView();
  initDiagnosticsView();
  initSettingsView();
  initCommandPalette();

  // Load capabilities from server
  try {
    const caps = await api.getCapabilities();
    state.capabilities = caps;
    updateStatusBarEngines(caps.engines);
  } catch (err) {
    console.error("Failed to load capabilities:", err);
  }

  // Setup navigation & controls
  setupNavigation();
  setupSidebarToggle();
  setupThemePalette();
  setupHyperspaceToggle();
  setupGlobalShortcuts();
  setupQueueDrawer();
  setupThemeToggle();
  setupPrototypeSwitcher();
  setupUniversalDragDrop();

  // Set initial view
  switchView("convert");
});

function setupNavigation() {
  // Sync all elements with data-nav (sidebar items and links)
  document.querySelectorAll("[data-nav]").forEach(elem => {
    elem.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = elem.getAttribute("data-nav");
      switchView(targetView);
    });
  });

  state.on("viewChange", (viewName) => {
    switchView(viewName);
  });
}

function switchView(viewName) {
  state.currentView = viewName;

  // Update sidebar active states
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-nav") === viewName) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Update breadcrumb
  const crumbElem = document.getElementById("crumb-current");
  if (crumbElem) {
    crumbElem.textContent = VIEW_TITLES[viewName] || viewName;
  }

  // Switch visible container
  document.querySelectorAll(".view-container").forEach(vc => {
    vc.classList.remove("active");
  });

  const targetElem = document.getElementById(`view-${viewName}`);
  if (targetElem) {
    targetElem.classList.add("active");
  }
}

function setupSidebarToggle() {
  const btn = document.getElementById("sidebar-toggle-btn");
  const sidebar = document.getElementById("sidebar");
  if (!btn || !sidebar) return;

  if (state.sidebarCollapsed) {
    sidebar.classList.add("collapsed");
  }

  btn.addEventListener("click", () => {
    state.toggleSidebar();
  });
}

function setupThemePalette() {
  const select = document.getElementById("theme-palette-select");
  if (!select) return;

  select.value = state.palette;
  select.addEventListener("change", (e) => {
    const pal = e.target.value;
    state.setPalette(pal);
    hyperspacePulse(2.4);
    showToast(`Palette: ${select.options[select.selectedIndex].text}`, "info", 1800);
  });

  state.on("paletteChange", (pal) => {
    if (select) select.value = pal;
  });
}

function setupHyperspaceToggle() {
  const btn = document.getElementById("topbar-hyperspace-btn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const isNowOn = toggleHyperspace();
    showToast(isNowOn ? "✦ Dynamic Background Enabled" : "Dynamic Background Disabled", "info", 1800);
  });
}

function setupGlobalShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Ctrl+O / Cmd+O: Open files
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "o") {
      e.preventDefault();
      const fileInput = document.getElementById("file-input-files");
      if (fileInput) fileInput.click();
    }
    // Ctrl+, / Cmd+,: Open settings
    else if ((e.ctrlKey || e.metaKey) && e.key === ",") {
      e.preventDefault();
      switchView("settings");
    }
    // Ctrl+Enter / Cmd+Enter: Start conversion
    else if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      const startBtn = document.getElementById("btn-start-convert") || document.getElementById("btn-dock-convert");
      if (startBtn && !startBtn.disabled) {
        startBtn.click();
      }
    }
    // Number keys 1-5 with Alt for fast workspace switching
    else if (e.altKey && !isNaN(e.key)) {
      const views = ["convert", "batch", "images", "audio", "documents"];
      const idx = parseInt(e.key, 10) - 1;
      if (views[idx]) {
        e.preventDefault();
        switchView(views[idx]);
      }
    }
  });
}

function setupPrototypeSwitcher() {
  const select = document.getElementById("prototype-layout-select");
  const appRoot = document.getElementById("app-root");
  if (!select || !appRoot) return;

  const savedProto = localStorage.getItem("morphix_prototype_layout") || "studio";
  select.value = savedProto;
  appRoot.setAttribute("data-prototype", savedProto);

  select.addEventListener("change", (e) => {
    const val = e.target.value;
    appRoot.setAttribute("data-prototype", val);
    localStorage.setItem("morphix_prototype_layout", val);
    state.emit("prototypeChange", val);
    showToast(`Switched Layout to: ${select.options[select.selectedIndex].text}`, "info", 2000);
  });
}

/**
 * Universal Global Drag and Drop.
 * Prevents browser navigation, handles child-element jitter with depth counter,
 * and routes files seamlessly to whichever workspace is active.
 */
function setupUniversalDragDrop() {
  const overlay = document.getElementById("global-drag-overlay");
  let dragCounter = 0;

  // Prevent default window navigation on drag/drop
  ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
    window.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  window.addEventListener("dragenter", (e) => {
    dragCounter++;
    if (e.dataTransfer && e.dataTransfer.types && Array.from(e.dataTransfer.types).includes("Files")) {
      e.dataTransfer.dropEffect = "copy";
      if (overlay) overlay.classList.add("active");
    }
  });

  window.addEventListener("dragover", (e) => {
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = "copy";
    }
  });

  window.addEventListener("dragleave", (e) => {
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      if (overlay) overlay.classList.remove("active");
    }
  });

  window.addEventListener("drop", (e) => {
    dragCounter = 0;
    if (overlay) overlay.classList.remove("active");

    const dt = e.dataTransfer;
    if (!dt || !dt.files || dt.files.length === 0) return;

    // Trigger subtle warp surge for physical tactile feedback
    hyperspacePulse(3.2);

    const files = Array.from(dt.files);

    // Route files to appropriate workspace handler
    const current = state.currentView;
    if (current === "images" && window.morphixImagesDrop) {
      window.morphixImagesDrop(files);
    } else if (current === "audio" && window.morphixAudioDrop) {
      window.morphixAudioDrop(files);
    } else if (current === "batch" && window.morphixBatchDrop) {
      window.morphixBatchDrop(files);
    } else if (current === "documents" && window.morphixDocsDrop) {
      window.morphixDocsDrop(files);
    } else {
      // Default to Convert Studio
      if (current !== "convert") {
        switchView("convert");
      }
      if (window.morphixConvertDrop) {
        window.morphixConvertDrop(files);
      }
    }
  });
}

function setupQueueDrawer() {
  const toggleBtn = document.getElementById("topbar-queue-btn");
  const drawer = document.getElementById("queue-drawer");
  const closeBtn = document.getElementById("queue-drawer-close");

  if (!toggleBtn || !drawer) return;

  toggleBtn.addEventListener("click", () => {
    drawer.classList.toggle("open");
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      drawer.classList.remove("open");
    });
  }

  state.on("queueChange", (queue) => {
    const badge = document.getElementById("topbar-queue-count");
    if (badge) badge.textContent = queue.length;

    const drawerCount = document.getElementById("drawer-queue-count");
    if (drawerCount) drawerCount.textContent = queue.length;

    const drawerBody = document.getElementById("queue-drawer-body");
    if (drawerBody) {
      if (queue.length === 0) {
        drawerBody.innerHTML = `<p style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 28px 0;">Queue is empty.</p>`;
      } else {
        drawerBody.innerHTML = queue.map(item => `
          <div style="padding: 10px 12px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); font-size: 12px; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 500; color: var(--text-primary); max-width: 190px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${item.name}</span>
              <span class="badge ${item.status === 'completed' ? 'badge-success' : item.status === 'failed' ? 'badge-danger' : item.status === 'converting' ? 'badge-primary' : 'badge-neutral'}" style="font-size: 10px;">${item.status}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-muted);">
              <span>${item.format.toUpperCase()} → ${item.selectedTarget.toUpperCase()}</span>
              <span>${formatBytes(item.size)}</span>
            </div>
          </div>
        `).join("");
      }
    }
  });
}

function setupThemeToggle() {
  const toggleBtn = document.getElementById("topbar-theme-btn");
  if (!toggleBtn) return;
  toggleBtn.addEventListener("click", () => {
    state.toggleTheme();
  });
}

function updateStatusBarEngines(engines) {
  const container = document.getElementById("status-engines-summary");
  if (!container || !engines) return;

  const available = engines.filter(e => e.available).map(e => e.name);
  container.textContent = `Active Engines: ${available.join(", ")}`;
}
