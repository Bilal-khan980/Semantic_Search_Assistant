import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clipboard,
  Search,
  Clock,
  Eye,
  Copy,
  ExternalLink,
  X,
  Lightbulb,
  FileText,
  Link,
  Code,
  Mail,
  Calendar,
  Hash,
  AtSign,
  Zap,
  History,
  Settings
} from 'lucide-react';
import { cn } from '../utils/cn';
import clipboardService from '../services/ClipboardService';

function ClipboardContextPanel({ isVisible, onClose, searchService }) {
  const [clipboardEvent, setClipboardEvent] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [clipboardHistory, setClipboardHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    // Initialize clipboard service
    if (searchService) {
      clipboardService.initialize(searchService);
    }

    // Subscribe to clipboard events
    const unsubscribe = clipboardService.onClipboardContext((event) => {
      setClipboardEvent(event);
    });

    // Load initial state
    setIsMonitoring(clipboardService.isActive());
    setClipboardHistory(clipboardService.getHistory());

    return () => {
      unsubscribe();
    };
  }, [searchService]);

  const toggleMonitoring = () => {
    if (isMonitoring) {
      clipboardService.stopMonitoring();
    } else {
      clipboardService.startMonitoring();
    }
    setIsMonitoring(!isMonitoring);
  };

  const getContextIcon = (context) => {
    switch (context.type) {
      case 'url': return Link;
      case 'email': return Mail;
      case 'code': return Code;
      case 'document': return FileText;
      default: return Clipboard;
    }
  };

  const getPatternIcon = (patternName) => {
    switch (patternName) {
      case 'url': return Link;
      case 'email': return Mail;
      case 'code': return Code;
      case 'hashtag': return Hash;
      case 'mention': return AtSign;
      case 'date': return Calendar;
      case 'time': return Clock;
      default: return Zap;
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const copyToClipboard = async (text) => {
    try {
      if (window.electronAPI && window.electronAPI.writeToClipboard) {
        await window.electronAPI.writeToClipboard(text);
      } else {
        await navigator.clipboard.writeText(text);
      }
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, x: 300 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 300 }}
      className="fixed right-4 top-4 bottom-4 w-96 bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col z-50"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2">
          <Clipboard className="w-5 h-5 text-blue-500" />
          <h2 className="font-semibold text-gray-900 dark:text-gray-100">
            Clipboard Context
          </h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={cn(
              "p-2 rounded-md transition-colors",
              showHistory 
                ? "bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            )}
            title="Toggle History"
          >
            <History className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={cn(
              "p-2 rounded-md transition-colors",
              showSettings 
                ? "bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            )}
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Monitoring Toggle */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isMonitoring ? "bg-green-500" : "bg-gray-400"
            )} />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {isMonitoring ? 'Monitoring Active' : 'Monitoring Inactive'}
            </span>
          </div>
          <button
            onClick={toggleMonitoring}
            className={cn(
              "px-3 py-1 rounded-md text-sm font-medium transition-colors",
              isMonitoring
                ? "bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900 dark:text-red-300"
                : "bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300"
            )}
          >
            {isMonitoring ? 'Stop' : 'Start'}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {showSettings ? (
          /* Settings Panel */
          <div className="p-4">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
              Clipboard Settings
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Auto-monitoring
                </span>
                <input type="checkbox" checked={isMonitoring} onChange={toggleMonitoring} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  History size
                </span>
                <span className="text-sm text-gray-500">
                  {clipboardHistory.length}/50
                </span>
              </div>
              <button
                onClick={() => {
                  clipboardService.clearHistory();
                  setClipboardHistory([]);
                }}
                className="w-full px-3 py-2 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 dark:bg-red-900 dark:text-red-300"
              >
                Clear History
              </button>
            </div>
          </div>
        ) : showHistory ? (
          /* History Panel */
          <div className="p-4">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
              Clipboard History
            </h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {clipboardHistory.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">
                  No clipboard history yet
                </p>
              ) : (
                clipboardHistory.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 dark:text-gray-100 truncate">
                          {item.content.substring(0, 60)}
                          {item.content.length > 60 && '...'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(item.timestamp)}
                        </p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(item.content)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-opacity"
                        title="Copy"
                      >
                        <Copy className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : (
          /* Main Context Panel */
          <div className="p-4 space-y-4">
            {!clipboardEvent ? (
              <div className="text-center py-8">
                <Clipboard className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-sm text-gray-500">
                  {isMonitoring 
                    ? 'Copy something to see contextual suggestions'
                    : 'Start monitoring to see clipboard context'
                  }
                </p>
              </div>
            ) : (
              <>
                {/* Current Clipboard Content */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                  <div className="flex items-center space-x-2 mb-2">
                    {React.createElement(getContextIcon(clipboardEvent.context), {
                      className: "w-4 h-4 text-blue-500"
                    })}
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {clipboardEvent.context.type.charAt(0).toUpperCase() + clipboardEvent.context.type.slice(1)} Content
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(clipboardEvent.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
                    {clipboardEvent.content}
                  </p>
                  <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                    <span>{clipboardEvent.wordCount} words</span>
                    <span>{clipboardEvent.charCount} chars</span>
                  </div>
                </div>

                {/* Detected Patterns */}
                {Object.keys(clipboardEvent.context.patterns).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                      Detected Patterns
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(clipboardEvent.context.patterns).map(([pattern, matches]) => {
                        const Icon = getPatternIcon(pattern);
                        return (
                          <div
                            key={pattern}
                            className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-xs dark:bg-blue-900 dark:text-blue-300"
                          >
                            <Icon className="w-3 h-3" />
                            <span>{pattern}</span>
                            <span className="bg-blue-200 dark:bg-blue-800 px-1 rounded">
                              {matches.length}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Contextual Suggestions */}
                {clipboardEvent.suggestions && clipboardEvent.suggestions.length > 0 && (
                  <div>
                    <div className="flex items-center space-x-2 mb-3">
                      <Lightbulb className="w-4 h-4 text-yellow-500" />
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Related Content
                      </h4>
                    </div>
                    <div className="space-y-2">
                      {clipboardEvent.suggestions.map((suggestion, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 transition-colors group"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <h5 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                {suggestion.title || suggestion.source.split('/').pop()}
                              </h5>
                              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                                {suggestion.content.substring(0, 100)}...
                              </p>
                              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                                {suggestion.relevanceReason}
                              </p>
                            </div>
                            <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => copyToClipboard(suggestion.content)}
                                className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                title="Copy content"
                              >
                                <Copy className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => {
                                  // Open in main search view
                                  if (window.electronAPI && window.electronAPI.focusSearch) {
                                    window.electronAPI.focusSearch();
                                  }
                                }}
                                className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                title="View in search"
                              >
                                <ExternalLink className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* No Suggestions */}
                {clipboardEvent.suggestions && clipboardEvent.suggestions.length === 0 && (
                  <div className="text-center py-4">
                    <Search className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">
                      No related content found
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default ClipboardContextPanel;
