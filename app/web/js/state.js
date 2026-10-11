/**
 * Morphix central reactive state.
 */

class AppState {
  constructor() {
    this.currentView = "convert";
    this.capabilities = { formats: {}, engines: [], routes: [] };
    this.queue = []; // Array of queued files { id, name, path, format, size, targets: [], selectedTarget, settings: {}, status, progress, jobId }
    this.selectedQueueItemId = null;
    this.activeJobs = [];
    this.theme = localStorage.getItem("morphix_theme") || "dark";
    this.settings = {};
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(cb => cb(data));
    }
  }

  setView(viewName) {
    this.currentView = viewName;
    this.emit("viewChange", viewName);
  }

  setTheme(theme) {
    this.theme = theme;
    localStorage.setItem("morphix_theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
    this.emit("themeChange", theme);
  }

  toggleTheme() {
    this.setTheme(this.theme === "dark" ? "light" : "dark");
  }

  addToQueue(item) {
    this.queue.push(item);
    if (!this.selectedQueueItemId) {
      this.selectedQueueItemId = item.id;
    }
    this.emit("queueChange", this.queue);
  }

  removeFromQueue(id) {
    this.queue = this.queue.filter(i => i.id !== id);
    if (this.selectedQueueItemId === id) {
      this.selectedQueueItemId = this.queue.length > 0 ? this.queue[0].id : null;
    }
    this.emit("queueChange", this.queue);
  }

  clearQueue() {
    this.queue = [];
    this.selectedQueueItemId = null;
    this.emit("queueChange", this.queue);
  }

  selectQueueItem(id) {
    this.selectedQueueItemId = id;
    this.emit("selectedItemChange", id);
  }

  getSelectedItem() {
    return this.queue.find(i => i.id === this.selectedQueueItemId);
  }

  updateQueueItem(id, updates) {
    const item = this.queue.find(i => i.id === id);
    if (item) {
      Object.assign(item, updates);
      this.emit("queueChange", this.queue);
    }
  }
}

export const state = new AppState();
