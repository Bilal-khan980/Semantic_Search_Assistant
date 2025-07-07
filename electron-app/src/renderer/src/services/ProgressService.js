/**
 * Real-time progress tracking service using Server-Sent Events
 */

class ProgressService {
  constructor() {
    this.activeStreams = new Map(); // taskId -> EventSource
    this.progressCallbacks = new Map(); // taskId -> callback function
  }

  /**
   * Start tracking progress for a task with real-time updates
   * @param {string} taskId - The task ID to track
   * @param {function} onProgress - Callback function for progress updates
   * @param {function} onComplete - Callback function when task completes
   * @param {function} onError - Callback function for errors
   */
  trackProgress(taskId, onProgress, onComplete = null, onError = null) {
    // Close existing stream if any
    this.stopTracking(taskId);

    try {
      // Create EventSource for real-time updates
      const eventSource = new EventSource(
        `http://127.0.0.1:8000/documents/processing/${taskId}/stream`
      );

      // Store the stream
      this.activeStreams.set(taskId, eventSource);

      // Handle messages
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Skip heartbeat messages
          if (data.type === 'heartbeat') {
            return;
          }

          // Call progress callback
          if (onProgress) {
            onProgress(data);
          }

          // Handle completion
          if (data.status === 'completed') {
            if (onComplete) {
              onComplete(data);
            }
            this.stopTracking(taskId);
          } else if (data.status === 'error') {
            if (onError) {
              onError(data);
            }
            this.stopTracking(taskId);
          }
        } catch (error) {
          console.error('Failed to parse progress data:', error);
          if (onError) {
            onError({ status: 'error', message: 'Failed to parse progress data' });
          }
        }
      };

      // Handle errors
      eventSource.onerror = (error) => {
        console.error('Progress stream error:', error);
        if (onError) {
          onError({ status: 'error', message: 'Connection lost' });
        }
        this.stopTracking(taskId);
      };

      // Handle connection open
      eventSource.onopen = () => {
        console.log(`Progress tracking started for task: ${taskId}`);
      };

    } catch (error) {
      console.error('Failed to start progress tracking:', error);
      if (onError) {
        onError({ status: 'error', message: 'Failed to start progress tracking' });
      }
    }
  }

  /**
   * Stop tracking progress for a task
   * @param {string} taskId - The task ID to stop tracking
   */
  stopTracking(taskId) {
    const eventSource = this.activeStreams.get(taskId);
    if (eventSource) {
      eventSource.close();
      this.activeStreams.delete(taskId);
      this.progressCallbacks.delete(taskId);
      console.log(`Progress tracking stopped for task: ${taskId}`);
    }
  }

  /**
   * Stop all active progress tracking
   */
  stopAllTracking() {
    for (const [taskId, eventSource] of this.activeStreams) {
      eventSource.close();
      console.log(`Progress tracking stopped for task: ${taskId}`);
    }
    this.activeStreams.clear();
    this.progressCallbacks.clear();
  }

  /**
   * Get the number of active tracking sessions
   */
  getActiveTrackingCount() {
    return this.activeStreams.size;
  }

  /**
   * Check if a task is being tracked
   * @param {string} taskId - The task ID to check
   */
  isTracking(taskId) {
    return this.activeStreams.has(taskId);
  }

  /**
   * Fallback to polling if SSE is not available
   * @param {string} taskId - The task ID to poll
   * @param {function} onProgress - Callback function for progress updates
   * @param {function} onComplete - Callback function when task completes
   * @param {function} onError - Callback function for errors
   */
  async pollProgress(taskId, onProgress, onComplete = null, onError = null) {
    const maxAttempts = 120; // 10 minutes max (5 second intervals)
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/documents/processing/${taskId}`);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Call progress callback
        if (onProgress) {
          onProgress(data);
        }

        // Handle completion
        if (data.status === 'completed') {
          if (onComplete) {
            onComplete(data);
          }
          return;
        } else if (data.status === 'error') {
          if (onError) {
            onError(data);
          }
          return;
        }

        // Continue polling if not complete and under max attempts
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else {
          if (onError) {
            onError({ status: 'error', message: 'Polling timeout' });
          }
        }

      } catch (error) {
        console.error('Polling error:', error);
        if (onError) {
          onError({ status: 'error', message: error.message });
        }
      }
    };

    // Start polling
    poll();
  }

  /**
   * Enhanced progress tracking with automatic fallback
   * @param {string} taskId - The task ID to track
   * @param {function} onProgress - Callback function for progress updates
   * @param {function} onComplete - Callback function when task completes
   * @param {function} onError - Callback function for errors
   * @param {boolean} useSSE - Whether to use SSE (default: true)
   */
  track(taskId, onProgress, onComplete = null, onError = null, useSSE = true) {
    if (useSSE && typeof EventSource !== 'undefined') {
      // Try SSE first
      this.trackProgress(taskId, onProgress, onComplete, (error) => {
        console.warn('SSE failed, falling back to polling:', error);
        // Fallback to polling
        this.pollProgress(taskId, onProgress, onComplete, onError);
      });
    } else {
      // Use polling directly
      this.pollProgress(taskId, onProgress, onComplete, onError);
    }
  }
}

// Create singleton instance
const progressService = new ProgressService();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    progressService.stopAllTracking();
  });
}

export default progressService;
