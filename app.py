#!/usr/bin/env python3
"""
Real-time Semantic Search Assistant
A desktop application that provides real-time text suggestions as you type in any text editor.
Features letter-by-letter search and spacebar clearing functionality.
"""

import asyncio
import threading
import time
import logging
import sys
import os
import webbrowser
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import uvicorn
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
# Optional imports - will work without these
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
import re

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import our backend components
from api_service import app as fastapi_app, initialize_backend
from document_processor import DocumentProcessor
from search_engine import SearchEngine
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealTimeTextMonitor:
    """Monitors text input in real-time across all applications."""
    
    def __init__(self, search_callback: Callable[[str], None]):
        self.search_callback = search_callback
        self.is_monitoring = False
        self.current_word = ""
        self.last_window = None
        self.typing_buffer = ""
        self.last_activity_time = 0
        
    def start_monitoring(self):
        """Start real-time text monitoring."""
        if self.is_monitoring:
            return

        if not KEYBOARD_AVAILABLE:
            logger.warning("Keyboard monitoring not available - install 'keyboard' package")
            return False

        self.is_monitoring = True
        logger.info("Starting real-time text monitoring...")

        try:
            # Set up keyboard hooks
            keyboard.on_press(self._on_key_press)
            logger.info("Real-time text monitoring started")
            return True
        except Exception as e:
            logger.error(f"Failed to start keyboard monitoring: {e}")
            self.is_monitoring = False
            return False

    def stop_monitoring(self):
        """Stop monitoring."""
        self.is_monitoring = False
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all()
            except:
                pass
        logger.info("Real-time text monitoring stopped")
        
    def _on_key_press(self, key):
        """Handle key press events."""
        if not self.is_monitoring:
            return
            
        try:
            # Get current active window (if available)
            current_window = ""
            if WIN32_AVAILABLE:
                try:
                    current_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                except:
                    current_window = ""

            # Only monitor text editors and word processors (if we can detect them)
            if WIN32_AVAILABLE and current_window and not self._is_text_application(current_window):
                return
                
            key_name = key.name if hasattr(key, 'name') else str(key)
            
            # Handle spacebar - clear current search
            if key_name == 'space':
                if self.current_word.strip():
                    self.current_word = ""
                    self.search_callback("")  # Clear search
                return
                
            # Handle backspace
            if key_name == 'backspace':
                if self.current_word:
                    self.current_word = self.current_word[:-1]
                    self.search_callback(self.current_word)
                return
                
            # Handle regular characters
            if len(key_name) == 1 and key_name.isalnum():
                self.current_word += key_name
                self.search_callback(self.current_word)
                
        except Exception as e:
            logger.error(f"Error in key press handler: {e}")
            
    def _is_text_application(self, window_title: str) -> bool:
        """Check if the current window is a text application."""
        text_apps = [
            'notepad', 'word', 'wordpad', 'sublime', 'vscode', 'code',
            'atom', 'notepad++', 'vim', 'emacs', 'gedit', 'nano',
            'writer', 'document', 'text', 'editor', 'typora',
            'obsidian', 'notion', 'roam', 'logseq', 'bear'
        ]
        
        window_lower = window_title.lower()
        return any(app in window_lower for app in text_apps)

