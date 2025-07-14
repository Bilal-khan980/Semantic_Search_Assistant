import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Folder,
  File,
  FileText,
  FilePdf,
  FileImage,
  Search,
  Check,
  RefreshCw,
  Eye,
  Download,
  Plus,
  Trash2,
  FolderOpen,
} from "lucide-react";

const FolderManager = () => {
  const [connectedFolders, setConnectedFolders] = useState([]);
  const [folderStats, setFolderStats] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("info");

  // File browsing state
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [folderFiles, setFolderFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [fileFilter, setFileFilter] = useState("all");
  const [showFiles, setShowFiles] = useState(false);

  useEffect(() => {
    loadFolders();
  }, []);

  const loadFolders = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/folders/list");
      setConnectedFolders(response.data.connected_folders || []);
      setFolderStats(response.data.stats || {});
    } catch (error) {
      console.error("Failed to load folders:", error);
      showMessage("Failed to load connected folders", "error");
    }
  };

  const showMessage = (text, type = "info") => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => setMessage(""), 5000);
  };

  const loadFolderFiles = async (folderPath) => {
    try {
      setIsLoading(true);
      setSelectedFolder(folderPath);

      const response = await axios.post("http://127.0.0.1:8000/folders/scan", {
        folder_path: folderPath,
      });

      setFolderFiles(response.data.files || []);
      setShowFiles(true);
    } catch (error) {
      console.error("Failed to load folder files:", error);
      showMessage("Failed to load folder files", "error");
      setFolderFiles([]);
    } finally {
      setIsLoading(false);
    }
  };

  const getFileIcon = (fileName) => {
    const extension = fileName.split(".").pop()?.toLowerCase();
    switch (extension) {
      case "pdf":
        return <FilePdf className="w-5 h-5 text-red-500" />;
      case "docx":
      case "doc":
        return <FileText className="w-5 h-5 text-blue-500" />;
      case "md":
      case "txt":
        return <FileText className="w-5 h-5 text-gray-500" />;
      case "jpg":
      case "jpeg":
      case "png":
      case "gif":
        return <FileImage className="w-5 h-5 text-green-500" />;
      default:
        return <File className="w-5 h-5 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleDateString();
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

  const selectFolder = async () => {
    try {
      // Use Electron's dialog to select folder
      const result = await window.electronAPI.selectFolder();

      if (result && !result.canceled && result.filePaths.length > 0) {
        const folderPath = result.filePaths[0];
        await addFolder(folderPath);
      }
    } catch (error) {
      console.error("Failed to select folder:", error);
      showMessage("Failed to select folder", "error");
    }
  };

  const addFolder = async (folderPath) => {
    setIsLoading(true);
    try {
      const response = await axios.post("http://127.0.0.1:8000/folders/add", {
        folder_path: folderPath,
      });

      showMessage(
        `Added folder: ${folderPath} (${response.data.documents_found} documents found)`,
        "success"
      );

      await loadFolders();
    } catch (error) {
      console.error("Failed to add folder:", error);
      const errorMsg = error.response?.data?.detail || "Failed to add folder";
      showMessage(errorMsg, "error");
    } finally {
      setIsLoading(false);
    }
  };

  const removeFolder = async (folderPath) => {
    if (!window.confirm(`Remove folder "${folderPath}" from monitoring?`)) {
      return;
    }

    setIsLoading(true);
    try {
      await axios.post("http://127.0.0.1:8000/folders/remove", {
        folder_path: folderPath,
      });

      showMessage(`Removed folder: ${folderPath}`, "success");
      await loadFolders();
    } catch (error) {
      console.error("Failed to remove folder:", error);
      const errorMsg =
        error.response?.data?.detail || "Failed to remove folder";
      showMessage(errorMsg, "error");
    } finally {
      setIsLoading(false);
    }
  };

  const rescanFolders = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post("http://127.0.0.1:8000/folders/rescan");

      showMessage(
        `Rescan complete: ${response.data.new_files} new files found`,
        "success"
      );

      await loadFolders();
    } catch (error) {
      console.error("Failed to rescan folders:", error);
      showMessage("Failed to rescan folders", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const reprocessFolder = async (folderPath) => {
    if (!window.confirm(`Reprocess all files in "${folderPath}"?`)) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/folders/reprocess",
        {
          folder_path: folderPath,
        }
      );

      showMessage(
        `Reprocessing queued: ${response.data.files_queued} files`,
        "success"
      );
    } catch (error) {
      console.error("Failed to reprocess folder:", error);
      const errorMsg =
        error.response?.data?.detail || "Failed to reprocess folder";
      showMessage(errorMsg, "error");
    } finally {
      setIsLoading(false);
    }
  };

  const openFolder = async (folderPath) => {
    try {
      await window.electronAPI.openFolder(folderPath);
    } catch (error) {
      console.error("Failed to open folder:", error);
      showMessage("Failed to open folder", "error");
    }
  };

  const filteredFiles = folderFiles.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = fileFilter === 'all' || file.extension === `.${fileFilter}`;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="folder-manager p-6 bg-white rounded-lg shadow-sm h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">
          {showFiles ? 'Browse Files' : 'Document Folders'}
        </h2>
        <div className="flex gap-2">
          {showFiles && (
            <button
              onClick={() => {
                setShowFiles(false);
                setSelectedFolder(null);
                setFolderFiles([]);
                setSelectedFiles([]);
              }}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 flex items-center gap-2"
            >
              <Folder className="w-4 h-4" />
              Back to Folders
            </button>
          )}
          <button
            onClick={selectFolder}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Folder
          </button>
          {!showFiles && (
            <button
              onClick={rescanFolders}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Rescan All
            </button>
          )}
        </div>
      </div>

      {/* Message Display */}
      {message && (
        <div
          className={`mb-4 p-3 rounded-md ${
            messageType === "error"
              ? "bg-red-100 text-red-700 border border-red-200"
              : messageType === "success"
              ? "bg-green-100 text-green-700 border border-green-200"
              : "bg-blue-100 text-blue-700 border border-blue-200"
          }`}
        >
          {message}
        </div>
      )}

      {/* Stats Summary - only show when not browsing files */}
      {!showFiles && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 p-3 rounded-md">
            <div className="text-sm text-gray-600">Connected Folders</div>
            <div className="text-xl font-semibold text-gray-800">
              {folderStats.connected_folders || 0}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-md">
            <div className="text-sm text-gray-600">Total Files</div>
            <div className="text-xl font-semibold text-gray-800">
              {folderStats.total_processed_files || 0}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-md">
            <div className="text-sm text-gray-600">Successful</div>
            <div className="text-xl font-semibold text-green-600">
              {folderStats.successful_files || 0}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded-md">
            <div className="text-sm text-gray-600">Failed</div>
            <div className="text-xl font-semibold text-red-600">
              {folderStats.failed_files || 0}
            </div>
          </div>
        </div>
      )}

      {/* File search and filters - only show when browsing files */}
      {showFiles && (
        <div className="mb-4 flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-md"
            />
          </div>
          <select
            value={fileFilter}
            onChange={(e) => setFileFilter(e.target.value)}
            className="px-3 py-2 border rounded-md"
          >
            <option value="all">All Files</option>
            <option value="pdf">PDF</option>
            <option value="docx">Word</option>
            <option value="md">Markdown</option>
            <option value="txt">Text</option>
          </select>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        {showFiles ? (
          /* File Browser */
          <div className="space-y-2">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-500">Loading files...</span>
              </div>
            ) : (
              <>
                {filteredFiles.map((file, index) => {
                  const isSelected = selectedFiles.some(f => f.path === file.path);
                  return (
                    <div
                      key={index}
                      onClick={() => toggleFileSelection(file)}
                      className={`p-3 border rounded-md cursor-pointer hover:bg-gray-50 transition-colors ${
                        isSelected ? 'bg-blue-50 border-blue-300' : 'border-gray-200'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex-shrink-0 relative">
                          {isSelected && (
                            <div className="absolute -top-1 -left-1 w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                              <Check className="w-3 h-3 text-white" />
                            </div>
                          )}
                          {getFileIcon(file.name)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{file.name}</div>
                          <div className="text-xs text-gray-500 flex gap-4">
                            <span>{formatFileSize(file.size)}</span>
                            <span>{formatDate(file.modified)}</span>
                            {file.needs_processing && (
                              <span className="text-orange-600">Needs Processing</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {filteredFiles.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    {searchQuery || fileFilter !== 'all'
                      ? 'No files match your search criteria'
                      : 'No files found in this folder'
                    }
                  </div>
                )}
              </>
            )}
          </div>
        ) : (
          /* Folder List */
          <div className="space-y-3">
            {connectedFolders.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Folder className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>No folders connected yet</p>
                <p className="text-sm">
                  Click "Add Folder" to connect your document repositories
                </p>
              </div>
            ) : (
          connectedFolders.map((folder, index) => {
            const folderStat =
              folderStats.folders?.find((f) => f.path === folder) || {};
            return (
              <div
                key={index}
                className="border border-gray-200 rounded-md p-4 hover:bg-gray-50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <svg
                        className="w-5 h-5 text-blue-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-5l-2-2H5a2 2 0 00-2 2z"
                        />
                      </svg>
                      <span
                        className="font-medium text-gray-800 truncate"
                        title={folder}
                      >
                        {folder}
                      </span>
                      {!folderStat.exists && (
                        <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded">
                          Not Found
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {folderStat.files_count || 0} files •{" "}
                      {folderStat.successful_files || 0} processed
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => loadFolderFiles(folder)}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                      title="Browse files in this folder"
                    >
                      <FolderOpen className="w-4 h-4 inline mr-1" />
                      Browse Files
                    </button>
                    <button
                      onClick={() => openFolder(folder)}
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="Open folder in file explorer"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                    </button>
                    <button
                      onClick={() => reprocessFolder(folder)}
                      disabled={isLoading}
                      className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded disabled:opacity-50"
                      title="Reprocess folder"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                    </button>
                    <button
                      onClick={() => removeFolder(folder)}
                      disabled={isLoading}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                      title="Remove folder"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {showFiles && (
        <div className="mt-4 p-4 border-t bg-gray-50 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {selectedFiles.length} file(s) selected from {selectedFolder}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                setShowFiles(false);
                setSelectedFolder(null);
                setFolderFiles([]);
                setSelectedFiles([]);
              }}
              className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                if (selectedFiles.length > 0) {
                  console.log('Processing selected files:', selectedFiles);
                  // Here you could trigger processing or show details
                  alert(`Selected ${selectedFiles.length} files for processing`);
                }
              }}
              disabled={selectedFiles.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Process Selected ({selectedFiles.length})
            </button>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span>Processing...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FolderManager;
