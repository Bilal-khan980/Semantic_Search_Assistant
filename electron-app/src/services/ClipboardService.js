/**
 * Cross-application clipboard enhancement service
 * Monitors clipboard changes and provides intelligent context-aware suggestions
 */

class ClipboardService {
  constructor() {
    this.isMonitoring = false;
    this.lastClipboardContent = '';
    this.clipboardHistory = [];
    this.maxHistorySize = 50;
    this.monitoringInterval = null;
    this.contextCallbacks = new Set();
    this.searchService = null;
    
    // Debounce settings
    this.debounceTimeout = null;
    this.debounceDelay = 500; // ms
    
    // Context detection patterns
    this.contextPatterns = {
      email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
      url: /https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)/g,
      phone: /(\+\d{1,3}[- ]?)?\d{10}/g,
      date: /\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b/g,
      time: /\b\d{1,2}:\d{2}(\s?(AM|PM))?\b/gi,
      code: /```[\s\S]*?```|`[^`]+`/g,
      hashtag: /#\w+/g,
      mention: /@\w+/g
    };
  }

  /**
   * Initialize the clipboard service
   * @param {Object} searchService - Reference to the search service
   */
  initialize(searchService) {
    this.searchService = searchService;
    this.loadClipboardHistory();
  }

  /**
   * Start monitoring clipboard changes
   */
  startMonitoring() {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    console.log('🔍 Starting clipboard monitoring...');
    
    // Initial clipboard read
    this.checkClipboard();
    
    // Set up periodic monitoring
    this.monitoringInterval = setInterval(() => {
      this.checkClipboard();
    }, 1000); // Check every second
    
    // Listen for window focus events to check clipboard immediately
    window.addEventListener('focus', () => {
      this.checkClipboard();
    });
  }

  /**
   * Stop monitoring clipboard changes
   */
  stopMonitoring() {
    if (!this.isMonitoring) return;
    
    this.isMonitoring = false;
    console.log('⏹️ Stopping clipboard monitoring...');
    
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
    
    if (this.debounceTimeout) {
      clearTimeout(this.debounceTimeout);
      this.debounceTimeout = null;
    }
  }

  /**
   * Check clipboard for changes
   */
  async checkClipboard() {
    try {
      let clipboardContent = '';
      
      if (window.electronAPI && window.electronAPI.readFromClipboard) {
        // Use Electron API
        clipboardContent = await window.electronAPI.readFromClipboard();
      } else if (navigator.clipboard && navigator.clipboard.readText) {
        // Use Web API (may require user permission)
        clipboardContent = await navigator.clipboard.readText();
      } else {
        return; // No clipboard access available
      }
      
      // Check if content has changed
      if (clipboardContent !== this.lastClipboardContent && clipboardContent.trim()) {
        this.handleClipboardChange(clipboardContent);
      }
    } catch (error) {
      // Silently handle clipboard access errors (common in browsers)
      console.debug('Clipboard access error:', error.message);
    }
  }

  /**
   * Handle clipboard content change
   * @param {string} content - New clipboard content
   */
  handleClipboardChange(content) {
    this.lastClipboardContent = content;
    
    // Debounce rapid changes
    if (this.debounceTimeout) {
      clearTimeout(this.debounceTimeout);
    }
    
    this.debounceTimeout = setTimeout(() => {
      this.processClipboardContent(content);
    }, this.debounceDelay);
  }

  /**
   * Process new clipboard content
   * @param {string} content - Clipboard content to process
   */
  async processClipboardContent(content) {
    console.log('📋 Processing clipboard content:', content.substring(0, 100) + '...');
    
    // Add to history
    this.addToHistory(content);
    
    // Detect content context
    const context = this.detectContext(content);
    
    // Get relevant suggestions if search service is available
    let suggestions = [];
    if (this.searchService && content.length > 10) {
      try {
        suggestions = await this.getContextualSuggestions(content, context);
      } catch (error) {
        console.error('Error getting contextual suggestions:', error);
      }
    }
    
    // Create clipboard event data
    const clipboardEvent = {
      content,
      context,
      suggestions,
      timestamp: Date.now(),
      wordCount: content.split(/\s+/).length,
      charCount: content.length
    };
    
    // Notify all registered callbacks
    this.notifyContextCallbacks(clipboardEvent);
  }

  /**
   * Detect context and patterns in clipboard content
   * @param {string} content - Content to analyze
   * @returns {Object} Detected context information
   */
  detectContext(content) {
    const context = {
      type: 'text',
      patterns: {},
      language: 'unknown',
      sentiment: 'neutral',
      topics: []
    };
    
    // Detect patterns
    for (const [patternName, regex] of Object.entries(this.contextPatterns)) {
      const matches = content.match(regex);
      if (matches) {
        context.patterns[patternName] = matches;
      }
    }
    
    // Determine content type
    if (context.patterns.url) {
      context.type = 'url';
    } else if (context.patterns.email) {
      context.type = 'email';
    } else if (context.patterns.code) {
      context.type = 'code';
    } else if (content.length > 500) {
      context.type = 'document';
    } else if (content.split('\n').length > 5) {
      context.type = 'multiline';
    }
    
    // Simple language detection (basic)
    if (/[а-яё]/i.test(content)) {
      context.language = 'russian';
    } else if (/[àâäéèêëïîôöùûüÿç]/i.test(content)) {
      context.language = 'french';
    } else if (/[äöüß]/i.test(content)) {
      context.language = 'german';
    } else if (/[ñáéíóúü]/i.test(content)) {
      context.language = 'spanish';
    } else {
      context.language = 'english';
    }
    
    // Extract potential topics (simple keyword extraction)
    const words = content.toLowerCase().match(/\b\w{4,}\b/g) || [];
    const wordFreq = {};
    words.forEach(word => {
      wordFreq[word] = (wordFreq[word] || 0) + 1;
    });
    
    context.topics = Object.entries(wordFreq)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([word]) => word);
    
    return context;
  }

  /**
   * Get contextual suggestions based on clipboard content
   * @param {string} content - Clipboard content
   * @param {Object} context - Detected context
   * @returns {Array} Array of suggestions
   */
  async getContextualSuggestions(content, context) {
    if (!this.searchService) return [];
    
    try {
      // Create search queries based on content and context
      const queries = this.generateSearchQueries(content, context);
      const suggestions = [];
      
      for (const query of queries.slice(0, 3)) { // Limit to 3 queries
        try {
          const results = await this.searchService.search(query, 3); // Get top 3 results per query
          suggestions.push(...results.map(result => ({
            ...result,
            query,
            relevanceReason: this.explainRelevance(content, context, result)
          })));
        } catch (error) {
          console.warn(`Search failed for query "${query}":`, error);
        }
      }
      
      // Remove duplicates and sort by relevance
      const uniqueSuggestions = this.deduplicateSuggestions(suggestions);
      return uniqueSuggestions.slice(0, 5); // Return top 5 suggestions
      
    } catch (error) {
      console.error('Error generating contextual suggestions:', error);
      return [];
    }
  }

  /**
   * Generate search queries based on content and context
   * @param {string} content - Clipboard content
   * @param {Object} context - Detected context
   * @returns {Array} Array of search queries
   */
  generateSearchQueries(content, context) {
    const queries = [];
    
    // Use top topics as queries
    if (context.topics.length > 0) {
      queries.push(...context.topics.slice(0, 2));
    }
    
    // Use first sentence or phrase
    const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 10);
    if (sentences.length > 0) {
      const firstSentence = sentences[0].trim();
      if (firstSentence.length < 100) {
        queries.push(firstSentence);
      }
    }
    
    // Extract key phrases (simple approach)
    const keyPhrases = content.match(/\b\w+\s+\w+\b/g) || [];
    if (keyPhrases.length > 0) {
      queries.push(keyPhrases[0]);
    }
    
    // Context-specific queries
    if (context.patterns.hashtag) {
      queries.push(...context.patterns.hashtag.map(tag => tag.substring(1)));
    }
    
    return [...new Set(queries)]; // Remove duplicates
  }

  /**
   * Explain why a result is relevant to the clipboard content
   * @param {string} content - Original clipboard content
   * @param {Object} context - Detected context
   * @param {Object} result - Search result
   * @returns {string} Explanation of relevance
   */
  explainRelevance(content, context, result) {
    const reasons = [];
    
    // Check for topic overlap
    const resultTopics = (result.content || '').toLowerCase();
    const sharedTopics = context.topics.filter(topic => 
      resultTopics.includes(topic)
    );
    
    if (sharedTopics.length > 0) {
      reasons.push(`Shares topics: ${sharedTopics.join(', ')}`);
    }
    
    // Check for pattern matches
    if (context.patterns.url && result.content.includes('http')) {
      reasons.push('Contains related URLs');
    }
    
    if (context.patterns.code && result.source.includes('.md')) {
      reasons.push('Technical documentation');
    }
    
    // Default reason
    if (reasons.length === 0) {
      reasons.push('Semantic similarity');
    }
    
    return reasons.join('; ');
  }

  /**
   * Remove duplicate suggestions
   * @param {Array} suggestions - Array of suggestions
   * @returns {Array} Deduplicated suggestions
   */
  deduplicateSuggestions(suggestions) {
    const seen = new Set();
    return suggestions.filter(suggestion => {
      const key = `${suggestion.source}-${suggestion.content.substring(0, 50)}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }

  /**
   * Add content to clipboard history
   * @param {string} content - Content to add
   */
  addToHistory(content) {
    // Don't add duplicates or very short content
    if (content.length < 5 || this.clipboardHistory.some(item => item.content === content)) {
      return;
    }
    
    const historyItem = {
      content,
      timestamp: Date.now(),
      id: Date.now().toString()
    };
    
    this.clipboardHistory.unshift(historyItem);
    
    // Maintain max history size
    if (this.clipboardHistory.length > this.maxHistorySize) {
      this.clipboardHistory = this.clipboardHistory.slice(0, this.maxHistorySize);
    }
    
    // Save to storage
    this.saveClipboardHistory();
  }

  /**
   * Register a callback for clipboard context events
   * @param {Function} callback - Callback function
   */
  onClipboardContext(callback) {
    this.contextCallbacks.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.contextCallbacks.delete(callback);
    };
  }

  /**
   * Notify all registered callbacks
   * @param {Object} clipboardEvent - Clipboard event data
   */
  notifyContextCallbacks(clipboardEvent) {
    this.contextCallbacks.forEach(callback => {
      try {
        callback(clipboardEvent);
      } catch (error) {
        console.error('Error in clipboard context callback:', error);
      }
    });
  }

  /**
   * Get clipboard history
   * @returns {Array} Clipboard history
   */
  getHistory() {
    return [...this.clipboardHistory];
  }

  /**
   * Clear clipboard history
   */
  clearHistory() {
    this.clipboardHistory = [];
    this.saveClipboardHistory();
  }

  /**
   * Save clipboard history to storage
   */
  saveClipboardHistory() {
    try {
      localStorage.setItem('clipboardHistory', JSON.stringify(this.clipboardHistory));
    } catch (error) {
      console.warn('Failed to save clipboard history:', error);
    }
  }

  /**
   * Load clipboard history from storage
   */
  loadClipboardHistory() {
    try {
      const saved = localStorage.getItem('clipboardHistory');
      if (saved) {
        this.clipboardHistory = JSON.parse(saved);
      }
    } catch (error) {
      console.warn('Failed to load clipboard history:', error);
      this.clipboardHistory = [];
    }
  }

  /**
   * Get current monitoring status
   * @returns {boolean} Whether monitoring is active
   */
  isActive() {
    return this.isMonitoring;
  }

  /**
   * Get clipboard service statistics
   * @returns {Object} Service statistics
   */
  getStats() {
    return {
      isMonitoring: this.isMonitoring,
      historySize: this.clipboardHistory.length,
      lastContent: this.lastClipboardContent ? this.lastClipboardContent.substring(0, 50) + '...' : 'None',
      callbackCount: this.contextCallbacks.size
    };
  }
}

// Create singleton instance
const clipboardService = new ClipboardService();

export default clipboardService;
