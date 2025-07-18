#!/usr/bin/env python3
"""
Real-time Word Document Monitor.
Monitors actual typing in Word documents and provides instant suggestions.
"""

import time
import threading
import logging
import requests
import win32com.client
import pythoncom
import re
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class WordMonitor:
    """Monitors Word documents in real-time."""
    
    def __init__(self, callback_func):
        self.callback_func = callback_func
        self.is_monitoring = False
        self.word_app = None
        self.last_text = ""
        self.last_position = 0
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start monitoring Word documents."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Word monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Word monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Initialize COM for this thread
                pythoncom.CoInitialize()
                
                # Get current context from Word
                context = self._get_word_context()
                
                if context and context != self.last_text:
                    self.last_text = context
                    # Call the callback with new context
                    self.callback_func(context)
                
                time.sleep(0.5)  # Check every 500ms for real-time feel
                
            except Exception as e:
                logger.error(f"Error in Word monitoring: {e}")
                time.sleep(2)
            finally:
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass
    
    def _get_word_context(self) -> Optional[str]:
        """Get current context from Word document."""
        try:
            # Connect to Word application
            if not self.word_app:
                self.word_app = win32com.client.GetActiveObject("Word.Application")
            
            if not self.word_app or self.word_app.Documents.Count == 0:
                return None
            
            # Get active document
            doc = self.word_app.ActiveDocument
            selection = self.word_app.Selection
            
            # Get current paragraph and surrounding context
            if selection.Paragraphs.Count > 0:
                current_para = selection.Paragraphs.Item(1)
                para_text = current_para.Range.Text.strip()
            else:
                # Fallback to selection text
                para_text = selection.Text.strip()
            
            # Get previous paragraphs for more context
            context_parts = []
            
            # Add current paragraph
            context_parts.append(para_text)

            # Try to get surrounding text using selection
            try:
                # Expand selection to get more context
                selection.MoveStart(Unit=1, Count=-50)  # Move back 50 words
                selection.MoveEnd(Unit=1, Count=50)     # Move forward 50 words
                expanded_text = selection.Text.strip()
                if expanded_text and len(expanded_text) > len(para_text):
                    context_parts = [expanded_text]
            except:
                pass
            
            # Combine context
            full_context = " ".join(context_parts)
            
            # Clean up the text
            full_context = re.sub(r'\s+', ' ', full_context)
            full_context = re.sub(r'[^\w\s.,!?;:\-\'"()]', '', full_context)
            
            # Return last 300 characters for context
            if len(full_context) > 300:
                full_context = full_context[-300:]
            
            return full_context.strip()
            
        except Exception as e:
            # Word might not be open or accessible
            self.word_app = None
            return None

class RealTimeContextProvider:
    """Provides real-time context suggestions."""
    
    def __init__(self, backend_url="http://127.0.0.1:8000"):
        self.backend_url = backend_url
        self.word_monitor = WordMonitor(self.on_context_change)
        self.last_suggestions = []
        self.suggestion_callbacks = []
        
    def add_suggestion_callback(self, callback):
        """Add callback for when suggestions change."""
        self.suggestion_callbacks.append(callback)
    
    def start(self):
        """Start real-time monitoring."""
        self.word_monitor.start_monitoring()
    
    def stop(self):
        """Stop monitoring."""
        self.word_monitor.stop_monitoring()
    
    def on_context_change(self, context):
        """Handle context change from Word."""
        if not context or len(context.strip()) < 10:
            return
        
        logger.info(f"Context changed: {context[:50]}...")
        
        # Get suggestions from backend
        suggestions = self._get_suggestions(context)
        
        if suggestions:
            self.last_suggestions = suggestions
            # Notify all callbacks
            for callback in self.suggestion_callbacks:
                try:
                    callback(context, suggestions)
                except Exception as e:
                    logger.error(f"Error in suggestion callback: {e}")
    
    def _get_suggestions(self, context) -> List[Dict[str, Any]]:
        """Get suggestions from backend."""
        try:
            response = requests.post(
                f"{self.backend_url}/search",
                json={
                    "query": context,
                    "limit": 8,
                    "similarity_threshold": 0.2
                },
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
        
        return []
    
    def manual_search(self, query) -> List[Dict[str, Any]]:
        """Perform manual search."""
        return self._get_suggestions(query)

def test_word_monitor():
    """Test the Word monitor."""
    def on_suggestions(context, suggestions):
        print(f"\n📝 Context: {context[:100]}...")
        print(f"💡 Found {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            content = suggestion.get('content', '')[:80]
            source = suggestion.get('source', 'Unknown')
            similarity = suggestion.get('similarity', 0)
            print(f"  {i}. {content}... [{source}] ({similarity:.1%})")
    
    provider = RealTimeContextProvider()
    provider.add_suggestion_callback(on_suggestions)
    
    print("🚀 Starting Word monitoring...")
    print("📝 Open Word and start typing to see real-time suggestions!")
    print("⏹️  Press Ctrl+C to stop")
    
    provider.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        provider.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_word_monitor()
