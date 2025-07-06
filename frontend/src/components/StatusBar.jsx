"use client"

import { Wifi, WifiOff, AlertCircle, Activity } from "lucide-react"
import { cn } from "../utils/cn"

export function StatusBar({ apiStatus, stats, processingTasks }) {
  const getStatusColor = () => {
    switch (apiStatus) {
      case "connected":
        return "text-green-600"
      case "disconnected":
        return "text-red-600"
      case "error":
        return "text-yellow-600"
      default:
        return "text-gray-400"
    }
  }

  const getStatusIcon = () => {
    switch (apiStatus) {
      case "connected":
        return <Wifi className="w-4 h-4" />
      case "disconnected":
        return <WifiOff className="w-4 h-4" />
      case "error":
        return <AlertCircle className="w-4 h-4" />
      default:
        return <WifiOff className="w-4 h-4" />
    }
  }

  const activeProcessingTasks = processingTasks.filter((t) => t.status === "processing")

  return (
    <div className="bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between text-sm">
      <div className="flex items-center space-x-6">
        {/* API Status */}
        <div className={cn("flex items-center space-x-2", getStatusColor())}>
          {getStatusIcon()}
          <span>
            API {apiStatus === "connected" ? "Connected" : apiStatus === "disconnected" ? "Disconnected" : "Error"}
          </span>
        </div>

        {/* Processing Status */}
        {activeProcessingTasks.length > 0 && (
          <div className="flex items-center space-x-2 text-blue-600">
            <Activity className="w-4 h-4 animate-pulse" />
            <span>
              Processing {activeProcessingTasks.length} task{activeProcessingTasks.length > 1 ? "s" : ""}
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center space-x-6 text-gray-500">
        {/* Stats */}
        <span>{stats.total_chunks} chunks indexed</span>
        <span>{stats.unique_sources} sources</span>

        {/* Version */}
        <span>v1.0.0</span>
      </div>
    </div>
  )
}
