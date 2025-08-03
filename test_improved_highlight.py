#!/usr/bin/env python3
"""
Test script for the improved highlight capture with better text selection
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import sys
import time

def test_text_selection():
    """Test text selection in different scenarios."""
    
    test_window = tk.Toplevel()
    test_window.title("🔍 Text Selection Test")
    test_window.geometry("700x600")
    test_window.attributes('-topmost', True)
    
    # Instructions
    instructions = tk.Label(test_window,
                          text="🔍 IMPROVED TEXT SELECTION TEST\n\n"
                               "✅ NEW HOTKEY: Ctrl+Alt+H (safer, no conflicts)\n"
                               "✅ BETTER DETECTION: Improved clipboard handling\n"
                               "✅ LONGER DELAYS: More time for copy operations\n\n"
                               "Test in different applications:",
                          font=('Arial', 12), justify=tk.LEFT, wraplength=650)
    instructions.pack(pady=20, padx=20)
    
    # Test scenarios
    scenarios_frame = tk.LabelFrame(test_window, text="Test Scenarios", 
                                  font=('Arial', 11, 'bold'))
    scenarios_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    scenarios_text = scrolledtext.ScrolledText(scenarios_frame, height=15, wrap=tk.WORD, 
                                             font=('Arial', 10))
    scenarios_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    test_scenarios = """📋 TEST SCENARIOS FOR HIGHLIGHT CAPTURE:

1. 📄 NOTEPAD TEST:
   • Open Notepad
   • Type some text: "This is a test of the highlight capture system"
   • Select the text with your mouse
   • Press Ctrl+Alt+H
   • Should work: Simple text editor, fast copy

2. 🌐 CHROME/BROWSER TEST:
   • Open any webpage
   • Select a paragraph of text
   • Press Ctrl+Alt+H
   • Should work: Web content, standard copy behavior

3. 📖 PDF READER TEST:
   • Open a PDF in Adobe Reader or any PDF viewer
   • Select text from the document
   • Press Ctrl+Alt+H
   • Should work: PDF text extraction

4. 📝 WORD DOCUMENT TEST:
   • Open Microsoft Word
   • Select text from a document
   • Press Ctrl+Alt+H
   • Should work: Rich text editor

5. 💻 CODE EDITOR TEST:
   • Open VS Code, Notepad++, or any code editor
   • Select some code or text
   • Press Ctrl+Alt+H
   • Should work: Programming environments

6. 📧 EMAIL CLIENT TEST:
   • Open Outlook, Gmail, or any email client
   • Select text from an email
   • Press Ctrl+Alt+H
   • Should work: Email content

🔧 TROUBLESHOOTING TIPS:

❌ If "No text detected":
   • Make sure text is actually selected (highlighted)
   • Try selecting again and wait a moment before pressing hotkey
   • Some apps need longer selection time

❌ If "Text too short":
   • Select at least 3-4 characters
   • Avoid selecting just spaces or punctuation

❌ If hotkey conflicts:
   • Ctrl+Alt+H is much safer than Ctrl+Shift+H
   • Very few applications use this combination
   • Adobe Reader auto-scroll was using Ctrl+Shift+H

✅ IMPROVEMENTS MADE:
   • Changed hotkey to Ctrl+Alt+H (no conflicts)
   • Clear clipboard before copy (better detection)
   • Longer delays for copy operations (0.2s instead of 0.1s)
   • Restore original clipboard content
   • Better error handling and retry logic

