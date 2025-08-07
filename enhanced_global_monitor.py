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

# Import highlight capture functionality
try:
    from highlight_capture import HighlightCapture
    HIGHLIGHT_CAPTURE_AVAILABLE = True
except ImportError:
    HIGHLIGHT_CAPTURE_AVAILABLE = False

# Import highlight capture system
try:
    from highlight_capture import HighlightCapture
    HIGHLIGHT_CAPTURE_AVAILABLE = True
except ImportError:
    HIGHLIGHT_CAPTURE_AVAILABLE = False
    print("Highlight capture not available - highlight_capture.py not found")

try:
    import win32gui
    import win32con
    import win32api
    import win32clipboard
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# Try to import tkinter DND
try:
    import tkinter.dnd as tkdnd
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

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

        # Initialize highlight capture
        if HIGHLIGHT_CAPTURE_AVAILABLE:
            self.highlight_capture = HighlightCapture()
        else:
            self.highlight_capture = None

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

        # Add Highlight Capture Button (prominent and user-friendly)
        highlight_state = "normal" if HIGHLIGHT_CAPTURE_AVAILABLE else "disabled"
        self.highlight_btn = ttk.Button(control_frame, text="🎯 Capture Selected Text",
                                       command=self.capture_highlight_manual, state=highlight_state)
        self.highlight_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Add helpful tooltip-style label
        if HIGHLIGHT_CAPTURE_AVAILABLE:
            tooltip_text = "1. Click button → 2. Go select text → 3. Text captured automatically"
        else:
            tooltip_text = "Install packages: pip install keyboard pyperclip pywin32"

        self.highlight_tooltip = tk.Label(control_frame, text=tooltip_text,
                                        font=('Arial', 8), fg='#666666')
        self.highlight_tooltip.pack(side=tk.LEFT, padx=(5, 0))
        

        
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

        # Remove double-click functionality - only drag-and-drop now
        self.results_text.bind('<Button-3>', self.show_context_menu)  # Right-click menu

        # Bind drag-and-drop events
        self.results_text.bind('<Button-1>', self.on_click_start)
        self.results_text.bind('<B1-Motion>', self.on_drag_motion)
        self.results_text.bind('<ButtonRelease-1>', self.on_drag_end)
        self.results_text.bind('<Motion>', self.on_mouse_motion)

        # Drag state variables
        self.drag_start_pos = None
        self.is_dragging = False
        self.drag_data = None
        self.drag_window = None
        self.target_window = None
        self.mouse_tracking_active = False
        
        # Initial message
        self.results_text.insert(tk.END, "🔍 Start global monitoring and type in Word or Notepad!\n\n")
        self.results_text.insert(tk.END, "💡 Supported applications:\n")
        self.results_text.insert(tk.END, "• Microsoft Word, WordPad, Notepad\n")
        self.results_text.insert(tk.END, "• VS Code, Sublime Text, Atom\n")
        self.results_text.insert(tk.END, "• Any text editor or input field\n\n")
        self.results_text.insert(tk.END, "🖱️ How to use search results:\n")
        self.results_text.insert(tk.END, "• 🖱️ Drag & Drop: Click and drag any highlighted chunk to external apps\n")
        self.results_text.insert(tk.END, "• ✋ Hover: Move mouse over chunks to see hand cursor\n")
        self.results_text.insert(tk.END, "• 📝 Drop anywhere: Word, Notepad, VS Code, etc.\n\n")
        self.results_text.insert(tk.END, "🔧 Troubleshooting:\n")
        self.results_text.insert(tk.END, "• Run as Administrator for best results\n")
        self.results_text.insert(tk.END, "• Try the manual test box if global monitoring fails\n")
        self.results_text.insert(tk.END, "• Make sure to add documents via web interface first\n\n")

        # Initialize highlight capture system (button-based, no hotkeys)
        if HIGHLIGHT_CAPTURE_AVAILABLE:
            self.results_text.insert(tk.END, "✨ HIGHLIGHT CAPTURE READY!\n")
            self.results_text.insert(tk.END, "📝 Select text in ANY app and click '📝 Capture Highlight' button\n")
            self.results_text.insert(tk.END, "🎯 No hotkey conflicts - works with Word, PDF, browsers, etc.\n\n")
            logger.info("✅ Highlight capture ready (button-based)")
        else:
            self.results_text.insert(tk.END, "⚠️ Highlight capture not available (missing dependencies)\n")
            self.results_text.insert(tk.END, "   Install: pip install keyboard pyperclip pywin32\n\n")

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

    def capture_highlight_manual(self):
        """Start capture mode - user will select text after clicking button."""
        if not self.highlight_capture:
            messagebox.showerror("Error", "Highlight capture not available.\n\nInstall required packages:\npip install keyboard pyperclip pywin32")
            return

        try:
            # Show instruction and start capture mode
            self._start_capture_mode()

        except Exception as e:
            logger.error(f"Manual highlight capture error: {e}")
            messagebox.showerror("Error", f"Failed to start capture: {e}")

    def _start_capture_mode(self):
        """Start capture mode - show instruction and wait for text selection."""
        try:
            # Create capture mode window
            self.capture_window = tk.Toplevel(self.root)
            self.capture_window.title("🎯 Capture Mode Active")
            self.capture_window.geometry("500x350")
            self.capture_window.attributes('-topmost', True)
            self.capture_window.configure(bg='#e8f5e8')

            # Center the window
            x = self.root.winfo_screenwidth() // 2 - 250
            y = self.root.winfo_screenheight() // 2 - 175
            self.capture_window.geometry(f"+{x}+{y}")

            # Title
            title_label = tk.Label(self.capture_window,
                                 text="🎯 Capture Mode Active!",
                                 font=('Arial', 16, 'bold'),
                                 bg='#e8f5e8', fg='#27ae60')
            title_label.pack(pady=20)

            # Instructions
            instructions_text = (
                "📝 Now select text in any application:\n\n"
                "1️⃣ Go to Word, PDF, browser, or any app\n"
                "2️⃣ Select text with your mouse\n"
                "3️⃣ Text will be captured automatically!\n\n"
                "💡 This window will stay on top so you can\n"
                "see when text is captured."
            )

            instructions_label = tk.Label(self.capture_window,
                                        text=instructions_text,
                                        font=('Arial', 12),
                                        bg='#e8f5e8', fg='#2c3e50',
                                        justify=tk.CENTER)
            instructions_label.pack(pady=15)

            # Status label
            self.capture_status_label = tk.Label(self.capture_window,
                                                text="⏳ Waiting for text selection...",
                                                font=('Arial', 11, 'bold'),
                                                bg='#e8f5e8', fg='#f39c12')
            self.capture_status_label.pack(pady=10)

            # Activity indicator
            self.activity_label = tk.Label(self.capture_window,
                                         text="🔍 Monitoring active - select text in any app",
                                         font=('Arial', 9),
                                         bg='#e8f5e8', fg='#666666')
            self.activity_label.pack(pady=5)

            # Button frame
            button_frame = tk.Frame(self.capture_window, bg='#e8f5e8')
            button_frame.pack(pady=20)

            # Stop capture button
            stop_btn = tk.Button(button_frame,
                               text="🛑 Stop Capture Mode",
                               command=self._stop_capture_mode,
                               bg='#e74c3c', fg='white',
                               font=('Arial', 12, 'bold'),
                               padx=20, pady=8)
            stop_btn.pack()

            # Start monitoring clipboard for changes
            self.capture_active = True
            self.last_clipboard = ""
            try:
                self.last_clipboard = pyperclip.paste()
            except:
                pass

            # Start monitoring
            logger.info("Starting text selection monitoring...")
            self._monitor_clipboard()

        except Exception as e:
            logger.error(f"Start capture mode error: {e}")
            messagebox.showerror("Error", f"Failed to start capture mode: {e}")

    def _monitor_clipboard(self):
        """Monitor for text selection by trying to copy selected text."""
        if not self.capture_active or not hasattr(self, 'capture_window') or not self.capture_window.winfo_exists():
            return

        try:
            # Save current clipboard
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass

            # Try to copy currently selected text
            try:
                # Send Ctrl+C to copy any selected text
                keyboard.send('ctrl+c')
                time.sleep(0.1)  # Brief wait for copy operation

                # Check if clipboard changed
                new_clipboard = pyperclip.paste()

                # If clipboard changed and has meaningful content
                if (new_clipboard != original_clipboard and
                    new_clipboard and
                    len(new_clipboard.strip()) >= 3):

                    # Text was selected and copied!
                    self._text_captured(new_clipboard.strip())
                    return
                else:
                    # Restore original clipboard if nothing was selected
                    try:
                        pyperclip.copy(original_clipboard)
                    except:
                        pass

            except Exception as copy_error:
                logger.debug(f"Copy attempt error: {copy_error}")
                # Restore original clipboard
                try:
                    pyperclip.copy(original_clipboard)
                except:
                    pass

            # Continue monitoring
            self.root.after(1000, self._monitor_clipboard)

        except Exception as e:
            logger.error(f"Monitor clipboard error: {e}")
            # Continue monitoring even if there's an error
            self.root.after(2000, self._monitor_clipboard)

    def _text_captured(self, captured_text):
        """Handle when text is captured."""
        try:
            # Update status
            if hasattr(self, 'capture_status_label') and self.capture_status_label.winfo_exists():
                self.capture_status_label.config(text=f"✅ Captured {len(captured_text)} characters!",
                                                fg='#27ae60')

            # Stop capture mode
            self.capture_active = False

            # Close capture window after a brief delay
            self.root.after(1500, self._close_capture_window)

            # Get source info
            source_info = self._get_source_application_info()

            # Show capture dialog
            self.root.after(1600, lambda: self._show_priority_capture_dialog(captured_text, source_info))

        except Exception as e:
            logger.error(f"Text captured error: {e}")
            self._stop_capture_mode()

    def _close_capture_window(self):
        """Close the capture window."""
        try:
            if hasattr(self, 'capture_window') and self.capture_window.winfo_exists():
                self.capture_window.destroy()
        except:
            pass

    def _stop_capture_mode(self):
        """Stop capture mode."""
        try:
            self.capture_active = False
            if hasattr(self, 'capture_window') and self.capture_window.winfo_exists():
                self.capture_window.destroy()
        except:
            pass





    def _process_captured_text(self, captured_text):
        """Process the captured selected text."""
        try:
            # Show success message briefly
            success_msg = tk.Toplevel(self.root)
            success_msg.title("✅ Text Captured!")
            success_msg.geometry("300x80")
            success_msg.attributes('-topmost', True)
            success_msg.configure(bg='#27ae60')

            msg_label = tk.Label(success_msg,
                               text=f"✅ Captured {len(captured_text)} characters!",
                               bg='#27ae60', fg='white',
                               font=('Arial', 12, 'bold'))
            msg_label.pack(expand=True)

            # Center and auto-close
            x = self.root.winfo_screenwidth() // 2 - 150
            y = self.root.winfo_screenheight() // 2 - 40
            success_msg.geometry(f"+{x}+{y}")

            self.root.after(1500, lambda: success_msg.destroy() if success_msg.winfo_exists() else None)

            # Get source info
            source_info = self._get_source_application_info()

            # Show the priority capture dialog
            self.root.after(1600, lambda: self._show_priority_capture_dialog(captured_text, source_info))

        except Exception as e:
            logger.error(f"Process captured text error: {e}")
            messagebox.showerror("Error", f"Failed to process text: {e}")





    def _get_source_application_info(self):
        """Get information about the source application where text was selected."""
        try:
            import win32gui

            # Get all windows to find the most likely source
            windows = []

            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    windows.append((hwnd, win32gui.GetWindowText(hwnd), win32gui.GetClassName(hwnd)))
                return True

            win32gui.EnumWindows(enum_windows_callback, windows)

            # Filter out our own windows and find likely source
            for hwnd, title, class_name in windows:
                if not self.highlight_capture._is_our_own_window(title):
                    # This is likely the source application
                    return {
                        'window_title': title,
                        'application': class_name,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'capture_method': 'Manual Button Click',
                        'priority': 'high'  # Mark as high priority
                    }

            # Fallback if no suitable window found
            return {
                'window_title': 'Unknown Application',
                'application': 'Manual Capture',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'capture_method': 'Manual Button Click',
                'priority': 'high'
            }

        except Exception as e:
            logger.error(f"Get source info error: {e}")
            return {
                'window_title': 'Manual Capture',
                'application': 'User Selected',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'capture_method': 'Manual Button Click',
                'priority': 'high'
            }

    def _perform_capture(self, capture_msg=None):
        """Perform the actual capture after delay."""
        try:
            # Close the "capturing..." message
            if capture_msg:
                capture_msg.destroy()

            # Use the highlight capture system without hotkey - try multiple methods
            captured_text = None

            # Method 1: Try clipboard method
            captured_text = self.highlight_capture._try_clipboard_method()

            # Method 2: If that fails, try Windows API method
            if not captured_text or len(captured_text.strip()) < 3:
                captured_text = self.highlight_capture._try_windows_api_method()

            # Method 3: If that fails, try alternative shortcuts
            if not captured_text or len(captured_text.strip()) < 3:
                captured_text = self.highlight_capture._try_alternative_shortcuts()

            if captured_text and len(captured_text.strip()) >= 3:
                # Get actual source info from active window
                try:
                    import win32gui
                    hwnd = win32gui.GetForegroundWindow()
                    window_title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)

                    source_info = {
                        'window_title': window_title or 'Unknown Application',
                        'application': class_name or 'Unknown',
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'capture_method': 'Manual Button Click'
                    }
                except:
                    source_info = {
                        'window_title': 'Manual Capture',
                        'application': 'User Selected',
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'capture_method': 'Manual Button Click'
                    }

                # Show success message briefly
                self._show_capture_success(len(captured_text))

                # Show the capture dialog
                self.highlight_capture.show_capture_dialog(captured_text.strip(), source_info)
            else:
                # Show helpful error message
                self._show_capture_failure()

        except Exception as e:
            logger.error(f"Capture performance error: {e}")
            messagebox.showerror("Error", f"Failed to capture text: {e}")

    def _show_capture_success(self, text_length):
        """Show brief success message."""
        try:
            success_msg = tk.Toplevel(self.root)
            success_msg.title("Success!")
            success_msg.geometry("300x80")
            success_msg.attributes('-topmost', True)
            success_msg.configure(bg='#27ae60')

            msg_label = tk.Label(success_msg,
                               text=f"✅ Captured {text_length} characters!",
                               bg='#27ae60', fg='white',
                               font=('Arial', 12, 'bold'))
            msg_label.pack(expand=True)

            # Center and auto-close
            x = self.root.winfo_screenwidth() // 2 - 150
            y = self.root.winfo_screenheight() // 2 - 40
            success_msg.geometry(f"+{x}+{y}")

            self.root.after(2000, lambda: success_msg.destroy() if success_msg.winfo_exists() else None)

        except Exception as e:
            logger.error(f"Show success message error: {e}")

    def _show_priority_capture_dialog(self, captured_text, source_info):
        """Show capture dialog with priority highlighting option."""
        try:
            # Create enhanced capture dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("🎯 Captured Text - Add Tags & Notes")
            dialog.geometry("700x600")
            dialog.attributes('-topmost', True)
            dialog.configure(bg='#f8f9fa')

            # Center the dialog
            x = self.root.winfo_screenwidth() // 2 - 350
            y = self.root.winfo_screenheight() // 2 - 300
            dialog.geometry(f"+{x}+{y}")

            # Title with source info
            title_text = f"🎯 Captured from: {source_info.get('window_title', 'Unknown')}"
            title_label = tk.Label(dialog, text=title_text,
                                 font=('Arial', 14, 'bold'),
                                 bg='#f8f9fa', fg='#2c3e50')
            title_label.pack(pady=15)

            # Captured text display
            text_frame = tk.LabelFrame(dialog, text="📝 Captured Text:",
                                     font=('Arial', 12, 'bold'))
            text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            text_display = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 11),
                                 height=8, bg='#ffffff', relief='sunken', bd=2)
            text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_display.insert('1.0', captured_text)
            text_display.config(state='disabled')

            # Priority checkbox (checked by default for manual captures)
            priority_frame = tk.Frame(dialog, bg='#f8f9fa')
            priority_frame.pack(fill=tk.X, padx=20, pady=5)

            priority_var = tk.BooleanVar(value=True)  # Default to high priority
            priority_check = tk.Checkbutton(priority_frame,
                                          text="⭐ High Priority (show first in search results)",
                                          variable=priority_var,
                                          font=('Arial', 11, 'bold'),
                                          bg='#f8f9fa', fg='#e67e22')
            priority_check.pack(anchor='w')

            # Tags input
            tags_frame = tk.LabelFrame(dialog, text="🏷️ Tags (comma-separated):",
                                     font=('Arial', 11, 'bold'))
            tags_frame.pack(fill=tk.X, padx=20, pady=5)

            tags_entry = tk.Entry(tags_frame, font=('Arial', 11), relief='sunken', bd=2)
            tags_entry.pack(fill=tk.X, padx=10, pady=8)
            tags_entry.focus()  # Focus on tags for quick entry

            # Notes input
            notes_frame = tk.LabelFrame(dialog, text="📝 Personal Notes:",
                                      font=('Arial', 11, 'bold'))
            notes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

            notes_text = tk.Text(notes_frame, wrap=tk.WORD, font=('Arial', 11),
                                height=4, relief='sunken', bd=2)
            notes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

            # Button frame
            button_frame = tk.Frame(dialog, bg='#f8f9fa')
            button_frame.pack(fill=tk.X, padx=20, pady=15)

            # Save button
            def save_highlight():
                tags = tags_entry.get().strip()
                notes = notes_text.get('1.0', tk.END).strip()
                is_priority = priority_var.get()

                # Save with priority information
                self._save_priority_highlight(captured_text, tags, notes, source_info, is_priority)
                dialog.destroy()

            save_btn = tk.Button(button_frame,
                               text="💾 Save Highlight",
                               command=save_highlight,
                               bg='#27ae60', fg='white',
                               font=('Arial', 12, 'bold'),
                               padx=25, pady=8)
            save_btn.pack(side=tk.LEFT, padx=5)

            # Cancel button
            cancel_btn = tk.Button(button_frame,
                                 text="❌ Cancel",
                                 command=dialog.destroy,
                                 bg='#e74c3c', fg='white',
                                 font=('Arial', 12, 'bold'),
                                 padx=25, pady=8)
            cancel_btn.pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            logger.error(f"Show priority capture dialog error: {e}")
            # Fallback to original dialog
            self.highlight_capture.show_capture_dialog(captured_text, source_info)

    def _show_immediate_capture_failure(self):
        """Show failure message for immediate capture."""
        try:
            error_window = tk.Toplevel(self.root)
            error_window.title("❌ No Text Selected")
            error_window.geometry("500x350")
            error_window.attributes('-topmost', True)
            error_window.configure(bg='#f8f9fa')

            # Title
            title_label = tk.Label(error_window,
                                 text="❌ No Text Was Selected",
                                 font=('Arial', 14, 'bold'),
                                 bg='#f8f9fa', fg='#e74c3c')
            title_label.pack(pady=15)

            # Instructions
            instructions_text = (
                "📝 How to use the button correctly:\n\n"
                "1️⃣ First: Go to any application (Word, PDF, browser)\n"
                "2️⃣ Second: Select text with your mouse (highlight it)\n"
                "3️⃣ Third: Come back here and click the button\n"
                "4️⃣ Fourth: Text should be captured automatically\n\n"
                "🔧 Troubleshooting:\n"
                "• Make sure text stays selected when you switch apps\n"
                "• Try selecting at least 3-4 characters\n"
                "• Some applications may not allow text copying\n"
                "• Test with Notepad first to verify it works"
            )

            instructions_label = tk.Label(error_window,
                                        text=instructions_text,
                                        font=('Arial', 10),
                                        bg='#f8f9fa', fg='#2c3e50',
                                        justify=tk.LEFT)
            instructions_label.pack(pady=10, padx=20)

            # Try again button
            button_frame = tk.Frame(error_window, bg='#f8f9fa')
            button_frame.pack(pady=15)

            try_again_btn = tk.Button(button_frame,
                                    text="🔄 Try Again",
                                    command=lambda: [error_window.destroy(), self.capture_highlight_manual()],
                                    bg='#3498db', fg='white',
                                    font=('Arial', 11, 'bold'),
                                    padx=20, pady=5)
            try_again_btn.pack(side=tk.LEFT, padx=10)

            close_btn = tk.Button(button_frame,
                                text="❌ Close",
                                command=error_window.destroy,
                                bg='#95a5a6', fg='white',
                                font=('Arial', 11, 'bold'),
                                padx=20, pady=5)
            close_btn.pack(side=tk.LEFT, padx=10)

        except Exception as e:
            logger.error(f"Show immediate failure message error: {e}")
            messagebox.showwarning("No Text Selected",
                                 "Please select text first, then click the button.\n\n"
                                 "Steps:\n"
                                 "1. Select text in any application\n"
                                 "2. Come back here\n"
                                 "3. Click the capture button")

    def _save_priority_highlight(self, text, tags, notes, source_info, is_priority):
        """Save highlight with priority information for search results."""
        try:
            import json
            import os
            from datetime import datetime

            # Create highlights directory if it doesn't exist
            highlights_dir = Path("highlights")
            highlights_dir.mkdir(exist_ok=True)

            # Create highlight data
            highlight_data = {
                'id': f"highlight_{int(time.time())}_{hash(text) % 10000}",
                'text': text,
                'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
                'notes': notes,
                'source': source_info,
                'priority': 'high' if is_priority else 'normal',
                'created_at': datetime.now().isoformat(),
                'type': 'manual_highlight',
                'length': len(text),
                'word_count': len(text.split())
            }

            # Save to individual file
            filename = f"highlight_{highlight_data['id']}.json"
            filepath = highlights_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(highlight_data, f, indent=2, ensure_ascii=False)

            # Also append to master highlights file for quick access
            master_file = highlights_dir / "all_highlights.jsonl"
            with open(master_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(highlight_data, ensure_ascii=False) + '\n')

            # Show success message
            self._show_save_success(highlight_data)

            logger.info(f"Saved priority highlight: {len(text)} chars, priority: {is_priority}")

        except Exception as e:
            logger.error(f"Save priority highlight error: {e}")
            messagebox.showerror("Save Error", f"Failed to save highlight: {e}")

    def _show_save_success(self, highlight_data):
        """Show success message after saving highlight."""
        try:
            success_window = tk.Toplevel(self.root)
            success_window.title("✅ Highlight Saved!")
            success_window.geometry("400x250")
            success_window.attributes('-topmost', True)
            success_window.configure(bg='#d5f4e6')

            # Center the window
            x = self.root.winfo_screenwidth() // 2 - 200
            y = self.root.winfo_screenheight() // 2 - 125
            success_window.geometry(f"+{x}+{y}")

            # Success message
            title_label = tk.Label(success_window,
                                 text="✅ Highlight Saved Successfully!",
                                 font=('Arial', 14, 'bold'),
                                 bg='#d5f4e6', fg='#27ae60')
            title_label.pack(pady=15)

            # Details
            details_text = (
                f"📝 Text: {len(highlight_data['text'])} characters\n"
                f"🏷️ Tags: {', '.join(highlight_data['tags']) if highlight_data['tags'] else 'None'}\n"
                f"📝 Notes: {'Yes' if highlight_data['notes'] else 'None'}\n"
                f"⭐ Priority: {'High (shows first)' if highlight_data['priority'] == 'high' else 'Normal'}\n"
                f"📱 Source: {highlight_data['source']['window_title']}"
            )

            details_label = tk.Label(success_window,
                                   text=details_text,
                                   font=('Arial', 10),
                                   bg='#d5f4e6', fg='#2c3e50',
                                   justify=tk.LEFT)
            details_label.pack(pady=10, padx=20)

            # Info about search priority
            if highlight_data['priority'] == 'high':
                priority_info = tk.Label(success_window,
                                       text="🎯 This highlight will appear FIRST in search results!",
                                       font=('Arial', 10, 'bold'),
                                       bg='#d5f4e6', fg='#e67e22')
                priority_info.pack(pady=5)

            # Close button
            close_btn = tk.Button(success_window,
                                text="✅ Great!",
                                command=success_window.destroy,
                                bg='#27ae60', fg='white',
                                font=('Arial', 11, 'bold'),
                                padx=20, pady=5)
            close_btn.pack(pady=15)

            # Auto-close after 5 seconds
            self.root.after(5000, lambda: success_window.destroy() if success_window.winfo_exists() else None)

        except Exception as e:
            logger.error(f"Show save success error: {e}")
            messagebox.showinfo("Success", "Highlight saved successfully!")


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
        """Search in background with priority highlights first."""
        try:
            # Get regular search results
            results = self.search_api.search(query)

            # Get priority highlights that match the query
            priority_highlights = self._search_priority_highlights(query)

            # Combine results with priority highlights first
            combined_results = priority_highlights + results

            self.root.after(0, lambda: self._update_results(query, combined_results))
        except Exception as e:
            logger.error(f"Search error: {e}")

    def _search_priority_highlights(self, query: str):
        """Search through saved priority highlights."""
        try:
            import json
            from pathlib import Path

            highlights_dir = Path("highlights")
            if not highlights_dir.exists():
                return []

            master_file = highlights_dir / "all_highlights.jsonl"
            if not master_file.exists():
                return []

            matching_highlights = []
            query_lower = query.lower()

            with open(master_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        highlight = json.loads(line.strip())

                        # Only include high priority highlights
                        if highlight.get('priority') != 'high':
                            continue

                        # Check if query matches text, tags, or notes
                        text_match = query_lower in highlight.get('text', '').lower()
                        tags_match = any(query_lower in tag.lower() for tag in highlight.get('tags', []))
                        notes_match = query_lower in highlight.get('notes', '').lower()

                        if text_match or tags_match or notes_match:
                            # Convert to search result format
                            search_result = {
                                'id': highlight['id'],
                                'content': highlight['text'],
                                'source': f"📌 Priority Highlight from {highlight['source']['window_title']}",
                                'similarity': 1.0,  # High similarity for exact matches
                                'is_priority_highlight': True,
                                'tags': highlight.get('tags', []),
                                'notes': highlight.get('notes', ''),
                                'created_at': highlight.get('created_at'),
                                'metadata': {
                                    'type': 'priority_highlight',
                                    'source_app': highlight['source']['window_title'],
                                    'tags': highlight.get('tags', []),
                                    'notes': highlight.get('notes', ''),
                                    'priority': True
                                }
                            }
                            matching_highlights.append(search_result)

                    except json.JSONDecodeError:
                        continue

            # Sort by creation date (newest first)
            matching_highlights.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            logger.info(f"Found {len(matching_highlights)} priority highlights for query: {query}")
            return matching_highlights

        except Exception as e:
            logger.error(f"Search priority highlights error: {e}")
            return []
            
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

            is_priority = result.get('is_priority_highlight', False)

            # Skip low relevance results (but not priority highlights)
            if not is_priority and similarity < 30:
                continue

            # Special formatting for priority highlights
            if is_priority:
                # Priority highlight header with special styling
                self.results_text.insert(tk.END, f"⭐ PRIORITY {i} ", "priority_header")
                self.results_text.insert(tk.END, f"[YOUR HIGHLIGHT] ", "priority_score")

                # Source with priority indicator
                filename = source.split('/')[-1] if '/' in source else source
                self.results_text.insert(tk.END, f"from {filename}\n", "priority_source")

                # Show tags if available
                tags = result.get('tags', [])
                if tags:
                    self.results_text.insert(tk.END, f"🏷️ Tags: {', '.join(tags)}\n", "priority_tags")

                # Show notes if available
                notes = result.get('notes', '')
                if notes:
                    self.results_text.insert(tk.END, f"📝 Notes: {notes[:100]}{'...' if len(notes) > 100 else ''}\n", "priority_notes")

                # Content box with priority styling
                self.results_text.insert(tk.END, "┌" + "─" * 50 + "\n", "priority_border")
                chunk_start = self.results_text.index(tk.INSERT)
                self.results_text.insert(tk.END, "│ ", "priority_border")

                # Full content for priority highlights (no truncation)
                self.results_text.insert(tk.END, content, "priority_content")
                chunk_end = self.results_text.index(tk.INSERT)
                self.results_text.insert(tk.END, "\n└" + "─" * 50 + "\n\n", "priority_border")

                # Tag the chunk with priority styling
                self.results_text.tag_add(f"chunk_{i}", chunk_start, chunk_end)
                self.results_text.tag_config(f"chunk_{i}", background="#fff3cd", relief="raised",
                                           borderwidth=2, lmargin1=20, lmargin2=20)
            else:
                # Regular result formatting
                self.results_text.insert(tk.END, f"┌─ Result {i} ", "card_header")
                self.results_text.insert(tk.END, f"[{similarity:.1f}%] ", "score")

                # Source filename
                filename = source.split('/')[-1] if '/' in source else source
                self.results_text.insert(tk.END, f"from {filename}\n", "source")

                # Content box
                self.results_text.insert(tk.END, "│\n", "card_border")
                chunk_start = self.results_text.index(tk.INSERT)
                self.results_text.insert(tk.END, "│ ", "card_border")

                # Truncate long content for regular results
                display_content = content
                if len(content) > 200:
                    display_content = content[:200] + "..."

                self.results_text.insert(tk.END, display_content, "content")
                chunk_end = self.results_text.index(tk.INSERT)
                self.results_text.insert(tk.END, "\n│\n", "card_border")
                self.results_text.insert(tk.END, "└" + "─" * 50 + "\n\n", "card_footer")

                # Tag the chunk for easy copying and dragging
                self.results_text.tag_add(f"chunk_{i}", chunk_start, chunk_end)
                self.results_text.tag_config(f"chunk_{i}", background="#f0f8ff", relief="raised",
                                           borderwidth=1, lmargin1=20, lmargin2=20)

        # Configure elegant text styles
        self.results_text.tag_config("header", font=('Arial', 14, 'bold'), foreground='#1e40af')
        self.results_text.tag_config("card_header", font=('Arial', 11, 'bold'), foreground='#374151')
        self.results_text.tag_config("score", font=('Arial', 10, 'bold'), foreground='#059669')
        self.results_text.tag_config("source", font=('Arial', 9), foreground='#6b7280')
        self.results_text.tag_config("content", font=('Arial', 10), foreground='#111827', spacing1=3, spacing3=3)
        self.results_text.tag_config("card_border", font=('Arial', 10), foreground='#d1d5db')

        # Configure priority highlight styles
        self.results_text.tag_config("priority_header", font=('Arial', 12, 'bold'), foreground='#d97706', background='#fef3c7')
        self.results_text.tag_config("priority_score", font=('Arial', 10, 'bold'), foreground='#92400e')
        self.results_text.tag_config("priority_source", font=('Arial', 9, 'bold'), foreground='#78350f')
        self.results_text.tag_config("priority_tags", font=('Arial', 9), foreground='#1d4ed8')
        self.results_text.tag_config("priority_notes", font=('Arial', 9), foreground='#7c2d12')
        self.results_text.tag_config("priority_content", font=('Arial', 10, 'bold'), foreground='#111827', spacing1=3, spacing3=3)
        self.results_text.tag_config("priority_border", font=('Arial', 10), foreground='#d97706')
        self.results_text.tag_config("card_footer", font=('Arial', 10), foreground='#d1d5db')
        self.results_text.tag_config("no_results", font=('Arial', 11), foreground='#6b7280')
        self.results_text.tag_config("tips", font=('Arial', 10, 'bold'), foreground='#1e40af')

        self.results_text.see(1.0)



    def on_mouse_motion(self, event):
        """Handle mouse motion to change cursor when over chunks."""
        try:
            # Get cursor position
            cursor_pos = self.results_text.index(f"@{event.x},{event.y}")

            # Check if cursor is over a chunk
            over_chunk = False
            for i, result in enumerate(self.search_results, 1):
                chunk_tag = f"chunk_{i}"
                try:
                    ranges = self.results_text.tag_ranges(chunk_tag)
                    if ranges:
                        start, end = ranges[0], ranges[1]
                        if self.results_text.compare(start, "<=", cursor_pos) and self.results_text.compare(cursor_pos, "<=", end):
                            over_chunk = True
                            break
                except:
                    continue

            # Change cursor based on whether we're over a chunk
            if over_chunk:
                self.results_text.config(cursor="hand2")  # Hand cursor for draggable chunks
            else:
                self.results_text.config(cursor="")  # Default cursor

        except Exception as e:
            logger.error(f"Mouse motion error: {e}")

    def on_click_start(self, event):
        """Handle mouse click start for potential drag operation."""
        try:
            # Get cursor position
            cursor_pos = self.results_text.index(f"@{event.x},{event.y}")

            # Check if click is on a chunk
            for i, result in enumerate(self.search_results, 1):
                chunk_tag = f"chunk_{i}"
                try:
                    ranges = self.results_text.tag_ranges(chunk_tag)
                    if ranges:
                        start, end = ranges[0], ranges[1]
                        if self.results_text.compare(start, "<=", cursor_pos) and self.results_text.compare(cursor_pos, "<=", end):
                            # Store drag start position and data
                            self.drag_start_pos = (event.x, event.y)
                            # Create citation
                            source_name = result.get('source', 'Unknown')
                            page_num = result.get('page', '')
                            citation = self.create_citation(source_name, page_num)

                            # Prepare content with citation
                            content = result.get('content', '').strip()
                            content_with_citation = f"{content}\n\n{citation}"

                            self.drag_data = {
                                'content': content,  # Original content without citation
                                'content_with_citation': content_with_citation,  # Content with citation for drag-drop
                                'source': source_name,
                                'page': page_num,
                                'citation': citation,
                                'similarity': result.get('similarity', 0),
                                'chunk_index': i
                            }

                            # Prevent text selection during drag by clearing selection
                            self.results_text.tag_remove("sel", "1.0", "end")
                            return "break"  # Prevent default text selection
                except:
                    continue

            # Not on a chunk, clear drag data
            self.drag_start_pos = None
            self.drag_data = None

        except Exception as e:
            logger.error(f"Click start error: {e}")

    def create_citation(self, source_name, page_num=None):
        """Create a citation for the content."""
        try:
            # Clean up source name
            if source_name and source_name != 'Unknown':
                # Remove file extensions
                clean_source = source_name.replace('.pdf', '').replace('.docx', '').replace('.txt', '')

                # Add page number if available
                if page_num and str(page_num).strip():
                    citation = f"(Source: {clean_source}, p. {page_num})"
                else:
                    citation = f"(Source: {clean_source})"
            else:
                citation = "(Source: Document)"

            return citation
        except Exception as e:
            logger.error(f"Create citation error: {e}")
            return "(Source: Document)"

    def on_drag_motion(self, event):
        """Handle drag motion."""
        try:
            if self.drag_start_pos and self.drag_data:
                # Calculate distance moved
                dx = event.x - self.drag_start_pos[0]
                dy = event.y - self.drag_start_pos[1]
                distance = (dx*dx + dy*dy) ** 0.5

                # Start dragging if moved enough distance
                if distance > 10 and not self.is_dragging:
                    self.is_dragging = True
                    self.mouse_tracking_active = True
                    self.start_drag_operation()

        except Exception as e:
            logger.error(f"Drag motion error: {e}")



    def on_drag_end(self, event):
        """Handle drag end - this is where the actual drop happens."""
        try:
            if self.is_dragging:
                # Stop mouse tracking
                self.mouse_tracking_active = False

                # Perform the actual drop
                self.perform_drop()

            # Reset drag state
            self.cleanup_drag_state()

        except Exception as e:
            logger.error(f"Drag end error: {e}")
            self.cleanup_drag_state()

    def cleanup_drag_state(self):
        """Clean up all drag-related state."""
        try:
            # Remove drag window
            if hasattr(self, 'drag_window') and self.drag_window:
                self.drag_window.destroy()
                self.drag_window = None

            # Reset cursor
            self.results_text.config(cursor="")

            # Reset state variables
            self.drag_start_pos = None
            self.is_dragging = False
            self.drag_data = None
            self.target_window = None
            self.mouse_tracking_active = False

            if hasattr(self, 'last_external_hwnd'):
                delattr(self, 'last_external_hwnd')

        except Exception as e:
            logger.error(f"Cleanup drag state error: {e}")

    def perform_drop(self):
        """Perform the actual drop operation."""
        try:
            if not self.drag_data:
                return

            # Get current cursor position to find target window
            if WIN32_AVAILABLE:
                x, y = win32gui.GetCursorPos()
                target_hwnd = win32gui.WindowFromPoint((x, y))

                if target_hwnd and target_hwnd != 0:
                    # Check if it's a different application
                    our_hwnd = self.root.winfo_id()
                    if target_hwnd != our_hwnd:
                        # This is an external application - perform drop
                        self.drop_to_external_window(target_hwnd)
                        return

            # Fallback - just copy to clipboard and show instruction
            self.copy_to_clipboard_and_notify()

        except Exception as e:
            logger.error(f"Perform drop error: {e}")
            self.copy_to_clipboard_and_notify()

    def drop_to_external_window(self, target_hwnd):
        """Drop content to external window."""
        try:
            # Copy content with citation to clipboard
            content_with_citation = self.drag_data.get('content_with_citation', self.drag_data['content'])
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(content_with_citation)
            else:
                self.root.clipboard_clear()
                self.root.clipboard_append(content_with_citation)

            # Activate target window
            win32gui.SetForegroundWindow(target_hwnd)
            win32gui.BringWindowToTop(target_hwnd)

            # Small delay then paste
            self.root.after(200, self.auto_paste)

            logger.info(f"Dropped content to external window: {target_hwnd}")

        except Exception as e:
            logger.error(f"Drop to external window error: {e}")
            self.copy_to_clipboard_and_notify()

    def auto_paste(self):
        """Automatically paste the content."""
        try:
            if WIN32_AVAILABLE:
                import win32api
                import win32con

                # Simulate Ctrl+V
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                win32api.keybd_event(ord('V'), 0, 0, 0)
                win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

                # Show success notification
                self.show_drop_success()

            else:
                self.copy_to_clipboard_and_notify()

        except Exception as e:
            logger.error(f"Auto paste error: {e}")
            self.copy_to_clipboard_and_notify()

    def copy_to_clipboard_and_notify(self):
        """Fallback: copy to clipboard and show notification."""
        try:
            content_with_citation = self.drag_data.get('content_with_citation', self.drag_data['content'])
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(content_with_citation)
            else:
                self.root.clipboard_clear()
                self.root.clipboard_append(content_with_citation)

            # Show instruction
            self.show_manual_paste_instruction()

        except Exception as e:
            logger.error(f"Copy to clipboard error: {e}")

    def show_drop_success(self):
        """Show success notification after drop."""
        try:
            notification = tk.Toplevel(self.root)
            notification.wm_overrideredirect(True)
            notification.attributes('-topmost', True)
            notification.configure(bg='#4CAF50', relief='solid', borderwidth=2)

            msg = tk.Label(notification,
                         text="✅ Content dropped successfully!",
                         bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'))
            msg.pack(padx=15, pady=8)

            # Position at top-right
            screen_width = self.root.winfo_screenwidth()
            notification.geometry(f"+{screen_width-250}+50")

            # Auto-close after 2 seconds
            self.root.after(2000, lambda: notification.destroy() if notification.winfo_exists() else None)

        except Exception as e:
            logger.error(f"Show drop success error: {e}")

    def show_manual_paste_instruction(self):
        """Show manual paste instruction."""
        try:
            content_preview = self.drag_data['content'][:50] + "..." if len(self.drag_data['content']) > 50 else self.drag_data['content']

            notification = tk.Toplevel(self.root)
            notification.wm_overrideredirect(True)
            notification.attributes('-topmost', True)
            notification.configure(bg='#2196F3', relief='solid', borderwidth=2)

            msg = tk.Label(notification,
                         text=f"📋 Content copied!\nSwitch to your app and press Ctrl+V\n\n{content_preview}",
                         bg='#2196F3', fg='white', font=('Arial', 10, 'bold'),
                         justify=tk.CENTER)
            msg.pack(padx=15, pady=10)

            # Position at center
            x = self.root.winfo_screenwidth() // 2 - 200
            y = self.root.winfo_screenheight() // 2 - 100
            notification.geometry(f"+{x}+{y}")

            # Auto-close after 4 seconds
            self.root.after(4000, lambda: notification.destroy() if notification.winfo_exists() else None)

        except Exception as e:
            logger.error(f"Show manual paste instruction error: {e}")

    def start_drag_operation(self):
        """Start the drag operation with visual feedback."""
        try:
            if not self.drag_data:
                return

            # Create drag window that follows cursor
            self.drag_window = tk.Toplevel(self.root)
            self.drag_window.wm_overrideredirect(True)
            self.drag_window.attributes('-topmost', True)
            self.drag_window.attributes('-alpha', 0.9)
            self.drag_window.configure(bg='#4CAF50', relief='solid', borderwidth=2)

            # Show preview of content being dragged
            content = self.drag_data['content']
            content_preview = content[:50] + "..." if len(content) > 50 else content
            label = tk.Label(self.drag_window, text=f"📄 {content_preview}",
                           bg='#4CAF50', fg='white', font=('Arial', 9, 'bold'))
            label.pack(padx=8, pady=4)

            # Position the drag window near the cursor
            x, y = self.root.winfo_pointerxy()
            self.drag_window.geometry(f"+{x+15}+{y+15}")

            # Change cursor to indicate dragging
            self.results_text.config(cursor="fleur")

            # Start global mouse tracking
            self.start_global_mouse_tracking()

            logger.info(f"Started dragging chunk {self.drag_data['chunk_index']}")

        except Exception as e:
            logger.error(f"Start drag operation error: {e}")

    def start_global_mouse_tracking(self):
        """Track mouse globally to update drag window position."""
        try:
            if self.mouse_tracking_active and self.is_dragging and hasattr(self, 'drag_window') and self.drag_window:
                # Update drag window position
                x, y = self.root.winfo_pointerxy()
                self.drag_window.geometry(f"+{x+15}+{y+15}")

                # Check for external applications and activate them
                self.check_and_activate_external_app()

                # Schedule next update
                self.root.after(30, self.start_global_mouse_tracking)  # Update every 30ms for smooth tracking

        except Exception as e:
            logger.error(f"Global mouse tracking error: {e}")

    def check_and_activate_external_app(self):
        """Check if hovering over external app and activate it."""
        try:
            if WIN32_AVAILABLE:
                # Get cursor position
                x, y = win32gui.GetCursorPos()
                target_hwnd = win32gui.WindowFromPoint((x, y))

                if target_hwnd and target_hwnd != 0:
                    our_hwnd = self.root.winfo_id()
                    if target_hwnd != our_hwnd:
                        # This is an external window
                        try:
                            class_name = win32gui.GetClassName(target_hwnd)
                            window_title = win32gui.GetWindowText(target_hwnd)

                            # Check if it's a text editor
                            text_apps = ['WordPadClass', 'OpusApp', 'Notepad', 'Chrome_WidgetWin_1',
                                       'HwndWrapper', 'ApplicationFrameWindow', 'Window']

                            if any(app in class_name for app in text_apps) or any(keyword in window_title.lower() for keyword in ['word', 'notepad', 'code', 'editor', 'text']):
                                # Activate this window immediately
                                win32gui.SetForegroundWindow(target_hwnd)

                                # Update drag window to show target
                                self.update_drag_window_for_target(window_title)

                        except Exception as e:
                            logger.debug(f"Window check error: {e}")

        except Exception as e:
            logger.error(f"Check external app error: {e}")

    def update_drag_window_for_target(self, target_title):
        """Update drag window to show target application."""
        try:
            if hasattr(self, 'drag_window') and self.drag_window:
                # Clear existing content
                for widget in self.drag_window.winfo_children():
                    widget.destroy()

                # Show target info
                content_preview = self.drag_data['content'][:30] + "..." if len(self.drag_data['content']) > 30 else self.drag_data['content']
                target_name = target_title[:25] + "..." if len(target_title) > 25 else target_title

                label = tk.Label(self.drag_window,
                               text=f"📄 Drop into: {target_name}\n{content_preview}",
                               bg='#FF9800', fg='white', font=('Arial', 9, 'bold'),
                               justify=tk.CENTER)
                label.pack(padx=8, pady=4)

                # Change color to indicate target
                self.drag_window.configure(bg='#FF9800')

        except Exception as e:
            logger.error(f"Update drag window for target error: {e}")



    def show_context_menu(self, event):
        """Show right-click context menu."""
        try:
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="🔍 Search in Web Interface",
                                   command=lambda: webbrowser.open(f"http://127.0.0.1:8000/static/app.html"))
            context_menu.add_separator()
            context_menu.add_command(label="📄 View All Results",
                                   command=lambda: self.show_all_results())
            context_menu.add_separator()
            context_menu.add_command(label="💡 Drag & Drop Help",
                                   command=lambda: self.show_drag_help())

            context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Context menu error: {e}")

    def show_drag_help(self):
        """Show drag and drop help."""
        messagebox.showinfo("Drag & Drop Help",
                          "🖱️ How to use Drag & Drop:\n\n"
                          "1. Hover over any highlighted chunk\n"
                          "2. Click and drag the chunk\n"
                          "3. Drag to any external application\n"
                          "4. Release to drop the content\n"
                          "5. Content will be pasted at cursor position\n\n"
                          "✅ Works with: Word, Notepad, VS Code, etc.\n"
                          "💡 No more double-clicking needed!")

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
