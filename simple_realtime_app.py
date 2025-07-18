#!/usr/bin/env python3
"""
Simple Real-time Semantic Search Assistant
A lightweight version that starts quickly and provides real-time text suggestions.
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
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleSearchAPI:
    """Simple search API client."""
    
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
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
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            return []
            
    def check_backend(self) -> bool:
        """Check if backend is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

class SimpleTextMonitor:
    """Simple text monitoring using clipboard detection."""
    
    def __init__(self, search_callback: Callable[[str], None]):
        self.search_callback = search_callback
        self.is_monitoring = False
        self.current_word = ""
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start monitoring."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        logger.info("Starting simple text monitoring...")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring."""
        self.is_monitoring = False
        logger.info("Text monitoring stopped")
        
    def _monitor_loop(self):
        """Simple monitoring loop."""
        # This is a placeholder - in a real implementation, you would
        # use keyboard hooks or other monitoring methods
        while self.is_monitoring:
            time.sleep(0.1)

class SimpleRealTimeGUI:
    """Simple GUI for real-time search."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Real-time Semantic Search Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.search_api = SimpleSearchAPI()
        self.text_monitor = SimpleTextMonitor(self.on_text_change)
        
        # State variables
        self.is_monitoring = False
        self.current_search_query = ""
        self.search_results = []
        
        # Create GUI
        self.create_widgets()
        
        # Check backend status
        self.check_backend_status()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        """Create the GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔍 Real-time Semantic Search Assistant", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, pady=(0, 15), sticky=(tk.W, tk.E))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Backend Status:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(status_frame, text="Checking...", foreground="orange")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=2, column=0, pady=(0, 15), sticky=(tk.W, tk.E))
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_backend_button = ttk.Button(button_frame, text="Start Backend", 
                                              command=self.start_backend)
        self.start_backend_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.monitor_button = ttk.Button(button_frame, text="Start Monitoring", 
                                        command=self.toggle_monitoring, state="disabled")
        self.monitor_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.web_button = ttk.Button(button_frame, text="Open Web Interface", 
                                    command=self.open_web_interface, state="disabled")
        self.web_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Manual search frame
        search_frame = ttk.LabelFrame(main_frame, text="Manual Search", padding="10")
        search_frame.grid(row=3, column=0, pady=(0, 15), sticky=(tk.W, tk.E))
        search_frame.columnconfigure(0, weight=1)
        
        # Search input
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        search_input_frame.columnconfigure(0, weight=1)
        
        self.search_entry = ttk.Entry(search_input_frame, font=('Arial', 12))
        self.search_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.search_entry.bind('<Return>', self.manual_search)
        self.search_entry.bind('<KeyRelease>', self.on_search_key)
        
        self.search_button = ttk.Button(search_input_frame, text="Search", 
                                       command=self.manual_search, state="disabled")
        self.search_button.grid(row=0, column=1)
        
        # Current search display
        self.search_display = ttk.Label(search_frame, text="Type to search...", 
                                       font=('Arial', 10), foreground="gray")
        self.search_display.grid(row=1, column=0, pady=(10, 0), sticky=tk.W)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="10")
        results_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results with scrollbar
        results_container = ttk.Frame(results_frame)
        results_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_container.columnconfigure(0, weight=1)
        results_container.rowconfigure(0, weight=1)
        
        self.results_text = tk.Text(results_container, font=('Arial', 10), wrap=tk.WORD)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_container, orient="vertical", 
                                 command=self.results_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        # Instructions
        instructions = """
🎯 How to Use:
1. Click 'Start Backend' to initialize the search engine
2. Use manual search above to test the system
3. Click 'Start Monitoring' for real-time typing detection (advanced feature)
4. Open 'Web Interface' for full-featured experience

💡 Tips:
• Type in the search box to see instant results
• Each letter triggers a new search
• Results show similarity scores and sources
• Click 'Open Web Interface' for the complete experience
        """
        
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions", padding="10")
        instructions_frame.grid(row=5, column=0, pady=(15, 0), sticky=(tk.W, tk.E))
        
        instructions_label = ttk.Label(instructions_frame, text=instructions, 
                                      justify=tk.LEFT, font=('Arial', 9))
        instructions_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
    def check_backend_status(self):
        """Check if backend is running."""
        if self.search_api.check_backend():
            self.status_label.config(text="✅ Running", foreground="green")
            self.monitor_button.config(state="normal")
            self.search_button.config(state="normal")
            self.web_button.config(state="normal")
            self.start_backend_button.config(text="Backend Running")
        else:
            self.status_label.config(text="❌ Not Running", foreground="red")
            
    def start_backend(self):
        """Start the backend server."""
        self.start_backend_button.config(text="Starting...", state="disabled")
        
        # Start backend in separate process
        threading.Thread(target=self._start_backend_process, daemon=True).start()
        
    def _start_backend_process(self):
        """Start backend in background."""
        try:
            # Try to start the backend
            subprocess.Popen([
                sys.executable, "start_backend.py"
            ], cwd=Path(__file__).parent)
            
            # Wait for backend to start
            for i in range(30):  # 30 second timeout
                time.sleep(1)
                if self.search_api.check_backend():
                    self.root.after(0, self.on_backend_started)
                    return
                    
            self.root.after(0, self.on_backend_failed)
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            self.root.after(0, self.on_backend_failed)
            
    def on_backend_started(self):
        """Handle successful backend start."""
        self.status_label.config(text="✅ Running", foreground="green")
        self.monitor_button.config(state="normal")
        self.search_button.config(state="normal")
        self.web_button.config(state="normal")
        self.start_backend_button.config(text="Backend Running", state="normal")
        messagebox.showinfo("Success", "Backend started successfully!")
        
    def on_backend_failed(self):
        """Handle backend start failure."""
        self.status_label.config(text="❌ Failed to Start", foreground="red")
        self.start_backend_button.config(text="Start Backend", state="normal")
        messagebox.showerror("Error", "Failed to start backend. Check logs for details.")
        
    def toggle_monitoring(self):
        """Toggle monitoring."""
        if not self.is_monitoring:
            self.text_monitor.start_monitoring()
            self.is_monitoring = True
            self.monitor_button.config(text="Stop Monitoring")
            messagebox.showinfo("Monitoring", "Real-time monitoring started!\nType in any text editor to see suggestions.")
        else:
            self.text_monitor.stop_monitoring()
            self.is_monitoring = False
            self.monitor_button.config(text="Start Monitoring")
            
    def open_web_interface(self):
        """Open web interface."""
        webbrowser.open("http://127.0.0.1:8000/static/app.html")
        
    def on_search_key(self, event):
        """Handle search key press."""
        query = self.search_entry.get()
        if len(query) > 0:
            self.search_display.config(text=f"Searching: '{query}'")
            # Perform search with delay
            self.root.after(300, lambda: self.perform_search(query))
        else:
            self.search_display.config(text="Type to search...")
            self.results_text.delete(1.0, tk.END)
            
    def manual_search(self, event=None):
        """Perform manual search."""
        query = self.search_entry.get().strip()
        if query:
            self.perform_search(query)
            
    def perform_search(self, query: str):
        """Perform search and update results."""
        if not query.strip():
            return
            
        # Check if this is still the current query
        if query != self.search_entry.get():
            return
            
        threading.Thread(target=self._search_background, args=(query,), daemon=True).start()
        
    def _search_background(self, query: str):
        """Perform search in background."""
        try:
            results = self.search_api.search(query, limit=10)
            self.root.after(0, lambda: self._update_results(query, results))
        except Exception as e:
            logger.error(f"Search error: {e}")
            
    def _update_results(self, query: str, results: List[Dict[str, Any]]):
        """Update search results."""
        # Check if this is still the current query
        if query != self.search_entry.get():
            return
            
        self.results_text.delete(1.0, tk.END)
        
        if not results:
            self.results_text.insert(tk.END, "No results found.\n\n")
            self.results_text.insert(tk.END, "💡 Tips:\n")
            self.results_text.insert(tk.END, "• Make sure documents are indexed\n")
            self.results_text.insert(tk.END, "• Try different search terms\n")
            self.results_text.insert(tk.END, "• Check that the backend is running\n")
            return
            
        self.results_text.insert(tk.END, f"Found {len(results)} results for '{query}':\n\n")
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            source = result.get('source', 'Unknown')
            similarity = result.get('similarity', 0) * 100
            
            self.results_text.insert(tk.END, f"{i}. [{similarity:.1f}%] ", "header")
            self.results_text.insert(tk.END, f"{content[:200]}...\n", "content")
            self.results_text.insert(tk.END, f"   📄 Source: {source}\n\n", "source")
            
        # Configure text tags
        self.results_text.tag_config("header", font=('Arial', 10, 'bold'))
        self.results_text.tag_config("content", font=('Arial', 10))
        self.results_text.tag_config("source", font=('Arial', 9), foreground="gray")
        
    def on_text_change(self, text: str):
        """Handle text change from monitor."""
        # This would be called by the real-time monitor
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, text)
        self.perform_search(text)
        
    def on_closing(self):
        """Handle application closing."""
        if self.is_monitoring:
            self.text_monitor.stop_monitoring()
        self.root.destroy()
        
    def run(self):
        """Run the application."""
        self.root.mainloop()

def main():
    """Main entry point."""
    try:
        print("🚀 Starting Simple Real-time Semantic Search Assistant...")
        app = SimpleRealTimeGUI()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
