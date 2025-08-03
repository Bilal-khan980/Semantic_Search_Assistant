#!/usr/bin/env python3
"""
Quick fix for text selection issues - simpler, more reliable approach
"""

import tkinter as tk
from tkinter import messagebox
import pyperclip
import keyboard
import time
import threading

class SimpleTextCapture:
    def __init__(self):
        self.is_active = False
        
    def start_capture(self):
        """Start the simple text capture system."""
        try:
            keyboard.add_hotkey('ctrl+alt+h', self.capture_text)
            self.is_active = True
            print("✅ Simple text capture active - Press Ctrl+Alt+H")
            return True
        except Exception as e:
            print(f"❌ Failed to start: {e}")
            return False
    
    def capture_text(self):
        """Capture text using a simple, reliable method."""
        try:
            print("🎯 Capture triggered!")

            # Save original clipboard
            original_clipboard = self.get_clipboard_safe()
            print(f"📋 Original clipboard: '{original_clipboard[:30]}...' ({len(original_clipboard)} chars)")

            # Method 1: Direct copy (most reliable)
            print("📋 Method 1: Direct copy...")
            keyboard.send('ctrl+c')
            time.sleep(0.5)  # Wait for copy

            # Check what we got
            new_clipboard = self.get_clipboard_safe()
            print(f"📋 After direct copy: '{new_clipboard[:30]}...' ({len(new_clipboard)} chars)")

            # Check if we got different text
            if new_clipboard and new_clipboard != original_clipboard and new_clipboard.strip():
                selected_text = new_clipboard.strip()
                if len(selected_text) >= 3:
                    print(f"✅ SUCCESS (Method 1)! Captured: '{selected_text[:50]}...'")
                    self.show_success_dialog(selected_text)
                    return

            # Method 2: Clear clipboard first, then copy
            print("📋 Method 2: Clear then copy...")
            self.set_clipboard_safe("")  # Clear clipboard
            time.sleep(0.1)

            keyboard.send('ctrl+c')
            time.sleep(0.5)  # Wait for copy

            # Check what we got
            cleared_clipboard = self.get_clipboard_safe()
            print(f"📋 After clear+copy: '{cleared_clipboard[:30]}...' ({len(cleared_clipboard)} chars)")

            # Restore original clipboard first
            self.set_clipboard_safe(original_clipboard)

            # Check if we got text
            if cleared_clipboard and cleared_clipboard.strip() and cleared_clipboard != "":
                selected_text = cleared_clipboard.strip()
                if len(selected_text) >= 3:
                    print(f"✅ SUCCESS (Method 2)! Captured: '{selected_text[:50]}...'")
                    self.show_success_dialog(selected_text)
                    return
                else:
                    print(f"❌ Text too short: {len(selected_text)} chars")

            # Method 3: Try alternative copy shortcut
            print("📋 Method 3: Alternative shortcut (Ctrl+Insert)...")
            self.set_clipboard_safe("")  # Clear clipboard
            time.sleep(0.1)

            keyboard.send('ctrl+insert')
            time.sleep(0.5)

            # Check what we got
            alt_clipboard = self.get_clipboard_safe()
            print(f"📋 After Ctrl+Insert: '{alt_clipboard[:30]}...' ({len(alt_clipboard)} chars)")

            # Restore original clipboard
            self.set_clipboard_safe(original_clipboard)

            # Check if we got text
            if alt_clipboard and alt_clipboard.strip() and alt_clipboard != "":
                selected_text = alt_clipboard.strip()
                if len(selected_text) >= 3:
                    print(f"✅ SUCCESS (Method 3)! Captured: '{selected_text[:50]}...'")
                    self.show_success_dialog(selected_text)
                    return

            print("❌ All methods failed - no text detected")
            self.show_error_dialog()

        except Exception as e:
            print(f"❌ Capture error: {e}")
            self.show_error_dialog(str(e))
    
    def get_clipboard_safe(self):
        """Safely get clipboard content."""
        try:
            return pyperclip.paste()
        except:
            return ""
    
    def set_clipboard_safe(self, text):
        """Safely set clipboard content."""
        try:
            pyperclip.copy(text)
            return True
        except:
            return False
    
    def show_success_dialog(self, text):
        """Show success dialog with captured text."""
        def show_dialog():
            root = tk.Tk()
            root.withdraw()
            
            dialog = tk.Toplevel(root)
            dialog.title("✅ Text Captured!")
            dialog.geometry("500x400")
            dialog.attributes('-topmost', True)
            
            # Title
            title_label = tk.Label(dialog, text="✅ Text Successfully Captured!", 
                                 font=('Arial', 14, 'bold'), fg='#27ae60')
            title_label.pack(pady=10)
            
            # Text display
            text_frame = tk.LabelFrame(dialog, text="Captured Text:", font=('Arial', 10, 'bold'))
            text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            text_display = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 11), height=10)
            text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_display.insert('1.0', text)
            text_display.config(state='disabled')
            
            # Info
            info_label = tk.Label(dialog, 
                                text=f"📊 Length: {len(text)} characters\n"
                                     f"📝 Words: {len(text.split())} words\n"
                                     f"🎯 This would be saved to your highlight database",
                                font=('Arial', 10), justify=tk.CENTER)
            info_label.pack(pady=10)
            
            # Close button
            close_btn = tk.Button(dialog, text="Close", command=root.quit,
                                bg='#3498db', fg='white', font=('Arial', 11, 'bold'),
                                padx=20, pady=8)
            close_btn.pack(pady=10)
            
            root.mainloop()
        
        # Run in separate thread to avoid blocking
        threading.Thread(target=show_dialog, daemon=True).start()
    
    def show_error_dialog(self, error_msg=""):
        """Show error dialog."""
        def show_dialog():
            root = tk.Tk()
            root.withdraw()
            
            error_text = "❌ No text selected or text too short\n\n"
            error_text += "💡 Troubleshooting tips:\n"
            error_text += "• Make sure text is highlighted (blue selection)\n"
            error_text += "• Select at least 3-4 characters\n"
            error_text += "• Wait a moment after selection\n"
            error_text += "• Try in Notepad first (simplest test)\n"
            
            if error_msg:
                error_text += f"\n🔍 Technical details: {error_msg}"
            
            messagebox.showerror("Text Capture Failed", error_text)
            root.quit()
        
        # Run in separate thread
        threading.Thread(target=show_dialog, daemon=True).start()

def main():
    """Main function to test the simple capture system."""
    print("🚀 Starting Simple Text Capture Test")
    print("="*50)
    
    capture = SimpleTextCapture()
    
    if capture.start_capture():
        print("\n✅ Text capture is now active!")
        print("📝 Instructions:")
        print("   1. Go to any application (Notepad, Chrome, Word, etc.)")
        print("   2. Select some text with your mouse")
        print("   3. Press Ctrl+Alt+H")
        print("   4. Check if the text is captured correctly")
        print("\n🛑 Press Ctrl+C in this window to stop")
        
        try:
            # Keep the script running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping text capture...")
            keyboard.unhook_all()
            print("✅ Stopped")
    else:
        print("❌ Failed to start text capture")

if __name__ == "__main__":
    main()
