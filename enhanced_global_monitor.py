#!/usr/bin/env python3
"""
Enhanced Global Keyboard Monitor with Multiple Detection Methods
Ensures typing detection works with Word and all applications.
"""

import threading
import time
import logging
import sys
import os
import subprocess
import ctypes
import webbrowser
from pathlib import Path
from typing import List, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
import requests

# Try multiple monitoring approaches
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
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedGlobalMonitor:
    """Enhanced global monitor with multiple detection methods."""
    
    def __init__(self, callback):
        self.callback = callback
        self.is_monitoring = False
        self.current_word = ""
        self.last_clipboard = ""
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start monitoring with multiple methods."""
        if self.is_monitoring:
            return True
            
        # Check if running as administrator
        if not self._is_admin():
            messagebox.showwarning("Administrator Required", 
                                 "For best results with Word and other applications,\n"
                                 "please run this application as Administrator.\n\n"
                                 "Right-click the .bat file and select 'Run as administrator'")
        
        success = False
        
        # Method 1: Try keyboard monitoring
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.on_press(self._on_key_press)
                self.is_monitoring = True
                success = True
                logger.info("✅ Keyboard monitoring started")
            except Exception as e:
                logger.error(f"❌ Keyboard monitoring failed: {e}")
        
        # Method 2: Start clipboard monitoring as backup
        if CLIPBOARD_AVAILABLE:
            self.monitor_thread = threading.Thread(target=self._clipboard_monitor, daemon=True)
            self.monitor_thread.start()
            logger.info("✅ Clipboard monitoring started as backup")
            success = True
        
        if success:
            logger.info("🌍 Global monitoring active")
            return True
        else:
            logger.error("❌ No monitoring methods available")
            return False
            
    def stop_monitoring(self):
        """Stop all monitoring."""
        self.is_monitoring = False
        
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all()
            except:
                pass
                
        logger.info("🛑 Global monitoring stopped")
        
    def _is_admin(self):
        """Check if running as administrator."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def _on_key_press(self, key):
        """Handle keyboard events."""
        if not self.is_monitoring:
            return
            
        try:
            key_name = key.name if hasattr(key, 'name') else str(key)
            
            # Handle spacebar - clear search
            if key_name == 'space':
                if self.current_word.strip():
                    self.current_word = ""
                    self.callback("")
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
            logger.error(f"Key press error: {e}")
            
    def _clipboard_monitor(self):
        """Monitor clipboard for text changes (backup method)."""
        while self.is_monitoring:
            try:
                if CLIPBOARD_AVAILABLE:
                    current_clipboard = pyperclip.paste()
                    
                    # If clipboard changed and contains new text
                    if (current_clipboard != self.last_clipboard and 
                        len(current_clipboard) > len(self.last_clipboard) and
                        len(current_clipboard) < 100):  # Reasonable word length
                        
                        # Extract the new part
                        if self.last_clipboard and current_clipboard.startswith(self.last_clipboard):
                            new_text = current_clipboard[len(self.last_clipboard):].strip()
                            if new_text and len(new_text) < 20:  # Single word
                                self.current_word = new_text
                                self.callback(new_text)
                        
                        self.last_clipboard = current_clipboard
                        
            except Exception as e:
                logger.error(f"Clipboard monitor error: {e}")
                
            time.sleep(0.5)

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
                json={"query": query, "limit": 10, "similarity_threshold": 0.1},
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                # Filter results with score > 30% for better relevance
                filtered_results = [r for r in results if r.get('similarity', 0) > 0.3]
                return filtered_results if filtered_results else results[:5]  # Show top 5 if no high-score results
            return []
        except Exception as e:
            logger.error(f"Search API error: {e}")
            return []
            
    def check_backend(self) -> bool:
        """Check if backend is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

class EnhancedGlobalApp:
    """Enhanced GUI with better monitoring."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Real-time Semantic Search")
        self.root.geometry("900x650")
        self.root.configure(bg='#f0f0f0')
        
        # Make window always on top for better visibility
        self.root.attributes('-topmost', True)
        
        # Components
        self.monitor = EnhancedGlobalMonitor(self.on_text_detected)
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
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔍 Real-time Semantic Search",
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        

        
        # Compact status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 15))

        # Backend status
        ttk.Label(status_frame, text="Backend:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.backend_status = ttk.Label(status_frame, text="Checking...", font=('Arial', 10))
        self.backend_status.pack(side=tk.LEFT, padx=(5, 20))

        # Monitor status
        ttk.Label(status_frame, text="Monitor:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.monitor_status = ttk.Label(status_frame, text="Stopped", font=('Arial', 10), foreground='red')
        self.monitor_status.pack(side=tk.LEFT, padx=(5, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_backend_btn = ttk.Button(control_frame, text="🚀 Start Backend", 
                                           command=self.start_backend)
        self.start_backend_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_monitor_btn = ttk.Button(control_frame, text="🌍 Start Monitor",
                                           command=self.toggle_monitoring, state="disabled")
        self.start_monitor_btn.pack(side=tk.LEFT, padx=(0, 10))
        

        
        # Current typing display
        typing_frame = ttk.Frame(main_frame)
        typing_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(typing_frame, text="Current Search:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        self.current_word_display = ttk.Label(typing_frame, text="(not monitoring)",
                                             font=('Arial', 18, 'bold'), foreground='#2563eb',
                                             background='#f8fafc', relief='solid', padding=15)
        self.current_word_display.pack(fill=tk.X, pady=(8, 0))
        
        # Search results
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Results header
        header_frame = ttk.Frame(results_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Search Results", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        self.results_count_label = ttk.Label(header_frame, text="", font=('Arial', 10), foreground='#666')
        self.results_count_label.pack(side=tk.LEFT, padx=(10, 0))

        # Results text widget with better formatting
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(text_frame, font=('Arial', 11), wrap=tk.WORD, height=15,
                                   selectbackground='#0078d4', selectforeground='white',
                                   background='#ffffff', relief='solid', borderwidth=1)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        # Bind double-click to copy chunk
        self.results_text.bind('<Double-1>', self.copy_chunk_at_cursor)
        self.results_text.bind('<Button-3>', self.show_context_menu)  # Right-click menu
        
        # Initial message
        self.results_text.insert(tk.END, "🔍 Start global monitoring and type in Word or Notepad!\n\n")
        self.results_text.insert(tk.END, "💡 Supported applications:\n")
        self.results_text.insert(tk.END, "• Microsoft Word, WordPad, Notepad\n")
        self.results_text.insert(tk.END, "• VS Code, Sublime Text, Atom\n")
        self.results_text.insert(tk.END, "• Any text editor or input field\n\n")
        self.results_text.insert(tk.END, "🔧 Troubleshooting:\n")
        self.results_text.insert(tk.END, "• Run as Administrator for best results\n")
        self.results_text.insert(tk.END, "• Try the manual test box if global monitoring fails\n")
        self.results_text.insert(tk.END, "• Make sure to add documents via web interface first\n")
        
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
            subprocess.Popen([sys.executable, "start_backend.py"], cwd=Path(__file__).parent)
            
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
        messagebox.showinfo("Success", "Backend started!\n\nNext steps:\n1. Click 'Start Global Monitor'\n2. Open Word/Notepad and start typing!")
        
    def on_backend_failed(self):
        """Backend failed to start."""
        self.backend_status.config(text="❌ Failed", foreground="red")
        self.start_backend_btn.config(text="🚀 Start Backend", state="normal")
        messagebox.showerror("Error", "Backend failed to start.\nCheck console for errors.")
        
    def toggle_monitoring(self):
        """Toggle global monitoring."""
        if not self.is_monitoring:
            success = self.monitor.start_monitoring()
            if success:
                self.is_monitoring = True
                self.start_monitor_btn.config(text="🛑 Stop Monitor")
                self.monitor_status.config(text="✅ Active", foreground="green")
                self.current_word_display.config(text="Ready! Type in Word/Notepad...", foreground="blue")
                
                messagebox.showinfo("Global Monitor Started", 
                                  "🌍 Global monitoring is now active!\n\n"
                                  "✨ Now type in:\n"
                                  "• Microsoft Word\n"
                                  "• Notepad\n"
                                  "• VS Code\n"
                                  "• Any text editor\n\n"
                                  "Watch your typing appear in this window!\n\n"
                                  "⚠️ If it doesn't work, try:\n"
                                  "• Running as Administrator\n"
                                  "• Using the manual test box")
            else:
                messagebox.showerror("Error", "Failed to start global monitoring.\n\nTry:\n• Running as Administrator\n• Installing: pip install keyboard pyperclip")
        else:
            self.monitor.stop_monitoring()
            self.is_monitoring = False
            self.start_monitor_btn.config(text="🌍 Start Global Monitor")
            self.monitor_status.config(text="❌ Stopped", foreground="red")
            self.current_word_display.config(text="(not monitoring)", foreground="gray")
            

        
    def on_text_detected(self, text: str):
        """Handle text detected from monitoring."""
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
        """Update search results with copyable chunks."""
        if query != self.current_query:
            return

        self.search_results = results
        self.results_text.delete(1.0, tk.END)

        if not results:
            self.results_count_label.config(text="(0 results)")
            self.results_text.insert(tk.END, f"🔍 '{query}'\n\n", "header")
            self.results_text.insert(tk.END, "No relevant results found.\n\n", "no_results")
            self.results_text.insert(tk.END, "💡 Try typing more letters or different keywords", "tips")
            return

        # Update results count in header
        self.results_count_label.config(text=f"({len(results)} results)")

        # Header
        self.results_text.insert(tk.END, f"🔍 '{query}'\n\n", "header")

        # Results with elegant formatting
        for i, result in enumerate(results, 1):
            content = result.get('content', '').strip()
            source = result.get('source', 'Unknown').replace('\\', '/')
            similarity = result.get('similarity', 0) * 100

            # Skip low relevance results
            if similarity < 30:
                continue

            # Chunk card header
            self.results_text.insert(tk.END, f"┌─ Result {i} ", "card_header")
            self.results_text.insert(tk.END, f"[{similarity:.1f}%] ", "score")

            # Source filename
            filename = source.split('/')[-1] if '/' in source else source
            self.results_text.insert(tk.END, f"from {filename}\n", "source")

            # Content box
            self.results_text.insert(tk.END, "│\n", "card_border")
            chunk_start = self.results_text.index(tk.INSERT)
            self.results_text.insert(tk.END, "│ ", "card_border")

            # Truncate long content
            display_content = content
            if len(content) > 200:
                display_content = content[:200] + "..."

            self.results_text.insert(tk.END, display_content, "content")
            chunk_end = self.results_text.index(tk.INSERT)
            self.results_text.insert(tk.END, "\n│\n", "card_border")
            self.results_text.insert(tk.END, "└" + "─" * 50 + "\n\n", "card_footer")

            # Tag the chunk for easy copying
            self.results_text.tag_add(f"chunk_{i}", chunk_start, chunk_end)
            self.results_text.tag_config(f"chunk_{i}", background="#f8fafc", relief="flat",
                                       borderwidth=1, lmargin1=20, lmargin2=20)

        # Configure elegant text styles
        self.results_text.tag_config("header", font=('Arial', 14, 'bold'), foreground='#1e40af')
        self.results_text.tag_config("card_header", font=('Arial', 11, 'bold'), foreground='#374151')
        self.results_text.tag_config("score", font=('Arial', 10, 'bold'), foreground='#059669')
        self.results_text.tag_config("source", font=('Arial', 9), foreground='#6b7280')
        self.results_text.tag_config("content", font=('Arial', 10), foreground='#111827', spacing1=3, spacing3=3)
        self.results_text.tag_config("card_border", font=('Arial', 10), foreground='#d1d5db')
        self.results_text.tag_config("card_footer", font=('Arial', 10), foreground='#d1d5db')
        self.results_text.tag_config("no_results", font=('Arial', 11), foreground='#6b7280')
        self.results_text.tag_config("tips", font=('Arial', 10, 'bold'), foreground='#1e40af')

        self.results_text.see(1.0)

    def copy_chunk_at_cursor(self, event):
        """Copy the chunk at cursor position."""
        try:
            # Get cursor position
            cursor_pos = self.results_text.index(tk.CURRENT)

            # Find which chunk was clicked
            for i, result in enumerate(self.search_results, 1):
                chunk_tag = f"chunk_{i}"
                try:
                    ranges = self.results_text.tag_ranges(chunk_tag)
                    if ranges:
                        start, end = ranges[0], ranges[1]
                        if self.results_text.compare(start, "<=", cursor_pos) and self.results_text.compare(cursor_pos, "<=", end):
                            # Copy this chunk
                            content = result.get('content', '').strip()
                            if CLIPBOARD_AVAILABLE:
                                pyperclip.copy(content)
                            else:
                                self.root.clipboard_clear()
                                self.root.clipboard_append(content)

                            # Show confirmation
                            source = result.get('source', 'Unknown').split('/')[-1]
                            similarity = result.get('similarity', 0) * 100
                            messagebox.showinfo("Copied!",
                                              f"📋 Chunk {i} copied to clipboard!\n\n"
                                              f"📄 Source: {source}\n"
                                              f"🎯 Match: {similarity:.1f}%\n"
                                              f"📝 Length: {len(content)} characters")
                            return
                except:
                    continue

            # If no chunk found, copy selected text
            try:
                selected_text = self.results_text.selection_get()
                if selected_text:
                    if CLIPBOARD_AVAILABLE:
                        pyperclip.copy(selected_text)
                    else:
                        self.root.clipboard_clear()
                        self.root.clipboard_append(selected_text)
                    messagebox.showinfo("Copied!", "Selected text copied to clipboard!")
            except:
                messagebox.showinfo("Copy", "Double-click on a highlighted chunk to copy it!")

        except Exception as e:
            logger.error(f"Copy error: {e}")

    def show_context_menu(self, event):
        """Show right-click context menu."""
        try:
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="📋 Copy Selected Text",
                                   command=lambda: self.copy_selected_text())
            context_menu.add_command(label="🔍 Search in Web Interface",
                                   command=lambda: webbrowser.open(f"http://127.0.0.1:8000/static/app.html"))
            context_menu.add_separator()
            context_menu.add_command(label="📄 View All Results",
                                   command=lambda: self.show_all_results())

            context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Context menu error: {e}")

    def copy_selected_text(self):
        """Copy currently selected text."""
        try:
            selected_text = self.results_text.selection_get()
            if selected_text:
                if CLIPBOARD_AVAILABLE:
                    pyperclip.copy(selected_text)
                else:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(selected_text)
                messagebox.showinfo("Copied!", "Selected text copied to clipboard!")
        except:
            messagebox.showwarning("No Selection", "Please select some text first!")

    def show_all_results(self):
        """Show all results in a new window."""
        if not self.search_results:
            return

        # Create new window
        results_window = tk.Toplevel(self.root)
        results_window.title(f"All Results for '{self.current_query}'")
        results_window.geometry("800x600")

        # Text widget with scrollbar
        frame = ttk.Frame(results_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(frame, font=('Arial', 10), wrap=tk.WORD)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Add all results
        for i, result in enumerate(self.search_results, 1):
            content = result.get('content', '').strip()
            source = result.get('source', 'Unknown')
            similarity = result.get('similarity', 0) * 100

            text_widget.insert(tk.END, f"Result {i} [{similarity:.1f}%] - {source}\n", "header")
            text_widget.insert(tk.END, "=" * 80 + "\n")
            text_widget.insert(tk.END, content + "\n\n")

        text_widget.tag_config("header", font=('Arial', 11, 'bold'), foreground='#0066cc')

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
    print("🌍 Enhanced Global Real-time Search Monitor")
    print("=" * 50)
    print("🎯 Type in Word/Notepad and see it here!")
    print()
    
    # Check dependencies
    missing = []
    if not KEYBOARD_AVAILABLE:
        missing.append("keyboard")
    if not CLIPBOARD_AVAILABLE:
        missing.append("pyperclip")
        
    if missing:
        print(f"⚠️  Install missing packages: pip install {' '.join(missing)}")
        print()
    
    try:
        app = EnhancedGlobalApp()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
