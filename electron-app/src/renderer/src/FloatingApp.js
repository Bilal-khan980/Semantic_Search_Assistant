import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useHotkeys } from 'react-hotkeys-hook';
import { 
  Search, 
  X, 
  Minimize2, 
  Copy, 
  ExternalLink,
  FileText,
  Bookmark,
  Clock
} from 'lucide-react';

// Services
import ApiService from './services/ApiService';

// Utils
import { cn } from './utils/cn';

function FloatingApp() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  
  const searchInputRef = useRef(null);
  const apiService = new ApiService();

  // Keyboard shortcuts
  useHotkeys('escape', () => {
    if (selectedResult) {
      setSelectedResult(null);
    } else {
      closeWindow();
    }
  });

  useHotkeys('ctrl+w, cmd+w', (e) => {
    e.preventDefault();
    closeWindow();
  });

  useHotkeys('enter', (e) => {
    if (searchResults.length > 0 && !selectedResult) {
      setSelectedResult(searchResults[0]);
    }
  });

  useHotkeys('ctrl+c, cmd+c', (e) => {
    if (selectedResult) {
      e.preventDefault();
      copyResult(selectedResult.content);
    }
  });

  // Initialize floating app
  useEffect(() => {
    initializeFloatingApp();
    setupEventListeners();
    
    // Focus search input on mount
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }

    return () => {
      cleanupEventListeners();
    };
  }, []);

  const initializeFloatingApp = async () => {
    try {
      await checkBackendStatus();
    } catch (error) {
      console.error('Failed to initialize floating app:', error);
    }
  };

  const setupEventListeners = () => {
    if (window.floatingAPI) {
      window.floatingAPI.onBackendReady(() => {
        setIsBackendReady(true);
      });

      window.floatingAPI.onFocusSearch(() => {
        if (searchInputRef.current) {
          searchInputRef.current.focus();
        }
      });
    }
  };

  const cleanupEventListeners = () => {
    // Cleanup if needed
  };

  const checkBackendStatus = async () => {
    try {
      const response = await apiService.checkHealth();
      setIsBackendReady(response.status === 'healthy');
    } catch (error) {
      console.error('Backend not ready:', error);
      setIsBackendReady(false);
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim() || !isBackendReady) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    setSelectedResult(null);

    try {
      const response = await apiService.search(query, {
        limit: 10,
        similarity_threshold: 0.3
      });
      setSearchResults(response.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleInputChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Debounced search
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      handleSearch(query);
    }, 300);
  };

  const closeWindow = () => {
    if (window.floatingAPI) {
      window.floatingAPI.closeWindow();
    }
  };

  const minimizeWindow = () => {
    if (window.floatingAPI) {
      window.floatingAPI.minimizeWindow();
    }
  };

  const copyResult = async (text) => {
    try {
      if (window.floatingAPI) {
        await window.floatingAPI.copyResult(text);
      }
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const startDrag = (result) => {
    setIsDragging(true);
    if (window.floatingAPI) {
      window.floatingAPI.dragResult({
        type: 'text',
        content: result.content,
        metadata: result.metadata
      });
    }
  };

  const formatSnippet = (content, maxLength = 150) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const getSourceIcon = (source) => {
    if (source.includes('.pdf')) return FileText;
    if (source.includes('readwise')) return Bookmark;
    return FileText;
  };

  return (
    <div className="floating-window h-full">
      {/* Header */}
      <div className="floating-header drag-handle">
        <div className="flex items-center gap-2 flex-1">
          <Search className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium">Search Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={minimizeWindow}
            className="p-1 hover:bg-muted rounded"
            title="Minimize"
          >
            <Minimize2 className="w-3 h-3" />
          </button>
          <button
            onClick={closeWindow}
            className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded"
            title="Close"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="p-3 border-b border-border/50">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={handleInputChange}
            placeholder={isBackendReady ? "Search your documents..." : "Backend starting..."}
            disabled={!isBackendReady}
            className="w-full pl-10 pr-4 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            data-search-input
          />
          {isSearching && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="w-4 h-4 border-2 border-muted border-t-primary rounded-full animate-spin" />
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      <div className="floating-content">
        <div className="h-full overflow-y-auto custom-scrollbar">
          <AnimatePresence>
            {searchResults.length > 0 ? (
              <div className="p-2">
                {searchResults.map((result, index) => {
                  const SourceIcon = getSourceIcon(result.source);
                  return (
                    <motion.div
                      key={result.id || index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ delay: index * 0.05 }}
                      className={cn(
                        "p-3 mb-2 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer group",
                        result.is_readwise && "border-l-4 border-l-blue-500",
                        selectedResult?.id === result.id && "bg-primary/10 border-primary"
                      )}
                      onClick={() => setSelectedResult(result)}
                      draggable
                      onDragStart={() => startDrag(result)}
                    >
                      <div className="flex items-start gap-2">
                        <SourceIcon className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-foreground mb-1 truncate">
                            {result.title || result.source.split('/').pop()}
                          </div>
                          <div className="text-xs text-muted-foreground mb-2">
                            {formatSnippet(result.content)}
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-2xs text-muted-foreground">
                              <Clock className="w-3 h-3" />
                              <span>Score: {(result.score * 100).toFixed(0)}%</span>
                              {result.is_readwise && (
                                <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-2xs">
                                  Readwise
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  copyResult(result.content);
                                }}
                                className="p-1 hover:bg-muted rounded"
                                title="Copy"
                              >
                                <Copy className="w-3 h-3" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  startDrag(result);
                                }}
                                className="p-1 hover:bg-muted rounded"
                                title="Drag"
                              >
                                <ExternalLink className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            ) : searchQuery && !isSearching ? (
              <div className="p-8 text-center text-muted-foreground">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No results found</p>
                <p className="text-xs mt-1">Try different keywords</p>
              </div>
            ) : !searchQuery ? (
              <div className="p-8 text-center text-muted-foreground">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Start typing to search</p>
                <p className="text-xs mt-1">Search across all your documents</p>
              </div>
            ) : null}
          </AnimatePresence>
        </div>
      </div>

      {/* Status */}
      {!isBackendReady && (
        <div className="p-2 bg-muted/50 border-t border-border/50">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
            <span>Connecting to backend...</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default FloatingApp;
