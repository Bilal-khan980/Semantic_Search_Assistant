const {
  app,
  BrowserWindow,
  Menu,
  ipcMain,
  globalShortcut,
  shell,
  dialog,
} = require("electron");
const path = require("path");
const isDev = require("electron-is-dev");
const Store = require("electron-store");
const { spawn } = require("child_process");
const fs = require("fs");

// Initialize electron store for settings
const store = new Store();

class SemanticSearchApp {
  constructor() {
    this.mainWindow = null;
    this.floatingWindow = null;
    this.backendProcess = null;
    this.isBackendReady = false;

    // Initialize app
    this.initializeApp();
  }

  initializeApp() {
    // Handle app ready
    app.whenReady().then(() => {
      this.createMainWindow();
      this.setupMenu();
      this.setupGlobalShortcuts();
      this.setupIPC();
      this.startBackend();

      app.on("activate", () => {
        if (BrowserWindow.getAllWindows().length === 0) {
          this.createMainWindow();
        }
      });
    });

    // Handle app window closed
    app.on("window-all-closed", () => {
      if (process.platform !== "darwin") {
        this.cleanup();
        app.quit();
      }
    });

    // Handle app before quit
    app.on("before-quit", () => {
      this.cleanup();
    });
  }

  createMainWindow() {
    // Create the main browser window
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      minWidth: 800,
      minHeight: 600,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, "preload.js"),
      },
      icon: path.join(__dirname, "../assets/icon.png"),
      show: false,
      titleBarStyle: "default",
    });

    // Load the app
    const startUrl = `file://${path.join(
      __dirname,
      "renderer/build/index.html"
    )}`;

    this.mainWindow.loadURL(startUrl);

    // Show window when ready
    this.mainWindow.once("ready-to-show", () => {
      this.mainWindow.show();

      // Open DevTools in development
      if (isDev) {
        this.mainWindow.webContents.openDevTools();
      }
    });

    // Handle window closed
    this.mainWindow.on("closed", () => {
      this.mainWindow = null;
    });

    // Handle external links
    this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      shell.openExternal(url);
      return { action: "deny" };
    });
  }

  createFloatingWindow() {
    if (this.floatingWindow) {
      this.floatingWindow.focus();
      return;
    }

    this.floatingWindow = new BrowserWindow({
      width: 400,
      height: 600,
      minWidth: 300,
      minHeight: 400,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, "preload.js"),
      },
      frame: false,
      alwaysOnTop: true,
      resizable: true,
      movable: true,
      minimizable: false,
      maximizable: false,
      skipTaskbar: true,
      transparent: true,
      hasShadow: true,
    });

    // Load floating window content
    const floatingUrl = `file://${path.join(
      __dirname,
      "renderer/build/floating.html"
    )}`;

    this.floatingWindow.loadURL(floatingUrl);

    // Handle window closed
    this.floatingWindow.on("closed", () => {
      this.floatingWindow = null;
    });

    // Save window position
    this.floatingWindow.on("moved", () => {
      const position = this.floatingWindow.getPosition();
      store.set("floatingWindow.position", position);
    });

    // Restore window position
    const savedPosition = store.get("floatingWindow.position");
    if (savedPosition) {
      this.floatingWindow.setPosition(savedPosition[0], savedPosition[1]);
    }
  }

  setupMenu() {
    const template = [
      {
        label: "File",
        submenu: [
          {
            label: "Browse Folder Files",
            accelerator: "CmdOrCtrl+O",
            click: () => this.browseFolderFiles(),
          },
          {
            label: "Import Readwise",
            click: () => this.importReadwise(),
          },
          { type: "separator" },
          {
            label: "Settings",
            accelerator: "CmdOrCtrl+,",
            click: () => this.openSettings(),
          },
          { type: "separator" },
          {
            label: "Quit",
            accelerator: process.platform === "darwin" ? "Cmd+Q" : "Ctrl+Q",
            click: () => {
              this.cleanup();
              app.quit();
            },
          },
        ],
      },
      {
        label: "View",
        submenu: [
          {
            label: "Toggle Floating Window",
            accelerator: "CmdOrCtrl+Shift+F",
            click: () => this.toggleFloatingWindow(),
          },
          {
            label: "Focus Search",
            accelerator: "CmdOrCtrl+K",
            click: () => this.focusSearch(),
          },
          { type: "separator" },
          { role: "reload" },
          { role: "forceReload" },
          { role: "toggleDevTools" },
          { type: "separator" },
          { role: "resetZoom" },
          { role: "zoomIn" },
          { role: "zoomOut" },
          { type: "separator" },
          { role: "togglefullscreen" },
        ],
      },
      {
        label: "Window",
        submenu: [{ role: "minimize" }, { role: "close" }],
      },
      {
        label: "Help",
        submenu: [
          {
            label: "About",
            click: () => this.showAbout(),
          },
        ],
      },
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
  }

  setupGlobalShortcuts() {
    // Global shortcut to toggle floating window
    globalShortcut.register("CommandOrControl+Shift+Space", () => {
      this.toggleFloatingWindow();
    });

    // Global shortcut to focus search
    globalShortcut.register("CommandOrControl+Alt+F", () => {
      this.focusSearch();
    });
  }

  setupIPC() {
    // Backend communication
    ipcMain.handle("backend-request", async (event, data) => {
      return this.sendBackendRequest(data);
    });

    // Window management
    ipcMain.handle("toggle-floating-window", () => {
      this.toggleFloatingWindow();
    });

    ipcMain.handle("close-floating-window", () => {
      if (this.floatingWindow) {
        this.floatingWindow.close();
      }
    });

    ipcMain.handle("minimize-floating-window", () => {
      if (this.floatingWindow) {
        this.floatingWindow.minimize();
      }
    });

    // File operations
    ipcMain.handle("select-files", async () => {
      const result = await dialog.showOpenDialog(this.mainWindow, {
        properties: ["openFile", "multiSelections"],
        filters: [
          { name: "Documents", extensions: ["pdf", "docx", "md", "txt"] },
          { name: "All Files", extensions: ["*"] },
        ],
      });
      return result.filePaths;
    });

    ipcMain.handle("select-folder", async () => {
      const result = await dialog.showOpenDialog(this.mainWindow, {
        properties: ["openDirectory"],
        title: "Select Document Folder",
      });
      return result;
    });

    ipcMain.handle("open-folder", async (event, folderPath) => {
      return await shell.openPath(folderPath);
    });

    // Settings
    ipcMain.handle("get-setting", (event, key) => {
      return store.get(key);
    });

    ipcMain.handle("set-setting", (event, key, value) => {
      store.set(key, value);
    });

    // App info
    ipcMain.handle("get-app-version", () => {
      return app.getVersion();
    });

    // Clipboard operations
    ipcMain.handle("write-to-clipboard", (event, text) => {
      const { clipboard } = require("electron");
      clipboard.writeText(text);
    });

    ipcMain.handle("read-from-clipboard", () => {
      const { clipboard } = require("electron");
      return clipboard.readText();
    });

    // Notifications
    ipcMain.handle("show-notification", (event, title, body) => {
      const { Notification } = require("electron");
      if (Notification.isSupported()) {
        new Notification({ title, body }).show();
      }
    });

    // External links
    ipcMain.handle("open-external", (event, url) => {
      shell.openExternal(url);
    });

    // Drag and drop
    ipcMain.handle("start-drag", (event, data) => {
      // Handle drag start for cross-application drag and drop
      return this.startDrag(data);
    });
  }

  async startBackend() {
    // Don't start backend from Electron - assume it's already running
    // Just check if it's available
    try {
      const axios = require("axios");
      const response = await axios.get("http://127.0.0.1:8000/health", {
        timeout: 5000,
      });
      if (response.data.status === "healthy") {
        this.isBackendReady = true;
        this.notifyBackendReady();
        console.log("Backend is already running and healthy");
      }
    } catch (error) {
      console.log("Backend not available yet, will retry...");
      this.isBackendReady = false;
      // Retry every 2 seconds
      setTimeout(() => this.startBackend(), 2000);
    }
  }

  cleanup() {
    // Unregister global shortcuts
    globalShortcut.unregisterAll();

    // Kill backend process
    if (this.backendProcess) {
      this.backendProcess.kill();
    }
  }

  // Window management methods
  toggleFloatingWindow() {
    if (this.floatingWindow) {
      this.floatingWindow.close();
    } else {
      this.createFloatingWindow();
    }
  }

  focusSearch() {
    const targetWindow = this.floatingWindow || this.mainWindow;
    if (targetWindow) {
      targetWindow.focus();
      targetWindow.webContents.send("focus-search");
    }
  }

  // Menu action methods
  async browseFolderFiles() {
    // Send message to frontend to show folder file browser
    this.mainWindow.webContents.send("browse-folder-files");
  }

  async importReadwise() {
    const folder = await this.selectFolder();
    if (folder) {
      this.mainWindow.webContents.send("import-readwise", folder);
    }
  }

  openSettings() {
    this.mainWindow.webContents.send("open-settings");
  }

  showAbout() {
    dialog.showMessageBox(this.mainWindow, {
      type: "info",
      title: "About Semantic Search Assistant",
      message: "Semantic Search Assistant",
      detail:
        "Privacy-first semantic search for your documents and highlights.\n\nVersion 1.0.0",
    });
  }

  // Helper methods
  async selectFiles() {
    const result = await dialog.showOpenDialog(this.mainWindow, {
      properties: ["openFile", "multiSelections"],
      filters: [
        { name: "Documents", extensions: ["pdf", "docx", "md", "txt"] },
        { name: "All Files", extensions: ["*"] },
      ],
    });
    return result.filePaths || [];
  }

  async selectFolder() {
    const result = await dialog.showOpenDialog(this.mainWindow, {
      properties: ["openDirectory"],
    });
    return result.filePaths[0];
  }

  notifyBackendReady() {
    if (this.mainWindow) {
      this.mainWindow.webContents.send("backend-ready");
    }
    if (this.floatingWindow) {
      this.floatingWindow.webContents.send("backend-ready");
    }
  }

  async sendBackendRequest(data) {
    // Implement actual backend communication via HTTP
    try {
      const axios = require("axios");
      const baseURL = "http://127.0.0.1:8000";

      switch (data.type) {
        case "search":
          const searchResponse = await axios.post(`${baseURL}/search`, {
            query: data.data.query,
            limit: data.data.limit || 20,
            similarity_threshold: data.data.similarity_threshold || 0.3,
          });
          return { success: true, data: searchResponse.data };

        case "process_documents":
          const processResponse = await axios.post(`${baseURL}/process`, {
            file_paths: data.data.file_paths,
          });
          return { success: true, data: processResponse.data };

        case "import_readwise":
          const readwiseResponse = await axios.post(
            `${baseURL}/readwise/import`,
            {
              folder_path: data.data.folder_path,
            }
          );
          return { success: true, data: readwiseResponse.data };

        case "get_stats":
          const statsResponse = await axios.get(`${baseURL}/stats`);
          return { success: true, data: statsResponse.data };

        case "health_check":
          const healthResponse = await axios.get(`${baseURL}/health`);
          return { success: true, data: healthResponse.data };

        default:
          throw new Error(`Unknown request type: ${data.type}`);
      }
    } catch (error) {
      console.error("Backend request failed:", error);
      return {
        success: false,
        error: error.message || "Backend communication failed",
      };
    }
  }

  startDrag(data) {
    // Enhanced cross-application drag and drop
    try {
      const { clipboard, nativeImage, shell } = require("electron");

      // Create a more sophisticated drag image
      const dragImage = this.createDragImage(data);

      // Set multiple clipboard formats for maximum compatibility
      if (data.type === "text") {
        // Plain text for basic compatibility
        clipboard.writeText(data.content);

        // Rich text with enhanced metadata
        if (data.metadata) {
          const richText = this.formatRichText(data);
          const htmlContent = this.formatHTMLContent(data);

          // Set multiple formats
          clipboard.write({
            text: data.content,
            html: htmlContent,
            rtf: richText,
          });
        }

        // Store drag data for potential file creation
        this.storeDragData(data);
      }

      // Show visual feedback
      this.showDragFeedback(data);

      return true;
    } catch (error) {
      console.error("Drag operation failed:", error);
      return false;
    }
  }

  createDragImage(data) {
    // Create a visual representation of the dragged content
    const { nativeImage } = require("electron");

    // Create a simple drag image with content preview
    const canvas = require("canvas");
    const canvasWidth = 200;
    const canvasHeight = 100;

    try {
      const canvasElement = canvas.createCanvas(canvasWidth, canvasHeight);
      const ctx = canvasElement.getContext("2d");

      // Background
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvasWidth, canvasHeight);

      // Border
      ctx.strokeStyle = "#cccccc";
      ctx.lineWidth = 1;
      ctx.strokeRect(0, 0, canvasWidth, canvasHeight);

      // Content preview
      ctx.fillStyle = "#333333";
      ctx.font = "12px Arial";
      const preview =
        data.content.substring(0, 50) + (data.content.length > 50 ? "..." : "");
      ctx.fillText(preview, 10, 30);

      // Source info
      if (data.metadata && data.metadata.source) {
        ctx.fillStyle = "#666666";
        ctx.font = "10px Arial";
        ctx.fillText(`From: ${data.metadata.source}`, 10, 80);
      }

      const buffer = canvasElement.toBuffer("image/png");
      return nativeImage.createFromBuffer(buffer);
    } catch (error) {
      // Fallback to simple image
      return nativeImage.createFromDataURL(
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
      );
    }
  }

  formatRichText(data) {
    // Create RTF format for rich text applications
    const content = data.content.replace(/\n/g, "\\par ");
    const source = data.metadata.source || "Unknown";
    const author = data.metadata.author || "";
    const title = data.metadata.title || "";

    let rtf = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}";
    rtf += "\\f0\\fs24 ";
    rtf += content;
    rtf += "\\par\\par";
    rtf += "{\\i Source: " + source;
    if (title) rtf += " - " + title;
    if (author) rtf += " by " + author;
    rtf += "}";
    rtf += "}";

    return rtf;
  }

  formatHTMLContent(data) {
    // Create rich HTML with proper citation
    const content = data.content.replace(/\n/g, "<br>");
    const metadata = data.metadata || {};

    let html = `<div style="font-family: Arial, sans-serif; line-height: 1.4;">`;
    html += `<div style="margin-bottom: 10px;">${content}</div>`;
    html += `<hr style="border: none; border-top: 1px solid #ccc; margin: 10px 0;">`;
    html += `<div style="font-size: 12px; color: #666;">`;
    html += `<strong>Source:</strong> ${metadata.source || "Unknown"}`;
    if (metadata.title) html += `<br><strong>Title:</strong> ${metadata.title}`;
    if (metadata.author)
      html += `<br><strong>Author:</strong> ${metadata.author}`;
    if (metadata.page) html += `<br><strong>Page:</strong> ${metadata.page}`;
    if (metadata.highlight_color)
      html += `<br><strong>Highlight:</strong> ${metadata.highlight_color}`;
    html += `</div></div>`;

    return html;
  }

  storeDragData(data) {
    // Store drag data temporarily for potential file operations
    const fs = require("fs");
    const path = require("path");
    const os = require("os");

    try {
      const tempDir = path.join(os.tmpdir(), "semantic-search-drag");
      if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
      }

      // Create a temporary file with the content
      const timestamp = Date.now();
      const filename = `drag-content-${timestamp}.txt`;
      const filepath = path.join(tempDir, filename);

      let fileContent = data.content;
      if (data.metadata) {
        fileContent += "\n\n---\n";
        fileContent += `Source: ${data.metadata.source || "Unknown"}\n`;
        if (data.metadata.title)
          fileContent += `Title: ${data.metadata.title}\n`;
        if (data.metadata.author)
          fileContent += `Author: ${data.metadata.author}\n`;
        if (data.metadata.page) fileContent += `Page: ${data.metadata.page}\n`;
      }

      fs.writeFileSync(filepath, fileContent, "utf8");

      // Clean up old files (older than 1 hour)
      this.cleanupOldDragFiles(tempDir);
    } catch (error) {
      console.warn("Failed to store drag data:", error);
    }
  }

  cleanupOldDragFiles(tempDir) {
    const fs = require("fs");
    const path = require("path");

    try {
      const files = fs.readdirSync(tempDir);
      const oneHourAgo = Date.now() - 60 * 60 * 1000;

      files.forEach((file) => {
        if (file.startsWith("drag-content-")) {
          const filepath = path.join(tempDir, file);
          const stats = fs.statSync(filepath);
          if (stats.mtime.getTime() < oneHourAgo) {
            fs.unlinkSync(filepath);
          }
        }
      });
    } catch (error) {
      console.warn("Failed to cleanup old drag files:", error);
    }
  }

  showDragFeedback(data) {
    // Show visual feedback for drag operation
    if (this.floatingWindow) {
      this.floatingWindow.webContents.send("drag-started", {
        content: data.content.substring(0, 100) + "...",
        source: data.metadata?.source || "Unknown",
      });
    }

    // Show system notification
    const { Notification } = require("electron");
    if (Notification.isSupported()) {
      new Notification({
        title: "Content Ready to Drag",
        body: `"${data.content.substring(0, 50)}..." copied to clipboard`,
        silent: true,
      }).show();
    }
  }
}

// Create app instance
new SemanticSearchApp();
