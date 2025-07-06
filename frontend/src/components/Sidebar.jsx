"use client"
import { cn } from "../utils/cn"
import { Wifi, WifiOff, AlertCircle, Activity } from 'lucide-react'

export function Sidebar({ items, activeItem, onItemSelect, stats, apiStatus, processingTasks }) {
  const getStatusIcon = () => {
    switch (apiStatus) {
      case "connected":
        return <Wifi className="w-4 h-4 text-green-500" />
      case "disconnected":
        return <WifiOff className="w-4 h-4 text-red-500" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
      default:
        return <WifiOff className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusText = () => {
    switch (apiStatus) {
      case "connected":
        return "Connected"
      case "disconnected":
        return "Disconnected"
      case "error":
        return "Error"
      default:
        return "Unknown"
    }
  }

  const activeProcessingTasks = processingTasks.filter((t) => t.status === "processing")

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {items.map((item) => {
          const Icon = item.icon
          const isActive = activeItem === item.id

          return (
            <button
              key={item.id}
              onClick={() => onItemSelect(item.id)}
              className={cn(
                "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive ? "bg-primary-100 text-primary-700" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
              )}
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </div>

              {item.badge && (
                <span
                  className={cn(
                    "px-2 py-0.5 text-xs rounded-full",
                    isActive ? "bg-primary-200 text-primary-800" : "bg-gray-200 text-gray-700",
                  )}
                >
                  {item.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Processing Tasks */}
      {activeProcessingTasks.length > 0 && (
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center space-x-2 mb-3">
            <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
            <span className="text-sm font-medium text-gray-700">Processing</span>
          </div>

          <div className="space-y-2">
            {activeProcessingTasks.slice(0, 3).map((task) => (
              <div key={task.id} className="bg-blue-50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-blue-700">
                    {task.type === "readwise" ? "Readwise Import" : "Documents"}
                  </span>
                  <span className="text-xs text-blue-600">{Math.round(task.progress)}%</span>
                </div>

                <div className="w-full bg-blue-200 rounded-full h-1.5 mb-2">
                  <div
                    className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${task.progress}%` }}
                  />
                </div>

                <p className="text-xs text-blue-600 truncate">{task.message}</p>
              </div>
            ))}

            {activeProcessingTasks.length > 3 && (
              <p className="text-xs text-gray-500 text-center">+{activeProcessingTasks.length - 3} more tasks</p>
            )}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="p-4 border-t border-gray-200 space-y-3">
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-lg font-semibold text-gray-900">{stats.document_chunks}</div>
            <div className="text-xs text-gray-500">Documents</div>
          </div>

          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-lg font-semibold text-gray-900">{stats.readwise_highlights}</div>
            <div className="text-xs text-gray-500">Highlights</div>
          </div>
        </div>

        <div className="text-center">
          <div className="text-sm font-medium text-gray-700">{stats.total_chunks} Total Chunks</div>
          <div className="text-xs text-gray-500">{stats.unique_sources} Sources</div>
        </div>
      </div>

      {/* API Status */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="text-sm text-gray-600">API {getStatusText()}</span>
        </div>
      </div>
    </div>
  )
}
