#!/usr/bin/env python3
"""
Global Keyboard Monitor for Real-time Semantic Search
Monitors typing in ANY application and mirrors it in the search interface.
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

# Try to import keyboard monitoring
try:
    import keyboard
    import pyperclip
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('global_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GlobalKeyboardMonitor:
    """Monitors keyboard input globally across all applications."""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.is_monitoring = False
        self.current_word = ""
        self.last_window_title = ""
        
    def start_monitoring(self):
        """Start global keyboard monitoring."""
        if not MONITORING_AVAILABLE:
            logger.error("Keyboard monitoring not available. Install: pip install keyboard pyperclip")
            return False
            
        if self.is_monitoring:
            return True
            
        try:
            self.is_monitoring = True
            
            # Set up global keyboard hooks
            keyboard.on_press(self._on_key_press)
            
            logger.info("Global keyboard monitoring started")
            logger.info("Type in any application - text will appear in search!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start keyboard monitoring: {e}")
            self.is_monitoring = False
            return False
            
    def stop_monitoring(self):
        """Stop monitoring."""
        if MONITORING_AVAILABLE and self.is_monitoring:
            try:
                keyboard.unhook_all()
            except:
                pass
        self.is_monitoring = False
        logger.info("Global keyboard monitoring stopped")
        
    def _on_key_press(self, key):
        """Handle global key press events."""
        if not self.is_monitoring:
            return
            
        try:
            key_name = key.name if hasattr(key, 'name') else str(key)
            
            # Handle spacebar - clear current word and search
            if key_name == 'space':
                if self.current_word.strip():
                    self.current_word = ""
                    self.callback("")  # Clear search
                return
                
            # Handle backspace
            elif key_name == 'backspace':
                if self.current_word:
                    self.current_word = self.current_word[:-1]
                    self.callback(self.current_word)
                return
                
            # Handle Enter - clear word
            elif key_name == 'enter':
                self.current_word = ""
                self.callback("")
                return
                
            # Handle regular characters (letters and numbers)
            elif len(key_name) == 1 and (key_name.isalnum() or key_name in ".,!?;:-'\""):
                self.current_word += key_name
                self.callback(self.current_word)
                
        except Exception as e:
            logger.error(f"Error in key press handler: {e}")

class SearchAPI:
    """Handles search API communication."""
    
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

class GlobalMonitorGUI:
    """GUI for global keyboard monitoring and search."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Global Real-time Search Monitor")
        self.root.geometry("1100x900")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.search_api = SearchAPI()
        self.keyboard_monitor = GlobalKeyboardMonitor(self.on_text_detected)
        
        # State variables
        self.is_monitoring = False
        self.current_query = ""
        self.search_results = []
        self.backend_running = False
        
        # Create GUI
        self.create_widgets()
        
        # Check backend status
        self.check_backend_status()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Make window always on top (optional)
        self.root.attributes('-topmost', True)
        
    def create_widgets(self):
        """Create the GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🌍 Global Real-time Search Monitor", 
                               font=('Arial', 22, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, 
                                  text="Type in ANY application • Watch text appear here • Get instant suggestions", 
                                  font=('Arial', 12), foreground='#666')
        subtitle_label.pack(pady=(5, 0))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding=15)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Backend status
        backend_frame = ttk.Frame(status_frame)
        backend_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(backend_frame, text="Backend:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
        self.backend_status = ttk.Label(backend_frame, text="Checking...", font=('Arial', 11))
        self.backend_status.pack(side=tk.LEFT, padx=(10, 0))
        
        # Monitoring status
        monitor_frame = ttk.Frame(status_frame)
        monitor_frame.pack(fill=tk.X)
        
        ttk.Label(monitor_frame, text="Global Monitoring:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
        self.monitor_status = ttk.Label(monitor_frame, text="Stopped", font=('Arial', 11), foreground='red')
        self.monitor_status.pack(side=tk.LEFT, padx=(10, 0))
        
        # Control buttons
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_backend_btn = ttk.Button(button_frame, text="🚀 Start Backend", 
                                           command=self.start_backend)
        self.start_backend_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_monitor_btn = ttk.Button(button_frame, text="🌍 Start Global Monitoring", 
                                           command=self.toggle_monitoring, state="disabled")
        self.start_monitor_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.web_btn = ttk.Button(button_frame, text="🌐 Web Interface", 
                                 command=self.open_web_interface, state="disabled")
        self.web_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Current typing display
        typing_frame = ttk.LabelFrame(main_frame, text="Live Typing Detection", padding=15)
        typing_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Current word display
        word_frame = ttk.Frame(typing_frame)
        word_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(word_frame, text="Current Word:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        self.current_word_label = ttk.Label(word_frame, text="(not monitoring)", 
                                           font=('Arial', 14), foreground='gray',
                                           background='white', relief='sunken', padding=10)
        self.current_word_label.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Instructions
        instructions_text = """
