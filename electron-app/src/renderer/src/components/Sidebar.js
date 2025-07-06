import React from "react";
import { motion } from "framer-motion";
import {
  Search,
  FileText,
  FolderOpen,
  Bookmark,
  Settings,
  Database,
  Activity,
  Zap,
} from "lucide-react";
import { cn } from "../utils/cn";

function Sidebar({ currentView, onViewChange, stats, isBackendReady }) {
  const menuItems = [
    {
      id: "search",
      label: "Search",
      icon: Search,
      description: "Find documents and highlights",
    },
    {
      id: "documents",
      label: "Documents",
      icon: FileText,
      description: "Browse and process documents from folders",
      badge: stats.totalDocuments,
    },
    {
      id: "folders",
      label: "Folders",
      icon: FolderOpen,
      description: "Manage connected document folders",
    },
    {
      id: "readwise",
      label: "Readwise",
      icon: Bookmark,
      description: "Import and manage highlights",
      badge: stats.readwiseHighlights,
    },
    {
      id: "settings",
      label: "Settings",
      icon: Settings,
      description: "Configure the application",
    },
  ];

  return (
    <div className="w-64 bg-muted/30 border-r border-border flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Zap className="w-4 h-4 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-semibold text-sm">Semantic Search</h1>
            <p className="text-xs text-muted-foreground">Assistant</p>
          </div>
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2 text-xs">
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              isBackendReady ? "bg-green-500" : "bg-yellow-500 animate-pulse"
            )}
          />
          <span className="text-muted-foreground">
            {isBackendReady ? "Ready" : "Starting..."}
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2">
        <div className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;

            return (
              <motion.button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors relative",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted text-muted-foreground hover:text-foreground"
                )}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{item.label}</div>
                  <div className="text-xs opacity-75 truncate">
                    {item.description}
                  </div>
                </div>
                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded-full text-xs font-medium",
                      isActive
                        ? "bg-primary-foreground/20 text-primary-foreground"
                        : "bg-primary text-primary-foreground"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </motion.button>
            );
          })}
        </div>
      </nav>

      {/* Stats */}
      <div className="p-4 border-t border-border">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-muted-foreground" />
            <div className="flex-1">
              <div className="text-sm font-medium">{stats.totalChunks}</div>
              <div className="text-xs text-muted-foreground">Text chunks</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-muted-foreground" />
            <div className="flex-1">
              <div className="text-sm font-medium">
                {stats.totalDocuments + stats.readwiseHighlights}
              </div>
              <div className="text-xs text-muted-foreground">Total items</div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-4 border-t border-border">
        <div className="space-y-2">
          <button
            onClick={() => {
              if (window.electronAPI) {
                window.electronAPI.toggleFloatingWindow();
              }
            }}
            className="w-full btn btn-secondary btn-sm"
            disabled={!isBackendReady}
          >
            <Zap className="w-4 h-4 mr-2" />
            Floating Window
          </button>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
