import { AnimatePresence, motion } from 'framer-motion';
import {
    Bookmark,
    FileText,
    Lightbulb,
    Minimize2,
    Search,
    X
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';

// Services
import clipboardService from '../services/ClipboardService';
import ApiService from './services/ApiService';

// Components

// Utils
import { cn } from './utils/cn';

function FloatingApp() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Context-aware features
  const [contextualSuggestions, setContextualSuggestions] = useState([]);
  const [currentContext, setCurrentContext] = useState('');
  const [activeTab, setActiveTab] = useState('context'); // 'context', 'search', 'canvas'
  const [canvasItems, setCanvasItems] = useState([]);
  const [clipboardHistory, setClipboardHistory] = useState([]);
  const [isContextMonitoring, setIsContextMonitoring] = useState(true);

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
    setupGlobalShortcutListeners();

    // Focus search input on mount
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }

    return () => {
      cleanupEventListeners();
    };
  }, []);

  const setupGlobalShortcutListeners = () => {
    if (window.electronAPI) {
      // Listen for global shortcut events from main process
      window.electronAPI.onFocusSearch(() => {
        if (searchInputRef.current) {
          searchInputRef.current.focus();
          searchInputRef.current.select();
        }
      });

      window.electronAPI.onQuickSearchClipboard(async () => {
        try {
          const clipboardText = await window.electronAPI.readFromClipboard();
          if (clipboardText && clipboardText.trim()) {
            setSearchQuery(clipboardText.trim());
            await handleSearch(clipboardText.trim());
            setActiveTab('search');
          }
        } catch (error) {
          console.error('Error with quick clipboard search:', error);
        }
      });

      window.electronAPI.onToggleCanvas(() => {
        setActiveTab('canvas');
      });

      window.electronAPI.onAddSelectionToCanvas(async () => {
        try {
          const clipboardText = await window.electronAPI.readFromClipboard();
          if (clipboardText && clipboardText.trim()) {
            const newItem = {
              id: Date.now().toString(),
              content: clipboardText.trim(),
              source: 'Clipboard Selection',
              addedAt: Date.now(),
              position: { x: Math.random() * 300, y: Math.random() * 200 }
            };
            addToCanvas(newItem);
            setActiveTab('canvas');
          }
        } catch (error) {
          console.error('Error adding selection to canvas:', error);
        }
      });

      window.electronAPI.onShowContextSuggestions(() => {
        setActiveTab('context');
        if (isContextMonitoring && contextualSuggestions.length === 0) {
          // Trigger context analysis
          if (clipboardService) {
            clipboardService.getContextualSuggestions().then(suggestions => {
              setContextualSuggestions(suggestions);
            });
          }
        }
      });
    }
  };

  const initializeFloatingApp = async () => {
    try {
      await checkBackendStatus();
      await initializeContextMonitoring();
      loadCanvasItems();
    } catch (error) {
      console.error('Failed to initialize floating app:', error);
    }
  };

  const initializeContextMonitoring = async () => {
    try {
      // Initialize clipboard service with search capability
      const searchService = {
        search: async (query, limit = 5) => {
          try {
            const results = await apiService.search(query, limit, 0.3);
            return results.results || [];
          } catch (error) {
            console.error('Search error:', error);
            return [];
          }
        }
      };

      clipboardService.initialize(searchService);

      if (isContextMonitoring) {
        clipboardService.startMonitoring();
      }

      // Listen for clipboard context changes
      clipboardService.onClipboardContext(handleClipboardContext);

      // Load initial clipboard history
      setClipboardHistory(clipboardService.getHistory());

      console.log('✅ Context monitoring initialized');
    } catch (error) {
      console.error('❌ Failed to initialize context monitoring:', error);
    }
  };

  const handleClipboardContext = (clipboardEvent) => {
    console.log('📋 Context changed:', clipboardEvent);

    setCurrentContext(clipboardEvent.content);
    setContextualSuggestions(clipboardEvent.suggestions || []);
    setClipboardHistory(clipboardService.getHistory());

    // Auto-switch to context tab when relevant suggestions are found
    if (clipboardEvent.suggestions && clipboardEvent.suggestions.length > 0) {
      setActiveTab('context');
    }
  };

  const loadCanvasItems = () => {
    try {
      const saved = localStorage.getItem('canvasItems');
      if (saved) {
        setCanvasItems(JSON.parse(saved));
      }
    } catch (error) {
      console.warn('Failed to load canvas items:', error);
    }
  };

  const saveCanvasItems = (items) => {
    try {
      localStorage.setItem('canvasItems', JSON.stringify(items));
    } catch (error) {
      console.warn('Failed to save canvas items:', error);
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
    // Cleanup context monitoring
    if (clipboardService) {
      clipboardService.stopMonitoring();
    }
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

  // Enhanced drag and drop functionality
  const handleDragStart = (item, event) => {
    console.log('🎯 Starting drag operation for:', item);

    setIsDragging(true);

    // Prepare rich drag data with citation
    const dragData = {
      type: 'text',
      content: item.content,
      metadata: {
        source: item.source || 'Semantic Search Assistant',
        title: item.title || '',
        author: item.author || '',
        page: item.page || '',
        similarity: item.similarity || 0,
        timestamp: Date.now(),
        highlight_color: item.highlight_color || '',
        readwise_id: item.readwise_id || ''
      }
    };

    // Set drag effect
    event.dataTransfer.effectAllowed = 'copy';

    // Set multiple data formats for cross-application compatibility
    const plainText = item.content;
    const richText = formatAsRichText(item);
    const htmlContent = formatAsHTML(item);

    event.dataTransfer.setData('text/plain', plainText);
    event.dataTransfer.setData('text/html', htmlContent);
    event.dataTransfer.setData('text/rtf', richText);
    event.dataTransfer.setData('application/json', JSON.stringify(dragData));

    // Use Electron's enhanced drag functionality
    if (window.electronAPI && window.electronAPI.startDrag) {
      window.electronAPI.startDrag(dragData);
    }

    // Visual feedback
    event.target.style.opacity = '0.6';
    event.target.style.transform = 'scale(0.95)';
  };

  const handleDragEnd = (event) => {
    setIsDragging(false);
    event.target.style.opacity = '1';
    event.target.style.transform = 'scale(1)';
  };

  const formatAsRichText = (item) => {
    // Create RTF format for rich text applications
    const content = item.content.replace(/\n/g, '\\par ');
    const source = item.source || 'Unknown';
    const author = item.author || '';
    const title = item.title || '';

    let rtf = '{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}';
    rtf += '\\f0\\fs24 ';
    rtf += content;
    rtf += '\\par\\par';
    rtf += '{\\i Source: ' + source;
    if (title) rtf += ' - ' + title;
    if (author) rtf += ' by ' + author;
    rtf += '}';
    rtf += '}';

    return rtf;
  };

  const formatAsHTML = (item) => {
    // Create rich HTML with proper citation
    const content = item.content.replace(/\n/g, '<br>');

    let html = `<div style="font-family: Arial, sans-serif; line-height: 1.4;">`;
    html += `<div style="margin-bottom: 10px;">${content}</div>`;
    html += `<hr style="border: none; border-top: 1px solid #ccc; margin: 10px 0;">`;
    html += `<div style="font-size: 12px; color: #666;">`;
    html += `<strong>Source:</strong> ${item.source || 'Unknown'}`;
    if (item.title) html += `<br><strong>Title:</strong> ${item.title}`;
    if (item.author) html += `<br><strong>Author:</strong> ${item.author}`;
    if (item.page) html += `<br><strong>Page:</strong> ${item.page}`;
    if (item.highlight_color) html += `<br><strong>Highlight:</strong> ${item.highlight_color}`;
    if (item.similarity) html += `<br><strong>Similarity:</strong> ${(item.similarity * 100).toFixed(1)}%`;
    html += `</div></div>`;

    return html;
  };

  // Canvas functionality
  const addToCanvas = (item) => {
    const canvasItem = {
      id: Date.now().toString(),
      ...item,
      addedAt: Date.now(),
      position: { x: Math.random() * 200, y: Math.random() * 200 }
    };

    const newItems = [...canvasItems, canvasItem];
    setCanvasItems(newItems);
    saveCanvasItems(newItems);

    // Show notification
    if (window.electronAPI && window.electronAPI.showNotification) {
      window.electronAPI.showNotification('Added to Canvas', `"${item.content.substring(0, 50)}..." added to canvas`);
    }
  };

  const removeFromCanvas = (itemId) => {
    const newItems = canvasItems.filter(item => item.id !== itemId);
    setCanvasItems(newItems);
    saveCanvasItems(newItems);
  };

  const clearCanvas = () => {
    setCanvasItems([]);
    saveCanvasItems([]);
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

      {/* Tabs */}
      <div className="flex border-b border-border/50">
        {[
          { id: 'context', label: 'Context', icon: Lightbulb },
          { id: 'search', label: 'Search', icon: Search },
          { id: 'canvas', label: 'Canvas', icon: Bookmark }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex-1 flex items-center justify-center gap-1 py-2 text-xs font-medium transition-colors",
              activeTab === tab.id
                ? "bg-primary/10 text-primary border-b-2 border-primary"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )}
          >
            <tab.icon size={12} />
            <span>{tab.label}</span>
            {tab.id === 'context' && contextualSuggestions.length > 0 && (
              <span className="ml-1 px-1 py-0.5 bg-blue-500 text-white text-2xs rounded-full">
                {contextualSuggestions.length}
              </span>
            )}
            {tab.id === 'canvas' && canvasItems.length > 0 && (
              <span className="ml-1 px-1 py-0.5 bg-green-500 text-white text-2xs rounded-full">
                {canvasItems.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="floating-content">
        <div className="h-full overflow-y-auto custom-scrollbar">
          <AnimatePresence mode="wait">
            {activeTab === 'context' && (
              <ContextTab
                suggestions={contextualSuggestions}
                currentContext={currentContext}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
                onCopy={copyResult}
                onAddToCanvas={addToCanvas}
                isMonitoring={isContextMonitoring}
                onToggleMonitoring={setIsContextMonitoring}
              />
            )}

            {activeTab === 'search' && (
              <SearchTab
                results={searchResults}
                isLoading={isSearching}
                searchQuery={searchQuery}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
                onCopy={copyResult}
                onAddToCanvas={addToCanvas}
                formatSnippet={formatSnippet}
                getSourceIcon={getSourceIcon}
                selectedResult={selectedResult}
                onSelectResult={setSelectedResult}
              />
            )}

            {activeTab === 'canvas' && (
              <CanvasTab
                items={canvasItems}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
                onCopy={copyResult}
                onRemove={removeFromCanvas}
                onClear={clearCanvas}
                onSearch={handleSearch}
                formatSnippet={formatSnippet}
                getSourceIcon={getSourceIcon}
              />
            )}
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

// Context Tab Component
const ContextTab = ({
  suggestions,
  currentContext,
  onDragStart,
  onDragEnd,
  onCopy,
  onAddToCanvas,
  isMonitoring,
  onToggleMonitoring
}) => {
  return (
    <div className="p-2">
      {/* Monitoring Status */}
      <div className="flex items-center justify-between mb-3 p-2 bg-muted/50 rounded-lg">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isMonitoring ? 'bg-green-500' : 'bg-gray-400'}`} />
          <span className="text-xs font-medium">Context Monitoring</span>
        </div>
        <button
          onClick={() => onToggleMonitoring(!isMonitoring)}
          className="p-1 hover:bg-muted rounded"
          title={isMonitoring ? 'Stop monitoring' : 'Start monitoring'}
        >
          {isMonitoring ? <Eye size={12} /> : <EyeOff size={12} />}
        </button>
      </div>

      {/* Current Context */}
      {currentContext && (
        <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-xs font-medium text-blue-800 mb-1">Current Context</div>
          <div className="text-xs text-blue-600">
            {currentContext.substring(0, 100)}...
          </div>
        </div>
      )}

      {/* Contextual Suggestions */}
      {suggestions.length > 0 ? (
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">
            Related to your current work:
          </div>
          {suggestions.map((suggestion, index) => (
            <ResultItem
              key={index}
              result={suggestion}
              onDragStart={onDragStart}
              onDragEnd={onDragEnd}
              onCopy={onCopy}
              onAddToCanvas={onAddToCanvas}
              showRelevance={true}
            />
          ))}
        </div>
      ) : (
        <div className="p-8 text-center text-muted-foreground">
          <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No contextual suggestions</p>
          <p className="text-xs mt-1">
            {isMonitoring ? 'Start writing to see related content' : 'Enable monitoring to see suggestions'}
          </p>
        </div>
      )}
    </div>
  );
};

// Search Tab Component
const SearchTab = ({
  results,
  isLoading,
  searchQuery,
  onDragStart,
  onDragEnd,
  onCopy,
  onAddToCanvas,
  formatSnippet,
  getSourceIcon,
  selectedResult,
  onSelectResult
}) => {
  return (
    <div className="p-2">
      {results.length > 0 ? (
        results.map((result, index) => (
          <ResultItem
            key={result.id || index}
            result={result}
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
            onCopy={onCopy}
            onAddToCanvas={onAddToCanvas}
            formatSnippet={formatSnippet}
            getSourceIcon={getSourceIcon}
            isSelected={selectedResult?.id === result.id}
            onSelect={() => onSelectResult(result)}
            index={index}
          />
        ))
      ) : searchQuery && !isLoading ? (
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
    </div>
  );
};

// Canvas Tab Component
const CanvasTab = ({
  items,
  onDragStart,
  onDragEnd,
  onCopy,
  onRemove,
  onClear,
  onSearch,
  formatSnippet,
  getSourceIcon
}) => {
  const [canvasItems, setCanvasItems] = useState(items);

  // Update canvas items when props change
  useEffect(() => {
    setCanvasItems(items);
  }, [items]);

  const handleUpdateItem = (itemId, updates) => {
    const updatedItems = canvasItems.map(item =>
      item.id === itemId ? { ...item, ...updates } : item
    );
    setCanvasItems(updatedItems);
    // Save to localStorage or backend
    try {
      localStorage.setItem('canvasItems', JSON.stringify(updatedItems));
    } catch (error) {
      console.warn('Failed to save canvas items:', error);
    }
  };

  const handleAddItem = (newItem) => {
    const itemWithId = {
      ...newItem,
      id: newItem.id || Date.now().toString(),
      position: newItem.position || { x: Math.random() * 300, y: Math.random() * 200 }
    };
    const updatedItems = [...canvasItems, itemWithId];
    setCanvasItems(updatedItems);
    try {
      localStorage.setItem('canvasItems', JSON.stringify(updatedItems));
    } catch (error) {
      console.warn('Failed to save canvas items:', error);
    }
  };

  const handleSearchRelated = async (query) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          limit: 10,
          similarity_threshold: 0.3
        })
      });
      const data = await response.json();
      return data.results || [];
    } catch (error) {
      console.error('Search error:', error);
      return [];
    }
  };

  return (
    <div className="h-full">
      <Canvas
        items={canvasItems}
        onAddItem={handleAddItem}
        onRemoveItem={onRemove}
        onUpdateItem={handleUpdateItem}
        onClearCanvas={onClear}
        onSearch={handleSearchRelated}
        onDragStart={onDragStart}
        onCopy={onCopy}
        className="h-full"
      />
    </div>
  );
};

// Reusable Result Item Component
const ResultItem = ({
  result,
  onDragStart,
  onDragEnd,
  onCopy,
  onAddToCanvas,
  onRemove,
  onSearch,
  formatSnippet,
  getSourceIcon,
  isSelected = false,
  onSelect,
  index = 0,
  showRelevance = false,
  showCanvasActions = false
}) => {
  const SourceIcon = getSourceIcon ? getSourceIcon(result.source) : FileText;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ delay: index * 0.05 }}
      className={cn(
        "p-3 mb-2 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer group",
        result.is_readwise && "border-l-4 border-l-blue-500",
        isSelected && "bg-primary/10 border-primary"
      )}
      onClick={onSelect}
      draggable
      onDragStart={(e) => onDragStart(result, e)}
      onDragEnd={onDragEnd}
    >
      <div className="flex items-start gap-2">
        <SourceIcon className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-foreground mb-1 truncate">
            {result.title || result.source.split('/').pop()}
          </div>
          <div className="text-xs text-muted-foreground mb-2">
            {formatSnippet ? formatSnippet(result.content) : result.content.substring(0, 150) + '...'}
          </div>

          {/* Relevance explanation for context suggestions */}
          {showRelevance && result.relevanceReason && (
            <div className="text-2xs text-blue-600 mb-2 italic">
              Why relevant: {result.relevanceReason}
            </div>
          )}

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-2xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>Score: {((result.score || result.similarity || 0) * 100).toFixed(0)}%</span>
              {result.is_readwise && (
                <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-2xs">
                  Readwise
                </span>
              )}
              {result.highlight_color && (
                <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded text-2xs">
                  {result.highlight_color}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCopy(result.content);
                }}
                className="p-1 hover:bg-muted rounded"
                title="Copy"
              >
                <Copy className="w-3 h-3" />
              </button>

              {onAddToCanvas && !showCanvasActions && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onAddToCanvas(result);
                  }}
                  className="p-1 hover:bg-muted rounded"
                  title="Add to Canvas"
                >
                  <Plus className="w-3 h-3" />
                </button>
              )}

              {showCanvasActions && onRemove && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove();
                  }}
                  className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded"
                  title="Remove from Canvas"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}

              {showCanvasActions && onSearch && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSearch(result.content.substring(0, 50));
                  }}
                  className="p-1 hover:bg-muted rounded"
                  title="Find Similar"
                >
                  <Search className="w-3 h-3" />
                </button>
              )}

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDragStart(result, e);
                }}
                className="p-1 hover:bg-muted rounded"
                title="Drag to Application"
              >
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default FloatingApp;
