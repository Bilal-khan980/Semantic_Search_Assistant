#!/usr/bin/env python3
"""
Debug script to test text selection methods
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import pyperclip
import keyboard
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextSelectionDebugger:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔍 Text Selection Debugger")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.is_monitoring = False
        
    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text="🔍 Text Selection Debugger", 
                        font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(self.root, 
                              text="This tool helps debug text selection issues.\n"
                                   "1. Click 'Start Monitoring'\n"
                                   "2. Go to any app and select text\n"
                                   "3. Press Ctrl+Alt+D to test selection\n"
                                   "4. Check the debug output below",
                              font=('Arial', 11), justify=tk.LEFT)
        instructions.pack(pady=10)
        
        # Control buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.start_btn = tk.Button(button_frame, text="🚀 Start Monitoring", 
                                 command=self.start_monitoring,
                                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                                 padx=15, pady=8)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="⏹️ Stop Monitoring", 
                                command=self.stop_monitoring,
                                bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                                padx=15, pady=8, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.test_btn = tk.Button(button_frame, text="🧪 Test Current Selection", 
                                command=self.test_current_selection,
                                bg='#3498db', fg='white', font=('Arial', 11, 'bold'),
                                padx=15, pady=8)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        # Test area
        test_frame = tk.LabelFrame(self.root, text="Test Area - Select text here and test", 
                                 font=('Arial', 10, 'bold'))
        test_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.test_text = scrolledtext.ScrolledText(test_frame, height=8, wrap=tk.WORD, 
                                                 font=('Arial', 11))
        self.test_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        sample_text = """This is sample text for testing text selection.

You can select any part of this text and then press Ctrl+Alt+D to test if the selection is detected properly.

Try selecting:
- A single word
- Multiple words
- A complete sentence
- A paragraph

