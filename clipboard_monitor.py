"""
Global clipboard monitoring for automatic content enhancement and smart paste functionality.
Monitors clipboard changes and provides intelligent suggestions based on copied content.
"""

import asyncio
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable
import re
import hashlib

try:
    import pynput
    from pynput import keyboard
except ImportError:
    pynput = None
    keyboard = None

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

class ClipboardMonitor:
    """Monitor clipboard changes and provide intelligent content enhancement."""
    
    def __init__(self, config, search_engine=None):
        self.config = config
        self.search_engine = search_engine
        self.is_monitoring = False
        self.last_clipboard_content = ""
        self.last_clipboard_hash = ""
        self.clipboard_history = []
        self.max_history_size = 50
        self.enhancement_callbacks = []
        self.keyboard_listener = None
        self.monitor_thread = None
        
        # Smart paste settings
        self.smart_paste_enabled = config.get('clipboard.smart_paste_enabled', True)
        self.auto_enhance_enabled = config.get('clipboard.auto_enhance_enabled', True)
        self.suggestion_threshold = config.get('clipboard.suggestion_threshold', 0.7)
        
    async def start_monitoring(self):
        """Start clipboard monitoring."""
        if self.is_monitoring:
            return
            
        logger.info("Starting clipboard monitoring...")
        self.is_monitoring = True
        
        # Start clipboard monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_clipboard_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start keyboard listener for smart paste
        if self.smart_paste_enabled and keyboard:
            self._start_keyboard_listener()
        
        logger.info("Clipboard monitoring started")
    
    def stop_monitoring(self):
        """Stop clipboard monitoring."""
        logger.info("Stopping clipboard monitoring...")
        self.is_monitoring = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        logger.info("Clipboard monitoring stopped")
    
    def _monitor_clipboard_loop(self):
        """Main clipboard monitoring loop."""
        try:
            import tkinter as tk
            
            # Create a hidden tkinter window for clipboard access
            root = tk.Tk()
            root.withdraw()  # Hide the window
            
            while self.is_monitoring:
                try:
                    # Get current clipboard content
                    current_content = root.clipboard_get()
                    current_hash = hashlib.md5(current_content.encode()).hexdigest()
                    
                    # Check if clipboard content changed
                    if current_hash != self.last_clipboard_hash and current_content.strip():
                        self._handle_clipboard_change(current_content)
                        self.last_clipboard_content = current_content
                        self.last_clipboard_hash = current_hash
                
                except tk.TclError:
                    # Clipboard is empty or contains non-text data
                    pass
                except Exception as e:
                    logger.warning(f"Error monitoring clipboard: {str(e)}")
                
                time.sleep(0.5)  # Check every 500ms
                
        except Exception as e:
            logger.error(f"Clipboard monitoring failed: {str(e)}")
        finally:
            try:
                root.destroy()
            except:
                pass
    
    def _handle_clipboard_change(self, content: str):
        """Handle clipboard content change."""
        try:
            # Add to history
            self._add_to_history(content)
            
            # Auto-enhance if enabled
            if self.auto_enhance_enabled and self.search_engine:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._auto_enhance_content(content))
                    else:
                        # If no loop is running, skip auto-enhancement
                        logger.debug("No event loop running, skipping auto-enhancement")
                except RuntimeError:
                    # No event loop available
                    logger.debug("No event loop available, skipping auto-enhancement")
            
            # Notify callbacks
            for callback in self.enhancement_callbacks:
                try:
                    callback(content)
                except Exception as e:
                    logger.warning(f"Enhancement callback failed: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error handling clipboard change: {str(e)}")
    
    def _add_to_history(self, content: str):
        """Add content to clipboard history."""
        # Clean and validate content
        cleaned_content = content.strip()
        if len(cleaned_content) < 10:  # Skip very short content
            return
            
        # Create history entry
        entry = {
            'content': cleaned_content,
            'timestamp': time.time(),
            'source_app': self._get_active_application(),
            'enhanced': False,
            'suggestions': []
        }
        
        # Add to history (avoid duplicates)
        if not any(h['content'] == cleaned_content for h in self.clipboard_history[-5:]):
            self.clipboard_history.append(entry)
            
            # Trim history if too large
            if len(self.clipboard_history) > self.max_history_size:
                self.clipboard_history = self.clipboard_history[-self.max_history_size:]
    
    async def _auto_enhance_content(self, content: str):
        """Automatically enhance clipboard content with related information."""
        try:
            if not self.search_engine:
                return
                
            # Search for related content
            results = await self.search_engine.search(
                content[:200],  # Use first 200 chars for search
                limit=5,
                similarity_threshold=self.suggestion_threshold
            )
            
            if results:
                # Update the latest history entry with suggestions
                if self.clipboard_history:
                    self.clipboard_history[-1]['suggestions'] = results
                    self.clipboard_history[-1]['enhanced'] = True
                    
                    # Notify about enhancements
                    logger.info(f"Found {len(results)} related items for clipboard content")
                    
        except Exception as e:
            logger.warning(f"Auto-enhancement failed: {str(e)}")
    
    def _start_keyboard_listener(self):
        """Start keyboard listener for smart paste functionality."""
        try:
            def on_key_combination():
                """Handle smart paste key combination."""
                asyncio.create_task(self._handle_smart_paste())
            
            # Listen for Ctrl+Shift+V (smart paste)
            self.keyboard_listener = keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+v': on_key_combination
            })
            self.keyboard_listener.start()
            
        except Exception as e:
            logger.warning(f"Failed to start keyboard listener: {str(e)}")
    
    async def _handle_smart_paste(self):
        """Handle smart paste operation."""
        try:
            if not self.clipboard_history:
                return
                
            latest_entry = self.clipboard_history[-1]
            
            # If we have suggestions, show them
            if latest_entry.get('suggestions'):
                # This would trigger UI to show suggestions
                # For now, just log
                logger.info(f"Smart paste: {len(latest_entry['suggestions'])} suggestions available")
                
        except Exception as e:
            logger.error(f"Smart paste failed: {str(e)}")
    
    def _get_active_application(self) -> str:
        """Get the currently active application name."""
        try:
            if psutil:
                # Get the active window process (platform-specific)
                import platform
                system = platform.system()
                
                if system == "Windows":
                    return self._get_active_app_windows()
                elif system == "Darwin":  # macOS
                    return self._get_active_app_macos()
                elif system == "Linux":
                    return self._get_active_app_linux()
                    
        except Exception as e:
            logger.warning(f"Failed to get active application: {str(e)}")
            
        return "Unknown"
    
    def _get_active_app_windows(self) -> str:
        """Get active application on Windows."""
        try:
            import win32gui
            import win32process
            
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            if psutil:
                process = psutil.Process(pid)
                return process.name()
                
        except Exception:
            pass
            
        return "Unknown"
    
    def _get_active_app_macos(self) -> str:
        """Get active application on macOS."""
        try:
            import subprocess
            result = subprocess.run([
                'osascript', '-e', 
                'tell application "System Events" to get name of first application process whose frontmost is true'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip()
                
        except Exception:
            pass
            
        return "Unknown"
    
    def _get_active_app_linux(self) -> str:
        """Get active application on Linux."""
        try:
            import subprocess
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip()
                
        except Exception:
            pass
            
        return "Unknown"
    
    def add_enhancement_callback(self, callback: Callable[[str], None]):
        """Add a callback for clipboard content changes."""
        self.enhancement_callbacks.append(callback)
    
    def remove_enhancement_callback(self, callback: Callable[[str], None]):
        """Remove a callback for clipboard content changes."""
        if callback in self.enhancement_callbacks:
            self.enhancement_callbacks.remove(callback)
    
    def get_clipboard_history(self) -> list:
        """Get the clipboard history."""
        return self.clipboard_history.copy()
    
    def get_enhanced_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Get enhanced version of clipboard content if available."""
        for entry in reversed(self.clipboard_history):
            if entry['content'] == content and entry.get('enhanced'):
                return entry
        return None
    
    def clear_history(self):
        """Clear clipboard history."""
        self.clipboard_history.clear()
        logger.info("Clipboard history cleared")