🎯 SUCCESS INDICATORS:
   • Dialog appears asking for tags and notes
   • Source application is correctly detected
   • Text content is properly captured
   • No conflicts with application shortcuts"""
    
    scenarios_text.insert('1.0', test_scenarios)
    scenarios_text.config(state='disabled')
    
    # Action buttons
    button_frame = tk.Frame(test_window)
    button_frame.pack(pady=20)
    
    def start_capture_test():
        try:
            from highlight_capture import HighlightCapture
            capture = HighlightCapture()
            if capture.start_global_listener():
                messagebox.showinfo("✅ Success", 
                                  "Highlight capture is now active!\n\n"
                                  "🎯 Go to any application\n"
                                  "📝 Select some text\n"
                                  "⌨️ Press Ctrl+Alt+H\n\n"
                                  "The capture dialog should appear!")
            else:
                messagebox.showerror("❌ Error", "Failed to start highlight capture")
        except ImportError:
            messagebox.showerror("❌ Error", "highlight_capture.py not found")
    
    def open_notepad_test():
        try:
            subprocess.Popen(['notepad.exe'])
            messagebox.showinfo("📄 Notepad Test", 
                              "Notepad opened!\n\n"
                              "1. Type some text\n"
                              "2. Select it with your mouse\n"
                              "3. Press Ctrl+Alt+H\n\n"
                              "This should work perfectly!")
        except:
            messagebox.showerror("Error", "Could not open Notepad")
    
    def open_browser_test():
        try:
            import webbrowser
            webbrowser.open('https://en.wikipedia.org/wiki/Natural_language_processing')
            messagebox.showinfo("🌐 Browser Test", 
                              "Wikipedia opened!\n\n"
                              "1. Select any paragraph\n"
                              "2. Press Ctrl+Alt+H\n\n"
                              "Perfect for research!")
        except:
            messagebox.showerror("Error", "Could not open browser")
    
    start_btn = tk.Button(button_frame, 
                        text="🚀 Start Highlight Capture",
                        command=start_capture_test,
                        bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                        padx=15, pady=8)
    start_btn.pack(side=tk.LEFT, padx=5)
    
    notepad_btn = tk.Button(button_frame, 
                          text="📄 Test in Notepad",
                          command=open_notepad_test,
                          bg='#3498db', fg='white', font=('Arial', 11, 'bold'),
                          padx=15, pady=8)
    notepad_btn.pack(side=tk.LEFT, padx=5)
    
    browser_btn = tk.Button(button_frame, 
                          text="🌐 Test in Browser",
                          command=open_browser_test,
                          bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                          padx=15, pady=8)
    browser_btn.pack(side=tk.LEFT, padx=5)

def main():
    """Main test interface."""
    root = tk.Tk()
    root.title("🔧 Improved Highlight Capture Test")
    root.geometry("500x300")
    
    # Main title
    title = tk.Label(root, text="🔧 Improved Highlight Capture", 
                    font=('Arial', 18, 'bold'), fg='#2c3e50')
    title.pack(pady=20)
    
    # Description
    desc = tk.Label(root, 
                   text="Fixed issues with text selection and hotkey conflicts.\n"
                        "Now uses Ctrl+Alt+H and improved text detection.",
                   font=('Arial', 12), justify=tk.CENTER, wraplength=450)
    desc.pack(pady=10)
    
    # Key improvements
    improvements = tk.Label(root,
                          text="✅ Changed hotkey to Ctrl+Alt+H (no conflicts)\n"
                               "✅ Better text selection detection\n"
                               "✅ Longer delays for copy operations\n"
                               "✅ Improved error handling",
                          font=('Arial', 11), justify=tk.LEFT, 
                          bg='#e8f5e8', relief='solid', borderwidth=1)
    improvements.pack(pady=20, padx=20, fill=tk.X)
    
    # Test button
    test_btn = tk.Button(root, 
                       text="🧪 Run Comprehensive Test",
                       command=test_text_selection,
                       bg='#3498db', fg='white', font=('Arial', 14, 'bold'),
                       padx=30, pady=15, relief='flat')
    test_btn.pack(pady=20)
    
    # Status
    status = tk.Label(root, text="Ready to test the improved highlight capture!", 
                     font=('Arial', 10, 'italic'), fg='#7f8c8d')
    status.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
