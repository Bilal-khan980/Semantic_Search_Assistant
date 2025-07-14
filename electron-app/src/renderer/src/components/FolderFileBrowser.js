import React, { useState, useEffect } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import {
  Folder,
  File,
  FileText,
  FileImage,
  X,
  Search,
  Check,
  RefreshCw,
  Eye,
  Download,
} from "lucide-react";

const FolderFileBrowser = ({
  isOpen,
  onClose,
  onFileSelect,
  showProcessOption = false,
  onProcessFiles,
}) => {
  const [connectedFolders, setConnectedFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [folderFiles, setFolderFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [fileFilter, setFileFilter] = useState("all");

  useEffect(() => {
    if (isOpen) {
      loadConnectedFolders();
    }
  }, [isOpen]);

  const loadConnectedFolders = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get("http://127.0.0.1:8000/folders/list");
      setConnectedFolders(response.data.connected_folders || []);
    } catch (error) {
      console.error("Failed to load folders:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadFolderFiles = async (folderPath) => {
    try {
      setIsLoading(true);
      setSelectedFolder(folderPath);

      // Get files from the folder by scanning it
      const response = await axios.post("http://127.0.0.1:8000/folders/scan", {
        folder_path: folderPath,
      });

      setFolderFiles(response.data.files || []);
    } catch (error) {
      console.error("Failed to load folder files:", error);
      // Fallback: try to get processed files info
      try {
        const statsResponse = await axios.get(
          "http://127.0.0.1:8000/folders/list"
        );
        const folderStats = statsResponse.data.stats?.folders?.find(
          (f) => f.path === folderPath
        );
        if (folderStats) {
          // Create mock file list from stats (this is a fallback)
          setFolderFiles([]);
        }
      } catch (fallbackError) {
        console.error("Fallback failed:", fallbackError);
        setFolderFiles([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getFileIcon = (fileName) => {
    const extension = fileName.split(".").pop()?.toLowerCase();
    switch (extension) {
      case "pdf":
        return <FileText className="w-5 h-5 text-red-500" />;
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

  const handleSelectFiles = () => {
    if (selectedFiles.length > 0) {
      onFileSelect(selectedFiles);
      onClose();
    }
  };

  const handleProcessFiles = () => {
    if (selectedFiles.length > 0 && onProcessFiles) {
      onProcessFiles(selectedFiles);
      onClose();
    }
  };

  const filteredFiles = folderFiles.filter((file) => {
    const matchesSearch = file.name
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesFilter =
      fileFilter === "all" || file.extension === `.${fileFilter}`;
    return matchesSearch && matchesFilter;
  });

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white rounded-lg shadow-xl w-4/5 h-4/5 max-w-6xl max-h-4xl flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-xl font-semibold">Browse Folder Files</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-1 overflow-hidden">
            {/* Sidebar - Folders */}
            <div className="w-1/3 border-r bg-gray-50 p-4">
              <h3 className="font-medium mb-3">Connected Folders</h3>
              {isLoading && !selectedFolder ? (
                <div className="flex items-center gap-2 text-gray-500">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Loading folders...
                </div>
              ) : (
                <div className="space-y-2">
                  {connectedFolders.map((folder, index) => (
                    <button
                      key={index}
                      onClick={() => loadFolderFiles(folder)}
                      className={`w-full text-left p-3 rounded-md hover:bg-white transition-colors ${
                        selectedFolder === folder
                          ? "bg-blue-100 border border-blue-300"
                          : "bg-white"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <Folder className="w-4 h-4 text-blue-600" />
                        <span className="text-sm truncate" title={folder}>
                          {folder.split("\\").pop() || folder.split("/").pop()}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1 truncate">
                        {folder}
                      </div>
                    </button>
                  ))}
                  {connectedFolders.length === 0 && (
                    <div className="text-gray-500 text-sm">
                      No folders connected. Add folders in the Folders tab.
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Main content - Files */}
            <div className="flex-1 flex flex-col">
              {selectedFolder ? (
                <>
                  {/* Search and filters */}
                  <div className="p-4 border-b bg-gray-50">
                    <div className="flex gap-4 items-center">
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
                  </div>

                  {/* File list */}
                  <div className="flex-1 overflow-auto p-4">
                    {isLoading ? (
                      <div className="flex items-center justify-center h-32">
                        <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
                        <span className="ml-2 text-gray-500">
                          Loading files...
                        </span>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 gap-2">
                        {filteredFiles.map((file, index) => {
                          const isSelected = selectedFiles.some(
                            (f) => f.path === file.path
                          );
                          return (
                            <div
                              key={index}
                              onClick={() => toggleFileSelection(file)}
                              className={`p-3 border rounded-md cursor-pointer hover:bg-gray-50 transition-colors ${
                                isSelected
                                  ? "bg-blue-50 border-blue-300"
                                  : "border-gray-200"
                              }`}
                            >
                              <div className="flex items-center gap-3">
                                <div className="flex-shrink-0">
                                  {isSelected && (
                                    <div className="absolute -mt-1 -ml-1 w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                                      <Check className="w-3 h-3 text-white" />
                                    </div>
                                  )}
                                  {getFileIcon(file.name)}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium text-sm truncate">
                                    {file.name}
                                  </div>
                                  <div className="text-xs text-gray-500 flex gap-4">
                                    <span>{formatFileSize(file.size)}</span>
                                    <span>{formatDate(file.modified)}</span>
                                    {file.needs_processing && (
                                      <span className="text-orange-600">
                                        Needs Processing
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                        {filteredFiles.length === 0 && (
                          <div className="text-center py-8 text-gray-500">
                            {searchQuery || fileFilter !== "all"
                              ? "No files match your search criteria"
                              : "No files found in this folder"}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="p-4 border-t bg-gray-50 flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                      {selectedFiles.length} file(s) selected
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={onClose}
                        className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-md"
                      >
                        Cancel
                      </button>
                      {showProcessOption && onProcessFiles && (
                        <button
                          onClick={handleProcessFiles}
                          disabled={selectedFiles.length === 0}
                          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Process Files ({selectedFiles.length})
                        </button>
                      )}
                      <button
                        onClick={handleSelectFiles}
                        disabled={selectedFiles.length === 0}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Select Files ({selectedFiles.length})
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Folder className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                    <p>Select a folder to browse its files</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default FolderFileBrowser;