The debug output below will show what text was captured and which method worked.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Vector embeddings capture semantic meaning by representing words as high-dimensional numerical vectors that preserve semantic relationships between concepts in natural language processing systems."""
        
        self.test_text.insert('1.0', sample_text)
        
        # Debug output
        debug_frame = tk.LabelFrame(self.root, text="Debug Output", 
                                  font=('Arial', 10, 'bold'))
        debug_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.debug_output = scrolledtext.ScrolledText(debug_frame, height=10, wrap=tk.WORD, 
                                                    font=('Consolas', 9))
        self.debug_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status
        self.status_label = tk.Label(self.root, text="Ready to debug text selection", 
                                   font=('Arial', 10), fg='#7f8c8d')
        self.status_label.pack(pady=5)
        
    def start_monitoring(self):
        """Start monitoring for text selection."""
        try:
            keyboard.add_hotkey('ctrl+alt+d', self.debug_text_selection)
            self.is_monitoring = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text="✅ Monitoring active - Press Ctrl+Alt+D to test selection", fg='#27ae60')
            self.log_debug("🚀 Text selection monitoring started")
            self.log_debug("📝 Select text in any application and press Ctrl+Alt+D")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
            
    def stop_monitoring(self):
        """Stop monitoring."""
        try:
            keyboard.unhook_all()
            self.is_monitoring = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.status_label.config(text="⏹️ Monitoring stopped", fg='#e74c3c')
            self.log_debug("⏹️ Text selection monitoring stopped")
        except Exception as e:
            self.log_debug(f"❌ Error stopping monitoring: {e}")
            
    def debug_text_selection(self):
        """Debug text selection when hotkey is pressed."""
        self.log_debug("\n" + "="*50)
        self.log_debug("🎯 TEXT SELECTION DEBUG TRIGGERED")
        self.log_debug("="*50)
        
        # Get window info
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            self.log_debug(f"🪟 Active window: '{window_title}' (class: {class_name})")
        except Exception as e:
            self.log_debug(f"❌ Failed to get window info: {e}")
        
        # Test all methods
        results = {}
        
        # Method 1: Standard clipboard
        self.log_debug("\n🔍 Testing Method 1: Standard Clipboard")
        results['clipboard'] = self.test_clipboard_method()
        
        # Method 2: Windows API
        self.log_debug("\n🔍 Testing Method 2: Windows API")
        results['windows_api'] = self.test_windows_api_method()
        
        # Method 3: Alternative shortcuts
        self.log_debug("\n🔍 Testing Method 3: Alternative Shortcuts")
        results['alternative'] = self.test_alternative_method()
        
        # Summary
        self.log_debug("\n" + "="*30)
        self.log_debug("📊 RESULTS SUMMARY:")
        self.log_debug("="*30)
        
        success_count = 0
        for method, result in results.items():
            if result:
                self.log_debug(f"✅ {method}: SUCCESS - '{result[:50]}...'")
                success_count += 1
            else:
                self.log_debug(f"❌ {method}: FAILED")
        
        if success_count == 0:
            self.log_debug("\n🚨 ALL METHODS FAILED!")
            self.log_debug("💡 Suggestions:")
            self.log_debug("   • Make sure text is actually selected (highlighted)")
            self.log_debug("   • Try selecting more text (at least 3-4 characters)")
            self.log_debug("   • Wait a moment after selection before pressing hotkey")
            self.log_debug("   • Try in different applications (Notepad, Chrome, etc.)")
        else:
            self.log_debug(f"\n✅ {success_count}/3 methods succeeded!")
            
    def test_clipboard_method(self):
        """Test standard clipboard method."""
        try:
            # Save original clipboard
            original = ""
            try:
                original = pyperclip.paste()
            except:
                pass
            
            # Clear and copy
            pyperclip.copy("")
            time.sleep(0.1)
            keyboard.send('ctrl+c')
            time.sleep(0.3)
            
            # Get result
            result = ""
            try:
                result = pyperclip.paste()
            except:
                pass
            
            # Restore clipboard
            try:
                if original:
                    pyperclip.copy(original)
            except:
                pass
            
            if result and result.strip():
                self.log_debug(f"   ✅ Got {len(result)} characters: '{result[:30]}...'")
                return result.strip()
            else:
                self.log_debug("   ❌ No text captured")
                return ""
                
        except Exception as e:
            self.log_debug(f"   ❌ Error: {e}")
            return ""
    
    def test_windows_api_method(self):
        """Test Windows API method."""
        try:
            import win32gui
            import win32con
            import win32api
            
            hwnd = win32gui.GetForegroundWindow()
            win32api.SendMessage(hwnd, win32con.WM_COPY, 0, 0)
            time.sleep(0.2)
            
            result = ""
            try:
                result = pyperclip.paste()
            except:
                pass
            
            if result and result.strip():
                self.log_debug(f"   ✅ Got {len(result)} characters: '{result[:30]}...'")
                return result.strip()
            else:
                self.log_debug("   ❌ No text captured")
                return ""
                
        except Exception as e:
            self.log_debug(f"   ❌ Error: {e}")
            return ""
    
    def test_alternative_method(self):
        """Test alternative keyboard shortcuts."""
        try:
            # Save original clipboard
            original = ""
            try:
                original = pyperclip.paste()
            except:
                pass
            
            # Clear and try Ctrl+Insert
            pyperclip.copy("")
            time.sleep(0.1)
            keyboard.send('ctrl+insert')
            time.sleep(0.3)
            
            # Get result
            result = ""
            try:
                result = pyperclip.paste()
            except:
                pass
            
            # Restore clipboard
            try:
                if original:
                    pyperclip.copy(original)
            except:
                pass
            
            if result and result.strip():
                self.log_debug(f"   ✅ Got {len(result)} characters: '{result[:30]}...'")
                return result.strip()
            else:
                self.log_debug("   ❌ No text captured")
                return ""
                
        except Exception as e:
            self.log_debug(f"   ❌ Error: {e}")
            return ""
    
    def test_current_selection(self):
        """Test current selection without hotkey."""
        self.debug_text_selection()
        
    def log_debug(self, message):
        """Log debug message to output."""
        timestamp = time.strftime("%H:%M:%S")
        self.debug_output.insert(tk.END, f"[{timestamp}] {message}\n")
        self.debug_output.see(tk.END)
        self.root.update()
        
    def run(self):
        """Run the debugger."""
        self.root.mainloop()

if __name__ == "__main__":
    debugger = TextSelectionDebugger()
    debugger.run()
