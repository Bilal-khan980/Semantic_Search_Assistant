import axios from "axios";
import { motion } from "framer-motion";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  Loader2,
  Play,
  RefreshCw,
  Search,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "../utils/cn";

function DocumentsView({ isBackendReady, stats, onStatsUpdate }) {
  const [folderFiles, setFolderFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [fileFilter, setFileFilter] = useState("all");
  const [processing, setProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(null);
  const [indexingStatus, setIndexingStatus] = useState({});
  const [overallIndexingStatus, setOverallIndexingStatus] = useState(null);

  // Hardcoded test_docs folder path
  const TEST_DOCS_FOLDER = "test_docs";

  useEffect(() => {
    console.log("📋 DocumentsView useEffect - isBackendReady:", isBackendReady);
    if (isBackendReady) {
      console.log("🔄 Loading test_docs files...");
      loadTestDocsFiles();
      checkIndexingStatus();
    }
  }, [isBackendReady]);

  // Periodic status check
  useEffect(() => {
    if (!isBackendReady) return;

    const interval = setInterval(() => {
      checkIndexingStatus();
    }, 2000); // Check every 2 seconds

    return () => clearInterval(interval);
  }, [isBackendReady]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cleanup any intervals or subscriptions if needed
    };
  }, []);

  const loadTestDocsFiles = async () => {
    try {
      setIsLoading(true);

      // First ensure test_docs folder is connected
      await ensureTestDocsFolderConnected();

      // Then load files from test_docs folder
      const response = await axios.post("http://127.0.0.1:8000/folders/scan", {
        folder_path: TEST_DOCS_FOLDER,
      });

      const files = response.data.files || [];
      console.log("📁 Loaded files from test_docs:", files);
      setFolderFiles(files);
      setSelectedFiles([]); // Clear selection when loading
    } catch (error) {
      console.error("Failed to load test_docs files:", error);
      console.error("Error details:", error.response?.data || error.message);
      setFolderFiles([]);
    } finally {
      setIsLoading(false);
    }
  };

  const ensureTestDocsFolderConnected = async () => {
    try {
      // Check if test_docs is already connected
      const listResponse = await axios.get(
        "http://127.0.0.1:8000/folders/list"
      );
      const connectedFolders = listResponse.data.connected_folders || [];

      // Check if test_docs folder is already connected (check for both relative and absolute paths)
      const isConnected = connectedFolders.some(
        (folder) => folder.includes("test_docs") || folder.endsWith("test_docs")
      );

      if (!isConnected) {
        // Add test_docs folder
        await axios.post("http://127.0.0.1:8000/folders/add", {
          folder_path: TEST_DOCS_FOLDER,
        });
      }
    } catch (error) {
      console.error("Failed to ensure test_docs folder is connected:", error);
    }
  };

  const checkIndexingStatus = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/indexing/status");
      const allStatus = response.data.indexing_status || {};

      // Calculate overall status
      const statusCounts = {
        pending: 0,
        indexing: 0,
        indexed: 0,
        failed: 0,
      };

      Object.values(allStatus).forEach((status) => {
        const statusType = status.status || "unknown";
        if (statusCounts.hasOwnProperty(statusType)) {
          statusCounts[statusType]++;
        }
      });

      let overallStatus = null;
      if (statusCounts.indexing > 0) {
        overallStatus = {
          status: "indexing",
          message: `Indexing ${statusCounts.indexing} files...`,
          progress: 0, // Could calculate average progress if needed
        };
      } else if (statusCounts.pending > 0) {
        overallStatus = {
          status: "pending",
          message: `${statusCounts.pending} files pending indexing`,
          progress: 0,
        };
      } else if (statusCounts.indexed > 0 || statusCounts.failed > 0) {
        overallStatus = {
          status: "completed",
          message: `${statusCounts.indexed} indexed, ${statusCounts.failed} failed`,
          progress: 100,
        };
      }

      setOverallIndexingStatus(overallStatus);
      setIndexingStatus(allStatus);
    } catch (error) {
      console.error("Failed to check indexing status:", error);
    }
  };

  const refreshFiles = async () => {
    setOverallIndexingStatus({
      status: "checking",
      message: "Checking files...",
      progress: 0,
    });
    await loadTestDocsFiles();
    await checkIndexingStatus();

    // Clear status after a delay if no active indexing
    setTimeout(() => {
      if (overallIndexingStatus?.status === "completed") {
        setOverallIndexingStatus(null);
      }
    }, 3000);
  };

  const toggleFileSelection = (file) => {
    setSelectedFiles((prev) => {
      const isSelected = prev.some((f) => f.path === file.path);
      if (isSelected) {
        return prev.filter((f) => f.path !== file.path);
      } else {
        return [...prev, file];
      }
    });
  };

  const selectAllFiles = () => {
    setSelectedFiles(filteredFiles);
  };

  const clearSelection = () => {
    setSelectedFiles([]);
  };

  const processSelectedFiles = async () => {
    if (selectedFiles.length === 0 || !isBackendReady) return;

    setProcessing(true);
    setProcessingProgress({
      status: "processing",
      message: "Processing selected files...",
      progress: 0,
    });

    try {
      const filePaths = selectedFiles.map((file) => file.path);

      // Call the backend to process files
      const response = await axios.post("http://127.0.0.1:8000/process", {
        file_paths: filePaths,
      });

      // Track progress in real-time if task_id is returned
      if (response.data.task_id) {
        trackProcessingProgress(response.data.task_id);
      } else {
        // No task ID returned, assume immediate completion
        setProcessingProgress({
          status: "completed",
          message: "Processing completed!",
          progress: 100,
        });

        if (onStatsUpdate) {
          onStatsUpdate();
        }
        setSelectedFiles([]);
        setProcessing(false);
        setTimeout(() => setProcessingProgress(null), 2000);
      }
    } catch (error) {
      console.error("Processing failed:", error);
      setProcessingProgress({
        status: "error",
        message: error.response?.data?.detail || error.message,
        progress: 0,
      });
      setProcessing(false);
      setTimeout(() => setProcessingProgress(null), 5000);
    }
  };

  const trackProcessingProgress = (taskId) => {
    // Simple polling-based progress tracking
    const pollProgress = async () => {
      try {
        const response = await axios.get(
          `http://127.0.0.1:8000/process/status/${taskId}`
        );
        const progressData = response.data;

        setProcessingProgress({
          status: progressData.status,
          message: progressData.message,
          progress: progressData.progress,
        });

        if (progressData.status === "completed") {
          if (onStatsUpdate) {
            onStatsUpdate();
          }
          setSelectedFiles([]);
          setProcessing(false);
          setTimeout(() => setProcessingProgress(null), 2000);
          // Also refresh indexing status
          checkIndexingStatus();
        } else if (progressData.status === "error") {
          setProcessing(false);
          setTimeout(() => setProcessingProgress(null), 5000);
        } else {
          // Continue polling
          setTimeout(pollProgress, 1000);
        }
      } catch (error) {
        console.error("Error tracking progress:", error);
        setProcessingProgress({
          status: "error",
          message: "Error tracking progress",
          progress: 0,
        });
        setProcessing(false);
        setTimeout(() => setProcessingProgress(null), 5000);
      }
    };

    pollProgress();
  };

  // Filter files based on search query and file type filter
  const filteredFiles = folderFiles.filter((file) => {
    const matchesSearch =
      !searchQuery ||
      file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      file.path.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesFilter =
      fileFilter === "all" ||
      (fileFilter === "pdf" && file.extension === ".pdf") ||
      (fileFilter === "docx" && file.extension === ".docx") ||
      (fileFilter === "md" && file.extension === ".md") ||
      (fileFilter === "txt" && file.extension === ".txt") ||
      (fileFilter === "unprocessed" && file.needs_processing);

    return matchesSearch && matchesFilter;
  });

  const getFileIcon = (extension) => {
    switch (extension?.toLowerCase()) {
      case ".pdf":
        return "📄";
      case ".docx":
        return "📝";
      case ".md":
        return "📋";
      case ".txt":
        return "📄";
      default:
        return "📄";
    }
  };

  const getIndexingStatusBadge = (file) => {
    const status = file.indexing_status || "unknown";
    const progress = file.indexing_progress || 0;
    const error = file.indexing_error;

    switch (status) {
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
            <Clock className="w-3 h-3" />
            Pending
          </span>
        );
      case "indexing":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
            <Loader2 className="w-3 h-3 animate-spin" />
            Indexing... {Math.round(progress)}%
          </span>
        );
      case "indexed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
            <CheckCircle className="w-3 h-3" />
            Indexed
          </span>
        );
      case "failed":
        return (
          <span
            className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full cursor-help"
            title={error || "Indexing failed"}
          >
            <AlertCircle className="w-3 h-3" />
            Failed
          </span>
        );
      case "unknown":
      default:
        if (file.needs_processing) {
          return (
            <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
              <Clock className="w-3 h-3" />
              Unprocessed
            </span>
          );
        }
        return null;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  if (!isBackendReady) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Waiting for backend...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full bg-background">
      {/* Main Content - File Browser */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b bg-background">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold">Test Documents</h2>
              <p className="text-sm text-muted-foreground mt-1">
                {TEST_DOCS_FOLDER} • {filteredFiles.length} files
              </p>
              <button
                onClick={refreshFiles}
                disabled={isLoading}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mt-2"
              >
                <RefreshCw
                  className={cn("w-4 h-4", isLoading && "animate-spin")}
                />
                Refresh Files
              </button>

              {/* Overall Indexing Status */}
              {overallIndexingStatus && (
                <div className="mt-2 flex items-center gap-2 text-sm">
                  {overallIndexingStatus.status === "indexing" && (
                    <div className="flex items-center gap-2 text-blue-600">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>{overallIndexingStatus.message}</span>
                    </div>
                  )}
                  {overallIndexingStatus.status === "pending" && (
                    <div className="flex items-center gap-2 text-yellow-600">
                      <Clock className="w-4 h-4" />
                      <span>{overallIndexingStatus.message}</span>
                    </div>
                  )}
                  {overallIndexingStatus.status === "completed" && (
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircle className="w-4 h-4" />
                      <span>{overallIndexingStatus.message}</span>
                    </div>
                  )}
                  {overallIndexingStatus.status === "checking" && (
                    <div className="flex items-center gap-2 text-blue-600">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>{overallIndexingStatus.message}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {selectedFiles.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {selectedFiles.length} selected
                </span>
                <button
                  onClick={processSelectedFiles}
                  disabled={processing || !isBackendReady}
                  className="btn btn-primary"
                >
                  {processing ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Process Selected
                    </>
                  )}
                </button>
                <button onClick={clearSelection} className="btn btn-secondary">
                  <X className="w-4 h-4 mr-2" />
                  Clear
                </button>
              </div>
            )}
          </div>

          {/* Search and Filters */}
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background"
              />
            </div>

            <select
              value={fileFilter}
              onChange={(e) => setFileFilter(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-background"
            >
              <option value="all">All Files</option>
              <option value="pdf">PDF</option>
              <option value="docx">Word</option>
              <option value="md">Markdown</option>
              <option value="txt">Text</option>
              <option value="unprocessed">Unprocessed</option>
            </select>

            {filteredFiles.length > 0 && (
              <button onClick={selectAllFiles} className="btn btn-secondary">
                Select All
              </button>
            )}
          </div>
        </div>

        {/* Enhanced Real-time Processing Progress */}
        {processingProgress && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="p-4 border-b bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20"
          >
            <div className="flex items-center gap-3">
              {processingProgress.status === "error" ? (
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              ) : processingProgress.status === "completed" ? (
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
              ) : (
                <RefreshCw className="w-5 h-5 animate-spin text-blue-500 flex-shrink-0" />
              )}

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {processingProgress.message}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                    {Math.round(processingProgress.progress || 0)}%
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <motion.div
                    className={cn(
                      "h-2 rounded-full transition-all duration-500",
                      processingProgress.status === "error"
                        ? "bg-red-500"
                        : processingProgress.status === "completed"
                        ? "bg-green-500"
                        : "bg-blue-500"
                    )}
                    initial={{ width: 0 }}
                    animate={{ width: `${processingProgress.progress || 0}%` }}
                  />
                </div>

                {/* Additional info */}
                {processingProgress.status === "processing" && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Processing {selectedFiles.length} file
                    {selectedFiles.length !== 1 ? "s" : ""}...
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* File List */}
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
              <span className="ml-3 text-muted-foreground">
                Loading files...
              </span>
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">No Files Found</h3>
              <p className="text-muted-foreground">
                {searchQuery
                  ? "No files match your search criteria"
                  : "The test_docs folder contains no supported documents"}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-2">
              {filteredFiles.map((file, index) => {
                const isSelected = selectedFiles.some(
                  (f) => f.path === file.path
                );
                return (
                  <motion.div
                    key={file.path}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.02 }}
                    onClick={() => toggleFileSelection(file)}
                    className={cn(
                      "p-4 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors",
                      isSelected
                        ? "bg-primary/10 border-primary/30"
                        : "border-border"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex-shrink-0 text-2xl">
                        {getFileIcon(file.extension)}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium truncate">{file.name}</h4>
                          {getIndexingStatusBadge(file)}
                        </div>

                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>{formatFileSize(file.size)}</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDate(file.modified)}
                          </span>
                          <span className="truncate">{file.relative_path}</span>
                        </div>
                      </div>

                      <div className="flex-shrink-0">
                        {isSelected && (
                          <CheckCircle className="w-5 h-5 text-primary" />
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DocumentsView;
