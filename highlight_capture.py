#!/usr/bin/env python3
"""
Global Highlight Capture System
Captures text from any application with Ctrl+Shift+H hotkey
"""

import threading
import time
import logging
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
import requests

# Try to import required libraries
try:
    import keyboard
    import pyperclip
    import win32gui
    import win32clipboard
    import win32con
    CAPTURE_AVAILABLE = True
except ImportError as e:
    CAPTURE_AVAILABLE = False
    print(f"Missing dependencies: {e}")
    print("Install with: pip install keyboard pyperclip pywin32")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HighlightCapture:
    """Global highlight capture system."""
    
    def __init__(self, api_base_url="http://127.0.0.1:8000"):
        self.api_base_url = api_base_url
        self.is_active = False
        self.capture_dialog = None
        self.last_captured_text = ""
        self.source_info = {}
        
    def start_global_listener(self):
        """Start the global hotkey listener."""
        if not CAPTURE_AVAILABLE:
            messagebox.showerror("Error", "Required libraries not available.\nInstall: pip install keyboard pyperclip pywin32")
            return False
            
        try:
            # Register global hotkey Ctrl+Alt+H (safer, less conflicts)
            keyboard.add_hotkey('ctrl+alt+h', self.capture_highlight)
            self.is_active = True
            logger.info("✅ Global highlight capture active (Ctrl+Alt+H)")
            return True
        except Exception as e:
            logger.error(f"Failed to start global listener: {e}")
            return False
    
    def stop_global_listener(self):
        """Stop the global hotkey listener."""
        try:
            keyboard.unhook_all()
            self.is_active = False
            logger.info("🛑 Global highlight capture stopped")
        except:
            pass
    
    def capture_highlight(self):
        """Capture highlighted text from any application, optimized for Adobe Reader/PDF."""
        try:
            logger.info("🎯 Highlight capture triggered!")

            # Wait a moment to ensure we're capturing from the right window
            time.sleep(0.1)

            # Show debug info about current state
            self._show_debug_info()

            # Check if we're in Adobe Reader or PDF application
            window_info = self._get_active_window_info()
            is_pdf_app = self._is_pdf_application(window_info)
            if is_pdf_app:
                logger.info("📄 PDF application detected - using optimized methods")

            # Make sure we're focused on the right window (not our own app)
            if self._is_our_own_window(window_info):
                logger.warning("⚠️ Hotkey triggered from our own window - ignoring")
                return

            # Get the currently selected text
            selected_text = self.get_selected_text()

            if not selected_text or len(selected_text.strip()) < 3:
                # Enhanced error message with debug info
                error_msg = f"No text selected or text too short\n\nDebug info:\n"
                error_msg += f"• Text length: {len(selected_text) if selected_text else 0}\n"
                error_msg += f"• Text content: '{selected_text[:50]}...'\n" if selected_text else "• Text content: None\n"
                error_msg += f"• Active window: {window_info}\n"
                error_msg += f"• PDF app: {'Yes' if is_pdf_app else 'No'}\n"

                if is_pdf_app:
                    error_msg += f"\n📄 PDF-specific tips:\n"
                    error_msg += f"• Make sure text is selectable (not an image)\n"
                    error_msg += f"• Try selecting text with mouse drag\n"
                    error_msg += f"• Some PDFs have copy protection\n"
                    error_msg += f"• Wait longer after selection (PDFs are slower)\n"
                    error_msg += f"• Try manually pressing Ctrl+C first to test"
                else:
                    error_msg += f"\nGeneral tips:\n• Make sure text is highlighted (blue selection)\n• Try selecting more text (at least 3 characters)\n• Wait a moment after selection before pressing hotkey"

                self.show_error_notification(error_msg)
                return

            # Get source information
            source_info = self.get_source_information()

            # Show capture dialog
            self.show_capture_dialog(selected_text, source_info)

        except Exception as e:
            logger.error(f"Capture highlight error: {e}")
            self.show_error_notification(f"Capture failed: {str(e)}")

    def _show_debug_info(self):
        """Show debug information for troubleshooting."""
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)

            logger.info(f"🔍 Debug - Active window: '{window_title}' (class: {class_name})")

            # Check clipboard state
            try:
                current_clipboard = pyperclip.paste()
                logger.info(f"🔍 Debug - Current clipboard: '{current_clipboard[:50]}...' ({len(current_clipboard)} chars)")
            except:
                logger.info("🔍 Debug - Clipboard access failed")

        except Exception as e:
            logger.error(f"Debug info error: {e}")

    def _is_pdf_application(self, window_info):
        """Check if the active window is a PDF application."""
        if not window_info:
            return False

        window_lower = window_info.lower()
        pdf_indicators = [
            'adobe', 'acrobat', 'reader', 'pdf', 'foxit', 'sumatra',
            'nitro', 'pdfxchange', 'chrome', 'firefox', 'edge'  # browsers can show PDFs
        ]

        return any(indicator in window_lower for indicator in pdf_indicators)

    def _is_our_own_window(self, window_info):
        """Check if the active window belongs to our own application."""
        if not window_info:
            return False

        window_lower = window_info.lower()
        our_app_indicators = [
            'global monitor', 'semantic search', 'highlight capture',
            'text capture', 'python', 'tkinter', 'enhanced admin'
        ]

        return any(indicator in window_lower for indicator in our_app_indicators)

    def _get_active_window_info(self):
        """Get information about the active window for debugging."""
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            return f"{window_title} ({class_name})"
        except:
            return "Unknown"
    
    def get_selected_text(self):
        """Get currently selected text from any application using multiple methods."""
        try:
            logger.info("🔍 Attempting to get selected text...")

            # Method 1: Standard clipboard approach with multiple attempts
            selected_text = self._try_clipboard_method()
            if selected_text:
                logger.info(f"✅ Got text via clipboard: {len(selected_text)} chars")
                return selected_text

            # Method 2: Windows API approach
            selected_text = self._try_windows_api_method()
            if selected_text:
                logger.info(f"✅ Got text via Windows API: {len(selected_text)} chars")
                return selected_text

            # Method 3: Alternative keyboard shortcuts
            selected_text = self._try_alternative_shortcuts()
            if selected_text:
                logger.info(f"✅ Got text via alternative method: {len(selected_text)} chars")
                return selected_text

            logger.warning("❌ All text selection methods failed")
            return ""

        except Exception as e:
            logger.error(f"Get selected text error: {e}")
            return ""

    def _try_clipboard_method(self):
        """Try the standard clipboard copy method optimized for Adobe Reader/PDF."""
        try:
            # Ensure we're focused on the right window
            try:
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd)
                logger.info(f"🪟 Copying from window: '{window_title}'")

                # Skip if it's our own window
                if self._is_our_own_window(window_title):
                    logger.warning("⚠️ Skipping copy from our own window")
                    return ""

                # Make sure window is focused
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
            except:
                pass

            # Save current clipboard content
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass

            logger.info(f"📋 Original clipboard: '{original_clipboard[:30]}...' ({len(original_clipboard)} chars)")

            # Adobe Reader/PDF Method: Multiple attempts with increasing delays
            for attempt in range(5):
                logger.info(f"🔄 PDF copy attempt {attempt + 1}/5...")

                # Clear clipboard first (important for PDFs)
                try:
                    pyperclip.copy("")
                    time.sleep(0.1)
                except:
                    pass

                # Send copy command
                keyboard.send('ctrl+c')

                # Progressive delay - PDFs need more time
                delay = 0.5 + (attempt * 0.3)  # 0.5, 0.8, 1.1, 1.4, 1.7 seconds
                logger.info(f"   Waiting {delay} seconds for PDF copy...")
                time.sleep(delay)

                # Get the copied text
                new_clipboard = ""
                try:
                    new_clipboard = pyperclip.paste()
                except:
                    pass

                logger.info(f"📋 Attempt {attempt + 1} result: '{new_clipboard[:30]}...' ({len(new_clipboard)} chars)")

                # Check if we got different text
                if new_clipboard and new_clipboard != original_clipboard and new_clipboard.strip():
                    logger.info(f"✅ PDF copy succeeded on attempt {attempt + 1}!")
                    return new_clipboard.strip()

                # Short pause between attempts
                if attempt < 4:
                    time.sleep(0.2)

            # All attempts failed
            logger.warning("❌ All PDF copy attempts failed")
            return ""

        except Exception as e:
            logger.error(f"Clipboard method error: {e}")
            return ""

    def _try_windows_api_method(self):
        """Try using Windows API optimized for Adobe Reader/PDF."""
        try:
            import win32gui
            import win32con
            import win32api

            # Get the focused window
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            logger.info(f"🪟 Trying API method on: {window_title}")

            # Save original clipboard
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass

            # Clear clipboard first (important for Adobe Reader)
            try:
                pyperclip.copy("")
                time.sleep(0.1)
            except:
                pass

            # Try to send WM_COPY message directly
            logger.info("📋 Sending WM_COPY message...")
            win32api.SendMessage(hwnd, win32con.WM_COPY, 0, 0)
            time.sleep(0.8)  # Longer delay for PDF applications

            # Check clipboard
            try:
                selected_text = pyperclip.paste()
                if selected_text and selected_text.strip() and selected_text != original_clipboard:
                    logger.info(f"✅ Windows API method succeeded: {len(selected_text)} chars")
                    return selected_text.strip()
            except:
                pass

            logger.info("❌ Windows API method failed")
            return ""

        except Exception as e:
            logger.error(f"Windows API method error: {e}")
            return ""

    def _try_alternative_shortcuts(self):
        """Try alternative keyboard shortcuts optimized for Adobe Reader/PDF."""
        try:
            # Save current clipboard
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass

            logger.info("🔄 Trying alternative shortcuts for PDF...")

            # Method 1: Ctrl+Insert (alternative copy shortcut)
            logger.info("   Trying Ctrl+Insert...")
            pyperclip.copy("")
            time.sleep(0.1)
            keyboard.send('ctrl+insert')
            time.sleep(0.6)  # Longer delay for PDF

            try:
                selected_text = pyperclip.paste()
                if selected_text and selected_text.strip() and selected_text != original_clipboard:
                    logger.info(f"✅ Ctrl+Insert succeeded: {len(selected_text)} chars")
                    return selected_text.strip()
            except:
                pass

            # Method 2: Right-click context menu simulation
            logger.info("   Trying right-click menu...")
            pyperclip.copy("")
            time.sleep(0.1)
            keyboard.send('shift+f10')  # Context menu
            time.sleep(0.3)
            keyboard.send('c')  # Copy option
            time.sleep(0.6)

            try:
                selected_text = pyperclip.paste()
                if selected_text and selected_text.strip() and selected_text != original_clipboard:
                    logger.info(f"✅ Right-click menu succeeded: {len(selected_text)} chars")
                    return selected_text.strip()
            except:
                pass

            # Method 3: Focus window and retry Ctrl+C
            logger.info("   Trying focus + Ctrl+C...")
            try:
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
            except:
                pass

            pyperclip.copy("")
            time.sleep(0.1)
            keyboard.send('ctrl+c')
            time.sleep(0.8)  # Even longer delay

            try:
                selected_text = pyperclip.paste()
                if selected_text and selected_text.strip() and selected_text != original_clipboard:
                    logger.info(f"✅ Focus + Ctrl+C succeeded: {len(selected_text)} chars")
                    return selected_text.strip()
            except:
                pass

            logger.info("❌ All alternative shortcuts failed")
            return ""

        except Exception as e:
            logger.error(f"Alternative shortcuts method error: {e}")
            return ""
    
    def get_source_information(self):
        """Get information about the source application and document."""
        try:
            # Get active window information
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # Try to extract meaningful source info
            source_info = {
                'window_title': window_title,
                'application': self.detect_application(class_name, window_title),
                'timestamp': datetime.now().isoformat(),
                'class_name': class_name
            }
            
            # Try to extract document/page info from title
            if 'Adobe' in window_title or '.pdf' in window_title.lower():
                source_info['document_type'] = 'PDF'
                source_info['document_name'] = self.extract_document_name(window_title)
            elif 'Chrome' in class_name or 'Firefox' in class_name:
                source_info['document_type'] = 'Web Page'
                source_info['document_name'] = window_title
            elif 'Word' in window_title or '.docx' in window_title.lower():
                source_info['document_type'] = 'Word Document'
                source_info['document_name'] = self.extract_document_name(window_title)
            else:
                source_info['document_type'] = 'Document'
                source_info['document_name'] = window_title
            
            return source_info
            
        except Exception as e:
            logger.error(f"Get source information error: {e}")
            return {
                'window_title': 'Unknown',
                'application': 'Unknown',
                'document_type': 'Document',
                'document_name': 'Unknown Source',
                'timestamp': datetime.now().isoformat()
            }
    
    def detect_application(self, class_name, window_title):
        """Detect the application type."""
        if 'Chrome' in class_name:
            return 'Google Chrome'
        elif 'Firefox' in class_name:
            return 'Mozilla Firefox'
        elif 'Adobe' in window_title:
            return 'Adobe Reader/Acrobat'
        elif 'Word' in window_title:
            return 'Microsoft Word'
        elif 'Notepad' in window_title:
            return 'Notepad'
        elif 'Code' in window_title:
            return 'VS Code'
        else:
            return class_name or 'Unknown Application'
    
    def extract_document_name(self, window_title):
        """Extract document name from window title."""
        try:
            # Remove common application suffixes
            title = window_title
            suffixes = [' - Adobe Acrobat', ' - Word', ' - Google Chrome', ' - Mozilla Firefox']
            for suffix in suffixes:
                if suffix in title:
                    title = title.replace(suffix, '')
            
            # Extract filename if path is present
            if '\\' in title or '/' in title:
                title = title.split('\\')[-1].split('/')[-1]
            
            return title.strip()
        except:
            return window_title
    
    def show_capture_dialog(self, selected_text, source_info):
        """Show the highlight capture dialog."""
        try:
            # Create dialog window
            dialog = tk.Toplevel()
            dialog.title("📝 Capture Highlight")
            dialog.geometry("600x500")
            dialog.attributes('-topmost', True)
            dialog.configure(bg='#f8f9fa')
            
            # Center the dialog
            dialog.transient()
            dialog.grab_set()
            
            # Main frame
            main_frame = tk.Frame(dialog, bg='#f8f9fa', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = tk.Label(main_frame, text="📝 Capture Highlight", 
                                 font=('Arial', 16, 'bold'), bg='#f8f9fa', fg='#2c3e50')
            title_label.pack(pady=(0, 15))
            
            # Selected text display
            text_frame = tk.LabelFrame(main_frame, text="Selected Text", 
                                     font=('Arial', 10, 'bold'), bg='#f8f9fa', fg='#34495e')
            text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            text_display = tk.Text(text_frame, height=6, wrap=tk.WORD, 
                                 font=('Arial', 10), bg='#ffffff', fg='#2c3e50',
                                 relief='solid', borderwidth=1)
            text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_display.insert('1.0', selected_text)
            
            # Source information
            source_frame = tk.LabelFrame(main_frame, text="Source Information", 
                                       font=('Arial', 10, 'bold'), bg='#f8f9fa', fg='#34495e')
            source_frame.pack(fill=tk.X, pady=(0, 15))
            
            source_text = f"📱 Application: {source_info['application']}\n📄 Document: {source_info['document_name']}\n🕒 Captured: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            source_label = tk.Label(source_frame, text=source_text, 
                                  font=('Arial', 9), bg='#f8f9fa', fg='#7f8c8d',
                                  justify=tk.LEFT)
            source_label.pack(padx=10, pady=8, anchor='w')
            
            # Tags input
            tags_frame = tk.Frame(main_frame, bg='#f8f9fa')
            tags_frame.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(tags_frame, text="🏷️ Tags:", font=('Arial', 10, 'bold'), 
                    bg='#f8f9fa', fg='#34495e').pack(side=tk.LEFT)
            tags_entry = tk.Entry(tags_frame, font=('Arial', 10), width=40,
                                relief='solid', borderwidth=1)
            tags_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
            tags_entry.insert(0, "#important #highlight")
            
            # Notes input
            notes_frame = tk.LabelFrame(main_frame, text="Personal Notes", 
                                      font=('Arial', 10, 'bold'), bg='#f8f9fa', fg='#34495e')
            notes_frame.pack(fill=tk.X, pady=(0, 15))
            
            notes_text = tk.Text(notes_frame, height=3, wrap=tk.WORD, 
                                font=('Arial', 10), bg='#ffffff', fg='#2c3e50',
                                relief='solid', borderwidth=1)
            notes_text.pack(fill=tk.X, padx=10, pady=10)
            notes_text.insert('1.0', "Why is this important? What does it mean for my work?")
            
            # Buttons
            button_frame = tk.Frame(main_frame, bg='#f8f9fa')
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            def save_highlight():
                self.save_highlight_to_database(
                    selected_text, 
                    tags_entry.get(), 
                    notes_text.get('1.0', 'end-1c'),
                    source_info
                )
                dialog.destroy()
            
            def cancel():
                dialog.destroy()
            
            save_btn = tk.Button(button_frame, text="💾 Save Highlight", 
                               command=save_highlight,
                               bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                               padx=20, pady=8, relief='flat')
            save_btn.pack(side=tk.RIGHT, padx=(10, 0))
            
            cancel_btn = tk.Button(button_frame, text="❌ Cancel", 
                                 command=cancel,
                                 bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                                 padx=20, pady=8, relief='flat')
            cancel_btn.pack(side=tk.RIGHT)
            
            # Focus on tags entry
            tags_entry.focus_set()
            tags_entry.select_range(0, tk.END)
            
            self.capture_dialog = dialog
            
        except Exception as e:
            logger.error(f"Show capture dialog error: {e}")
            self.show_error_notification(f"Dialog error: {str(e)}")
    
    def save_highlight_to_database(self, text, tags, notes, source_info):
        """Save the highlight to the database."""
        try:
            # Prepare highlight data
            highlight_data = {
                'content': text,
                'tags': tags,
                'notes': notes,
                'source_info': source_info,
                'highlight_type': 'manual_capture',
                'timestamp': datetime.now().isoformat(),
                'is_highlight': True
            }
            
            # Send to backend API
            response = requests.post(
                f"{self.api_base_url}/highlights/add",
                json=highlight_data,
                timeout=5
            )
            
            if response.status_code == 200:
                self.show_success_notification("Highlight saved successfully!")
                logger.info(f"✅ Highlight saved: {len(text)} chars")
            else:
                # Fallback: save to local file
                self.save_highlight_locally(highlight_data)
                self.show_success_notification("Highlight saved locally!")
                
        except Exception as e:
            logger.error(f"Save highlight error: {e}")
            # Fallback: save to local file
            self.save_highlight_locally(highlight_data)
            self.show_success_notification("Highlight saved locally!")
    
    def save_highlight_locally(self, highlight_data):
        """Save highlight to local file as fallback."""
        try:
            highlights_file = Path("captured_highlights.json")
            
            # Load existing highlights
            highlights = []
            if highlights_file.exists():
                with open(highlights_file, 'r', encoding='utf-8') as f:
                    highlights = json.load(f)
            
            # Add new highlight
            highlights.append(highlight_data)
            
            # Save back to file
            with open(highlights_file, 'w', encoding='utf-8') as f:
                json.dump(highlights, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Highlight saved locally to {highlights_file}")
            
        except Exception as e:
            logger.error(f"Save highlight locally error: {e}")
    
    def show_success_notification(self, message):
        """Show success notification."""
        try:
            notification = tk.Toplevel()
            notification.wm_overrideredirect(True)
            notification.attributes('-topmost', True)
            notification.configure(bg='#27ae60', relief='solid', borderwidth=2)
            
            msg = tk.Label(notification, text=f"✅ {message}", 
                         bg='#27ae60', fg='white', font=('Arial', 11, 'bold'))
            msg.pack(padx=15, pady=10)
            
            # Position at top-right
            screen_width = notification.winfo_screenwidth()
            notification.geometry(f"+{screen_width-300}+50")
            
            # Auto-close after 3 seconds
            notification.after(3000, notification.destroy)
            
        except Exception as e:
            logger.error(f"Show success notification error: {e}")
    
    def show_error_notification(self, message):
        """Show error notification."""
        try:
            notification = tk.Toplevel()
            notification.wm_overrideredirect(True)
            notification.attributes('-topmost', True)
            notification.configure(bg='#e74c3c', relief='solid', borderwidth=2)
            
            msg = tk.Label(notification, text=f"❌ {message}", 
                         bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'))
            msg.pack(padx=15, pady=8)
            
            # Position at top-right
            screen_width = notification.winfo_screenwidth()
            notification.geometry(f"+{screen_width-300}+100")
            
            # Auto-close after 4 seconds
            notification.after(4000, notification.destroy)
            
        except Exception as e:
            logger.error(f"Show error notification error: {e}")

def main():
    """Test the highlight capture system."""
    print("🎯 Testing Global Highlight Capture System")
    print("=" * 50)
    
    if not CAPTURE_AVAILABLE:
        print("❌ Required libraries not available")
        print("Install with: pip install keyboard pyperclip pywin32")
        return
    
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Create highlight capture system
    capture = HighlightCapture()
    
    # Start global listener
    if capture.start_global_listener():
        print("✅ Global highlight capture is active!")
        print("📝 Select text in any application and press Ctrl+Alt+H")
        print("🛑 Close this window to stop")
        
        # Show status window
        status_window = tk.Toplevel(root)
        status_window.title("Highlight Capture Active")
        status_window.geometry("400x200")
        status_window.attributes('-topmost', True)
        
        status_label = tk.Label(status_window, 
                              text="🎯 Global Highlight Capture Active!\n\n"
                                   "📝 Select text in any app\n"
                                   "⌨️ Press Ctrl+Alt+H\n"
                                   "💾 Add tags and notes\n\n"
                                   "Close this window to stop",
                              font=('Arial', 12), justify=tk.CENTER)
        status_label.pack(expand=True)
        
        def on_closing():
            capture.stop_global_listener()
            root.quit()
        
        status_window.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    else:
        print("❌ Failed to start global listener")

if __name__ == "__main__":
    main()