class BackendServer:
    """Manages the FastAPI backend server."""
    
    def __init__(self):
        self.server_process = None
        self.is_running = False
        
    async def start(self):
        """Start the backend server."""
        try:
            logger.info("Initializing backend...")
            await initialize_backend()
            
            logger.info("Starting FastAPI server...")
            config = uvicorn.Config(
                fastapi_app,
                host="127.0.0.1",
                port=8000,
                log_level="info",
                access_log=False
            )
            
            server = uvicorn.Server(config)
            
            # Run server in background thread
            def run_server():
                asyncio.run(server.serve())
                
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Wait for server to start
            await self._wait_for_server()
            self.is_running = True
            logger.info("Backend server started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            raise
            
    async def _wait_for_server(self, timeout=30):
        """Wait for server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://127.0.0.1:8000/health", timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
            await asyncio.sleep(1)
        raise Exception("Server failed to start within timeout")
        
    def stop(self):
        """Stop the backend server."""
        self.is_running = False
        logger.info("Backend server stopped")

class SearchAPI:
    """Handles search API calls."""
    
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform search query."""
        if not query.strip():
            return []
            
        try:
            response = requests.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "limit": limit,
                    "similarity_threshold": 0.3
                },
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                logger.error(f"Search API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            return []
            
    async def process_documents(self, file_paths: List[str]) -> bool:
        """Process documents for indexing."""
        try:
            response = requests.post(
                f"{self.base_url}/process",
                json={"file_paths": file_paths},
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return False

class RealTimeSearchGUI:
    """Main GUI application for real-time search."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Real-time Semantic Search Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')

        # Initialize components
        self.backend_server = BackendServer()
        self.search_api = SearchAPI()
        self.text_monitor = RealTimeTextMonitor(self.on_text_change)

        # State variables
        self.is_monitoring = False
        self.current_search_query = ""
        self.search_results = []

        # Create GUI
        self.create_widgets()
        self.setup_styles()

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """Create the main GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🔍 Real-time Semantic Search Assistant",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))

        # Start/Stop monitoring button
        self.monitor_button = ttk.Button(control_frame, text="Start Monitoring",
                                        command=self.toggle_monitoring)
        self.monitor_button.pack(side=tk.LEFT, padx=(0, 10))

        # Add documents button
        self.add_docs_button = ttk.Button(control_frame, text="Add Documents",
                                         command=self.add_documents)
        self.add_docs_button.pack(side=tk.LEFT, padx=(0, 10))

        # Open web interface button
        self.web_button = ttk.Button(control_frame, text="Open Web Interface",
                                    command=self.open_web_interface)
        self.web_button.pack(side=tk.LEFT, padx=(0, 10))

        # Status label
        self.status_label = ttk.Label(control_frame, text="Backend: Not Started",
                                     foreground="red")
        self.status_label.pack(side=tk.RIGHT)

        # Search display frame
        search_frame = ttk.LabelFrame(main_frame, text="Current Search", padding="10")
        search_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        search_frame.columnconfigure(0, weight=1)

        # Current search query display
        self.search_display = ttk.Label(search_frame, text="No active search",
                                       font=('Arial', 12), background="white",
                                       relief="sunken", padding="5")
        self.search_display.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Results listbox with scrollbar
        results_container = ttk.Frame(results_frame)
        results_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_container.columnconfigure(0, weight=1)
        results_container.rowconfigure(0, weight=1)

        self.results_listbox = tk.Listbox(results_container, font=('Arial', 10))
        self.results_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar for results
        scrollbar = ttk.Scrollbar(results_container, orient="vertical",
                                 command=self.results_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_listbox.configure(yscrollcommand=scrollbar.set)

        # Bind double-click to copy result
        self.results_listbox.bind('<Double-1>', self.copy_selected_result)

        # Instructions frame
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions", padding="10")
        instructions_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))

        instructions_text = """
1. Click 'Start Monitoring' to begin real-time text monitoring
2. Open any text editor (Notepad, Word, VS Code, etc.)
3. Start typing - each letter will trigger a search
4. Press SPACEBAR to clear the current search and start a new word
5. Double-click any result to copy it to clipboard
6. Use 'Add Documents' to index your files for searching
        """

        instructions_label = ttk.Label(instructions_frame, text=instructions_text,
                                      justify=tk.LEFT, font=('Arial', 9))
        instructions_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

    def setup_styles(self):
        """Setup custom styles for the GUI."""
        style = ttk.Style()
        style.theme_use('clam')

    async def start_backend(self):
        """Start the backend server."""
        try:
            await self.backend_server.start()
            self.status_label.config(text="Backend: Running", foreground="green")
            self.monitor_button.config(state="normal")
            self.add_docs_button.config(state="normal")
            self.web_button.config(state="normal")
        except Exception as e:
            self.status_label.config(text=f"Backend: Error - {str(e)}", foreground="red")
            messagebox.showerror("Backend Error", f"Failed to start backend: {e}")

    def toggle_monitoring(self):
        """Toggle real-time monitoring."""
        if not self.is_monitoring:
            self.text_monitor.start_monitoring()
            self.is_monitoring = True
            self.monitor_button.config(text="Stop Monitoring")
            logger.info("Real-time monitoring started")
        else:
            self.text_monitor.stop_monitoring()
            self.is_monitoring = False
            self.monitor_button.config(text="Start Monitoring")
            self.search_display.config(text="No active search")
            self.results_listbox.delete(0, tk.END)
            logger.info("Real-time monitoring stopped")

    def add_documents(self):
        """Add documents for indexing."""
        file_paths = filedialog.askopenfilenames(
            title="Select Documents to Index",
            filetypes=[
                ("All supported", "*.txt *.pdf *.docx *.md"),
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )

        if file_paths:
            # Process documents in background
            threading.Thread(
                target=self._process_documents_background,
                args=(list(file_paths),),
                daemon=True
            ).start()

    def _process_documents_background(self, file_paths: List[str]):
        """Process documents in background thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            success = loop.run_until_complete(
                self.search_api.process_documents(file_paths)
            )

            if success:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", f"Successfully processed {len(file_paths)} documents!"
                ))
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Failed to process some documents. Check logs for details."
                ))

        except Exception as e:
            logger.error(f"Document processing error: {e}")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", f"Document processing failed: {e}"
            ))

    def open_web_interface(self):
        """Open the web interface in browser."""
        webbrowser.open("http://127.0.0.1:8000/static/app.html")

    def on_text_change(self, text: str):
        """Handle text change from monitor."""
        self.current_search_query = text

        # Update search display
        if text:
            self.search_display.config(text=f"Searching: '{text}'")
        else:
            self.search_display.config(text="Search cleared")
            self.results_listbox.delete(0, tk.END)
            return

        # Perform search in background
        threading.Thread(
            target=self._search_background,
            args=(text,),
            daemon=True
        ).start()

    def _search_background(self, query: str):
        """Perform search in background thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            results = loop.run_until_complete(
                self.search_api.search(query, limit=10)
            )

            # Update GUI in main thread
            self.root.after(0, lambda: self._update_search_results(results))

        except Exception as e:
            logger.error(f"Search error: {e}")

    def _update_search_results(self, results: List[Dict[str, Any]]):
        """Update search results in GUI."""
        self.search_results = results
        self.results_listbox.delete(0, tk.END)

        if not results:
            self.results_listbox.insert(tk.END, "No results found")
            return

        for i, result in enumerate(results):
            content = result.get('content', '')[:100] + "..."
            source = result.get('source', 'Unknown')
            similarity = result.get('similarity', 0) * 100

            display_text = f"[{similarity:.1f}%] {content} - {source}"
            self.results_listbox.insert(tk.END, display_text)

    def copy_selected_result(self, event):
        """Copy selected result to clipboard."""
        selection = self.results_listbox.curselection()
        if not selection or not self.search_results:
            return

        index = selection[0]
        if index < len(self.search_results):
            result = self.search_results[index]
            content = result.get('content', '')

            if CLIPBOARD_AVAILABLE:
                try:
                    pyperclip.copy(content)
                    messagebox.showinfo("Copied", "Result copied to clipboard!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            else:
                # Fallback: copy to tkinter clipboard
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(content)
                    messagebox.showinfo("Copied", "Result copied to clipboard!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")

    def on_closing(self):
        """Handle application closing."""
        if self.is_monitoring:
            self.text_monitor.stop_monitoring()
        self.backend_server.stop()
        self.root.destroy()

    def run(self):
        """Run the application."""
        # Start backend in background
        threading.Thread(
            target=lambda: asyncio.run(self.start_backend()),
            daemon=True
        ).start()

        # Start GUI main loop
        self.root.mainloop()

def main():
    """Main entry point."""
    try:
        # Create and run the application
        app = RealTimeSearchGUI()
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")
    finally:
        # Cleanup
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all()
            except:
                pass

if __name__ == "__main__":
    main()
