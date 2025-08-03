#!/usr/bin/env python3
"""
Manual test - you copy text manually, we detect it
"""

import pyperclip
import time
import tkinter as tk
from tkinter import messagebox

def monitor_clipboard():
    """Monitor clipboard for changes."""
    print("🔍 Clipboard Monitor Started")
    print("="*40)
    
    last_clipboard = ""
    try:
        last_clipboard = pyperclip.paste()
        print(f"📋 Initial clipboard: '{last_clipboard[:50]}...'")
    except:
        pass
    
    print("\n📝 Instructions:")
    print("1. Go to any application")
    print("2. Select some text")
    print("3. Press Ctrl+C manually")
    print("4. Come back here to see if it was detected")
    print("5. Press Enter to stop monitoring")
    print()
    
    changes_detected = 0
    
    try:
        while True:
            time.sleep(0.5)  # Check every 500ms
            
            try:
                current_clipboard = pyperclip.paste()
                
                if current_clipboard != last_clipboard:
                    changes_detected += 1
                    print(f"\n🎯 CHANGE #{changes_detected} DETECTED!")
                    print(f"📋 Old: '{last_clipboard[:30]}...'")
                    print(f"📋 New: '{current_clipboard[:30]}...'")
                    print(f"📊 Length: {len(current_clipboard)} chars")
                    print(f"📊 Words: {len(current_clipboard.split())} words")
                    
                    if len(current_clipboard.strip()) >= 3:
                        print("✅ This would be valid for highlight capture!")
                    else:
                        print("❌ Too short for highlight capture")
                    
                    last_clipboard = current_clipboard
                    print("-" * 40)
                    
            except Exception as e:
                print(f"❌ Clipboard read error: {e}")
            
            # Check if user wants to stop
            try:
                import select
                import sys
                if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    break
            except:
                # Windows doesn't have select, so we'll just continue
                pass
                
    except KeyboardInterrupt:
        pass
    
    print(f"\n🛑 Monitoring stopped. Detected {changes_detected} clipboard changes.")

def test_with_gui():
    """Test with a GUI that has selectable text."""
    root = tk.Tk()
    root.title("📝 Manual Copy Test")
    root.geometry("600x400")
    
    # Instructions
    instructions = tk.Label(root, 
                          text="📝 MANUAL COPY TEST\n\n"
                               "1. Select text in the box below\n"
                               "2. Press Ctrl+C\n"
                               "3. Click 'Check Clipboard' to see what was copied",
                          font=('Arial', 12), justify=tk.CENTER)
    instructions.pack(pady=20)
    
    # Test text area
    text_frame = tk.LabelFrame(root, text="Select text here:", font=('Arial', 10, 'bold'))
    text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    test_text = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 11))
    test_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    sample_text = """This is sample text for testing text selection and copying.

Select any part of this text and press Ctrl+C, then click the button below to see what was copied.

Try selecting:
- A single word like "testing"
- Multiple words like "text selection and copying"
- A complete sentence
- This entire paragraph

The goal is to verify that basic copy operations work correctly before we try to automate them with the highlight capture feature."""
    
    test_text.insert('1.0', sample_text)
    
    # Result area
    result_frame = tk.LabelFrame(root, text="Clipboard Content:", font=('Arial', 10, 'bold'))
    result_frame.pack(fill=tk.X, padx=20, pady=10)
    
    result_text = tk.Text(result_frame, height=4, wrap=tk.WORD, font=('Arial', 10))
    result_text.pack(fill=tk.X, padx=10, pady=10)
    
    def check_clipboard():
        """Check what's in the clipboard."""
        try:
            clipboard_content = pyperclip.paste()
            result_text.delete('1.0', tk.END)
            result_text.insert('1.0', f"Clipboard content:\n{clipboard_content}")
            
            if clipboard_content.strip():
                messagebox.showinfo("✅ Success", 
                                  f"Clipboard contains {len(clipboard_content)} characters:\n\n"
                                  f"'{clipboard_content[:100]}{'...' if len(clipboard_content) > 100 else ''}'")
            else:
                messagebox.showwarning("⚠️ Empty", "Clipboard is empty or contains only whitespace")
                
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to read clipboard: {e}")
    
    # Check button
    check_btn = tk.Button(root, text="🔍 Check Clipboard", command=check_clipboard,
                         bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                         padx=20, pady=10)
    check_btn.pack(pady=10)
    
    # Status
    status = tk.Label(root, text="Select text above, press Ctrl+C, then click the button", 
                     font=('Arial', 10), fg='#7f8c8d')
    status.pack(pady=5)
    
    root.mainloop()

def main():
    """Main function."""
    print("🧪 Manual Copy Test")
    print("="*50)
    print("Choose a test method:")
    print("1. Monitor clipboard changes (console)")
    print("2. GUI test with selectable text")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        monitor_clipboard()
    elif choice == "2":
        test_with_gui()
    else:
        print("Invalid choice. Running GUI test...")
        test_with_gui()

if __name__ == "__main__":
    main()
