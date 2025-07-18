#!/usr/bin/env python3
"""
Simple Real-time Floating App.
Shows real-time suggestions as you type in Word.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import requests
import pyperclip
import keyboard
from realtime_monitor import RealTimeContextProvider

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleFloatingApp:
    """Simple floating app with real-time Word monitoring."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_ui()
        
        # Context provider
        self.context_provider = RealTimeContextProvider()
        self.context_provider.add_suggestion_callback(self.on_suggestions_update)
        
        # State
        self.current_context = ""
        self.current_suggestions = []
        
        # Setup hotkeys
        self.setup_hotkeys()
        
        # Check backend
        self.check_backend()
        
    def setup_window(self):
        """Setup floating window."""
        self.root.title("Semantic Search - Real-time Assistant")
        self.root.geometry("400x600")
        
        # Always on top and semi-transparent
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.95)
        
        # Position on right side
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"400x600+{screen_width-420}+50")
        
        self.root.configure(bg='#f8f9fa')
        
    def setup_ui(self):
        """Setup clean UI."""
        # Main container
        main_frame = tk.Frame(self.root, bg='#f8f9fa', padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(header_frame, text="🔍 Real-time Assistant", 
                              font=("Segoe UI", 14, "bold"), 
                              bg='#f8f9fa', fg='#2c3e50')
        title_label.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(header_frame, text="● Connecting...", 
                                   font=("Segoe UI", 9), 
                                   bg='#f8f9fa', fg='#e67e22')
        self.status_label.pack(side=tk.RIGHT)
        
        # Control buttons
        control_frame = tk.Frame(main_frame, bg='#f8f9fa')
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.monitor_btn = tk.Button(control_frame, text="Start Monitoring", 
                                   command=self.toggle_monitoring,
                                   font=("Segoe UI", 9, "bold"),
                                   bg='#3498db', fg='white',
                                   relief=tk.FLAT, padx=20, pady=8)
        self.monitor_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Manual search
        search_frame = tk.Frame(main_frame, bg='#f8f9fa')
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(search_frame, text="Manual Search:", 
                font=("Segoe UI", 9, "bold"), bg='#f8f9fa', fg='#2c3e50').pack(anchor=tk.W)
        
        search_container = tk.Frame(search_frame, bg='#f8f9fa')
        search_container.pack(fill=tk.X, pady=(5, 0))
        
        self.search_entry = tk.Entry(search_container, font=("Segoe UI", 10))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", self.manual_search)
        
        search_btn = tk.Button(search_container, text="Search",
                             font=("Segoe UI", 9), bg='#27ae60', fg='white',
                             relief=tk.FLAT, padx=15, pady=5,
                             command=self.manual_search)
        search_btn.pack(side=tk.RIGHT)
        
        # Current context
        context_frame = tk.Frame(main_frame, bg='#f8f9fa')
        context_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(context_frame, text="Current Context:", 
                font=("Segoe UI", 9, "bold"), bg='#f8f9fa', fg='#2c3e50').pack(anchor=tk.W)
        
        self.context_text = tk.Text(context_frame, height=3, wrap=tk.WORD, 
                                  font=("Segoe UI", 9), bg='white',
                                  relief=tk.FLAT, bd=1, padx=10, pady=5)
        self.context_text.pack(fill=tk.X, pady=(5, 0))
        
        # Suggestions
        suggestions_frame = tk.Frame(main_frame, bg='#f8f9fa')
        suggestions_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(suggestions_frame, text="Real-time Suggestions:", 
                font=("Segoe UI", 9, "bold"), bg='#f8f9fa', fg='#2c3e50').pack(anchor=tk.W)
        
        # Suggestions list with scrollbar
        list_container = tk.Frame(suggestions_frame, bg='#f8f9fa')
        list_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.suggestions_listbox = tk.Listbox(list_container, 
                                            font=("Segoe UI", 9),
                                            bg='white', selectmode=tk.SINGLE)
        scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL, 
                               command=self.suggestions_listbox.yview)
        self.suggestions_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.suggestions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.suggestions_listbox.bind("<Double-Button-1>", self.copy_suggestion)
        self.suggestions_listbox.bind("<Button-3>", self.show_context_menu)
        
        # Instructions
        instructions = tk.Label(main_frame, 
                              text="💡 Start monitoring and type in Word to see real-time suggestions\n"
                                   "🖱️ Double-click to copy with citation • Right-click for options",
                              font=("Segoe UI", 8), bg='#f8f9fa', fg='#7f8c8d',
                              justify=tk.LEFT)
        instructions.pack(pady=(10, 0))
        
    def setup_hotkeys(self):
        """Setup global hotkeys."""
        try:
            keyboard.add_hotkey('ctrl+shift+space', self.toggle_window)
            keyboard.add_hotkey('ctrl+shift+s', self.quick_search_clipboard)
        except Exception as e:
            logger.error(f"Failed to setup hotkeys: {e}")
    
    def toggle_window(self):
        """Toggle window visibility."""
        if self.root.winfo_viewable():
            self.root.withdraw()
        else:
            self.root.deiconify()
            self.root.lift()
    
    def check_backend(self):
        """Check backend status."""
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=2)
            if response.status_code == 200:
                self.status_label.config(text="● Connected", fg="#27ae60")
                return True
        except:
            pass
        
        self.status_label.config(text="● Disconnected", fg="#e74c3c")
        return False
    
    def toggle_monitoring(self):
        """Toggle Word monitoring."""
        if not self.check_backend():
            messagebox.showerror("Error", "Backend not available!\n\nPlease start the backend first:\npython -m uvicorn api_service:app --host 127.0.0.1 --port 8000")
            return
        
        if self.monitor_btn.cget("text") == "Start Monitoring":
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start Word monitoring."""
        try:
            self.context_provider.start()
            self.monitor_btn.config(text="Stop Monitoring", bg="#e74c3c")
            self.status_label.config(text="● Monitoring Word", fg="#f39c12")
            logger.info("Started Word monitoring")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop Word monitoring."""
        self.context_provider.stop()
        self.monitor_btn.config(text="Start Monitoring", bg="#3498db")
        self.status_label.config(text="● Connected", fg="#27ae60")
        logger.info("Stopped Word monitoring")
    
    def on_suggestions_update(self, context, suggestions):
        """Handle suggestions update from Word monitor."""
        # Update UI in main thread
        self.root.after(0, self._update_ui, context, suggestions)
    
    def _update_ui(self, context, suggestions):
        """Update UI with new context and suggestions."""
        # Update context
        self.context_text.delete(1.0, tk.END)
        display_context = context[:200] + "..." if len(context) > 200 else context
        self.context_text.insert(tk.END, display_context)
        
        # Update suggestions
        self.suggestions_listbox.delete(0, tk.END)
        self.current_suggestions = suggestions
        
        for i, suggestion in enumerate(suggestions):
            content = suggestion.get("content", "")
            source = suggestion.get("source", "Unknown")
            similarity = suggestion.get("similarity", 0)
            
            # Format for display
            display_text = f"{content[:60]}..." if len(content) > 60 else content
            display_text += f" [{source}] ({similarity:.1%})"
            
            self.suggestions_listbox.insert(tk.END, display_text)
        
        # Show count
        count_text = f"● Found {len(suggestions)} suggestions" if suggestions else "● No suggestions"
        self.status_label.config(text=count_text, fg="#27ae60" if suggestions else "#7f8c8d")
    
    def manual_search(self, event=None):
        """Perform manual search."""
        query = self.search_entry.get().strip()
        if not query:
            return
        
        try:
            suggestions = self.context_provider.manual_search(query)
            self._update_ui(f"Manual search: {query}", suggestions)
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")
    
    def quick_search_clipboard(self):
        """Quick search with clipboard content."""
        try:
            clipboard_text = pyperclip.paste().strip()
            if clipboard_text:
                self.search_entry.delete(0, tk.END)
                self.search_entry.insert(0, clipboard_text)
                self.manual_search()
        except Exception as e:
            logger.error(f"Clipboard search error: {e}")
    
    def copy_suggestion(self, event):
        """Copy selected suggestion with citation."""
        selection = self.suggestions_listbox.curselection()
        if not selection or not self.current_suggestions:
            return
        
        index = selection[0]
        if index < len(self.current_suggestions):
            suggestion = self.current_suggestions[index]
            content = suggestion.get("content", "")
            source = suggestion.get("source", "Unknown")
            
            # Create citation text
            citation_text = f"{content}\n\n[Source: {source}]"
            
            pyperclip.copy(citation_text)
            
            # Show confirmation
            self.show_notification("📋 Copied with citation!")
    
    def show_context_menu(self, event):
        """Show context menu for suggestions."""
        selection = self.suggestions_listbox.curselection()
        if not selection or not self.current_suggestions:
            return
        
        index = selection[0]
        if index >= len(self.current_suggestions):
            return
        
        suggestion = self.current_suggestions[index]
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📋 Copy with Citation", 
                        command=lambda: self.copy_with_citation(suggestion))
        menu.add_command(label="📄 Copy Text Only", 
                        command=lambda: self.copy_text_only(suggestion))
        menu.add_command(label="🔍 Search Similar", 
                        command=lambda: self.search_similar(suggestion))
        
        menu.tk_popup(event.x_root, event.y_root)
    
    def copy_with_citation(self, suggestion):
        """Copy suggestion with citation."""
        content = suggestion.get("content", "")
        source = suggestion.get("source", "Unknown")
        citation_text = f"{content}\n\n[Source: {source}]"
        pyperclip.copy(citation_text)
        self.show_notification("📋 Copied with citation!")
    
    def copy_text_only(self, suggestion):
        """Copy only the text."""
        content = suggestion.get("content", "")
        pyperclip.copy(content)
        self.show_notification("📄 Text copied!")
    
    def search_similar(self, suggestion):
        """Search for similar content."""
        content = suggestion.get("content", "")
        if content:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, content[:50])
            self.manual_search()
    
    def show_notification(self, message):
        """Show brief notification."""
        # Create temporary notification
        notification = tk.Label(self.root, text=message, 
                              font=("Segoe UI", 9, "bold"), 
                              bg='#27ae60', fg='white',
                              padx=10, pady=5)
        notification.place(relx=0.5, rely=0.95, anchor=tk.CENTER)
        
        # Remove after 2 seconds
        self.root.after(2000, notification.destroy)
    
    def run(self):
        """Run the application."""
        logger.info("Starting Simple Floating App")
        
        # Show startup message
        self.show_notification("🚀 Ready! Start monitoring to see real-time suggestions")
        
        self.root.mainloop()

def main():
    """Main entry point."""
    app = SimpleFloatingApp()
    app.run()

if __name__ == "__main__":
    main()
