#!/usr/bin/env python3
"""
Web-specific text capture that handles browser selection issues
"""

import pyperclip
import keyboard
import time
import win32gui
import win32con
import win32api
import tkinter as tk
from tkinter import messagebox
import threading

class WebTextCapture:
    def __init__(self):
        self.is_active = False
        
    def start_capture(self):
        """Start web-specific text capture."""
        try:
            keyboard.add_hotkey('ctrl+shift+g', self.capture_web_text)
            self.is_active = True
            print("✅ Web text capture active - Press Ctrl+Shift+G")
            return True
        except Exception as e:
            print(f"❌ Failed to start: {e}")
            return False
    
    def capture_web_text(self):
        """Capture text from web browsers with multiple methods."""
        try:
            print("\n🎯 Web text capture triggered!")
            
            # Get window info
            window_info = self.get_window_info()
            print(f"🪟 Active window: {window_info}")
            
            # Check if it's a browser
            is_browser = self.is_browser_window(window_info)
            print(f"🌐 Browser detected: {'✅ YES' if is_browser else '❌ NO'}")
            
            # Try multiple web-specific methods
            selected_text = None
            
            # Method 1: Multiple copy attempts with longer delays
            print("📋 Method 1: Extended copy attempts...")
            selected_text = self.try_extended_copy()
            if selected_text:
                print(f"✅ Method 1 success: '{selected_text[:50]}...'")
                self.show_success(selected_text, "Extended Copy")
                return
            
            # Method 2: Focus + copy
            print("📋 Method 2: Focus window + copy...")
            selected_text = self.try_focus_copy()
            if selected_text:
                print(f"✅ Method 2 success: '{selected_text[:50]}...'")
                self.show_success(selected_text, "Focus Copy")
                return
            
            # Method 3: Alternative shortcuts
            print("📋 Method 3: Alternative shortcuts...")
            selected_text = self.try_alternative_shortcuts()
            if selected_text:
                print(f"✅ Method 3 success: '{selected_text[:50]}...'")
                self.show_success(selected_text, "Alternative Shortcuts")
                return
            
            # Method 4: Browser-specific approach
            if is_browser:
                print("📋 Method 4: Browser-specific approach...")
                selected_text = self.try_browser_specific()
                if selected_text:
                    print(f"✅ Method 4 success: '{selected_text[:50]}...'")
                    self.show_success(selected_text, "Browser Specific")
                    return
            
            # All methods failed
            print("❌ All methods failed")
            self.show_web_specific_error(window_info, is_browser)
            
        except Exception as e:
            print(f"❌ Capture error: {e}")
            self.show_error(str(e))
    
    def get_window_info(self):
        """Get information about the active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            return f"{window_title} ({class_name})"
        except:
            return "Unknown"
    
    def is_browser_window(self, window_info):
        """Check if the active window is a browser."""
        browser_indicators = [
            'chrome', 'firefox', 'edge', 'safari', 'opera', 'brave',
            'mozilla', 'webkit', 'browser', 'internet explorer'
        ]
        window_lower = window_info.lower()
        return any(indicator in window_lower for indicator in browser_indicators)
    
    def try_extended_copy(self):
        """Try copy with extended delays and multiple attempts."""
        original_clipboard = self.safe_get_clipboard()
        
        for attempt in range(5):  # 5 attempts
            try:
                print(f"   Attempt {attempt + 1}/5...")
                
                # Clear clipboard
                pyperclip.copy("")
                time.sleep(0.1)
                
                # Send copy command
                keyboard.send('ctrl+c')
                
                # Progressive delay (longer each time)
                delay = 0.3 + (attempt * 0.2)  # 0.3, 0.5, 0.7, 0.9, 1.1 seconds
                time.sleep(delay)
                
                # Check result
                new_clipboard = self.safe_get_clipboard()
                if new_clipboard and new_clipboard.strip() and new_clipboard != original_clipboard:
                    return new_clipboard.strip()
                    
            except Exception as e:
                print(f"   Attempt {attempt + 1} error: {e}")
        
        return None
    
    def try_focus_copy(self):
        """Try focusing the window first, then copy."""
        try:
            # Get and focus the window
            hwnd = win32gui.GetForegroundWindow()
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.2)
            
            # Try copy
            original_clipboard = self.safe_get_clipboard()
            keyboard.send('ctrl+c')
            time.sleep(0.8)  # Longer delay
            
            new_clipboard = self.safe_get_clipboard()
            if new_clipboard and new_clipboard.strip() and new_clipboard != original_clipboard:
                return new_clipboard.strip()
                
        except Exception as e:
            print(f"   Focus copy error: {e}")
        
        return None
    
    def try_alternative_shortcuts(self):
        """Try alternative copy shortcuts."""
        original_clipboard = self.safe_get_clipboard()
        
        shortcuts = ['ctrl+insert', 'shift+f10', 'ctrl+a,ctrl+c']
        
        for shortcut in shortcuts:
            try:
                print(f"   Trying {shortcut}...")
                
                if shortcut == 'ctrl+a,ctrl+c':
                    # Select all then copy (last resort)
                    keyboard.send('ctrl+a')
                    time.sleep(0.3)
                    keyboard.send('ctrl+c')
                    time.sleep(0.5)
                else:
                    keyboard.send(shortcut)
                    time.sleep(0.5)
                
                new_clipboard = self.safe_get_clipboard()
                if new_clipboard and new_clipboard.strip() and new_clipboard != original_clipboard:
                    return new_clipboard.strip()
                    
            except Exception as e:
                print(f"   {shortcut} error: {e}")
        
        return None
    
    def try_browser_specific(self):
        """Try browser-specific methods."""
        try:
            # Method: Right-click context menu approach
            print("   Trying right-click method...")
            
            # Simulate right-click
            keyboard.send('shift+f10')  # Context menu key
            time.sleep(0.3)
            keyboard.send('c')  # Press 'c' for copy
            time.sleep(0.5)
            
            new_clipboard = self.safe_get_clipboard()
            if new_clipboard and new_clipboard.strip():
                return new_clipboard.strip()
                
        except Exception as e:
            print(f"   Browser method error: {e}")
        
        return None
    
    def safe_get_clipboard(self):
        """Safely get clipboard content."""
        try:
            return pyperclip.paste()
        except:
            return ""
    
    def show_success(self, text, method):
        """Show success dialog."""
        def show_dialog():
            root = tk.Tk()
            root.withdraw()
            
            dialog = tk.Toplevel(root)
            dialog.title("✅ Web Text Captured!")
            dialog.geometry("600x400")
            dialog.attributes('-topmost', True)
            
            # Title
            title = tk.Label(dialog, text=f"✅ Success with {method}!", 
                           font=('Arial', 14, 'bold'), fg='#27ae60')
            title.pack(pady=10)
            
            # Text display
            text_frame = tk.LabelFrame(dialog, text="Captured Text:")
            text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            text_display = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 11))
            text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_display.insert('1.0', text)
            text_display.config(state='disabled')
            
            # Stats
            stats = f"📊 Length: {len(text)} chars | Words: {len(text.split())} | Method: {method}"
            stats_label = tk.Label(dialog, text=stats, font=('Arial', 10))
            stats_label.pack(pady=5)
            
            # Close button
            close_btn = tk.Button(dialog, text="Close", command=root.quit,
                                bg='#3498db', fg='white', font=('Arial', 11, 'bold'))
            close_btn.pack(pady=10)
            
            root.mainloop()
        
        threading.Thread(target=show_dialog, daemon=True).start()
    
    def show_web_specific_error(self, window_info, is_browser):
        """Show web-specific error message."""
        def show_error():
            root = tk.Tk()
            root.withdraw()
            
            error_msg = "❌ Web Text Capture Failed\n\n"
            error_msg += f"Window: {window_info}\n"
            error_msg += f"Browser: {'Yes' if is_browser else 'No'}\n\n"
            
            if is_browser:
                error_msg += "🌐 Browser-specific solutions:\n"
                error_msg += "• Try selecting text and manually pressing Ctrl+C first\n"
                error_msg += "• Some websites prevent text copying\n"
                error_msg += "• Try right-clicking and selecting 'Copy'\n"
                error_msg += "• Check if the page has copy protection\n"
                error_msg += "• Try in a different browser or incognito mode\n"
            else:
                error_msg += "💡 General solutions:\n"
                error_msg += "• Make sure text is actually selectable\n"
                error_msg += "• Try in a simpler application (like Notepad)\n"
                error_msg += "• Check if the application allows copying\n"
            
            error_msg += "\n🔧 Technical note: All copy methods failed,\n"
            error_msg += "which suggests the application or website\n"
            error_msg += "may be blocking clipboard operations."
            
            messagebox.showerror("Web Text Capture Failed", error_msg)
            root.quit()
        
        threading.Thread(target=show_error, daemon=True).start()
    
    def show_error(self, error_details):
        """Show general error."""
        def show_error():
            messagebox.showerror("Error", f"Capture failed: {error_details}")
        
        threading.Thread(target=show_error, daemon=True).start()

def main():
    """Main function."""
    print("🌐 Web Text Capture System")
    print("="*40)
    print("Specialized for capturing text from web browsers and HTML content")
    print()
    
    capture = WebTextCapture()
    
    if capture.start_capture():
        print("✅ Web text capture is active!")
        print()
        print("📝 Instructions:")
        print("   1. Go to your web page")
        print("   2. Select text (make sure it's highlighted)")
        print("   3. Press Ctrl+Alt+H")
        print("   4. System will try multiple web-specific methods")
        print()
        print("🔧 This version tries:")
        print("   • Extended copy attempts with longer delays")
        print("   • Window focusing before copy")
        print("   • Alternative keyboard shortcuts")
        print("   • Browser-specific methods")
        print()
        print("🛑 Press Ctrl+C here to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            keyboard.unhook_all()
            print("✅ Stopped")
    else:
        print("❌ Failed to start")

if __name__ == "__main__":
    main()
