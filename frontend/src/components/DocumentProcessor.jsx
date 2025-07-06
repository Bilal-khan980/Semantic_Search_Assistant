"use client"

import { useState, useRef } from "react"
import { cn } from "../utils/cn"
import { Upload, FileText, Folder, X, CheckCircle, AlertCircle, Clock } from "lucide-react"

export function DocumentProcessor({ onUpload, stats, processingTasks }) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const files = Array.from(e.dataTransfer.files)
      handleFiles(files)
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      handleFiles(files)
    }
  }

  const handleFiles = (files) => {
    const supportedExtensions = [".pdf", ".docx", ".md", ".txt"]
    const validFiles = files.filter((file) => {
      const extension = "." + file.name.split(".").pop().toLowerCase()
      return supportedExtensions.includes(extension)
    })

    if (validFiles.length !== files.length) {
      alert(`Some files were skipped. Supported formats: ${supportedExtensions.join(", ")}`)
    }

    setSelectedFiles((prev) => [...prev, ...validFiles])
  }

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    await onUpload(selectedFiles)
    setSelectedFiles([])
  }

  const selectFiles = async () => {
    if (window.electronAPI) {
      try {
        const filePaths = await window.electronAPI.selectFiles()
        if (filePaths && filePaths.length > 0) {
          // Convert file paths to File objects (simplified for demo)
          const files = filePaths.map((path) => ({
            name: path.split(/[/\\]/).pop(),
            path: path,
            size: 0, // Would need to get actual size
            type: "application/octet-stream",
          }))
          setSelectedFiles((prev) => [...prev, ...files])
        }
      } catch (error) {
        console.error("Error selecting files:", error)
      }
    } else {
      fileInputRef.current?.click()
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const getTaskStatusIcon = (status) => {
    switch (status) {
      case "processing":
        return <Clock className="w-4 h-4 text-blue-500 animate-pulse" />
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Document Processing</h1>
        <p className="text-gray-600">Upload documents to add them to your searchable knowledge base</p>
      </div>

      {/* Upload Area */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold flex items-center">
            <Upload className="w-5 h-5 mr-2" />
            Upload Documents
          </h2>
        </div>
        <div className="card-content">
          <div
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
              dragActive ? "border-primary-500 bg-primary-50" : "border-gray-300 hover:border-gray-400",
            )}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Drop files here or click to browse</h3>
            <p className="text-gray-600 mb-4">Supports PDF, DOCX, Markdown, and text files</p>

            <div className="flex justify-center space-x-4">
              <button onClick={selectFiles} className="btn-primary">
                Choose Files
              </button>

              <button
                onClick={() => {
                  // Would implement folder selection
                  console.log("Select folder")
                }}
                className="btn-secondary"
              >
                <Folder className="w-4 h-4 mr-2" />
                Add Folder
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.md,.txt"
              onChange={handleFileInput}
              className="hidden"
            />
          </div>
        </div>
      </div>

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Selected Files ({selectedFiles.length})</h3>
              <button onClick={handleUpload} className="btn-primary" disabled={selectedFiles.length === 0}>
                Process Files
              </button>
            </div>
          </div>
          <div className="card-content">
            <div className="space-y-2">
              {selectedFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-gray-500" />
                    <div>
                      <p className="font-medium text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-500">{file.size ? formatFileSize(file.size) : "Unknown size"}</p>
                    </div>
                  </div>
                  <button onClick={() => removeFile(index)} className="btn-ghost p-2 text-red-500 hover:bg-red-50">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Processing Tasks */}
      {processingTasks.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Processing Status</h3>
          </div>
          <div className="card-content">
            <div className="space-y-4">
              {processingTasks.map((task) => (
                <div key={task.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      {getTaskStatusIcon(task.status)}
                      <span className="font-medium">{task.files ? `${task.files.length} files` : "Processing"}</span>
                    </div>
                    <span className="text-sm text-gray-500">{Math.round(task.progress)}%</span>
                  </div>

                  {task.status === "processing" && (
                    <div className="mb-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <p className="text-sm text-gray-600">{task.message}</p>

                  {task.files && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500">Files:</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {task.files.slice(0, 3).map((fileName, index) => (
                          <span key={index} className="badge badge-secondary text-xs">
                            {fileName}
                          </span>
                        ))}
                        {task.files.length > 3 && (
                          <span className="badge badge-outline text-xs">+{task.files.length - 3} more</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="card-content text-center py-6">
            <div className="text-3xl font-bold text-blue-600 mb-2">{stats.document_chunks}</div>
            <div className="text-sm text-gray-600">Document Chunks</div>
          </div>
        </div>

        <div className="card">
          <div className="card-content text-center py-6">
            <div className="text-3xl font-bold text-green-600 mb-2">{stats.unique_sources}</div>
            <div className="text-sm text-gray-600">Unique Sources</div>
          </div>
        </div>

        <div className="card">
          <div className="card-content text-center py-6">
            <div className="text-3xl font-bold text-purple-600 mb-2">{stats.total_chunks}</div>
            <div className="text-sm text-gray-600">Total Chunks</div>
          </div>
        </div>
      </div>

      {/* Help */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">Processing Information</h3>
        <div className="text-sm text-blue-800 space-y-1">
          <p>• Documents are processed locally for privacy</p>
          <p>• Text is extracted and split into searchable chunks</p>
          <p>• Vector embeddings are generated for semantic search</p>
          <p>• Processing time depends on document size and complexity</p>
        </div>
      </div>
    </div>
  )
}
