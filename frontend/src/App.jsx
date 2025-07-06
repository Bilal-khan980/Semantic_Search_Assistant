import { useState, useEffect } from "react"
import { SearchInterface } from "./components/SearchInterface"
import { DocumentProcessor } from "./components/DocumentProcessor"
import { ReadwiseImporter } from "./components/ReadwiseImporter"
import { SettingsPanel } from "./components/SettingsPanel"
import { StatusBar } from "./components/StatusBar"
import { Sidebar } from "./components/Sidebar"
import { TitleBar } from "./components/TitleBar"
import { ApiService } from "./services/ApiService"
import { Search, FileText, BookOpen, Settings } from "lucide-react"

function App() {
  const [activeTab, setActiveTab] = useState("search")
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [stats, setStats] = useState({
    total_chunks: 0,
    document_chunks: 0,
    readwise_highlights: 0,
    unique_sources: 0,
  })
  const [apiStatus, setApiStatus] = useState("disconnected")
  const [processingTasks, setProcessingTasks] = useState([])

  // Check API connection on startup
  useEffect(() => {
    checkApiConnection()
    loadStats()

    // Set up periodic health checks
    const interval = setInterval(checkApiConnection, 30000)
    return () => clearInterval(interval)
  }, [])

  // Set up Electron menu listeners
  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.onMenuOpenDocuments(() => {
        setActiveTab("documents")
      })

      window.electronAPI.onMenuImportReadwise(() => {
        setActiveTab("readwise")
      })

      window.electronAPI.onMenuFocusSearch(() => {
        setActiveTab("search")
        // Focus search input
        const searchInput = document.querySelector('input[type="search"]')
        if (searchInput) searchInput.focus()
      })

      window.electronAPI.onMenuClearSearch(() => {
        setSearchResults([])
      })

      return () => {
        window.electronAPI.removeAllListeners("menu-open-documents")
        window.electronAPI.removeAllListeners("menu-import-readwise")
        window.electronAPI.removeAllListeners("menu-focus-search")
        window.electronAPI.removeAllListeners("menu-clear-search")
      }
    }
  }, [])

  const checkApiConnection = async () => {
    try {
      const health = await ApiService.checkHealth()
      setApiStatus(health.status === "healthy" ? "connected" : "error")
    } catch (error) {
      setApiStatus("disconnected")
    }
  }

  const loadStats = async () => {
    try {
      const statsData = await ApiService.getStats()
      setStats(statsData)
    } catch (error) {
      console.error("Failed to load stats:", error)
    }
  }

  const handleSearch = async (query, options = {}) => {
    setIsSearching(true)
    try {
      const results = await ApiService.search(query, options)
      setSearchResults(results.results)
    } catch (error) {
      console.error("Search failed:", error)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const handleDocumentUpload = async (files) => {
    try {
      const response = await ApiService.uploadDocuments(files)
      const taskId = response.task_id

      // Add to processing tasks
      setProcessingTasks((prev) => [
        ...prev,
        {
          id: taskId,
          status: "processing",
          progress: 0,
          message: "Starting document processing...",
          files: files.map((f) => f.name),
        },
      ])

      // Poll for status updates
      pollTaskStatus(taskId)
    } catch (error) {
      console.error("Document upload failed:", error)
    }
  }

  const handleReadwiseImport = async (markdownContent) => {
    try {
      const response = await ApiService.importReadwise(markdownContent)
      const taskId = response.task_id

      // Add to processing tasks
      setProcessingTasks((prev) => [
        ...prev,
        {
          id: taskId,
          status: "processing",
          progress: 0,
          message: "Starting Readwise import...",
          type: "readwise",
        },
      ])

      // Poll for status updates
      pollTaskStatus(taskId)
    } catch (error) {
      console.error("Readwise import failed:", error)
    }
  }

  const pollTaskStatus = async (taskId) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await ApiService.getProcessingStatus(taskId)

        setProcessingTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, ...status } : task)))

        if (status.status === "completed" || status.status === "error") {
          clearInterval(pollInterval)

          // Refresh stats after completion
          if (status.status === "completed") {
            setTimeout(loadStats, 1000)
          }

          // Remove completed task after delay
          setTimeout(() => {
            setProcessingTasks((prev) => prev.filter((task) => task.id !== taskId))
          }, 5000)
        }
      } catch (error) {
        console.error("Failed to poll task status:", error)
        clearInterval(pollInterval)
      }
    }, 1000)
  }

  const sidebarItems = [
    {
      id: "search",
      label: "Search",
      icon: Search,
      badge: searchResults.length > 0 ? searchResults.length : null,
    },
    {
      id: "documents",
      label: "Documents",
      icon: FileText,
      badge: stats.document_chunks > 0 ? stats.document_chunks : null,
    },
    {
      id: "readwise",
      label: "Readwise",
      icon: BookOpen,
      badge: stats.readwise_highlights > 0 ? stats.readwise_highlights : null,
    },
    {
      id: "settings",
      label: "Settings",
      icon: Settings,
    },
  ]

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <TitleBar />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          items={sidebarItems}
          activeItem={activeTab}
          onItemSelect={setActiveTab}
          stats={stats}
          apiStatus={apiStatus}
          processingTasks={processingTasks}
        />

        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-auto p-6">
            {activeTab === "search" && (
              <SearchInterface
                onSearch={handleSearch}
                searchResults={searchResults}
                isSearching={isSearching}
                stats={stats}
              />
            )}

            {activeTab === "documents" && (
              <DocumentProcessor
                onUpload={handleDocumentUpload}
                stats={stats}
                processingTasks={processingTasks.filter((t) => t.type !== "readwise")}
              />
            )}

            {activeTab === "readwise" && (
              <ReadwiseImporter
                onImport={handleReadwiseImport}
                stats={stats}
                processingTasks={processingTasks.filter((t) => t.type === "readwise")}
              />
            )}

            {activeTab === "settings" && <SettingsPanel stats={stats} onRefreshStats={loadStats} />}
          </div>

          <StatusBar apiStatus={apiStatus} stats={stats} processingTasks={processingTasks} />
        </main>
      </div>
    </div>
  )
}

export default App
