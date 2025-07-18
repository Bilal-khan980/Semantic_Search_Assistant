#!/usr/bin/env python3
"""
Simple Global Keyboard Monitor with Search
Exactly what you requested: Type in any editor, see text in search app, get suggestions.
"""

import threading
import time
import logging
import sys
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
import requests

# Try to import keyboard monitoring
try:
    import keyboard
    import pyperclip
    MONITORING_AVAILABLE = True
    print("✅ Keyboard monitoring available")
except ImportError:
    MONITORING_AVAILABLE = False
    print("❌ Keyboard monitoring not available - install: pip install keyboard pyperclip")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleGlobalMonitor:
    """Simple global keyboard monitor that captures typing from any application."""
    
    def __init__(self, callback):
        self.callback = callback
        self.is_monitoring = False
        self.current_word = ""
        
    def start_monitoring(self):
        """Start global keyboard monitoring."""
        if not MONITORING_AVAILABLE:
            return False
            
        if self.is_monitoring:
            return True
            
        try:
            self.is_monitoring = True
            keyboard.on_press(self._on_key_press)
            logger.info("Global keyboard monitoring started")
            return True
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
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
        logger.info("Monitoring stopped")
        
    def _on_key_press(self, key):
        """Handle key press events."""
        if not self.is_monitoring:
            return
            
        try:
            key_name = key.name if hasattr(key, 'name') else str(key)
            
            # Handle spacebar - clear search
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
                
            # Handle regular characters
            elif len(key_name) == 1 and key_name.isalnum():
                self.current_word += key_name
                self.callback(self.current_word)
                
        except Exception as e:
            logger.error(f"Error in key handler: {e}")

class SimpleSearchAPI:
    """Simple search API client."""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for query."""
        if not query.strip():
            return []
            
        try:
            response = requests.post(
                f"{self.base_url}/search",
                json={"query": query, "limit": 10, "similarity_threshold": 0.3},
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            return []
        except:
            return []
            
    def check_backend(self) -> bool:
        """Check if backend is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

