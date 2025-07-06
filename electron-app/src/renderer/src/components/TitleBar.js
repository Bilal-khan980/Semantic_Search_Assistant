import React from 'react';
import { Zap, Minimize2, Square, X } from 'lucide-react';
import { cn } from '../utils/cn';

function TitleBar({ isBackendReady, onToggleFloating }) {
  return (
    <div className="h-8 bg-background border-b border-border flex items-center justify-between px-4 select-none drag-handle">
      {/* Left side - App info */}
      <div className="flex items-center gap-2">
        <Zap className="w-4 h-4 text-primary" />
        <span className="text-sm font-medium">Semantic Search Assistant</span>
        <div className={cn(
          "w-2 h-2 rounded-full ml-2",
          isBackendReady ? "bg-green-500" : "bg-yellow-500 animate-pulse"
        )} />
      </div>

      {/* Right side - Window controls */}
      <div className="flex items-center gap-1">
        <button
          onClick={onToggleFloating}
          className="p-1 hover:bg-muted rounded text-xs"
          title="Toggle floating window"
        >
          <Zap className="w-3 h-3" />
        </button>
        <button
          onClick={() => {
            if (window.electronAPI) {
              // Minimize window
            }
          }}
          className="p-1 hover:bg-muted rounded"
          title="Minimize"
        >
          <Minimize2 className="w-3 h-3" />
        </button>
        <button
          onClick={() => {
            if (window.electronAPI) {
              // Maximize/restore window
            }
          }}
          className="p-1 hover:bg-muted rounded"
          title="Maximize"
        >
          <Square className="w-3 h-3" />
        </button>
        <button
          onClick={() => {
            if (window.electronAPI) {
              // Close window
            }
          }}
          className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded"
          title="Close"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}

export default TitleBar;
