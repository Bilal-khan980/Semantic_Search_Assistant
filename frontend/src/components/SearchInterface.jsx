"use client"

import { useState, useRef, useEffect } from "react"
import { Search, Copy, ExternalLink, BookOpen, FileText, Sparkles } from "lucide-react"

export function SearchInterface({ onSearch, searchResults, isSearching, stats }) {
  const [query, setQuery] = useState("")
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedResult, setSelectedResult] = useState(null)
  const searchInputRef = useRef(null)

  useEffect(() => {
    // Focus search input when component mounts
    if (searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [])

  const handleSearch = async (searchQuery = query) => {
    if (!searchQuery.trim()) return

    setShowSuggestions(false)
    await onSearch(searchQuery, {
      limit: 20,
      similarity_threshold: 0.3,
    })
  }

  const handleInputChange = (e) => {
    const value = e.target.value
    setQuery(value)

    // Show suggestions for queries longer than 2 characters
    if (value.length > 2) {
      // Mock suggestions - in real app, call API
      const mockSuggestions = [
        "artificial intelligence",
        "machine learning",
        "deep work",
        "productivity",
        "focus",
      ].filter((s) => s.toLowerCase().includes(value.toLowerCase()))

      setSuggestions(mockSuggestions)
      setShowSuggestions(mockSuggestions.length > 0)
    } else {
      setShowSuggestions(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSearch()
    } else if (e.key === "Escape") {
      setShowSuggestions(false)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
  }

  const formatSource = (source) => {
    if (source.includes("/") || source.includes("\\")) {
      return source.split(/[/\\]/).pop()
    }
    return source
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Search Your Knowledge</h1>
        <p className="text-gray-600">
          {stats.total_chunks > 0
            ? `Search across ${stats.total_chunks} indexed chunks from ${stats.unique_sources} sources`
            : "Upload documents or import Readwise highlights to get started"}
        </p>
      </div>

      {/* Search Input */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            ref={searchInputRef}
            type="search"
            placeholder="Search your documents and highlights..."
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white shadow-sm"
          />
          <button
            onClick={() => handleSearch()}
            disabled={!query.trim() || isSearching}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 btn-primary px-6 py-2 disabled:opacity-50"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => {
                  setQuery(suggestion)
                  setShowSuggestions(false)
                  handleSearch(suggestion)
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
              >
                <div className="flex items-center space-x-2">
                  <Search className="w-4 h-4 text-gray-400" />
                  <span>{suggestion}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {stats.total_chunks === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <Sparkles className="w-12 h-12 text-blue-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Get Started</h3>
          <p className="text-blue-700 mb-4">Upload documents or import your Readwise highlights to start searching</p>
          <div className="flex justify-center space-x-4">
            <button className="btn-primary">
              <FileText className="w-4 h-4 mr-2" />
              Upload Documents
            </button>
            <button className="btn-secondary">
              <BookOpen className="w-4 h-4 mr-2" />
              Import Readwise
            </button>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Search Results ({searchResults.length})</h2>
          </div>

          <div className="space-y-4">
            {searchResults.map((result, index) => (
              <div
                key={result.id || index}
                className="card hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedResult(selectedResult === result.id ? null : result.id)}
              >
                <div className="card-header pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        {result.is_readwise ? (
                          <BookOpen className="w-4 h-4 text-blue-500" />
                        ) : (
                          <FileText className="w-4 h-4 text-gray-500" />
                        )}
                        <h3 className="font-semibold text-gray-900">
                          {result.is_readwise
                            ? result.metadata?.book || "Readwise Highlight"
                            : formatSource(result.source)}
                        </h3>
                        {result.is_readwise && <span className="badge badge-secondary">Readwise</span>}
                      </div>

                      {result.is_readwise && result.metadata?.author && (
                        <p className="text-sm text-gray-600 mb-2">by {result.metadata.author}</p>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="badge badge-outline text-xs">{Math.round(result.similarity * 100)}% match</span>
                    </div>
                  </div>
                </div>

                <div className="card-content">
                  <p className="text-gray-700 leading-relaxed mb-4">{result.content}</p>

                  {result.metadata?.note && (
                    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 mb-4">
                      <p className="text-sm text-yellow-800">
                        <strong>Note:</strong> {result.metadata.note}
                      </p>
                    </div>
                  )}

                  {result.metadata?.tags && result.metadata.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {result.metadata.tags.map((tag, tagIndex) => (
                        <span key={tagIndex} className="badge badge-secondary text-xs">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <div className="text-sm text-gray-500">
                      {result.is_readwise ? (
                        <span>
                          {result.metadata?.location && `${result.metadata.location} • `}
                          Readwise Highlight
                        </span>
                      ) : (
                        <span>Document • {formatSource(result.source)}</span>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          copyToClipboard(result.content)
                        }}
                        className="btn-ghost p-2"
                        title="Copy content"
                      >
                        <Copy className="w-4 h-4" />
                      </button>

                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          // Open source - would need to implement
                        }}
                        className="btn-ghost p-2"
                        title="Open source"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {query && searchResults.length === 0 && !isSearching && (
        <div className="text-center py-12">
          <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600 mb-4">No documents or highlights match your search for "{query}"</p>
          <div className="space-y-2 text-sm text-gray-500">
            <p>Try:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Using different keywords</li>
              <li>Checking your spelling</li>
              <li>Using more general terms</li>
              <li>Uploading more documents</li>
            </ul>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isSearching && (
        <div className="text-center py-12">
          <div className="loading-dots mb-4">
            <div style={{ "--i": 0 }}></div>
            <div style={{ "--i": 1 }}></div>
            <div style={{ "--i": 2 }}></div>
          </div>
          <p className="text-gray-600">Searching your knowledge base...</p>
        </div>
      )}
    </div>
  )
}
