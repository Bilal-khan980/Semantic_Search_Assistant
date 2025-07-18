#!/usr/bin/env python3
"""
True Desktop Floating Application for Semantic Search Assistant.
Floats above all applications and provides real-time context suggestions.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import asyncio
import logging
import json
import requests
from pathlib import Path
import pyperclip
import win32gui
import win32con
import win32api
import win32clipboard
import psutil
import subprocess
from typing import Dict, List, Any, Optional
import keyboard
import pyautogui

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FloatingDesktopApp:
    """True floating desktop application that stays above all windows."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_ui()
        
        # State management
        self.backend_url = "http://127.0.0.1:8000"
        self.is_monitoring = False
        self.current_context = ""
        self.suggestions = []
        self.canvas_items = []
        
        # Context monitoring
        self.last_clipboard = ""
        self.last_active_window = ""
        self.context_thread = None
        
        # Setup global hotkeys
        self.setup_hotkeys()
        
        # Start backend check
        self.check_backend()
        
    def setup_window(self):
        """Setup the floating window properties."""
        self.root.title("Semantic Search Assistant")
        self.root.geometry("400x600")
        
        # Make window always on top
        self.root.wm_attributes("-topmost", True)
        
        # Make window semi-transparent
        self.root.wm_attributes("-alpha", 0.95)
        
        # Remove window decorations for cleaner look
        self.root.overrideredirect(False)
        
        # Position window on right side of screen
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"400x600+{screen_width-420}+50")
        
        # Make window resizable
        self.root.resizable(True, True)
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        ttk.Label(header_frame, text="🔍 Semantic Search", font=("Arial", 12, "bold")).grid(row=0, column=0)
        
        # Status indicator
        self.status_label = ttk.Label(header_frame, text="● Connecting...", foreground="orange")
        self.status_label.grid(row=0, column=1, sticky=tk.E)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.monitor_btn = ttk.Button(control_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(control_frame, text="Canvas", command=self.open_canvas).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Settings", command=self.open_settings).grid(row=0, column=2, padx=5)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Suggestions tab
        self.suggestions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.suggestions_frame, text="Context Suggestions")
        self.setup_suggestions_tab()
        
        # Search tab
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Search")
        self.setup_search_tab()
        
        # Recent tab
        self.recent_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recent_frame, text="Recent")
        self.setup_recent_tab()
        
    def setup_suggestions_tab(self):
        """Setup the context suggestions tab."""
        # Context display
        ttk.Label(self.suggestions_frame, text="Current Context:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 0))
        
        self.context_text = tk.Text(self.suggestions_frame, height=3, wrap=tk.WORD, font=("Arial", 8))
        self.context_text.pack(fill=tk.X, pady=(2, 10))
        
        # Suggestions list
        ttk.Label(self.suggestions_frame, text="Related Suggestions:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        # Suggestions listbox with scrollbar
        suggestions_container = ttk.Frame(self.suggestions_frame)
        suggestions_container.pack(fill=tk.BOTH, expand=True, pady=(2, 0))
        
        self.suggestions_listbox = tk.Listbox(suggestions_container, font=("Arial", 8))
        scrollbar = ttk.Scrollbar(suggestions_container, orient=tk.VERTICAL, command=self.suggestions_listbox.yview)
        self.suggestions_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.suggestions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to copy suggestion
        self.suggestions_listbox.bind("<Double-Button-1>", self.copy_suggestion)
        self.suggestions_listbox.bind("<Button-3>", self.show_suggestion_menu)  # Right-click
        
        # Instructions
        instructions = tk.Text(self.suggestions_frame, height=3, wrap=tk.WORD, font=("Arial", 8))
        instructions.pack(fill=tk.X, pady=(10, 0))
        instructions.insert(tk.END, "💡 Start writing in any app to see suggestions.\n🖱️ Double-click to copy text.\n🎯 Right-click for more options.")
        instructions.config(state=tk.DISABLED)
        
    def setup_search_tab(self):
        """Setup the search tab."""
        # Search entry
        search_frame = ttk.Frame(self.search_frame)
        search_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.search_entry = ttk.Entry(search_frame, font=("Arial", 10))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", self.perform_search)
        
        ttk.Button(search_frame, text="Search", command=self.perform_search).pack(side=tk.RIGHT)
        
        # Results listbox
        ttk.Label(self.search_frame, text="Search Results:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        results_container = ttk.Frame(self.search_frame)
        results_container.pack(fill=tk.BOTH, expand=True, pady=(2, 0))
        
        self.results_listbox = tk.Listbox(results_container, font=("Arial", 8))
        results_scrollbar = ttk.Scrollbar(results_container, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_listbox.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_listbox.bind("<Double-Button-1>", self.copy_search_result)
        self.results_listbox.bind("<Button-3>", self.show_result_menu)
        
    def setup_recent_tab(self):
        """Setup the recent items tab."""
        ttk.Label(self.recent_frame, text="Recently Used:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 0))
        
        recent_container = ttk.Frame(self.recent_frame)
        recent_container.pack(fill=tk.BOTH, expand=True, pady=(2, 0))
        
        self.recent_listbox = tk.Listbox(recent_container, font=("Arial", 8))
        recent_scrollbar = ttk.Scrollbar(recent_container, orient=tk.VERTICAL, command=self.recent_listbox.yview)
        self.recent_listbox.configure(yscrollcommand=recent_scrollbar.set)
        
        self.recent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recent_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.recent_listbox.bind("<Double-Button-1>", self.copy_recent_item)
        
    def setup_hotkeys(self):
        """Setup global hotkeys."""
        try:
            # Ctrl+Shift+Space to toggle window
            keyboard.add_hotkey('ctrl+shift+space', self.toggle_window)
            
            # Ctrl+Shift+S for quick search with clipboard
            keyboard.add_hotkey('ctrl+shift+s', self.quick_search_clipboard)
            
            # Ctrl+Shift+C to open canvas
            keyboard.add_hotkey('ctrl+shift+c', self.open_canvas)
            
            # Ctrl+Shift+X to force context update
            keyboard.add_hotkey('ctrl+shift+x', self.force_context_update)
            
            logger.info("Global hotkeys registered successfully")
        except Exception as e:
            logger.error(f"Failed to register hotkeys: {e}")
    
    def toggle_window(self):
        """Toggle window visibility."""
        if self.root.winfo_viewable():
            self.root.withdraw()
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
    
    def check_backend(self):
        """Check if backend is running."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=2)
            if response.status_code == 200:
                self.status_label.config(text="● Connected", foreground="green")
                return True
        except:
            pass
        
        self.status_label.config(text="● Disconnected", foreground="red")
        return False
    
    def toggle_monitoring(self):
        """Toggle context monitoring."""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start context monitoring."""
        if not self.check_backend():
            messagebox.showerror("Error", "Backend not available. Please start the backend first.")
            return
        
        self.is_monitoring = True
        self.monitor_btn.config(text="Stop Monitoring")
        
        # Start monitoring thread
        self.context_thread = threading.Thread(target=self.monitor_context, daemon=True)
        self.context_thread.start()
        
        logger.info("Context monitoring started")
    
    def stop_monitoring(self):
        """Stop context monitoring."""
        self.is_monitoring = False
        self.monitor_btn.config(text="Start Monitoring")
        logger.info("Context monitoring stopped")
    
    def monitor_context(self):
        """Monitor context from active applications."""
        while self.is_monitoring:
            try:
                # Get active window
                active_window = self.get_active_window_text()
                
                # Get clipboard content
                current_clipboard = self.get_clipboard_text()
                
                # Check if context changed
                if (active_window != self.last_active_window or 
                    current_clipboard != self.last_clipboard):
                    
                    # Update context
                    context = f"{active_window}\n{current_clipboard}"
                    if context.strip():
                        self.update_context(context.strip())
                    
                    self.last_active_window = active_window
                    self.last_clipboard = current_clipboard
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in context monitoring: {e}")
                time.sleep(5)
    
    def get_active_window_text(self):
        """Get text from the active window."""
        try:
            # Get active window handle
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            # Skip our own window
            if "Semantic Search Assistant" in window_title:
                return ""
            
            return window_title
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
            return ""
    
    def get_clipboard_text(self):
        """Get current clipboard text."""
        try:
            return pyperclip.paste()
        except Exception as e:
            logger.error(f"Error getting clipboard: {e}")
            return ""
    
    def update_context(self, context):
        """Update context and get suggestions."""
        self.current_context = context
        
        # Update UI
        self.root.after(0, self.update_context_ui, context)
        
        # Get suggestions
        self.get_suggestions(context)
    
    def update_context_ui(self, context):
        """Update context UI."""
        self.context_text.delete(1.0, tk.END)
        self.context_text.insert(tk.END, context[:200] + "..." if len(context) > 200 else context)
    
    def get_suggestions(self, context):
        """Get suggestions from backend."""
        try:
            response = requests.post(
                f"{self.backend_url}/search",
                json={
                    "query": context,
                    "limit": 10,
                    "similarity_threshold": 0.3
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("results", [])
                self.root.after(0, self.update_suggestions_ui, suggestions)
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
    
    def update_suggestions_ui(self, suggestions):
        """Update suggestions UI."""
        self.suggestions_listbox.delete(0, tk.END)
        self.suggestions = suggestions
        
        for i, suggestion in enumerate(suggestions):
            content = suggestion.get("content", "")
            source = suggestion.get("source", "Unknown")
            similarity = suggestion.get("similarity", 0)
            
            # Truncate content for display
            display_text = f"{content[:80]}..." if len(content) > 80 else content
            display_text += f" [{source}] ({similarity:.1%})"
            
            self.suggestions_listbox.insert(tk.END, display_text)
    
    def copy_suggestion(self, event):
        """Copy selected suggestion to clipboard."""
        selection = self.suggestions_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.suggestions):
                suggestion = self.suggestions[index]
                content = suggestion.get("content", "")
                source = suggestion.get("source", "")
                
                # Create citation
                citation_text = f"{content}\n\n[Source: {source}]"
                
                pyperclip.copy(citation_text)
                messagebox.showinfo("Copied", "Text with citation copied to clipboard!")
    
    def show_suggestion_menu(self, event):
        """Show context menu for suggestions."""
        selection = self.suggestions_listbox.curselection()
        if selection:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Copy with Citation", command=lambda: self.copy_suggestion(event))
            menu.add_command(label="Copy Text Only", command=lambda: self.copy_text_only(selection[0]))
            menu.add_command(label="Add to Canvas", command=lambda: self.add_to_canvas(selection[0]))
            menu.add_command(label="Open Source", command=lambda: self.open_source(selection[0]))
            
            menu.tk_popup(event.x_root, event.y_root)
    
    def copy_text_only(self, index):
        """Copy only the text without citation."""
        if index < len(self.suggestions):
            content = self.suggestions[index].get("content", "")
            pyperclip.copy(content)
            messagebox.showinfo("Copied", "Text copied to clipboard!")
    
    def add_to_canvas(self, index):
        """Add suggestion to canvas."""
        if index < len(self.suggestions):
            suggestion = self.suggestions[index]
            self.canvas_items.append(suggestion)
            messagebox.showinfo("Added", "Item added to canvas!")
    
    def open_source(self, index):
        """Open the source document."""
        if index < len(self.suggestions):
            suggestion = self.suggestions[index]
            source = suggestion.get("source", "")
            if source and Path(source).exists():
                subprocess.Popen(['start', source], shell=True)
            else:
                messagebox.showwarning("Warning", "Source file not found or not accessible.")
    
    def perform_search(self, event=None):
        """Perform manual search."""
        query = self.search_entry.get().strip()
        if not query:
            return
        
        try:
            response = requests.post(
                f"{self.backend_url}/search",
                json={
                    "query": query,
                    "limit": 20,
                    "similarity_threshold": 0.2
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                self.update_search_results(results)
            
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")
    
    def update_search_results(self, results):
        """Update search results UI."""
        self.results_listbox.delete(0, tk.END)
        
        for result in results:
            content = result.get("content", "")
            source = result.get("source", "Unknown")
            similarity = result.get("similarity", 0)
            
            display_text = f"{content[:80]}..." if len(content) > 80 else content
            display_text += f" [{source}] ({similarity:.1%})"
            
            self.results_listbox.insert(tk.END, display_text)
    
    def copy_search_result(self, event):
        """Copy selected search result."""
        # Similar to copy_suggestion but for search results
        pass
    
    def show_result_menu(self, event):
        """Show context menu for search results."""
        # Similar to show_suggestion_menu but for search results
        pass
    
    def copy_recent_item(self, event):
        """Copy recent item."""
        pass
    
    def quick_search_clipboard(self):
        """Quick search with clipboard content."""
        clipboard_text = self.get_clipboard_text()
        if clipboard_text.strip():
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, clipboard_text.strip())
            self.perform_search()
            self.notebook.select(1)  # Switch to search tab
    
    def force_context_update(self):
        """Force context update."""
        if self.is_monitoring:
            context = self.get_clipboard_text()
            if context.strip():
                self.update_context(context.strip())
    
    def open_canvas(self):
        """Open canvas window."""
        CanvasWindow(self.root, self.canvas_items)
    
    def open_settings(self):
        """Open settings window."""
        SettingsWindow(self.root)
    
    def run(self):
        """Run the application."""
        logger.info("Starting Floating Desktop Application")
        self.root.mainloop()

class CanvasWindow:
    """Canvas window for organizing notes like SUBLIME."""
    
    def __init__(self, parent, canvas_items):
        self.window = tk.Toplevel(parent)
        self.window.title("Canvas - Organize Your Notes")
        self.window.geometry("800x600")
        self.window.wm_attributes("-topmost", True)
        
        self.canvas_items = canvas_items
        self.setup_canvas_ui()
    
    def setup_canvas_ui(self):
        """Setup canvas UI."""
        # Canvas area
        self.canvas = tk.Canvas(self.window, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add items to canvas
        for i, item in enumerate(self.canvas_items):
            x = 50 + (i % 3) * 200
            y = 50 + (i // 3) * 150
            
            content = item.get("content", "")[:100]
            source = item.get("source", "Unknown")
            
            # Create note rectangle
            rect = self.canvas.create_rectangle(x, y, x+180, y+120, fill="lightblue", outline="blue")
            text = self.canvas.create_text(x+90, y+60, text=f"{content}\n\n[{source}]", width=160, anchor=tk.CENTER)
            
            # Make draggable
            self.canvas.tag_bind(rect, "<Button-1>", lambda e, r=rect, t=text: self.start_drag(e, r, t))
            self.canvas.tag_bind(text, "<Button-1>", lambda e, r=rect, t=text: self.start_drag(e, r, t))
    
    def start_drag(self, event, rect, text):
        """Start dragging a canvas item."""
        # Implement drag functionality
        pass

class SettingsWindow:
    """Settings window."""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x300")
        self.window.wm_attributes("-topmost", True)
        
        self.setup_settings_ui()
    
    def setup_settings_ui(self):
        """Setup settings UI."""
        ttk.Label(self.window, text="Global Hotkeys:", font=("Arial", 12, "bold")).pack(pady=10)
        
        hotkeys = [
            ("Toggle Window", "Ctrl+Shift+Space"),
            ("Quick Search", "Ctrl+Shift+S"),
            ("Open Canvas", "Ctrl+Shift+C"),
            ("Force Context Update", "Ctrl+Shift+X")
        ]
        
        for name, key in hotkeys:
            frame = ttk.Frame(self.window)
            frame.pack(fill=tk.X, padx=20, pady=2)
            ttk.Label(frame, text=name).pack(side=tk.LEFT)
            ttk.Label(frame, text=key, font=("Arial", 9, "bold")).pack(side=tk.RIGHT)

def main():
    """Main entry point."""
    app = FloatingDesktopApp()
    app.run()

if __name__ == "__main__":
    main()
