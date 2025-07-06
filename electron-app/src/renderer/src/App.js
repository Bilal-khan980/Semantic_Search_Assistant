import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useHotkeys } from "react-hotkeys-hook";

// Components
import Sidebar from "./components/Sidebar";
import SearchInterface from "./components/SearchInterface";
import DocumentsView from "./components/DocumentsView";
import FolderManager from "./components/FolderManager";
import FolderFileBrowser from "./components/FolderFileBrowser";
import ReadwiseImporter from "./components/ReadwiseImporter";
import SettingsPanel from "./components/SettingsPanel";
import StatusBar from "./components/StatusBar";
import TitleBar from "./components/TitleBar";

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
    floatingWindow: false,
    autoIndex: true,
    chunkSize: 1000,
    chunkOverlap: 200,
  });
  const [showFolderBrowser, setShowFolderBrowser] = useState(false);

  // Initialize API service
  const apiService = new ApiService();

  // Setup keyboard shortcuts
  useHotkeys("ctrl+k, cmd+k", (e) => {
    e.preventDefault();
    focusSearch();
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
        "h-screen flex flex-col bg-background text-foreground",
        settings.theme === "dark" && "dark"
      )}
    >
      {/* Custom title bar for desktop */}
      <TitleBar
        isBackendReady={isBackendReady}
        onToggleFloating={toggleFloatingWindow}
      />

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
      <StatusBar
        isBackendReady={isBackendReady}
        stats={stats}
        currentView={currentView}
      />

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
    </div>
  );
}

export default App;
