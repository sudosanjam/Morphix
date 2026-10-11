/**
 * Command Palette component (Ctrl+K).
 */

import { state } from "../state.js";
import { api } from "../api.js";
import { ICONS, showToast, openModal, closeModal } from "../ui.js";

const COMMANDS = [
  { id: "nav-convert", title: "Open Convert Workspace", category: "Navigation", icon: ICONS.convert, action: () => state.setView("convert") },
  { id: "nav-batch", title: "Open Batch Jobs Workspace", category: "Navigation", icon: ICONS.batch, action: () => state.setView("batch") },
  { id: "nav-images", title: "Open Image Tools Workspace", category: "Navigation", icon: ICONS.image, action: () => state.setView("images") },
  { id: "nav-audio", title: "Open Audio Tools Workspace", category: "Navigation", icon: ICONS.audio, action: () => state.setView("audio") },
  { id: "nav-docs", title: "Open Documents Workspace", category: "Navigation", icon: ICONS.document, action: () => state.setView("documents") },
  { id: "nav-history", title: "View Conversion History", category: "Navigation", icon: ICONS.history, action: () => state.setView("history") },
  { id: "nav-presets", title: "Manage Presets", category: "Navigation", icon: ICONS.preset, action: () => state.setView("presets") },
  { id: "nav-diag", title: "Run Diagnostics & Doctor", category: "Navigation", icon: ICONS.doctor, action: () => state.setView("diagnostics") },
  { id: "nav-settings", title: "Open Application Settings", category: "Navigation", icon: ICONS.settings, action: () => state.setView("settings") },
  { id: "act-theme", title: "Toggle Theme (Dark / Light)", category: "Appearance", icon: ICONS.sun, action: () => state.toggleTheme() },
  { id: "act-clear-queue", title: "Clear Conversion Queue", category: "Queue", icon: ICONS.trash, action: () => { state.clearQueue(); showToast("Queue cleared", "info"); } },
  { id: "act-clean-temp", title: "Clean Temporary Files", category: "System", icon: ICONS.trash, action: async () => { const r = await api.cleanTemp(); showToast(`Cleaned ${r.cleaned_files_count} temp files`, "success"); } },
];

let selectedIndex = 0;
let filteredCommands = [...COMMANDS];

export function initCommandPalette() {
  const trigger = document.getElementById("topbar-search-trigger");
  const modal = document.getElementById("modal-command-palette");
  const input = document.getElementById("palette-search-input");
  const resultsContainer = document.getElementById("palette-results-list");

  if (!trigger || !modal || !input || !resultsContainer) return;

  trigger.addEventListener("click", () => openPalette());

  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openPalette();
    } else if (e.key === "Escape" && modal.classList.contains("open")) {
      closeModal("modal-command-palette");
    }
  });

  input.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    filteredCommands = COMMANDS.filter(cmd => 
      cmd.title.toLowerCase().includes(query) || cmd.category.toLowerCase().includes(query)
    );
    selectedIndex = 0;
    renderResults();
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedIndex = (selectedIndex + 1) % filteredCommands.length;
      renderResults();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedIndex = (selectedIndex - 1 + filteredCommands.length) % filteredCommands.length;
      renderResults();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filteredCommands[selectedIndex]) {
        executeCommand(filteredCommands[selectedIndex]);
      }
    }
  });

  function openPalette() {
    input.value = "";
    filteredCommands = [...COMMANDS];
    selectedIndex = 0;
    renderResults();
    openModal("modal-command-palette");
    setTimeout(() => input.focus(), 50);
  }

  function renderResults() {
    resultsContainer.innerHTML = "";
    if (filteredCommands.length === 0) {
      resultsContainer.innerHTML = `
        <div style="padding: var(--space-4); text-align: center; color: var(--text-muted); font-size: var(--font-size-sm);">
          No matching commands found.
        </div>
      `;
      return;
    }

    filteredCommands.forEach((cmd, idx) => {
      const item = document.createElement("div");
      item.className = `palette-item ${idx === selectedIndex ? "active" : ""}`;
      item.innerHTML = `
        <div class="palette-item-icon-title">
          <span style="width: 18px; height: 18px; color: var(--color-primary);">${cmd.icon}</span>
          <strong>${cmd.title}</strong>
        </div>
        <span class="badge badge-neutral">${cmd.category}</span>
      `;
      item.addEventListener("click", () => executeCommand(cmd));
      resultsContainer.appendChild(item);
    });
  }

  function executeCommand(cmd) {
    closeModal("modal-command-palette");
    cmd.action();
  }
}
