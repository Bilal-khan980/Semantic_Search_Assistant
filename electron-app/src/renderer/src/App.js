import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";

// Components
import DocumentsView from "./components/DocumentsView";
import FolderFileBrowser from "./components/FolderFileBrowser";
import FolderManager from "./components/FolderManager";
import ReadwiseImporter from "./components/ReadwiseImporter";
import SearchInterface from "./components/SearchInterface";
import SettingsPanel from "./components/SettingsPanel";
import Sidebar from "./components/Sidebar";

// Services
import ApiService from "./services/ApiService";

// Utils
import { cn } from "./utils/cn";

function App() {
  const [currentView, setCurrentView] = useState("search");
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    totalChunks: 0,
    readwiseHighlights: 0,
  });
  const [settings, setSettings] = useState({
    theme: "light",
    floatingWindow: true, // Now always floating
    autoIndex: true,
    chunkSize: 1000,
    chunkOverlap: 200,
    alwaysOnTop: true,
  });
  const [showFolderBrowser, setShowFolderBrowser] = useState(false);
  const [isCompactMode, setIsCompactMode] = useState(false);
  const [showClipboardPanel, setShowClipboardPanel] = useState(false);

  // Initialize API service
  const apiService = new ApiService();

  // Setup keyboard shortcuts
  useHotkeys("ctrl+k, cmd+k", (e) => {
    e.preventDefault();
    focusSearch();
  });

  useHotkeys("ctrl+shift+c, cmd+shift+c", (e) => {
    e.preventDefault();
    setShowClipboardPanel(!showClipboardPanel);
  });

  useHotkeys("ctrl+shift+f, cmd+shift+f", (e) => {
    e.preventDefault();
    toggleFloatingWindow();
  });

  useHotkeys("ctrl+comma, cmd+comma", (e) => {
    e.preventDefault();
    setCurrentView("settings");
  });

  // Initialize app
  useEffect(() => {
    initializeApp();
    setupEventListeners();

    return () => {
      cleanupEventListeners();
    };
  }, []);

  const initializeApp = async () => {
    try {
      // Load settings
      await loadSettings();

      // Check backend status
      await checkBackendStatus();

      // Load initial stats
      await loadStats();
    } catch (error) {
      console.error("Failed to initialize app:", error);
    }
  };

  const setupEventListeners = () => {
    if (window.electronAPI) {
      window.electronAPI.onBackendReady(() => {
        setIsBackendReady(true);
        loadStats();
      });

      window.electronAPI.onFocusSearch(() => {
        focusSearch();
      });

      window.electronAPI.onBrowseFolderFiles(() => {
        setShowFolderBrowser(true);
      });

      window.electronAPI.onImportReadwise((event, folder) => {
        setCurrentView("readwise");
        // Handle Readwise import
      });

      window.electronAPI.onOpenSettings(() => {
        setCurrentView("settings");
      });
    }
  };

  const cleanupEventListeners = () => {
    if (window.electronAPI) {
      window.electronAPI.removeAllListeners("backend-ready");
      window.electronAPI.removeAllListeners("focus-search");
      window.electronAPI.removeAllListeners("browse-folder-files");
      window.electronAPI.removeAllListeners("import-readwise");
      window.electronAPI.removeAllListeners("open-settings");
    }
  };

  const loadSettings = async () => {
    try {
      if (window.electronAPI) {
        const savedSettings = await window.electronAPI.getSetting(
          "app.settings"
        );
        if (savedSettings) {
          setSettings((prev) => ({ ...prev, ...savedSettings }));
        }
      }
    } catch (error) {
      console.error("Failed to load settings:", error);
    }
  };

  const saveSettings = async (newSettings) => {
    try {
      setSettings(newSettings);
      if (window.electronAPI) {
        await window.electronAPI.setSetting("app.settings", newSettings);
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
    }
  };

  const checkBackendStatus = async () => {
    try {
      const response = await apiService.checkHealth();
      setIsBackendReady(response.status === "healthy");
    } catch (error) {
      console.error("Backend not ready:", error);
      setIsBackendReady(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiService.getStats();
      setStats(response);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  const handleSearch = async (query, options = {}) => {
    if (!query.trim() || !isBackendReady) return;

    setIsSearching(true);
    setSearchQuery(query);

    try {
      const response = await apiService.search(query, options);
      setSearchResults(response.results || []);
    } catch (error) {
      console.error("Search failed:", error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const focusSearch = () => {
    const searchInput = document.querySelector("[data-search-input]");
    if (searchInput) {
      searchInput.focus();
    }
  };

  const toggleFloatingWindow = () => {
    if (window.electronAPI) {
      window.electronAPI.toggleFloatingWindow();
    }
  };

  const renderCurrentView = () => {
    const viewProps = {
      isBackendReady,
      stats,
      settings,
      onSettingsChange: saveSettings,
    };

    switch (currentView) {
      case "search":
        return (
          <SearchInterface
            {...viewProps}
            searchQuery={searchQuery}
            searchResults={searchResults}
            isSearching={isSearching}
            onSearch={handleSearch}
          />
        );
      case "documents":
        return <DocumentsView {...viewProps} onStatsUpdate={loadStats} />;
      case "folders":
        return <FolderManager {...viewProps} onStatsUpdate={loadStats} />;
      case "readwise":
        return <ReadwiseImporter {...viewProps} onStatsUpdate={loadStats} />;
      case "settings":
        return <SettingsPanel {...viewProps} />;
      default:
        return (
          <SearchInterface
            {...viewProps}
            searchQuery={searchQuery}
            searchResults={searchResults}
            isSearching={isSearching}
            onSearch={handleSearch}
          />
        );
    }
  };

  return (
    <div
      className={cn(
        "h-screen flex flex-col bg-white dark:bg-gray-900 text-foreground",
        settings.theme === "dark" && "dark"
      )}
    >
      {/* Custom title bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 drag-region">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-600 cursor-pointer no-drag transition-colors"
               onClick={() => window.electronAPI?.close?.()}></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-600 cursor-pointer no-drag transition-colors"
               onClick={() => window.electronAPI?.minimize?.()}></div>
          <div className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-600 cursor-pointer no-drag transition-colors"
               onClick={() => window.electronAPI?.maximize?.()}></div>
        </div>
        <h1 className="text-sm font-medium text-gray-700 dark:text-gray-300 select-none">
          Semantic Search Assistant
        </h1>
        <div className="flex items-center space-x-2">
          <button
            className="w-4 h-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 no-drag"
            onClick={() => setShowClipboardPanel(!showClipboardPanel)}
            title="Toggle Clipboard Context (Ctrl+Shift+C)"
          >
            📋
          </button>
          <button
            className="w-4 h-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 no-drag"
            onClick={() => setSettings(prev => ({ ...prev, alwaysOnTop: !prev.alwaysOnTop }))}
            title="Toggle Always on Top"
          >
            📌
          </button>
        </div>
      </div>

      {/* Main layout with sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          currentView={currentView}
          onViewChange={setCurrentView}
          stats={stats}
          isBackendReady={isBackendReady}
        />

        {/* Main content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentView}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              className="flex-1 overflow-hidden"
            >
              {renderCurrentView()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Status bar */}
      <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-2">
              <span className={`w-2 h-2 rounded-full ${isBackendReady ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span>{isBackendReady ? 'Backend Ready' : 'Connecting...'}</span>
            </span>
            <span>{stats.totalChunks} chunks indexed</span>
            <span>{stats.totalDocuments} documents</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>Press Ctrl+K to search</span>
          </div>
        </div>
      </div>

      {/* Folder File Browser Modal */}
      <FolderFileBrowser
        isOpen={showFolderBrowser}
        onClose={() => setShowFolderBrowser(false)}
        showProcessOption={true}
        onFileSelect={(files) => {
          console.log("Selected files:", files);
          // Here you could process the selected files or show them in a view
          setShowFolderBrowser(false);
        }}
        onProcessFiles={async (files) => {
          console.log("Processing files:", files);
          try {
            const filePaths = files.map((file) => file.path);
            const response = await apiService.processDocuments(filePaths);
            console.log("Processing result:", response);
            loadStats(); // Refresh stats after processing
          } catch (error) {
            console.error("Failed to process files:", error);
          }
          setShowFolderBrowser(false);
        }}
      />

      {/* Clipboard Context Panel */}
      <ClipboardContextPanel
        isVisible={showClipboardPanel}
        onClose={() => setShowClipboardPanel(false)}
        searchService={apiService}
      />
    </div>
  );
}

export default App;