🎯 How it works:
1. Start Backend → 2. Start Global Monitoring → 3. Type in ANY application
4. Watch your typing appear above in real-time!
5. Press SPACEBAR to clear and start new word
        """
        
        ttk.Label(typing_frame, text=instructions_text, font=('Arial', 10), 
                 justify=tk.LEFT, foreground='#555').pack(anchor=tk.W, pady=(10, 0))
        
        # Search results
        results_frame = ttk.LabelFrame(main_frame, text="Live Search Results", padding=15)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results display
        results_container = ttk.Frame(results_frame)
        results_container.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget for results
        self.results_text = tk.Text(results_container, font=('Arial', 11), wrap=tk.WORD, height=15)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_container, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        # Bind double-click to copy
        self.results_text.bind('<Double-1>', self.copy_result_at_cursor)
        
        # Initial message
        self.results_text.insert(tk.END, "🔍 Start global monitoring and type in any application to see live search results!\n\n")
        self.results_text.insert(tk.END, "💡 Tips:\n")
        self.results_text.insert(tk.END, "• Type in Notepad, Word, VS Code, or any text editor\n")
        self.results_text.insert(tk.END, "• Each letter triggers a search\n")
        self.results_text.insert(tk.END, "• Press SPACEBAR to clear and start new word\n")
        self.results_text.insert(tk.END, "• Double-click any result to copy it\n")
        
    def check_backend_status(self):
        """Check backend status."""
        if self.search_api.check_backend():
            self.backend_status.config(text="✅ Running", foreground="green")
            self.backend_running = True
            self.start_backend_btn.config(text="✅ Backend Running")
            self.start_monitor_btn.config(state="normal")
            self.web_btn.config(state="normal")
        else:
            self.backend_status.config(text="❌ Not Running", foreground="red")
            self.backend_running = False
            
    def start_backend(self):
        """Start the backend server."""
        if self.backend_running:
            return
            
        self.start_backend_btn.config(text="Starting...", state="disabled")
        self.backend_status.config(text="🔄 Starting...", foreground="orange")
        
        # Start backend in background
        threading.Thread(target=self._start_backend_process, daemon=True).start()
        
    def _start_backend_process(self):
        """Start backend process."""
        try:
            subprocess.Popen([sys.executable, "start_backend.py"], cwd=Path(__file__).parent)
            
            # Wait for backend to start
            for i in range(30):
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
        self.backend_status.config(text="✅ Running", foreground="green")
        self.start_backend_btn.config(text="✅ Backend Running", state="normal")
        self.start_monitor_btn.config(state="normal")
        self.web_btn.config(state="normal")
        messagebox.showinfo("Success", "Backend started!\nNow click 'Start Global Monitoring' to begin.")
        
    def on_backend_failed(self):
        """Handle backend start failure."""
        self.backend_status.config(text="❌ Failed", foreground="red")
        self.start_backend_btn.config(text="🚀 Start Backend", state="normal")
        messagebox.showerror("Error", "Failed to start backend.\nMake sure dependencies are installed.")
        
    def toggle_monitoring(self):
        """Toggle global monitoring."""
        if not MONITORING_AVAILABLE:
            messagebox.showerror("Error", 
                               "Global monitoring requires additional packages.\n\n"
                               "Install with: pip install keyboard pyperclip\n\n"
                               "Note: You may need to run as administrator.")
            return
            
        if not self.is_monitoring:
            success = self.keyboard_monitor.start_monitoring()
            if success:
                self.is_monitoring = True
                self.start_monitor_btn.config(text="🛑 Stop Monitoring")
                self.monitor_status.config(text="✅ Active", foreground="green")
                self.current_word_label.config(text="Ready - type in any application!", foreground="blue")
                
                messagebox.showinfo("Global Monitoring Started", 
                                  "🌍 Global keyboard monitoring is now active!\n\n"
                                  "✨ Type in ANY application:\n"
                                  "• Notepad, Word, VS Code, etc.\n"
                                  "• Watch text appear in this window\n"
                                  "• Get instant search suggestions\n"
                                  "• Press SPACEBAR to clear search\n\n"
                                  "⚠️ If monitoring doesn't work, try running as administrator.")
            else:
                messagebox.showerror("Error", "Failed to start global monitoring.\nTry running as administrator.")
        else:
            self.keyboard_monitor.stop_monitoring()
            self.is_monitoring = False
            self.start_monitor_btn.config(text="🌍 Start Global Monitoring")
            self.monitor_status.config(text="❌ Stopped", foreground="red")
            self.current_word_label.config(text="(not monitoring)", foreground="gray")
            
    def open_web_interface(self):
        """Open web interface."""
        webbrowser.open("http://127.0.0.1:8000/static/app.html")
        
    def on_text_detected(self, text: str):
        """Handle text detected from global monitoring."""
        self.current_query = text
        
        # Update current word display
        if text:
            self.current_word_label.config(text=f"'{text}'", foreground="blue")
        else:
            self.current_word_label.config(text="(cleared - ready for next word)", foreground="green")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Search cleared. Start typing for new search...\n")
            return
            
        # Perform search
        if len(text) >= 1:  # Search even for single characters
            threading.Thread(target=self._search_background, args=(text,), daemon=True).start()
            
    def _search_background(self, query: str):
        """Perform search in background."""
        try:
            results = self.search_api.search(query, limit=10)
            self.root.after(0, lambda: self._update_results(query, results))
        except Exception as e:
            logger.error(f"Search error: {e}")
            
    def _update_results(self, query: str, results: List[Dict[str, Any]]):
        """Update search results."""
        # Check if query is still current
        if query != self.current_query:
            return
            
        self.search_results = results
        self.results_text.delete(1.0, tk.END)
        
        if not results:
            self.results_text.insert(tk.END, f"🔍 Searching for: '{query}'\n\n")
            self.results_text.insert(tk.END, "No results found.\n\n")
            self.results_text.insert(tk.END, "💡 Try:\n")
            self.results_text.insert(tk.END, "• Adding more documents\n")
            self.results_text.insert(tk.END, "• Different search terms\n")
            self.results_text.insert(tk.END, "• Continuing to type more letters\n")
            return
            
        self.results_text.insert(tk.END, f"🔍 Live search for: '{query}' ({len(results)} results)\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            source = result.get('source', 'Unknown')
            similarity = result.get('similarity', 0) * 100
            
            self.results_text.insert(tk.END, f"{i}. [{similarity:.1f}%] ", "header")
            self.results_text.insert(tk.END, f"{content[:200]}...\n", "content")
            self.results_text.insert(tk.END, f"   📄 {source}\n\n", "source")
            
        self.results_text.insert(tk.END, "💡 Double-click any result to copy it to clipboard!\n")
        
        # Configure text tags
        self.results_text.tag_config("header", font=('Arial', 11, 'bold'), foreground='#0066cc')
        self.results_text.tag_config("content", font=('Arial', 11))
        self.results_text.tag_config("source", font=('Arial', 10), foreground='gray')
        
        # Scroll to top
        self.results_text.see(1.0)
        
    def copy_result_at_cursor(self, event):
        """Copy result at cursor position."""
        if not self.search_results:
            return
            
        # Get the line number where user clicked
        index = self.results_text.index(tk.CURRENT)
        line_num = int(index.split('.')[0])
        
        # Find which result this corresponds to
        text_content = self.results_text.get(1.0, tk.END)
        lines = text_content.split('\n')
        
        result_index = -1
        current_result = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{current_result + 1}."):
                if i + 1 <= line_num <= i + 3:  # Result spans 3 lines
                    result_index = current_result
                    break
                current_result += 1
                
        if 0 <= result_index < len(self.search_results):
            result = self.search_results[result_index]
            content = result.get('content', '')
            
            try:
                if MONITORING_AVAILABLE:
                    pyperclip.copy(content)
                else:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(content)
                    
                messagebox.showinfo("Copied", f"Result {result_index + 1} copied to clipboard!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy: {e}")
                
    def on_closing(self):
        """Handle application closing."""
        if self.is_monitoring:
            self.keyboard_monitor.stop_monitoring()
        self.root.destroy()
        
    def run(self):
        """Run the application."""
        self.root.mainloop()

def main():
    """Main entry point."""
    try:
        print("🌍 Global Real-time Search Monitor")
        print("=" * 50)
        print("✨ Features:")
        print("  • Monitors typing in ANY application")
        print("  • Real-time search as you type")
        print("  • Press SPACEBAR to clear search")
        print("  • Copy results with double-click")
        print("=" * 50)
        print()
        
        if not MONITORING_AVAILABLE:
            print("⚠️  Global monitoring requires additional packages:")
            print("   pip install keyboard pyperclip")
            print("   (You may need to run as administrator)")
            print()
        
        app = GlobalMonitorGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
