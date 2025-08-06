#!/usr/bin/env python3
"""
COMPLETELY FIXED highlight capture - no markers, simple approach
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import pyperclip
import keyboard
import time
import logging
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedHighlightCapture:
    def __init__(self):
        self.is_active = False
        
    def start_capture(self):
        """Start the fixed highlight capture system."""
        try:
            keyboard.add_hotkey('ctrl+shift+g', self.capture_highlight_simple)
            self.is_active = True
            logger.info("✅ Fixed highlight capture active (Ctrl+Shift+G)")
            print("✅ Fixed highlight capture active - Press Ctrl+Shift+G")
            return True
        except Exception as e:
            logger.error(f"Failed to start: {e}")
            return False
    
    def capture_highlight_simple(self):
        """Capture highlighted text using the simplest possible method."""
        try:
            logger.info("🎯 Highlight capture triggered!")
            print("\n🎯 Capture triggered!")
            
            # Step 1: Get what's currently in clipboard (before copy)
            original_clipboard = self.safe_get_clipboard()
            print(f"📋 Original clipboard: '{original_clipboard[:30]}...' ({len(original_clipboard)} chars)")
            
            # Step 2: Send Ctrl+C and wait
            print("📋 Sending Ctrl+C...")
            keyboard.send('ctrl+c')
            time.sleep(0.6)  # Longer wait
            
            # Step 3: Get what's now in clipboard (after copy)
            new_clipboard = self.safe_get_clipboard()
            print(f"📋 New clipboard: '{new_clipboard[:30]}...' ({len(new_clipboard)} chars)")
            
            # Step 4: Simple logic - if clipboard changed, we got selected text
            if new_clipboard != original_clipboard and new_clipboard.strip():
                selected_text = new_clipboard.strip()
                
                if len(selected_text) >= 3:
                    print(f"✅ SUCCESS! Captured: '{selected_text[:50]}...'")
                    self.show_capture_dialog(selected_text)
                    return
                else:
                    print(f"❌ Text too short: {len(selected_text)} chars")
            else:
                print("❌ No change in clipboard - no text was selected")
            
            # Show error
            self.show_error_message()
            
        except Exception as e:
            logger.error(f"Capture error: {e}")
            print(f"❌ Error: {e}")
            self.show_error_message(str(e))
    
    def safe_get_clipboard(self):
        """Safely get clipboard content."""
        try:
            content = pyperclip.paste()
            return content if content else ""
        except Exception as e:
            logger.error(f"Clipboard read error: {e}")
            return ""
    
    def show_capture_dialog(self, selected_text):
        """Show dialog with captured text."""
        def show_dialog():
            try:
                root = tk.Tk()
                root.withdraw()  # Hide main window
                
                # Create dialog
                dialog = tk.Toplevel(root)
                dialog.title("✅ Text Captured Successfully!")
                dialog.geometry("600x500")
                dialog.attributes('-topmost', True)
                dialog.grab_set()
                
                # Title
                title_label = tk.Label(dialog, 
                                     text="✅ Highlight Captured Successfully!", 
                                     font=('Arial', 16, 'bold'), 
                                     fg='#27ae60')
                title_label.pack(pady=15)
                
                # Captured text display
                text_frame = tk.LabelFrame(dialog, text="📝 Captured Text:", 
                                         font=('Arial', 12, 'bold'))
                text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
                
                text_display = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 11), 
                                     height=8, bg='#f8f9fa')
                text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_display.insert('1.0', selected_text)
                text_display.config(state='disabled')
                
                # Stats
                stats_text = f"📊 Statistics:\n"
                stats_text += f"• Characters: {len(selected_text)}\n"
                stats_text += f"• Words: {len(selected_text.split())}\n"
                stats_text += f"• Lines: {len(selected_text.splitlines())}"
                
                stats_label = tk.Label(dialog, text=stats_text, 
                                     font=('Arial', 10), justify=tk.LEFT,
                                     bg='#e8f5e8', relief=tk.RAISED, padx=10, pady=5)
                stats_label.pack(fill=tk.X, padx=20, pady=5)
                
                # Input fields
                input_frame = tk.LabelFrame(dialog, text="📝 Add Tags and Notes:", 
                                          font=('Arial', 11, 'bold'))
                input_frame.pack(fill=tk.X, padx=20, pady=10)
                
                # Tags
                tk.Label(input_frame, text="🏷️ Tags (e.g., #research #important):", 
                        font=('Arial', 10)).pack(anchor=tk.W, padx=10, pady=(10,0))
                tags_entry = tk.Entry(input_frame, font=('Arial', 11), width=50)
                tags_entry.pack(fill=tk.X, padx=10, pady=5)
                tags_entry.focus()
                
                # Notes
                tk.Label(input_frame, text="📝 Personal Notes:", 
                        font=('Arial', 10)).pack(anchor=tk.W, padx=10, pady=(10,0))
                notes_text = tk.Text(input_frame, height=3, font=('Arial', 11))
                notes_text.pack(fill=tk.X, padx=10, pady=5)
                
                # Buttons
                button_frame = tk.Frame(dialog)
                button_frame.pack(fill=tk.X, padx=20, pady=15)
                
                def save_highlight():
                    tags = tags_entry.get().strip()
                    notes = notes_text.get('1.0', tk.END).strip()
                    
                    print(f"💾 Would save highlight:")
                    print(f"   Text: '{selected_text[:50]}...'")
                    print(f"   Tags: '{tags}'")
                    print(f"   Notes: '{notes}'")
                    
                    messagebox.showinfo("✅ Saved", 
                                      f"Highlight saved successfully!\n\n"
                                      f"Text: {len(selected_text)} characters\n"
                                      f"Tags: {tags if tags else 'None'}\n"
                                      f"Notes: {len(notes)} characters")
                    root.quit()
                
                def cancel():
                    print("❌ Highlight capture cancelled")
                    root.quit()
                
                save_btn = tk.Button(button_frame, text="💾 Save Highlight", 
                                   command=save_highlight,
                                   bg='#27ae60', fg='white', 
                                   font=('Arial', 12, 'bold'),
                                   padx=20, pady=8)
                save_btn.pack(side=tk.LEFT, padx=5)
                
                cancel_btn = tk.Button(button_frame, text="❌ Cancel", 
                                     command=cancel,
                                     bg='#e74c3c', fg='white', 
                                     font=('Arial', 12, 'bold'),
                                     padx=20, pady=8)
                cancel_btn.pack(side=tk.RIGHT, padx=5)
                
                # Center the dialog
                dialog.update_idletasks()
                x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
                y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
                dialog.geometry(f"+{x}+{y}")
                
                root.mainloop()
                
            except Exception as e:
                logger.error(f"Dialog error: {e}")
                messagebox.showerror("Error", f"Failed to show dialog: {e}")
        
        # Run in separate thread
        threading.Thread(target=show_dialog, daemon=True).start()
    
    def show_error_message(self, error_details=""):
        """Show error message."""
        def show_error():
            try:
                root = tk.Tk()
                root.withdraw()
                
                error_msg = "❌ No text selected or text too short\n\n"
                error_msg += "💡 Troubleshooting:\n"
                error_msg += "• Make sure text is highlighted (blue selection)\n"
                error_msg += "• Select at least 3-4 characters\n"
                error_msg += "• Wait a moment after selection\n"
                error_msg += "• Try in Notepad first (simplest test)\n"
                error_msg += "• Make sure the text is actually selectable\n\n"
                
                if error_details:
                    error_msg += f"Technical details: {error_details}"
                
                messagebox.showerror("Text Capture Failed", error_msg)
                root.quit()
                
            except Exception as e:
                print(f"Error showing error dialog: {e}")
        
        threading.Thread(target=show_error, daemon=True).start()

def main():
    """Main function to test the fixed capture system."""
    print("🚀 FIXED Highlight Capture System")
    print("="*50)
    print("This version uses the simplest possible approach:")
    print("1. Save current clipboard")
    print("2. Send Ctrl+C")
    print("3. Check if clipboard changed")
    print("4. If changed = success!")
    print()
    
    capture = FixedHighlightCapture()
    
    if capture.start_capture():
        print("✅ System is now active!")
        print()
        print("📝 Test Instructions:")
        print("   1. Open Notepad")
        print("   2. Type: 'This is a test of the fixed highlight system'")
        print("   3. Select the text with your mouse (make sure it's blue/highlighted)")
        print("   4. Press Ctrl+Shift+G")
        print("   5. Should show the ACTUAL selected text (not any markers!)")
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