class SimpleGlobalApp:
    """Simple GUI for global monitoring and search."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Global Real-time Search Monitor")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Components
        self.monitor = SimpleGlobalMonitor(self.on_text_detected)
        self.search_api = SimpleSearchAPI()
        
        # State
        self.is_monitoring = False
        self.current_query = ""
        self.search_results = []
        
        # Create GUI
        self.create_widgets()
        
        # Check backend
        self.check_backend()
        
        # Bind close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        """Create GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🌍 Global Real-time Search Monitor", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, 
                                  text="Type in ANY application → Watch text appear here → Get instant suggestions", 
                                  font=('Arial', 11), foreground='#666')
        subtitle_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Backend status
        backend_frame = ttk.Frame(status_frame)
        backend_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(backend_frame, text="Backend:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.backend_status = ttk.Label(backend_frame, text="Checking...", font=('Arial', 10))
        self.backend_status.pack(side=tk.LEFT, padx=(10, 0))
        
        # Monitor status
        monitor_frame = ttk.Frame(status_frame)
        monitor_frame.pack(fill=tk.X)
        ttk.Label(monitor_frame, text="Global Monitor:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.monitor_status = ttk.Label(monitor_frame, text="Stopped", font=('Arial', 10), foreground='red')
        self.monitor_status.pack(side=tk.LEFT, padx=(10, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.start_backend_btn = ttk.Button(control_frame, text="🚀 Start Backend", 
                                           command=self.start_backend)
        self.start_backend_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_monitor_btn = ttk.Button(control_frame, text="🌍 Start Global Monitor", 
                                           command=self.toggle_monitoring, state="disabled")
        self.start_monitor_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Current typing display
        typing_frame = ttk.LabelFrame(main_frame, text="Live Typing Detection", padding=10)
        typing_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(typing_frame, text="Current Word:", font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        self.current_word_display = ttk.Label(typing_frame, text="(not monitoring)", 
                                             font=('Arial', 14), foreground='gray',
                                             background='white', relief='sunken', padding=10)
        self.current_word_display.pack(fill=tk.X, pady=(5, 0))
        
        # Instructions
        instructions = """
🎯 How to use:
1. Click "Start Backend" → 2. Click "Start Global Monitor" → 3. Type in ANY application!
4. Open Notepad, Word, VS Code, etc. and start typing
5. Watch your typing appear above in real-time
6. See instant search suggestions below
7. Press SPACEBAR to clear search and start new word
        """
        ttk.Label(typing_frame, text=instructions, font=('Arial', 9), 
                 justify=tk.LEFT, foreground='#555').pack(anchor=tk.W, pady=(10, 0))
        
        # Search results
        results_frame = ttk.LabelFrame(main_frame, text="Live Search Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results text widget
        self.results_text = tk.Text(results_frame, font=('Arial', 10), wrap=tk.WORD, height=15)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        # Initial message
        self.results_text.insert(tk.END, "🔍 Start global monitoring and type in any application!\n\n")
        self.results_text.insert(tk.END, "💡 Supported applications:\n")
        self.results_text.insert(tk.END, "• Notepad, WordPad, Microsoft Word\n")
        self.results_text.insert(tk.END, "• VS Code, Sublime Text, Atom\n")
        self.results_text.insert(tk.END, "• Any text editor or input field\n\n")
        self.results_text.insert(tk.END, "⚠️ Note: You may need to run as administrator for global monitoring\n")
        
    def check_backend(self):
        """Check backend status."""
        if self.search_api.check_backend():
            self.backend_status.config(text="✅ Running", foreground="green")
            self.start_backend_btn.config(text="✅ Backend Running")
            self.start_monitor_btn.config(state="normal")
        else:
            self.backend_status.config(text="❌ Not Running", foreground="red")
            
    def start_backend(self):
        """Start backend."""
        self.start_backend_btn.config(text="Starting...", state="disabled")
        self.backend_status.config(text="🔄 Starting...", foreground="orange")
        
        threading.Thread(target=self._start_backend_process, daemon=True).start()
        
    def _start_backend_process(self):
        """Start backend process."""
        try:
            # Try to start backend
            subprocess.Popen([sys.executable, "start_backend.py"], cwd=Path(__file__).parent)
            
            # Wait for it to start
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
        """Backend started successfully."""
        self.backend_status.config(text="✅ Running", foreground="green")
        self.start_backend_btn.config(text="✅ Backend Running", state="normal")
        self.start_monitor_btn.config(state="normal")
        messagebox.showinfo("Success", "Backend started!\nNow click 'Start Global Monitor'")
        
    def on_backend_failed(self):
        """Backend failed to start."""
        self.backend_status.config(text="❌ Failed", foreground="red")
        self.start_backend_btn.config(text="🚀 Start Backend", state="normal")
        messagebox.showerror("Error", "Backend failed to start.\nCheck if dependencies are installed.")
        
    def toggle_monitoring(self):
        """Toggle global monitoring."""
        if not MONITORING_AVAILABLE:
            messagebox.showerror("Error", 
                               "Global monitoring requires:\n\n"
                               "pip install keyboard pyperclip\n\n"
                               "You may also need to run as administrator.")
            return
            
        if not self.is_monitoring:
            success = self.monitor.start_monitoring()
            if success:
                self.is_monitoring = True
                self.start_monitor_btn.config(text="🛑 Stop Monitor")
                self.monitor_status.config(text="✅ Active", foreground="green")
                self.current_word_display.config(text="Ready! Type in any application...", foreground="blue")
                
                messagebox.showinfo("Global Monitor Started", 
                                  "🌍 Global monitoring is now active!\n\n"
                                  "✨ Type in ANY application:\n"
                                  "• Notepad, Word, VS Code, etc.\n"
                                  "• Watch text appear in this window\n"
                                  "• Get instant search suggestions\n"
                                  "• Press SPACEBAR to clear search\n\n"
                                  "⚠️ If it doesn't work, try running as administrator")
            else:
                messagebox.showerror("Error", "Failed to start global monitoring.\nTry running as administrator.")
        else:
            self.monitor.stop_monitoring()
            self.is_monitoring = False
            self.start_monitor_btn.config(text="🌍 Start Global Monitor")
            self.monitor_status.config(text="❌ Stopped", foreground="red")
            self.current_word_display.config(text="(not monitoring)", foreground="gray")
            
    def on_text_detected(self, text: str):
        """Handle text detected from global monitoring."""
        self.current_query = text
        
        # Update display
        if text:
            self.current_word_display.config(text=f"'{text}'", foreground="blue")
        else:
            self.current_word_display.config(text="(cleared - ready for next word)", foreground="green")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Search cleared. Start typing for new search...\n")
            return
            
        # Search
        if len(text) >= 1:
            threading.Thread(target=self._search_background, args=(text,), daemon=True).start()
            
    def _search_background(self, query: str):
        """Search in background."""
        try:
            results = self.search_api.search(query)
            self.root.after(0, lambda: self._update_results(query, results))
        except Exception as e:
            logger.error(f"Search error: {e}")
            
    def _update_results(self, query: str, results: List[Dict[str, Any]]):
        """Update search results."""
        if query != self.current_query:
            return
            
        self.search_results = results
        self.results_text.delete(1.0, tk.END)
        
        if not results:
            self.results_text.insert(tk.END, f"🔍 Searching for: '{query}'\n\n")
            self.results_text.insert(tk.END, "No results found.\n\n")
            self.results_text.insert(tk.END, "💡 Make sure to add documents first using the web interface:\n")
            self.results_text.insert(tk.END, "http://127.0.0.1:8000/static/app.html\n")
            return
            
        self.results_text.insert(tk.END, f"🔍 Live search for: '{query}' ({len(results)} results)\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            source = result.get('source', 'Unknown')
            similarity = result.get('similarity', 0) * 100
            
            self.results_text.insert(tk.END, f"{i}. [{similarity:.1f}%] ")
            self.results_text.insert(tk.END, f"{content[:150]}...\n")
            self.results_text.insert(tk.END, f"   📄 {source}\n\n")
            
        self.results_text.insert(tk.END, "💡 Copy any result by selecting text and Ctrl+C\n")
        self.results_text.see(1.0)
        
    def on_closing(self):
        """Handle closing."""
        if self.is_monitoring:
            self.monitor.stop_monitoring()
        self.root.destroy()
        
    def run(self):
        """Run the app."""
        self.root.mainloop()

def main():
    """Main entry point."""
    print("🌍 Simple Global Real-time Search Monitor")
    print("=" * 50)
    print("🎯 Type in ANY application and see it here!")
    print()
    
    if not MONITORING_AVAILABLE:
        print("⚠️  Install required packages:")
        print("   pip install keyboard pyperclip")
        print("   (Run as administrator if needed)")
        print()
    
    try:
        app = SimpleGlobalApp()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
