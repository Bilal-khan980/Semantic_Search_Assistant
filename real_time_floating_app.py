#!/usr/bin/env python3
"""
Real-time Floating Desktop Application.
Monitors actual typing and provides context-aware suggestions with drag & drop.
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
import keyboard
import pyautogui
from typing import Dict, List, Any, Optional
import re
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeFloatingApp:
    """Real-time floating app that monitors actual typing."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_ui()
        
        # State management
        self.backend_url = "http://127.0.0.1:8000"
        self.is_monitoring = False
        self.current_context = ""
        self.suggestions = []
        self.typing_buffer = ""
        self.last_typing_time = 0
        
        # Context detection
        self.context_thread = None
        self.typing_thread = None
        
        # Setup global hotkeys and monitoring
        self.setup_hotkeys()
        self.check_backend()
        
    def setup_window(self):
        """Setup the floating window properties."""
        self.root.title("Semantic Search - Context Assistant")
        self.root.geometry("380x500")
        
        # Make window always on top and semi-transparent
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.95)
        
        # Position on right side of screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"380x500+{screen_width-400}+50")
        
        # Custom window styling
        self.root.configure(bg='#f8f9fa')
        
    def setup_ui(self):
        """Setup the clean, modern user interface."""
        # Main container with padding
        main_frame = tk.Frame(self.root, bg='#f8f9fa', padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section
        header_frame = tk.Frame(main_frame, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title and status
        title_label = tk.Label(header_frame, text="🔍 Context Assistant", 
                              font=("Segoe UI", 14, "bold"), 
                              bg='#f8f9fa', fg='#2c3e50')
        title_label.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(header_frame, text="● Connecting...", 
                                   font=("Segoe UI", 9), 
                                   bg='#f8f9fa', fg='#e67e22')
        self.status_label.pack(side=tk.RIGHT)
        
        # Control section
        control_frame = tk.Frame(main_frame, bg='#f8f9fa')
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.monitor_btn = tk.Button(control_frame, text="Start Monitoring", 
                                   command=self.toggle_monitoring,
                                   font=("Segoe UI", 9, "bold"),
                                   bg='#3498db', fg='white',
                                   relief=tk.FLAT, padx=20, pady=8,
                                   cursor='hand2')
        self.monitor_btn.pack(side=tk.LEFT)
        
        # Search section
        search_frame = tk.LabelFrame(main_frame, text="Manual Search",
                                   font=("Segoe UI", 9, "bold"),
                                   bg='#f8f9fa', fg='#2c3e50',
                                   relief=tk.FLAT, bd=1)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        search_container = tk.Frame(search_frame, bg='#f8f9fa')
        search_container.pack(fill=tk.X, padx=10, pady=10)

        self.search_entry = tk.Entry(search_container, font=("Segoe UI", 10),
                                   relief=tk.FLAT, bd=5)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", self.perform_manual_search)

        search_btn = tk.Button(search_container, text="Search",
                             font=("Segoe UI", 9, "bold"), bg='#27ae60', fg='white',
                             relief=tk.FLAT, padx=15, pady=5, cursor='hand2',
                             command=self.perform_manual_search)
        search_btn.pack(side=tk.RIGHT)

        # Context display section
        context_frame = tk.LabelFrame(main_frame, text="Current Context",
                                    font=("Segoe UI", 9, "bold"),
                                    bg='#f8f9fa', fg='#2c3e50',
                                    relief=tk.FLAT, bd=1)
        context_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.context_text = tk.Text(context_frame, height=3, wrap=tk.WORD, 
                                  font=("Segoe UI", 9), bg='white',
                                  relief=tk.FLAT, bd=5, padx=10, pady=5)
        self.context_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Suggestions section
        suggestions_frame = tk.LabelFrame(main_frame, text="Related Suggestions", 
                                        font=("Segoe UI", 9, "bold"),
                                        bg='#f8f9fa', fg='#2c3e50',
                                        relief=tk.FLAT, bd=1)
        suggestions_frame.pack(fill=tk.BOTH, expand=True)
        
        # Suggestions container with scrollbar
        suggestions_container = tk.Frame(suggestions_frame, bg='white')
        suggestions_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a proper scrollable text widget for suggestions
        self.suggestions_text = tk.Text(suggestions_container,
                                      font=("Segoe UI", 9), bg='white',
                                      relief=tk.FLAT, bd=0, padx=10, pady=5,
                                      wrap=tk.WORD, state=tk.DISABLED)

        scrollbar = tk.Scrollbar(suggestions_container, orient=tk.VERTICAL,
                               command=self.suggestions_text.yview)
        self.suggestions_text.configure(yscrollcommand=scrollbar.set)

        self.suggestions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel to scrolling
        def on_mousewheel(event):
            self.suggestions_text.yview_scroll(int(-1*(event.delta/120)), "units")

        self.suggestions_text.bind("<MouseWheel>", on_mousewheel)
        
        # Instructions
        instructions_frame = tk.Frame(main_frame, bg='#f8f9fa')
        instructions_frame.pack(fill=tk.X, pady=(10, 0))
        
        instructions = tk.Label(instructions_frame, 
                              text="💡 Start typing in any app to see suggestions\n🖱️ Drag suggestions directly into your document",
                              font=("Segoe UI", 8), bg='#f8f9fa', fg='#7f8c8d',
                              justify=tk.LEFT)
        instructions.pack(anchor=tk.W)
        
    def setup_hotkeys(self):
        """Setup global hotkeys."""
        try:
            keyboard.add_hotkey('ctrl+shift+space', self.toggle_window)
            keyboard.add_hotkey('ctrl+shift+x', self.force_context_update)
            logger.info("Global hotkeys registered")
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
                self.status_label.config(text="● Connected", fg="#27ae60")
                return True
        except:
            pass
        
        self.status_label.config(text="● Disconnected", fg="#e74c3c")
        return False
    
    def toggle_monitoring(self):
        """Toggle context monitoring."""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start real-time context monitoring."""
        if not self.check_backend():
            messagebox.showerror("Error", "Backend not available. Please start the backend first.")
            return
        
        self.is_monitoring = True
        self.monitor_btn.config(text="Stop Monitoring", bg="#e74c3c")
        
        # Start typing detection thread
        self.typing_thread = threading.Thread(target=self.monitor_typing, daemon=True)
        self.typing_thread.start()
        
        logger.info("Real-time context monitoring started")
    
    def stop_monitoring(self):
        """Stop context monitoring."""
        self.is_monitoring = False
        self.monitor_btn.config(text="Start Monitoring", bg="#3498db")
        logger.info("Context monitoring stopped")
    
    def monitor_typing(self):
        """Monitor real-time typing across all applications."""
        last_clipboard = ""
        typing_buffer = ""
        last_active_window = ""
        last_word_check = 0

        # Setup keyboard hook for real-time typing detection
        self.setup_keyboard_hook()

        while self.is_monitoring:
            try:
                # Get current active window
                current_window = self.get_active_window_info()

                # Check Word document every 2 seconds if Word is active
                current_time = time.time()
                if current_window and "Word" in current_window and current_time - last_word_check > 2:
                    self.get_word_document_context()
                    last_word_check = current_time

                # Get current clipboard (to detect copy operations)
                current_clipboard = self.get_clipboard_text()

                # Detect typing by monitoring clipboard changes
                if current_clipboard != last_clipboard and len(current_clipboard) > len(last_clipboard):
                    # New text was copied/typed
                    new_text = current_clipboard[len(last_clipboard):]
                    typing_buffer += new_text

                    # Update context if we have enough new text
                    if len(new_text.strip()) > 5:
                        self.update_context_from_typing(typing_buffer[-300:])  # Last 300 chars

                last_clipboard = current_clipboard
                last_active_window = current_window

                time.sleep(1)  # Check every second

            except Exception as e:
                logger.error(f"Error in typing monitoring: {e}")
                time.sleep(2)

    def setup_keyboard_hook(self):
        """Setup keyboard hook to detect typing."""
        self.typed_text = ""
        self.last_key_time = 0

        def on_key_event(event):
            try:
                current_time = time.time()

                # Only process if Word is active
                active_window = self.get_active_window_info()
                if not active_window or "Word" not in active_window:
                    return

                # Reset buffer if too much time passed
                if current_time - self.last_key_time > 5:
                    self.typed_text = ""

                self.last_key_time = current_time

                # Capture typed characters
                if event.event_type == keyboard.KEY_DOWN and len(event.name) == 1:
                    self.typed_text += event.name
                elif event.event_type == keyboard.KEY_DOWN and event.name == 'space':
                    self.typed_text += " "
                elif event.event_type == keyboard.KEY_DOWN and event.name == 'backspace':
                    if self.typed_text:
                        self.typed_text = self.typed_text[:-1]

                # Update context when we have a sentence
                if len(self.typed_text) > 20 and ('. ' in self.typed_text or '? ' in self.typed_text or '! ' in self.typed_text):
                    self.update_context_from_typing(self.typed_text)

            except Exception as e:
                logger.error(f"Error in keyboard hook: {e}")

        # Register keyboard hook
        keyboard.hook(on_key_event)
    
    def get_active_window_info(self):
        """Get information about the active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            return window_title
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
            return ""
    
    def get_clipboard_text(self):
        """Get current clipboard text."""
        try:
            return pyperclip.paste()
        except Exception as e:
            return ""
    
    def get_word_document_context(self):
        """Get context from Word document using automation."""
        try:
            # Initialize COM
            import pythoncom
            pythoncom.CoInitialize()

            # Try to get Word document content using COM automation
            import win32com.client

            word_app = win32com.client.Dispatch("Word.Application")
            if word_app.Documents.Count > 0:
                doc = word_app.ActiveDocument
                
                # Get current selection or paragraph
                selection = word_app.Selection
                current_text = selection.Text
                
                # Get surrounding context (current paragraph + previous)
                current_para = selection.Paragraphs(1)
                para_text = current_para.Range.Text
                
                # Get previous paragraph for more context
                if current_para.Previous is not None:
                    prev_para = current_para.Previous.Range.Text
                    context = f"{prev_para} {para_text}"
                else:
                    context = para_text
                
                if context.strip():
                    self.update_context_from_typing(context.strip())

        except Exception as e:
            logger.error(f"Error getting Word context: {e}")
            # Fallback to clipboard monitoring
            pass
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except:
                pass
    
    def update_context_from_typing(self, text):
        """Update context based on detected typing."""
        if not text or len(text.strip()) < 10:
            return
        
        # Clean and process the text
        cleaned_text = self.clean_context_text(text)
        
        if cleaned_text != self.current_context:
            self.current_context = cleaned_text
            
            # Update UI
            self.root.after(0, self.update_context_ui, cleaned_text)
            
            # Get suggestions
            self.get_suggestions(cleaned_text)
    
    def clean_context_text(self, text):
        """Clean and normalize context text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        
        # Get the last few sentences for context
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) > 3:
            text = '. '.join(sentences[-3:])
        
        return text.strip()
    
    def update_context_ui(self, context):
        """Update context UI."""
        self.context_text.delete(1.0, tk.END)
        display_text = context[:300] + "..." if len(context) > 300 else context
        self.context_text.insert(tk.END, display_text)
    
    def get_suggestions(self, context):
        """Get suggestions from backend."""
        try:
            response = requests.post(
                f"{self.backend_url}/search",
                json={
                    "query": context,
                    "limit": 8,
                    "similarity_threshold": 0.25
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
        """Update suggestions UI with better display."""
        # Clear existing suggestions
        self.suggestions_text.config(state=tk.NORMAL)
        self.suggestions_text.delete(1.0, tk.END)

        self.suggestions = suggestions

        if not suggestions:
            self.suggestions_text.insert(tk.END, "No suggestions yet...\n\n")
            self.suggestions_text.insert(tk.END, "💡 Start typing in Word to see related content!\n")
            self.suggestions_text.insert(tk.END, "🔍 Or use the search box above for manual search.")
            self.suggestions_text.config(state=tk.DISABLED)
            return

        # Display suggestions in a clean format
        for i, suggestion in enumerate(suggestions, 1):
            content = suggestion.get("content", "")
            source = suggestion.get("source", "Unknown")
            similarity = suggestion.get("similarity", 0)

            # Add suggestion header
            self.suggestions_text.insert(tk.END, f"📄 Result {i}\n", "header")
            self.suggestions_text.insert(tk.END, f"Source: {source}\n", "source")
            self.suggestions_text.insert(tk.END, f"Match: {similarity:.1%}\n\n", "similarity")

            # Add content
            display_content = content[:200] + "..." if len(content) > 200 else content
            self.suggestions_text.insert(tk.END, f"{display_content}\n\n", "content")

            # Add action buttons info
            self.suggestions_text.insert(tk.END, "💡 Double-click to copy with citation\n", "action")
            self.suggestions_text.insert(tk.END, "-" * 50 + "\n\n", "separator")

        # Configure text tags for styling
        self.suggestions_text.tag_config("header", font=("Segoe UI", 10, "bold"), foreground="#2c3e50")
        self.suggestions_text.tag_config("source", font=("Segoe UI", 9, "bold"), foreground="#3498db")
        self.suggestions_text.tag_config("similarity", font=("Segoe UI", 8), foreground="#7f8c8d")
        self.suggestions_text.tag_config("content", font=("Segoe UI", 9), foreground="#2c3e50")
        self.suggestions_text.tag_config("action", font=("Segoe UI", 8), foreground="#27ae60")
        self.suggestions_text.tag_config("separator", foreground="#bdc3c7")

        # Bind double-click to copy
        self.suggestions_text.bind("<Double-Button-1>", self.on_suggestion_double_click)

        self.suggestions_text.config(state=tk.DISABLED)
    
    def on_suggestion_double_click(self, event):
        """Handle double-click on suggestions."""
        if self.suggestions:
            # Get the first suggestion for now (could be improved to detect which one was clicked)
            suggestion = self.suggestions[0]
            self.copy_with_citation(suggestion)

    def create_suggestion_widget(self, suggestion, index):
        """Create a draggable suggestion widget."""
        content = suggestion.get("content", "")
        source = suggestion.get("source", "Unknown")
        similarity = suggestion.get("similarity", 0)
        
        # Main suggestion frame
        suggestion_frame = tk.Frame(self.scrollable_frame, bg='white', 
                                  relief=tk.FLAT, bd=1, padx=5, pady=5)
        suggestion_frame.pack(fill=tk.X, padx=5, pady=3)
        
        # Add hover effects
        def on_enter(e):
            suggestion_frame.config(bg='#f8f9fa', relief=tk.RAISED)
        
        def on_leave(e):
            suggestion_frame.config(bg='white', relief=tk.FLAT)
        
        suggestion_frame.bind("<Enter>", on_enter)
        suggestion_frame.bind("<Leave>", on_leave)
        
        # Header with source and similarity
        header_frame = tk.Frame(suggestion_frame, bg='white')
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        source_label = tk.Label(header_frame, text=source[:40] + "..." if len(source) > 40 else source,
                              font=("Segoe UI", 8, "bold"), bg='white', fg='#3498db')
        source_label.pack(side=tk.LEFT)
        
        similarity_label = tk.Label(header_frame, text=f"{similarity:.1%}",
                                  font=("Segoe UI", 8), bg='#ecf0f1', fg='#7f8c8d',
                                  padx=6, pady=2)
        similarity_label.pack(side=tk.RIGHT)
        
        # Content
        content_text = content[:150] + "..." if len(content) > 150 else content
        content_label = tk.Label(suggestion_frame, text=content_text,
                               font=("Segoe UI", 9), bg='white', fg='#2c3e50',
                               wraplength=320, justify=tk.LEFT)
        content_label.pack(fill=tk.X, pady=(0, 5))
        
        # Action buttons
        actions_frame = tk.Frame(suggestion_frame, bg='white')
        actions_frame.pack(fill=tk.X)
        
        # Drag button (main action)
        drag_btn = tk.Button(actions_frame, text="📋 Drag to Document",
                           font=("Segoe UI", 8, "bold"), bg='#3498db', fg='white',
                           relief=tk.FLAT, padx=10, pady=3, cursor='hand2',
                           command=lambda: self.copy_with_citation(suggestion))
        drag_btn.pack(side=tk.LEFT)
        
        # Copy button
        copy_btn = tk.Button(actions_frame, text="Copy",
                           font=("Segoe UI", 8), bg='#95a5a6', fg='white',
                           relief=tk.FLAT, padx=8, pady=3, cursor='hand2',
                           command=lambda: self.copy_text_only(suggestion))
        copy_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Make the entire frame draggable
        self.make_draggable(suggestion_frame, suggestion)
    
    def make_draggable(self, widget, suggestion):
        """Make widget draggable for drag & drop functionality."""
        def start_drag(event):
            widget.config(cursor='grabbing')
            # Store the suggestion data for drag & drop
            self.drag_data = suggestion
        
        def end_drag(event):
            widget.config(cursor='hand2')
            # Simulate drag & drop by copying to clipboard and showing instruction
            self.copy_with_citation(suggestion)
            messagebox.showinfo("Drag & Drop", 
                              "Text with citation copied to clipboard!\n\n"
                              "Paste it into your document (Ctrl+V)")
        
        widget.bind("<Button-1>", start_drag)
        widget.bind("<ButtonRelease-1>", end_drag)
        widget.config(cursor='hand2')
    
    def copy_with_citation(self, suggestion):
        """Copy suggestion with citation."""
        content = suggestion.get("content", "")
        source = suggestion.get("source", "Unknown")
        
        # Create formatted text with citation
        citation_text = f"{content}\n\n[Source: {source}]"
        
        pyperclip.copy(citation_text)
        
        # Show brief confirmation
        self.show_copy_confirmation("Text with citation copied!")
    
    def copy_text_only(self, suggestion):
        """Copy only the text without citation."""
        content = suggestion.get("content", "")
        pyperclip.copy(content)
        self.show_copy_confirmation("Text copied!")
    
    def show_copy_confirmation(self, message):
        """Show brief copy confirmation."""
        # Create temporary label
        confirm_label = tk.Label(self.root, text=message, 
                               font=("Segoe UI", 8), bg='#27ae60', fg='white',
                               padx=10, pady=5)
        confirm_label.place(relx=0.5, rely=0.95, anchor=tk.CENTER)
        
        # Remove after 2 seconds
        self.root.after(2000, confirm_label.destroy)
    
    def perform_manual_search(self, event=None):
        """Perform manual search."""
        query = self.search_entry.get().strip()
        if not query:
            return

        # Update context and get suggestions
        self.update_context_from_typing(query)
        self.get_suggestions(query)

    def force_context_update(self):
        """Force context update from clipboard."""
        clipboard_text = self.get_clipboard_text()
        if clipboard_text.strip():
            self.update_context_from_typing(clipboard_text.strip())
    
    def run(self):
        """Run the application."""
        logger.info("Starting Real-time Floating Desktop Application")
        self.root.mainloop()

def main():
    """Main entry point."""
    app = RealTimeFloatingApp()
    app.run()

if __name__ == "__main__":
    main()
