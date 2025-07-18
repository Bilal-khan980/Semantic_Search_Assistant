const { contextBridge, ipcRenderer } = require("electron");

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld("electronAPI", {
  // Backend communication
  backendRequest: (data) => ipcRenderer.invoke("backend-request", data),

  // Window management
  toggleFloatingWindow: () => ipcRenderer.invoke("toggle-floating-window"),
  closeFloatingWindow: () => ipcRenderer.invoke("close-floating-window"),

  // File operations
  selectFiles: () => ipcRenderer.invoke("select-files"),
  selectFolder: () => ipcRenderer.invoke("select-folder"),
  openFolder: (folderPath) => ipcRenderer.invoke("open-folder", folderPath),

  // Settings
  getSetting: (key) => ipcRenderer.invoke("get-setting", key),
  setSetting: (key, value) => ipcRenderer.invoke("set-setting", key, value),

  // Drag and drop
  startDrag: (data) => ipcRenderer.invoke("start-drag", data),

  // Event listeners
  onBackendReady: (callback) => ipcRenderer.on("backend-ready", callback),
  onFocusSearch: (callback) => ipcRenderer.on("focus-search", callback),
  onBrowseFolderFiles: (callback) =>
    ipcRenderer.on("browse-folder-files", callback),
  onImportReadwise: (callback) => ipcRenderer.on("import-readwise", callback),
  onOpenSettings: (callback) => ipcRenderer.on("open-settings", callback),

  // Global shortcut event listeners
  onQuickSearchClipboard: (callback) => ipcRenderer.on("quick-search-clipboard", callback),
  onToggleCanvas: (callback) => ipcRenderer.on("toggle-canvas", callback),
  onAddSelectionToCanvas: (callback) => ipcRenderer.on("add-selection-to-canvas", callback),
  onShowContextSuggestions: (callback) => ipcRenderer.on("show-context-suggestions", callback),

  // Remove listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel),

  // Platform info
  platform: process.platform,

  // App info
  getAppVersion: () => ipcRenderer.invoke("get-app-version"),

  // Clipboard operations
  writeToClipboard: (text) => ipcRenderer.invoke("write-to-clipboard", text),
  readFromClipboard: () => ipcRenderer.invoke("read-from-clipboard"),

  // Notifications
  showNotification: (title, body) =>
    ipcRenderer.invoke("show-notification", title, body),

  // External links
  openExternal: (url) => ipcRenderer.invoke("open-external", url),
});

// Expose a limited API for the floating window
contextBridge.exposeInMainWorld("floatingAPI", {
  // Window controls
  closeWindow: () => ipcRenderer.invoke("close-floating-window"),
  minimizeWindow: () => ipcRenderer.invoke("minimize-floating-window"),

  // Search functionality
  search: (query) =>
    ipcRenderer.invoke("backend-request", {
      type: "search",
      data: { query },
    }),

  // Quick actions
  copyResult: (text) => ipcRenderer.invoke("write-to-clipboard", text),
  dragResult: (data) => ipcRenderer.invoke("start-drag", data),

  // Event listeners for floating window
  onFocusSearch: (callback) => ipcRenderer.on("focus-search", callback),
  onBackendReady: (callback) => ipcRenderer.on("backend-ready", callback),

  // Settings access
  getSetting: (key) => ipcRenderer.invoke("get-setting", key),
  setSetting: (key, value) => ipcRenderer.invoke("set-setting", key, value),
});

// Security: Remove the ability to access Node.js APIs from the renderer
delete window.require;
delete window.exports;
delete window.module;
