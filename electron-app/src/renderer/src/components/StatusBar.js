import React from 'react';
import { Database, Activity, Clock, Zap } from 'lucide-react';
import { cn } from '../utils/cn';

function StatusBar({ isBackendReady, stats, currentView }) {
  return (
    <div className="h-6 bg-muted/30 border-t border-border flex items-center justify-between px-4 text-xs">
      {/* Left side - Status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <div className={cn(
            "w-2 h-2 rounded-full",
            isBackendReady ? "bg-green-500" : "bg-yellow-500 animate-pulse"
          )} />
          <span className="text-muted-foreground">
            {isBackendReady ? 'Ready' : 'Starting...'}
          </span>
        </div>
        
        <div className="flex items-center gap-1">
          <Database className="w-3 h-3 text-muted-foreground" />
          <span className="text-muted-foreground">
            {stats.totalChunks} chunks
          </span>
        </div>
        
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3 text-muted-foreground" />
          <span className="text-muted-foreground">
            {stats.totalDocuments} docs
          </span>
        </div>
      </div>

      {/* Right side - Current view and shortcuts */}
      <div className="flex items-center gap-4">
        <span className="text-muted-foreground capitalize">
          {currentView}
        </span>
        
        <div className="flex items-center gap-2 text-muted-foreground">
          <kbd className="px-1 py-0.5 bg-muted rounded text-2xs">Ctrl+K</kbd>
          <span>Search</span>
        </div>
        
        <div className="flex items-center gap-2 text-muted-foreground">
          <kbd className="px-1 py-0.5 bg-muted rounded text-2xs">Ctrl+Shift+F</kbd>
          <span>Float</span>
        </div>
      </div>
    </div>
  );
}

export default StatusBar;
