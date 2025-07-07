import { AnimatePresence, motion } from 'framer-motion';
import {
    Bookmark,
    Clock,
    Copy,
    ExternalLink,
    Eye,
    FileText,
    Filter,
    Search,
    Star
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { cn } from '../utils/cn';

function SearchInterface({ 
  searchQuery, 
  searchResults, 
  isSearching, 
  onSearch, 
  isBackendReady 
}) {
  const [localQuery, setLocalQuery] = useState(searchQuery || '');
  const [filters, setFilters] = useState({
    fileType: 'all',
    source: 'all',
    dateRange: 'all',
    minScore: 0.3
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const searchInputRef = useRef(null);
  const debounceRef = useRef(null);
  const dragPreviewRef = useRef(null);

  useEffect(() => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    setLocalQuery(searchQuery || '');
  }, [searchQuery]);

  const handleInputChange = (e) => {
    const query = e.target.value;
    setLocalQuery(query);
    
    // Clear previous debounce
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    // Debounced search
    debounceRef.current = setTimeout(() => {
      if (query.trim()) {
        onSearch(query, filters);
      }
    }, 300);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (localQuery.trim()) {
      onSearch(localQuery, filters);
    }
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    
    if (localQuery.trim()) {
      onSearch(localQuery, newFilters);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      if (window.electronAPI) {
        await window.electronAPI.writeToClipboard(text);
      } else {
        await navigator.clipboard.writeText(text);
      }
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const startDrag = (result) => {
    // Create formatted content with citation
    const citation = formatCitation(result);
    const contentWithCitation = `${result.content}\n\n${citation}`;

    if (window.electronAPI) {
      // Use Electron's native drag-and-drop
      window.electronAPI.startDrag({
        type: 'text',
        content: contentWithCitation,
        metadata: {
          ...result.metadata,
          source: result.source,
          score: result.final_score,
          timestamp: new Date().toISOString(),
          citation: citation
        }
      });
    }
  };

  const formatCitation = (result) => {
    const filename = result.source.split('/').pop();
    const date = new Date(result.created_at * 1000).toLocaleDateString();
    const score = Math.round(result.final_score * 100);

    if (result.is_readwise) {
      return `— From ${filename} (Readwise highlight, ${score}% relevance, ${date})`;
    } else {
      return `— From ${filename} (${score}% relevance, ${date})`;
    }
  };

  const handleDragStart = (e, result) => {
    e.stopPropagation();

    // Create formatted content with citation
    const citation = formatCitation(result);
    const contentWithCitation = `${result.content}\n\n${citation}`;

    // Set drag data for web compatibility
    e.dataTransfer.setData('text/plain', contentWithCitation);
    e.dataTransfer.setData('application/json', JSON.stringify({
      content: result.content,
      citation: citation,
      metadata: result.metadata,
      source: result.source,
      score: result.final_score,
      isReadwise: result.is_readwise
    }));

    // Set drag effect
    e.dataTransfer.effectAllowed = 'copy';

    // Create custom drag preview
    const dragPreview = document.createElement('div');
    dragPreview.className = 'drag-preview';
    dragPreview.innerHTML = `
      <div class="flex items-center space-x-2 bg-primary text-primary-foreground px-3 py-2 rounded-md shadow-lg">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1zM6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
        </svg>
        <span>Dragging content with citation</span>
      </div>
    `;

    document.body.appendChild(dragPreview);
    e.dataTransfer.setDragImage(dragPreview, 0, 0);

    // Clean up drag preview after drag starts
    setTimeout(() => {
      if (document.body.contains(dragPreview)) {
        document.body.removeChild(dragPreview);
      }
    }, 0);
  };

  const formatSnippet = (content, query, maxLength = 200) => {
    if (!content) return '';
    
    // Highlight search terms
    let snippet = content;
    if (query) {
      const terms = query.toLowerCase().split(' ').filter(term => term.length > 2);
      terms.forEach(term => {
        const regex = new RegExp(`(${term})`, 'gi');
        snippet = snippet.replace(regex, '<mark class="highlight">$1</mark>');
      });
    }
    
    if (snippet.length <= maxLength) return snippet;
    return snippet.substring(0, maxLength) + '...';
  };

  const getSourceIcon = (source) => {
    if (source.includes('.pdf')) return FileText;
    if (source.includes('readwise')) return Bookmark;
    if (source.includes('.docx')) return FileText;
    if (source.includes('.md')) return FileText;
    return FileText;
  };

  const getFileTypeFromSource = (source) => {
    const ext = source.split('.').pop().toLowerCase();
    return ext || 'unknown';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Search Header */}
      <div className="p-6 border-b border-border">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              ref={searchInputRef}
              type="text"
              value={localQuery}
              onChange={handleInputChange}
              placeholder={isBackendReady ? "Search your documents and highlights..." : "Backend starting..."}
              disabled={!isBackendReady}
              className="w-full pl-12 pr-12 py-3 bg-background border border-input rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              data-search-input
            />
            {isSearching && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="w-5 h-5 border-2 border-muted border-t-primary rounded-full animate-spin" />
              </div>
            )}
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                "absolute right-12 top-1/2 transform -translate-y-1/2 p-1 rounded hover:bg-muted",
                showFilters && "bg-muted"
              )}
              title="Filters"
            >
              <Filter className="w-4 h-4" />
            </button>
          </div>

          {/* Filters */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted/50 rounded-lg"
              >
                <div>
                  <label className="block text-sm font-medium mb-1">File Type</label>
                  <select
                    value={filters.fileType}
                    onChange={(e) => handleFilterChange('fileType', e.target.value)}
                    className="w-full p-2 border border-input rounded text-sm"
                  >
                    <option value="all">All Types</option>
                    <option value="pdf">PDF</option>
                    <option value="docx">Word</option>
                    <option value="md">Markdown</option>
                    <option value="txt">Text</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Source</label>
                  <select
                    value={filters.source}
                    onChange={(e) => handleFilterChange('source', e.target.value)}
                    className="w-full p-2 border border-input rounded text-sm"
                  >
                    <option value="all">All Sources</option>
                    <option value="documents">Documents</option>
                    <option value="readwise">Readwise</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Date Range</label>
                  <select
                    value={filters.dateRange}
                    onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                    className="w-full p-2 border border-input rounded text-sm"
                  >
                    <option value="all">All Time</option>
                    <option value="week">Past Week</option>
                    <option value="month">Past Month</option>
                    <option value="year">Past Year</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Min Score</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={filters.minScore}
                    onChange={(e) => handleFilterChange('minScore', parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <span className="text-xs text-muted-foreground">{(filters.minScore * 100).toFixed(0)}%</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </form>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto custom-scrollbar">
          <AnimatePresence>
            {searchResults.length > 0 ? (
              <div className="p-4">
                <div className="mb-4 text-sm text-muted-foreground">
                  Found {searchResults.length} results
                  {localQuery && ` for "${localQuery}"`}
                </div>
                
                <div className="space-y-4">
                  {searchResults.map((result, index) => {
                    const SourceIcon = getSourceIcon(result.source);
                    const fileType = getFileTypeFromSource(result.source);
                    
                    return (
                      <motion.div
                        key={result.id || index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ delay: index * 0.05 }}
                        className={cn(
                          "p-4 border border-border rounded-lg hover:border-primary/50 transition-colors group cursor-pointer",
                          result.is_readwise && "border-l-4 border-l-blue-500",
                          selectedResult?.id === result.id && "bg-primary/5 border-primary"
                        )}
                        onClick={() => setSelectedResult(result)}
                        draggable
                        onDragStart={(e) => handleDragStart(e, result)}
                        title="Click to select, drag to copy with citation"
                      >
                        <div className="flex items-start gap-3">
                          <SourceIcon className="w-5 h-5 text-muted-foreground mt-1 flex-shrink-0" />
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between mb-2">
                              <h3 className="font-medium text-foreground truncate">
                                {result.title || result.source.split('/').pop()}
                              </h3>
                              <div className="flex items-center gap-1 ml-2">
                                <Star className="w-4 h-4 text-yellow-500" />
                                <span className="text-sm text-muted-foreground">
                                  {(() => {
                                    const score = result.final_score || result.similarity || 0;
                                    return isNaN(score) ? '0' : (score * 100).toFixed(0);
                                  })()}%
                                </span>
                              </div>
                            </div>
                            
                            <div 
                              className="text-sm text-muted-foreground mb-3 leading-relaxed"
                              dangerouslySetInnerHTML={{
                                __html: formatSnippet(result.content, localQuery)
                              }}
                            />
                            
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                <div className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  <span>{new Date(result.created_at * 1000).toLocaleDateString()}</span>
                                </div>
                                <span className="px-2 py-1 bg-muted rounded text-xs">
                                  {fileType.toUpperCase()}
                                </span>
                                {result.is_readwise && (
                                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                    Readwise
                                  </span>
                                )}
                                {result.highlight_color && (
                                  <div 
                                    className="w-3 h-3 rounded-full border"
                                    style={{ backgroundColor: result.highlight_color }}
                                    title={`${result.highlight_color} highlight`}
                                  />
                                )}
                              </div>
                              
                              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    copyToClipboard(result.content);
                                  }}
                                  className="p-2 hover:bg-muted rounded"
                                  title="Copy content"
                                >
                                  <Copy className="w-4 h-4" />
                                </button>
                                <div
                                  className="p-2 hover:bg-muted rounded cursor-grab active:cursor-grabbing"
                                  title="Drag to other app"
                                  draggable
                                  onDragStart={(e) => handleDragStart(e, result)}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    startDrag(result);
                                  }}
                                >
                                  <ExternalLink className="w-4 h-4" />
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedResult(result);
                                  }}
                                  className="p-2 hover:bg-muted rounded"
                                  title="View details"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            ) : localQuery && !isSearching ? (
              <div className="p-12 text-center">
                <Search className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="text-lg font-medium mb-2">No results found</h3>
                <p className="text-muted-foreground mb-4">
                  Try different keywords or adjust your filters
                </p>
                <button
                  onClick={() => setShowFilters(true)}
                  className="btn btn-secondary btn-sm"
                >
                  <Filter className="w-4 h-4 mr-2" />
                  Adjust Filters
                </button>
              </div>
            ) : !localQuery ? (
              <div className="p-12 text-center">
                <Search className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="text-lg font-medium mb-2">Search your documents</h3>
                <p className="text-muted-foreground mb-4">
                  Find information across all your documents and Readwise highlights
                </p>
                <div className="text-sm text-muted-foreground">
                  <p>• Use natural language queries</p>
                  <p>• Search by concepts, not just keywords</p>
                  <p>• Readwise highlights are prioritized</p>
                </div>
              </div>
            ) : null}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

export default SearchInterface;
