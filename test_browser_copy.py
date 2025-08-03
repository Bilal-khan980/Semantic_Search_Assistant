#!/usr/bin/env python3
"""
Test if manual copy works in the browser where selection failed
"""

import pyperclip
import time
import tkinter as tk
from tkinter import messagebox

def test_manual_browser_copy():
    """Test if manual copy works in browser."""
    print("🧪 Testing manual copy in browser...")
    
    try:
        clipboard_content = pyperclip.paste()
        
        if clipboard_content and clipboard_content.strip():
            print(f"✅ Manual copy worked!")
            print(f"Content: '{clipboard_content}'")
            
            result_msg = f"✅ MANUAL COPY WORKS!\n\n"
            result_msg += f"Your browser DOES support copying.\n"
            result_msg += f"The issue is with our automated method.\n\n"
            result_msg += f"Captured text:\n'{clipboard_content}'\n\n"
            result_msg += f"Length: {len(clipboard_content)} characters\n\n"
            result_msg += f"Solution: We need to improve the automated\n"
            result_msg += f"copy timing for your specific browser."
            
            messagebox.showinfo("✅ Manual Copy Success", result_msg)
            return True
        else:
            print("❌ Manual copy failed or clipboard empty")
            
            result_msg = f"❌ MANUAL COPY FAILED\n\n"
            result_msg += f"This means your browser or the website\n"
            result_msg += f"is preventing text copying entirely.\n\n"
            result_msg += f"Possible causes:\n"
            result_msg += f"• Website has copy protection\n"
            result_msg += f"• Browser security settings\n"
            result_msg += f"• Text is not actually selectable\n"
            result_msg += f"• JavaScript blocking copy operations\n\n"
            result_msg += f"Try:\n"
            result_msg += f"• Right-click → Copy\n"
            result_msg += f"• Different browser\n"
            result_msg += f"• Incognito/private mode"
            
            messagebox.showerror("❌ Manual Copy Failed", result_msg)
            return False
            
    except Exception as e:
        error_msg = f"❌ Error checking clipboard: {e}"
        messagebox.showerror("❌ Clipboard Error", error_msg)
        return False

def main():
    """Main test function."""
    print("🧪 Browser Copy Test")
    print("="*30)
    print()
    print("This will test if manual copying works in your browser.")
    print()
    print("📝 Steps:")
    print("1. Go back to your browser")
    print("2. Select the SAME text that failed before")
    print("3. Manually press Ctrl+C (not our hotkey)")
    print("4. Come back here and click the test button")
    print()
    print("This will tell us if the problem is:")
    print("• Browser/website blocking copy (fundamental issue)")
    print("• Our automated timing needs adjustment")
    print()
    
    # Create GUI
    root = tk.Tk()
    root.title("🧪 Browser Copy Test")
    root.geometry("500x350")
    
    # Instructions
    instructions = tk.Label(root,
                          text="🧪 Browser Copy Test\n\n"
                               "1. Go to your browser\n"
                               "2. Select the same text\n"
                               "3. Press Ctrl+C manually\n"
                               "4. Click the button below",
                          font=('Arial', 12), justify=tk.CENTER)
    instructions.pack(pady=30)
    
    # Test button
    test_btn = tk.Button(root,
                        text="🔍 Test Manual Copy",
                        command=test_manual_browser_copy,
                        bg='#e74c3c', fg='white',
                        font=('Arial', 14, 'bold'),
                        padx=25, pady=15)
    test_btn.pack(pady=20)
    
    # Info
    info_text = ("If manual copy works: We can fix the automation\n"
                "If manual copy fails: The browser/site blocks copying")
    
    info_label = tk.Label(root, text=info_text,
                         font=('Arial', 10), fg='#7f8c8d',
                         justify=tk.CENTER)
    info_label.pack(pady=15)
    
    # Additional tips
    tips = tk.Label(root,
                   text="💡 If manual copy fails, try:\n"
                        "• Right-click → Copy\n"
                        "• Different browser\n"
                        "• Incognito mode",
                   font=('Arial', 9), fg='#95a5a6',
                   justify=tk.CENTER)
    tips.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
