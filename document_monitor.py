"""
Real-time document monitoring service that watches for active documents
and provides contextual suggestions based on user's current work.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import json
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil
import platform

logger = logging.getLogger(__name__)

class DocumentMonitor:
    """Monitors user's active documents and provides contextual suggestions."""
    
    def __init__(self, search_engine, config):
        self.search_engine = search_engine
        self.config = config
        self.is_monitoring = False
        self.observer = None
        
        # Active document tracking
        self.active_documents = {}
        self.document_activity = {}
        self.context_callbacks = []
        
        # Monitoring settings
        self.check_interval = config.get('monitoring.check_interval', 5)  # seconds
        self.activity_threshold = config.get('monitoring.activity_threshold', 30)  # seconds
        self.max_suggestions = config.get('monitoring.max_suggestions', 5)
        
        # File patterns to monitor
        self.monitored_extensions = config.get('monitoring.file_extensions', [
            '.txt', '.md', '.docx', '.pdf', '.rtf', '.odt'
        ])
        
        # Folders to watch
        self.watch_folders = config.get('monitoring.watch_folders', [])
        
    async def start_monitoring(self):
        """Start monitoring user's document activity."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        logger.info("🔍 Starting document monitoring...")
        
        # Start file system monitoring
        await self._start_file_monitoring()
        
        # Start active window monitoring
        asyncio.create_task(self._monitor_active_windows())
        
        # Start periodic context analysis
        asyncio.create_task(self._periodic_context_analysis())
        
        logger.info("✅ Document monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring."""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
        logger.info("⏹️ Document monitoring stopped")
    
    async def _start_file_monitoring(self):
        """Start monitoring file system changes."""
        if not self.watch_folders:
            # Default to common document folders
            home = Path.home()
            self.watch_folders = [
                str(home / "Documents"),
                str(home / "Desktop"),
                str(home / "Downloads")
            ]
        
        self.observer = Observer()
        event_handler = DocumentEventHandler(self)
        
        for folder in self.watch_folders:
            folder_path = Path(folder)
            if folder_path.exists():
                self.observer.schedule(event_handler, str(folder_path), recursive=True)
                logger.info(f"📁 Watching folder: {folder_path}")
        
        self.observer.start()
    
    async def _monitor_active_windows(self):
        """Monitor active windows to detect document editing."""
        while self.is_monitoring:
            try:
                active_window = await self._get_active_window_info()
                if active_window:
                    await self._process_active_window(active_window)
                    
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring active windows: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _get_active_window_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active window."""
        try:
            if platform.system() == "Windows":
                return await self._get_windows_active_window()
            elif platform.system() == "Darwin":
                return await self._get_macos_active_window()
            elif platform.system() == "Linux":
                return await self._get_linux_active_window()
        except Exception as e:
            logger.debug(f"Could not get active window info: {e}")
        
        return None
    
    async def _get_windows_active_window(self) -> Optional[Dict[str, Any]]:
        """Get active window info on Windows."""
        try:
            import win32gui
            import win32process
            
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
                
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                
                return {
                    'title': window_title,
                    'process': process_name,
                    'pid': pid,
                    'timestamp': time.time()
                }
            except psutil.NoSuchProcess:
                return None
                
        except ImportError:
            logger.debug("win32gui not available for Windows window monitoring")
            return None
    
    async def _get_macos_active_window(self) -> Optional[Dict[str, Any]]:
        """Get active window info on macOS."""
        try:
            import subprocess
            
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                set windowTitle to name of first window of frontApp
                return appName & "|" & windowTitle
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout:
                parts = result.stdout.strip().split('|', 1)
                if len(parts) == 2:
                    return {
                        'title': parts[1],
                        'process': parts[0],
                        'timestamp': time.time()
                    }
                    
        except Exception as e:
            logger.debug(f"macOS window monitoring error: {e}")
            
        return None
    
    async def _get_linux_active_window(self) -> Optional[Dict[str, Any]]:
        """Get active window info on Linux."""
        try:
            import subprocess
            
            # Try xdotool first
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout:
                return {
                    'title': result.stdout.strip(),
                    'process': 'unknown',
                    'timestamp': time.time()
                }
                
        except Exception as e:
            logger.debug(f"Linux window monitoring error: {e}")
            
        return None
    
    async def _process_active_window(self, window_info: Dict[str, Any]):
        """Process active window information to detect document activity."""
        title = window_info.get('title', '').lower()
        process = window_info.get('process', '').lower()
        
        # Check if it's a document editing application
        document_apps = [
            'word', 'writer', 'pages', 'notepad', 'textedit', 'sublime',
            'vscode', 'atom', 'vim', 'emacs', 'nano', 'gedit', 'kate',
            'typora', 'obsidian', 'notion', 'bear', 'ulysses'
        ]
        
        is_document_app = any(app in process for app in document_apps)
        
        # Check if title suggests a document
        document_indicators = ['.txt', '.md', '.doc', '.rtf', '.pdf']
        has_document_title = any(ext in title for ext in document_indicators)
        
        if is_document_app or has_document_title:
            await self._track_document_activity(window_info)
    
    async def _track_document_activity(self, window_info: Dict[str, Any]):
        """Track activity on a specific document."""
        doc_key = f"{window_info.get('process', 'unknown')}:{window_info.get('title', 'untitled')}"
        current_time = time.time()
        
        # Update activity tracking
        if doc_key not in self.document_activity:
            self.document_activity[doc_key] = {
                'first_seen': current_time,
                'last_seen': current_time,
                'total_time': 0,
                'window_info': window_info
            }
        else:
            activity = self.document_activity[doc_key]
            time_diff = current_time - activity['last_seen']
            
            # Only count as active time if less than activity threshold
            if time_diff < self.activity_threshold:
                activity['total_time'] += time_diff
            
            activity['last_seen'] = current_time
        
        # Check if this is significant activity (more than 30 seconds)
        activity = self.document_activity[doc_key]
        if activity['total_time'] > 30:
            await self._generate_contextual_suggestions(doc_key, window_info)
    
    async def _generate_contextual_suggestions(self, doc_key: str, window_info: Dict[str, Any]):
        """Generate contextual suggestions based on document activity."""
        try:
            # Extract potential search terms from window title
            title = window_info.get('title', '')
            search_terms = self._extract_search_terms(title)
            
            suggestions = []
            for term in search_terms[:3]:  # Limit to 3 terms
                if len(term) > 3:  # Only meaningful terms
                    results = await self.search_engine.search(
                        term, 
                        limit=self.max_suggestions,
                        similarity_threshold=0.4
                    )
                    suggestions.extend(results)
            
            # Remove duplicates and limit results
            unique_suggestions = self._deduplicate_suggestions(suggestions)
            
            if unique_suggestions:
                context_event = {
                    'type': 'document_activity',
                    'document_key': doc_key,
                    'window_info': window_info,
                    'suggestions': unique_suggestions[:self.max_suggestions],
                    'timestamp': time.time()
                }
                
                await self._notify_context_callbacks(context_event)
                
        except Exception as e:
            logger.error(f"Error generating contextual suggestions: {e}")
    
    def _extract_search_terms(self, title: str) -> List[str]:
        """Extract meaningful search terms from window title."""
        import re
        
        # Remove common file extensions and application names
        title = re.sub(r'\.(txt|md|doc|docx|pdf|rtf)$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*-\s*(Microsoft Word|Pages|TextEdit|Notepad).*$', '', title, flags=re.IGNORECASE)
        
        # Split into words and filter
        words = re.findall(r'\b\w{3,}\b', title)
        
        # Remove common stop words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        
        meaningful_words = [word for word in words if word.lower() not in stop_words]
        
        return meaningful_words[:5]  # Return top 5 terms
    
    def _deduplicate_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate suggestions."""
        seen = set()
        unique = []
        
        for suggestion in suggestions:
            content_key = suggestion.get('content', '')[:100]  # First 100 chars as key
            if content_key not in seen:
                seen.add(content_key)
                unique.append(suggestion)
        
        return unique
    
    async def _periodic_context_analysis(self):
        """Periodically analyze context and clean up old activity."""
        while self.is_monitoring:
            try:
                current_time = time.time()
                
                # Clean up old activity (older than 1 hour)
                cutoff_time = current_time - 3600
                self.document_activity = {
                    k: v for k, v in self.document_activity.items()
                    if v['last_seen'] > cutoff_time
                }
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in periodic context analysis: {e}")
                await asyncio.sleep(300)
    
    def add_context_callback(self, callback: Callable):
        """Add a callback for context events."""
        self.context_callbacks.append(callback)
    
    async def _notify_context_callbacks(self, context_event: Dict[str, Any]):
        """Notify all registered context callbacks."""
        for callback in self.context_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(context_event)
                else:
                    callback(context_event)
            except Exception as e:
                logger.error(f"Error in context callback: {e}")


class DocumentEventHandler(FileSystemEventHandler):
    """Handles file system events for document monitoring."""
    
    def __init__(self, monitor: DocumentMonitor):
        self.monitor = monitor
    
    def on_modified(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.monitor.monitored_extensions:
                asyncio.create_task(self._handle_file_change(file_path, 'modified'))
    
    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.monitor.monitored_extensions:
                asyncio.create_task(self._handle_file_change(file_path, 'created'))
    
    async def _handle_file_change(self, file_path: Path, change_type: str):
        """Handle file change events."""
        try:
            # Generate suggestions based on file name and content
            search_terms = self.monitor._extract_search_terms(file_path.stem)
            
            if search_terms:
                suggestions = []
                for term in search_terms[:2]:
                    results = await self.monitor.search_engine.search(
                        term,
                        limit=3,
                        similarity_threshold=0.4
                    )
                    suggestions.extend(results)
                
                if suggestions:
                    context_event = {
                        'type': 'file_change',
                        'change_type': change_type,
                        'file_path': str(file_path),
                        'suggestions': suggestions[:3],
                        'timestamp': time.time()
                    }
                    
                    await self.monitor._notify_context_callbacks(context_event)
                    
        except Exception as e:
            logger.error(f"Error handling file change: {e}")
