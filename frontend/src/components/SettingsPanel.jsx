"use client"

import { useState } from "react"
import { Database, Zap, Shield, RefreshCw } from "lucide-react"

export function SettingsPanel({ stats, onRefreshStats }) {
  const [apiUrl, setApiUrl] = useState("http://127.0.0.1:8000")
  const [searchSettings, setSearchSettings] = useState({
    maxResults: 20,
    similarityThreshold: 0.3,
    enableSuggestions: true,
  })

  const handleRefreshStats = () => {
    onRefreshStats()
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">Configure your local document search application</p>
      </div>

      {/* API Configuration */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold flex items-center">
            <Database className="w-5 h-5 mr-2" />
            API Configuration
          </h2>
        </div>
        <div className="card-content space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">API Server URL</label>
            <input
              type="url"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="input w-full"
              placeholder="http://127.0.0.1:8000"
            />
            <p className="text-sm text-gray-500 mt-1">URL of your local Python API server</p>
          </div>

          <button className="btn-secondary">Test Connection</button>
        </div>
      </div>

      {/* Search Settings */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold flex items-center">
            <Zap className="w-5 h-5 mr-2" />
            Search Settings
          </h2>
        </div>
        <div className="card-content space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Max Results</label>
              <input
                type="number"
                value={searchSettings.maxResults}
                onChange={(e) =>
                  setSearchSettings((prev) => ({
                    ...prev,
                    maxResults: Number.parseInt(e.target.value),
                  }))
                }
                className="input w-full"
                min="5"
                max="100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Similarity Threshold</label>
              <input
                type="number"
                step="0.1"
                value={searchSettings.similarityThreshold}
                onChange={(e) =>
                  setSearchSettings((prev) => ({
                    ...prev,
                    similarityThreshold: Number.parseFloat(e.target.value),
                  }))
                }
                className="input w-full"
                min="0.1"
                max="1.0"
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="enable-suggestions"
              checked={searchSettings.enableSuggestions}
              onChange={(e) =>
                setSearchSettings((prev) => ({
                  ...prev,
                  enableSuggestions: e.target.checked,
                }))
              }
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="enable-suggestions" className="text-sm text-gray-700">
              Enable search suggestions
            </label>
          </div>
        </div>
      </div>

      {/* Privacy & Security */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold flex items-center">
            <Shield className="w-5 h-5 mr-2" />
            Privacy & Security
          </h2>
        </div>
        <div className="card-content">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Shield className="w-5 h-5 text-green-600" />
              <span className="font-medium text-green-900">Local-First Processing</span>
            </div>
            <ul className="text-sm text-green-800 space-y-1">
              <li>• All documents processed locally on your device</li>
              <li>• No data sent to external servers</li>
              <li>• Vector embeddings generated offline</li>
              <li>• Full control over your data</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Database Stats */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Database Statistics</h2>
            <button onClick={handleRefreshStats} className="btn-ghost p-2" title="Refresh stats">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total_chunks}</div>
              <div className="text-sm text-gray-600">Total Chunks</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.document_chunks}</div>
              <div className="text-sm text-gray-600">Documents</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.readwise_highlights}</div>
              <div className="text-sm text-gray-600">Highlights</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.unique_sources}</div>
              <div className="text-sm text-gray-600">Sources</div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              <p>
                <strong>Embedding Model:</strong> {stats.embedding_model || "sentence-transformers/all-MiniLM-L6-v2"}
              </p>
              <p>
                <strong>Embedding Dimension:</strong> {stats.embedding_dimension || 384}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold">Database Actions</h2>
        </div>
        <div className="card-content">
          <div className="flex space-x-4">
            <button className="btn-secondary">Export Settings</button>
            <button className="btn-secondary">Clear All Data</button>
            <button className="btn-secondary">Backup Database</button>
          </div>
          <p className="text-sm text-gray-500 mt-2">Use these actions carefully. Clearing data cannot be undone.</p>
        </div>
      </div>
    </div>
  )
}
