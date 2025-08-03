#!/usr/bin/env python3
"""
Manual verification - test if copy works at all in the problematic application
"""

import pyperclip
import time
import tkinter as tk
from tkinter import messagebox

def check_manual_copy():
    """Check if manual copy worked."""
    try:
        clipboard_content = pyperclip.paste()
        
        if clipboard_content and clipboard_content.strip():
            result = f"✅ SUCCESS! Manual copy worked!\n\n"
            result += f"Clipboard contains:\n"
            result += f"'{clipboard_content}'\n\n"
            result += f"Length: {len(clipboard_content)} characters\n"
            result += f"Words: {len(clipboard_content.split())} words\n\n"
            result += f"This means the application DOES support copying.\n"
            result += f"The issue is with our automated copy method."
            
            messagebox.showinfo("✅ Manual Copy Works!", result)
            print("✅ Manual copy successful!")
            print(f"Content: '{clipboard_content}'")
            return True
        else:
            result = f"❌ Manual copy failed or clipboard is empty.\n\n"
            result += f"This suggests:\n"
            result += f"• The application doesn't support copying\n"
            result += f"• The text isn't actually selectable\n"
            result += f"• There's a security restriction\n\n"
            result += f"Try selecting text in Notepad first to verify\n"
            result += f"the basic copy functionality works."
            
            messagebox.showerror("❌ Manual Copy Failed", result)
            print("❌ Manual copy failed")
            return False
            
    except Exception as e:
        error_msg = f"❌ Error checking clipboard: {e}\n\n"
        error_msg += f"This might indicate a clipboard access issue."
        messagebox.showerror("❌ Clipboard Error", error_msg)
        print(f"❌ Clipboard error: {e}")
        return False

def main():
    """Main verification function."""
    print("🧪 Manual Copy Verification")
    print("="*40)
    print()
    print("This test will verify if manual copying works")
    print("in the application where you're having issues.")
    print()
    print("📝 Instructions:")
    print("1. Go to the application where text selection failed")
    print("2. Select the same text you tried before")
    print("3. Manually press Ctrl+C (don't use our hotkey)")
    print("4. Come back here and click the button below")
    print()
    print("This will tell us if the problem is:")
    print("• The application doesn't support copying (fundamental issue)")
    print("• Our automated copy method needs improvement")
    print()
    
    # Create simple GUI
    root = tk.Tk()
    root.title("🧪 Manual Copy Verification")
    root.geometry("500x300")
    
    # Instructions
    instructions = tk.Label(root, 
                          text="Manual Copy Verification Test\n\n"
                               "1. Go to your application\n"
                               "2. Select text\n"
                               "3. Press Ctrl+C manually\n"
                               "4. Click the button below",
                          font=('Arial', 12), justify=tk.CENTER)
    instructions.pack(pady=30)
    
    # Test button
    test_btn = tk.Button(root, 
                        text="🔍 Check If Manual Copy Worked",
                        command=check_manual_copy,
                        bg='#3498db', fg='white',
                        font=('Arial', 14, 'bold'),
                        padx=20, pady=15)
    test_btn.pack(pady=20)
    
    # Status
    status = tk.Label(root, 
                     text="Select text in your app, press Ctrl+C, then click the button",
                     font=('Arial', 10), fg='#7f8c8d')
    status.pack(pady=10)
    
    # Additional info
    info = tk.Label(root,
                   text="If manual copy doesn't work, the application\n"
                        "may not support text copying at all.",
                   font=('Arial', 9), fg='#95a5a6')
    info.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
