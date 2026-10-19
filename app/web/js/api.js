/**
 * Morphix Frontend API client.
 */

const BASE_URL = "";

async function request(endpoint, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, options);
    if (!res.ok) {
      let errorDetail = `Request failed: ${res.status}`;
      try {
        const errorJson = await res.json();
        errorDetail = errorJson.detail || errorJson.message || errorDetail;
      } catch (_) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  getHealth: () => request("/api/health"),
  getCapabilities: () => request("/api/capabilities"),
  getTargets: (sourceFormat) => request(`/api/capabilities/targets?source_format=${encodeURIComponent(sourceFormat)}`),
  
  inspectPath: (path) => {
    const fd = new FormData();
    fd.append("path", path);
    return request("/api/inspect", { method: "POST", body: fd });
  },

  uploadFile: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/api/upload", { method: "POST", body: fd });
  },

  convert: (job) => request("/api/convert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(job)
  }),

  batchConvert: (items) => request("/api/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items })
  }),

  getJobs: () => request("/api/jobs"),
  getJob: (jobId) => request(`/api/jobs/${jobId}`),
  getJobFiles: (jobId) => request(`/api/jobs/${jobId}/files`),
  cancelJob: (jobId) => request(`/api/jobs/${jobId}/cancel`, { method: "POST" }),
  
  openFolder: (path) => {
    const fd = new FormData();
    fd.append("path", path);
    return request("/api/open-folder", { method: "POST", body: fd });
  },

  getHistory: (limit = 100, offset = 0, status = null, search = null) => {
    const params = new URLSearchParams({ limit, offset });
    if (status) params.append("status", status);
    if (search) params.append("search", search);
    return request(`/api/history?${params.toString()}`);
  },

  clearHistory: () => request("/api/history", { method: "DELETE" }),

  getPresets: (category = null) => {
    const q = category ? `?category=${encodeURIComponent(category)}` : "";
    return request(`/api/presets${q}`);
  },

  createPreset: (presetData) => request("/api/presets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(presetData)
  }),

  deletePreset: (id) => request(`/api/presets/${id}`, { method: "DELETE" }),

  getDiagnostics: () => request("/api/diagnostics"),
  getSettings: () => request("/api/settings"),
  updateSettings: (settings) => request("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings)
  }),

  cleanTemp: () => request("/api/settings/clean-temp", { method: "POST" })
};
