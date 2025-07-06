"use client"

import { useState } from "react"
import { cn } from "../utils/cn"
import { Upload, Download, CheckCircle, AlertCircle, Clock } from "lucide-react"

export function ReadwiseImporter({ onImport, stats, processingTasks }) {
  const [importData, setImportData] = useState("")
  const [isValidFormat, setIsValidFormat] = useState(null)

  const validateReadwiseFormat = (content) => {
    if (!content.trim()) return null

    // Check for common Readwise export patterns
    const indicators = [
      /^## .+/m, // Book titles
      /> .+/m, // Blockquoted highlights
      /Author: .+/m, // Author information
    ]

    let matches = 0
    indicators.forEach((pattern) => {
      if (pattern.test(content)) matches++
    })

    return matches >= 2
  }

  const handleContentChange = (e) => {
    const content = e.target.value
    setImportData(content)
    setIsValidFormat(validateReadwiseFormat(content))
  }

  const handleImport = async () => {
    if (!importData.trim()) return

    await onImport(importData)
    setImportData("")
    setIsValidFormat(null)
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Readwise Import</h1>
        <p className="text-gray-600">Import your highlights and annotations from Readwise</p>
      </div>

      {/* Instructions */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold flex items-center">
            <Download className="w-5 h-5 mr-2" />
            How to Export from Readwise
          </h2>
        </div>
        <div className="card-content">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800">
              <li>
                Go to <strong>readwise.io/export</strong>
              </li>
              <li>
                Select <strong>"Markdown"</strong> format
              </li>
              <li>Choose your export options (all highlights recommended)</li>
              <li>Download the export file</li>
              <li>Copy and paste the content below</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Import Area */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold flex items-center">
            <Upload className="w-5 h-5 mr-2" />
            Import Highlights
          </h2>
        </div>
        <div className="card-content space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Paste Readwise Markdown Export:</label>
            <textarea
              value={importData}
              onChange={handleContentChange}
              placeholder="Paste your Readwise markdown export here..."
              rows={12}
              className="w-full p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Format Validation */}
          {isValidFormat !== null && (
            <div
              className={cn(
                "flex items-center space-x-2 p-3 rounded-lg",
                isValidFormat
                  ? "bg-green-50 border border-green-200 text-green-800"
                  : "bg-red-50 border border-red-200 text-red-800",
              )}
            >
              {isValidFormat ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-600" />
              )}
              <span className="text-sm font-medium">
                {isValidFormat
                  ? "Valid Readwise format detected"
                  : "This doesn't appear to be a Readwise export. Please check the format."}
              </span>
            </div>
          )}

          <button
            onClick={handleImport}
            disabled={!importData.trim() || isValidFormat === false}
            className="btn-primary w-full disabled:opacity-50"
          >
            <Upload className="w-4 h-4 mr-2" />
            Import Highlights
          </button>
        </div>
      </div>

      {/* Processing Tasks */}
      {processingTasks.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Import Status</h3>
          </div>
          <div className="card-content">
            <div className="space-y-4">
              {processingTasks.map((task) => (
                <div key={task.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      {getTaskStatusIcon(task.status)}
                      <span className="font-medium">Readwise Import</span>
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
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-content text-center py-6">
            <div className="text-3xl font-bold text-blue-600 mb-2">{stats.readwise_highlights}</div>
            <div className="text-sm text-gray-600">Readwise Highlights</div>
          </div>
        </div>

        <div className="card">
          <div className="card-content text-center py-6">
            <div className="text-3xl font-bold text-purple-600 mb-2">{stats.total_chunks}</div>
            <div className="text-sm text-gray-600">Total Searchable Items</div>
          </div>
        </div>
      </div>

      {/* Sample Format */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Expected Format Example</h3>
        </div>
        <div className="card-content">
          <pre className="bg-gray-50 p-4 rounded-lg text-sm font-mono overflow-x-auto">
            {`## Deep Work - Cal Newport

> The ability to focus without distraction on a cognitively demanding task is becoming increasingly valuable—and increasingly rare.

Author: Cal Newport
Tags: productivity, focus, deep-work

> Human beings, it seems, are at their best when immersed deeply in something challenging.

Note: This resonates with the concept of flow state`}
          </pre>
        </div>
      </div>

      {/* Help */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 className="font-semibold text-yellow-900 mb-2">Import Tips</h3>
        <div className="text-sm text-yellow-800 space-y-1">
          <p>• Make sure to export in Markdown format from Readwise</p>
          <p>• Include all your highlights for the best search experience</p>
          <p>• Personal notes and tags will be preserved and searchable</p>
          <p>• Large imports may take a few minutes to process</p>
        </div>
      </div>
    </div>
  )
}
