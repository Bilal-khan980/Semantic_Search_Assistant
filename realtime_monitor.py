#!/usr/bin/env python3
"""
Real-time Typing Monitor.
Monitors typing in real-time using keyboard hooks and clipboard detection.
"""

import time
import threading
import logging
import requests
import pyperclip
import win32gui
import keyboard
import re
from typing import Optional, List, Dict, Any, Callable

logger = logging.getLogger(__name__)

class RealtimeTypingMonitor:
    """Monitors typing in real-time across all applications."""
    
    def __init__(self, callback_func: Callable[[str], None]):
        self.callback_func = callback_func
        self.is_monitoring = False
        self.monitor_thread = None
        self.typing_buffer = ""
        self.last_activity_time = 0
        self.last_clipboard = ""
        
    def start_monitoring(self):
        """Start monitoring."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        
        # Start clipboard monitoring thread
        self.monitor_thread = threading.Thread(target=self._clipboard_monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Setup keyboard hook for real-time typing
        self._setup_keyboard_hook()
        
        logger.info("Real-time typing monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        # Unhook keyboard
        try:
            keyboard.unhook_all()
        except:
            pass
            
        logger.info("Real-time typing monitoring stopped")
    
    def _setup_keyboard_hook(self):
        """Setup keyboard hook for real-time typing detection."""
        def on_key_event(event):
            try:
                if not self.is_monitoring:
                    return
                
                current_time = time.time()
                
                # Check if we're in a text application
                active_window = self._get_active_window()
                if not self._is_text_application(active_window):
                    return
                
                # Reset buffer if too much time passed (3 seconds)
                if current_time - self.last_activity_time > 3:
                    self.typing_buffer = ""
                
                self.last_activity_time = current_time
                
                # Handle different key events
                if event.event_type == keyboard.KEY_DOWN:
                    if len(event.name) == 1:  # Regular character
                        self.typing_buffer += event.name
                    elif event.name == 'space':
                        self.typing_buffer += " "
                    elif event.name in ['enter', 'tab']:
                        self.typing_buffer += " "
                    elif event.name == 'backspace':
                        if self.typing_buffer:
                            self.typing_buffer = self.typing_buffer[:-1]
                    
                    # Trigger context update when we have enough text
                    if len(self.typing_buffer) > 20:
                        # Clean the buffer
                        cleaned_text = self._clean_text(self.typing_buffer)
                        
                        # Check if we have meaningful content
                        if len(cleaned_text.split()) >= 5:  # At least 5 words
                            context = cleaned_text[-200:]  # Last 200 chars
                            self.callback_func(context.strip())
                            
                            # Keep only recent text in buffer
                            self.typing_buffer = self.typing_buffer[-100:]
                            
            except Exception as e:
                logger.error(f"Error in keyboard hook: {e}")
        
        # Register the hook
        keyboard.hook(on_key_event)
    
    def _clipboard_monitor_loop(self):
        """Monitor clipboard for copy/paste operations."""
        while self.is_monitoring:
            try:
                current_clipboard = self._get_clipboard()
                active_window = self._get_active_window()
                
                # Detect clipboard changes in text applications
                if (current_clipboard != self.last_clipboard and 
                    len(current_clipboard) > len(self.last_clipboard) and
                    len(current_clipboard) > 20 and
                    self._is_text_application(active_window)):
                    
                    # New text was copied/pasted
                    if len(current_clipboard.strip()) > 20:
                        cleaned_text = self._clean_text(current_clipboard)
                        context = cleaned_text[-300:]  # Last 300 chars
                        self.callback_func(context.strip())
                
                self.last_clipboard = current_clipboard
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in clipboard monitoring: {e}")
                time.sleep(2)
    
    def _get_clipboard(self) -> str:
        """Get current clipboard content."""
        try:
            return pyperclip.paste()
        except Exception as e:
            return ""
    
    def _get_active_window(self) -> str:
        """Get active window title."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd)
        except Exception as e:
            return ""
    
    def _is_text_application(self, window_title: str) -> bool:
        """Check if the window is a text application."""
        if not window_title:
            return False
        
        text_apps = [
            'Word', 'Microsoft Word', 'Notepad', 'WordPad', 
            'Visual Studio Code', 'Sublime Text', 'Atom',
            'Notion', 'Obsidian', 'Typora', 'Bear',
            'Google Docs', 'Office', 'Writer', 'TextEdit',
            'Scrivener', 'Draft', 'Ulysses'
        ]
        
        window_lower = window_title.lower()
        return any(app.lower() in window_lower for app in text_apps)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s.,!?;:\-\'"()]', '', text)
        
        return text.strip()

class RealTimeContextProvider:
    """Provides real-time context suggestions using typing monitoring."""
    
    def __init__(self, backend_url="http://127.0.0.1:8000"):
        self.backend_url = backend_url
        self.typing_monitor = RealtimeTypingMonitor(self.on_context_change)
        self.last_suggestions = []
        self.suggestion_callbacks = []
        self.last_context = ""
        self.last_update_time = 0
        
    def add_suggestion_callback(self, callback):
        """Add callback for when suggestions change."""
        self.suggestion_callbacks.append(callback)
    
    def start(self):
        """Start real-time monitoring."""
        self.typing_monitor.start_monitoring()
    
    def stop(self):
        """Stop monitoring."""
        self.typing_monitor.stop_monitoring()
    
    def on_context_change(self, context):
        """Handle context change."""
        if not context or len(context.strip()) < 15:
            return
        
        # Avoid too frequent updates
        current_time = time.time()
        if current_time - self.last_update_time < 1.5:  # Wait at least 1.5 seconds
            return
        
        # Avoid very similar contexts
        if self._is_similar_context(context, self.last_context):
            return
        
        self.last_context = context
        self.last_update_time = current_time
        
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
    
    def _is_similar_context(self, context1: str, context2: str) -> bool:
        """Check if two contexts are very similar."""
        if not context1 or not context2:
            return False
        
        # Simple similarity check
        words1 = set(context1.lower().split())
        words2 = set(context2.lower().split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity > 0.8  # 80% similarity threshold
    
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
    
    def force_update(self):
        """Force context update from clipboard."""
        try:
            clipboard_text = pyperclip.paste().strip()
            if clipboard_text:
                self.on_context_change(clipboard_text)
        except Exception as e:
            logger.error(f"Error in force update: {e}")

def test_realtime_monitor():
    """Test the real-time monitor."""
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
    
    print("🚀 Starting real-time typing monitoring...")
    print("📝 Start typing in Word, Notepad, or any text editor!")
    print("💡 Type continuously to see real-time suggestions")
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
    test_realtime_monitor()
