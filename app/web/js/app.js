/**
 * Morphix Application Bootstrap & Navigation Router.
 */

import { state } from "./state.js?v=1.1.0";
import { api } from "./api.js?v=1.1.0";
import { ICONS, showToast } from "./ui.js?v=1.1.0";

import { initConvertView } from "./views/convert.js?v=1.1.0";
import { initBatchView } from "./views/batch.js?v=1.1.0";
import { initImagesView } from "./views/images.js?v=1.1.0";
import { initAudioView } from "./views/audio.js?v=1.1.0";
import { initDocumentsView } from "./views/documents.js?v=1.1.0";
import { initHistoryView } from "./views/history.js?v=1.1.0";
import { initPresetsView } from "./views/presets.js?v=1.1.0";
import { initDiagnosticsView } from "./views/diagnostics.js?v=1.1.0";
import { initSettingsView } from "./views/settings.js?v=1.1.0";
import { initCommandPalette } from "./components/command_palette.js?v=1.1.0";

document.addEventListener("DOMContentLoaded", async () => {
  // Apply saved theme immediately
  document.documentElement.setAttribute("data-theme", state.theme);

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

  // Setup navigation listeners
  setupNavigation();
  setupGlobalShortcuts();
  setupQueueDrawer();
  setupThemeToggle();

  // Set initial view
  switchView("convert");
});

function setupNavigation() {
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
  // Update sidebar active states
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-nav") === viewName) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Switch visible container
  document.querySelectorAll(".view-container").forEach(vc => {
    vc.classList.remove("active");
  });

  const targetElem = document.getElementById(`view-${viewName}`);
  if (targetElem) {
    targetElem.classList.add("active");
  }
}

function setupGlobalShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Ctrl+O: Open files
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "o") {
      e.preventDefault();
      const fileInput = document.getElementById("file-input-files");
      if (fileInput) fileInput.click();
    }
    // Ctrl+,: Open settings
    else if ((e.ctrlKey || e.metaKey) && e.key === ",") {
      e.preventDefault();
      switchView("settings");
    }
    // Ctrl+Enter: Start conversion
    else if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      const startBtn = document.getElementById("btn-start-convert");
      if (startBtn && !startBtn.disabled) {
        startBtn.click();
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

    const drawerBody = document.getElementById("queue-drawer-body");
    if (drawerBody) {
      if (queue.length === 0) {
        drawerBody.innerHTML = `<p style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 20px 0;">Queue is empty.</p>`;
      } else {
        drawerBody.innerHTML = queue.map(item => `
          <div style="padding: 8px; background: var(--bg-surface-elevated); border-radius: 6px; font-size: 12px; display: flex; justify-content: space-between; align-items: center;">
            <span style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${item.name}</span>
            <span class="badge badge-neutral">${item.status}</span>
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
