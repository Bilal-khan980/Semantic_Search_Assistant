#!/usr/bin/env python3
"""
Real-time Semantic Search Assistant - Working Version
A desktop application that provides real-time text suggestions with letter-by-letter search.
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SearchAPI:
    """Handles communication with the backend search API."""
    
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
            
    def check_backend(self) -> bool:
        """Check if backend is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def process_documents(self, file_paths: List[str]) -> bool:
        """Process documents for indexing."""
        try:
            response = requests.post(
                f"{self.base_url}/process",
                json={"file_paths": file_paths},
                timeout=60
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
        self.root.geometry("1000x800")
        self.root.configure(bg='#f5f5f5')
        
        # Initialize components
        self.search_api = SearchAPI()
        
        # State variables
        self.current_search_query = ""
        self.search_results = []
        self.backend_running = False
        
        # Create GUI
        self.create_widgets()
        self.setup_styles()
        
        # Check backend status
        self.check_backend_status()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🔍 Real-time Semantic Search Assistant", 
                               font=('Arial', 20, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Type to search • Press SPACEBAR to clear • Letter-by-letter suggestions", 
                                  font=('Arial', 11), foreground='gray')
        subtitle_label.pack(pady=(5, 0))
        
        # Status and controls frame
        control_frame = ttk.LabelFrame(main_container, text="Controls", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Backend Status:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Checking...", font=('Arial', 11))
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_backend_btn = ttk.Button(button_frame, text="🚀 Start Backend", 
                                           command=self.start_backend)
        self.start_backend_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.add_docs_btn = ttk.Button(button_frame, text="📁 Add Documents", 
                                      command=self.add_documents, state="disabled")
        self.add_docs_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.web_btn = ttk.Button(button_frame, text="🌐 Web Interface", 
                                 command=self.open_web_interface, state="disabled")
        self.web_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Real-time search frame
        search_frame = ttk.LabelFrame(main_container, text="Real-time Search", padding=15)
        search_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Search input
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_input_frame, text="Type here:", font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        self.search_entry = ttk.Entry(search_input_frame, font=('Arial', 14))
        self.search_entry.pack(fill=tk.X, pady=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.on_key_release)
        self.search_entry.bind('<Key>', self.on_key_press)
        
        # Current search display
        self.search_display = ttk.Label(search_frame, text="Start typing to see real-time suggestions...", 
                                       font=('Arial', 10), foreground="gray")
        self.search_display.pack(anchor=tk.W, pady=(5, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_container, text="Search Results", padding=15)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results display
        results_container = ttk.Frame(results_frame)
        results_container.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for better results display
        columns = ('Score', 'Content', 'Source')
        self.results_tree = ttk.Treeview(results_container, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.results_tree.heading('Score', text='Score')
        self.results_tree.heading('Content', text='Content')
        self.results_tree.heading('Source', text='Source')
        
        self.results_tree.column('Score', width=80, minwidth=80)
        self.results_tree.column('Content', width=600, minwidth=400)
        self.results_tree.column('Source', width=200, minwidth=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_container, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_container, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and treeview
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind double-click to copy
        self.results_tree.bind('<Double-1>', self.copy_selected_result)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(main_container, text="How to Use", padding=10)
        instructions_frame.pack(fill=tk.X, pady=(20, 0))
        
        instructions = """
🎯 Quick Start: 1) Start Backend → 2) Add Documents → 3) Type in the search box above
⌨️  Real-time Search: Each letter you type triggers an instant search
🔄 Clear Search: Press SPACEBAR to clear and start a new word  
📋 Copy Results: Double-click any result to copy it to clipboard
🌐 Full Features: Click 'Web Interface' for the complete experience
        """
        
        ttk.Label(instructions_frame, text=instructions, font=('Arial', 9), justify=tk.LEFT).pack(anchor=tk.W)
        
    def setup_styles(self):
        """Setup custom styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
    def check_backend_status(self):
        """Check backend status and update UI."""
        if self.search_api.check_backend():
            self.status_label.config(text="✅ Running", foreground="green")
            self.backend_running = True
            self.start_backend_btn.config(text="✅ Backend Running")
            self.add_docs_btn.config(state="normal")
            self.web_btn.config(state="normal")
        else:
            self.status_label.config(text="❌ Not Running", foreground="red")
            self.backend_running = False
            
    def start_backend(self):
        """Start the backend server."""
        if self.backend_running:
            return
            
        self.start_backend_btn.config(text="Starting...", state="disabled")
        self.status_label.config(text="🔄 Starting...", foreground="orange")
        
        # Start backend in background
        threading.Thread(target=self._start_backend_process, daemon=True).start()
        
    def _start_backend_process(self):
        """Start backend process."""
        try:
            # Start the backend
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
        self.backend_running = True
        self.status_label.config(text="✅ Running", foreground="green")
        self.start_backend_btn.config(text="✅ Backend Running", state="normal")
        self.add_docs_btn.config(state="normal")
        self.web_btn.config(state="normal")
        messagebox.showinfo("Success", "Backend started successfully!\nYou can now add documents and start searching.")
        
    def on_backend_failed(self):
        """Handle backend start failure."""
        self.status_label.config(text="❌ Failed", foreground="red")
        self.start_backend_btn.config(text="🚀 Start Backend", state="normal")
        messagebox.showerror("Error", "Failed to start backend.\nMake sure all dependencies are installed.")
        
    def add_documents(self):
        """Add documents for indexing."""
        if not self.backend_running:
            messagebox.showwarning("Warning", "Please start the backend first.")
            return
            
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
            self.add_docs_btn.config(text="Processing...", state="disabled")
            threading.Thread(
                target=self._process_documents_background,
                args=(list(file_paths),),
                daemon=True
            ).start()
            
    def _process_documents_background(self, file_paths: List[str]):
        """Process documents in background."""
        try:
            success = self.search_api.process_documents(file_paths)
            
            if success:
                self.root.after(0, lambda: self._on_documents_processed(len(file_paths), True))
            else:
                self.root.after(0, lambda: self._on_documents_processed(len(file_paths), False))
                
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            self.root.after(0, lambda: self._on_documents_processed(len(file_paths), False))
            
    def _on_documents_processed(self, count: int, success: bool):
        """Handle document processing completion."""
        self.add_docs_btn.config(text="📁 Add Documents", state="normal")
        
        if success:
            messagebox.showinfo("Success", f"Successfully processed {count} documents!\nYou can now search for content.")
        else:
            messagebox.showerror("Error", "Failed to process some documents.\nCheck the logs for details.")
            
    def open_web_interface(self):
        """Open web interface."""
        if not self.backend_running:
            messagebox.showwarning("Warning", "Please start the backend first.")
            return
            
        webbrowser.open("http://127.0.0.1:8000/static/app.html")
        
    def on_key_press(self, event):
        """Handle key press events."""
        # Handle spacebar to clear search
        if event.keysym == 'space':
            self.root.after(10, self.clear_search)  # Clear after the space is processed
            
    def clear_search(self):
        """Clear the search."""
        self.search_entry.delete(0, tk.END)
        self.search_display.config(text="Search cleared - start typing for new search...")
        self.clear_results()
        
    def on_key_release(self, event):
        """Handle key release for real-time search."""
        query = self.search_entry.get().strip()
        
        if not query:
            self.search_display.config(text="Start typing to see real-time suggestions...")
            self.clear_results()
            return
            
        # Update search display
        self.search_display.config(text=f"🔍 Searching: '{query}' (Press SPACEBAR to clear)")
        
        # Perform search with slight delay for better performance
        self.root.after(200, lambda: self.perform_search(query))
        
    def perform_search(self, query: str):
        """Perform search if query is still current."""
        current_query = self.search_entry.get().strip()
        if query != current_query:
            return  # Query has changed, skip this search
            
        if not self.backend_running:
            return
            
        threading.Thread(target=self._search_background, args=(query,), daemon=True).start()
        
    def _search_background(self, query: str):
        """Perform search in background."""
        try:
            results = self.search_api.search(query, limit=15)
            self.root.after(0, lambda: self._update_results(query, results))
        except Exception as e:
            logger.error(f"Search error: {e}")
            
    def _update_results(self, query: str, results: List[Dict[str, Any]]):
        """Update search results."""
        # Check if query is still current
        current_query = self.search_entry.get().strip()
        if query != current_query:
            return
            
        self.search_results = results
        self.clear_results()
        
        if not results:
            # Insert "no results" message
            self.results_tree.insert('', 'end', values=('--', 'No results found. Try different search terms.', '--'))
            return
            
        # Insert results
        for result in results:
            content = result.get('content', '')[:150] + "..." if len(result.get('content', '')) > 150 else result.get('content', '')
            source = result.get('source', 'Unknown')
            similarity = f"{result.get('similarity', 0) * 100:.1f}%"
            
            self.results_tree.insert('', 'end', values=(similarity, content, source))
            
    def clear_results(self):
        """Clear search results."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
    def copy_selected_result(self, event):
        """Copy selected result to clipboard."""
        selection = self.results_tree.selection()
        if not selection or not self.search_results:
            return
            
        item = self.results_tree.item(selection[0])
        if not item['values'] or item['values'][0] == '--':
            return
            
        # Find the corresponding result
        content_preview = item['values'][1]
        for result in self.search_results:
            if result.get('content', '').startswith(content_preview.replace('...', '')):
                full_content = result.get('content', '')
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(full_content)
                    messagebox.showinfo("Copied", "Result copied to clipboard!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy: {e}")
                break
                
    def on_closing(self):
        """Handle application closing."""
        self.root.destroy()
        
    def run(self):
        """Run the application."""
        self.root.mainloop()

def main():
    """Main entry point."""
    try:
        print("🚀 Starting Real-time Semantic Search Assistant...")
        print("📝 Features: Letter-by-letter search, spacebar clearing, instant results")
        print("=" * 70)
        
        app = RealTimeSearchGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
