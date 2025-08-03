#!/usr/bin/env python3
"""
Demo script showing the new highlight capture and citation features
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
from pathlib import Path

def demo_highlight_capture():
    """Demo the highlight capture feature."""
    demo_text = """
🎯 HIGHLIGHT CAPTURE DEMO

This feature allows you to capture text from ANY application:

1. 📖 Open a PDF in Adobe Reader
2. 🌐 Browse to a web article in Chrome  
3. 📝 Open a Word document
4. 📄 View any text document

Then:
✨ Select interesting text with your mouse
⌨️ Press Ctrl+Alt+H
📝 Add your tags (#research #important)
💭 Write your personal notes
💾 Save to searchable database

Example workflow:
• Reading "The attention mechanism allows models to focus on relevant parts"
• Press Ctrl+Alt+H
• Tags: "#ai #attention #transformers"
• Note: "Key concept for my NLP project - explains how BERT works"
• Now searchable with your personal context!

🔍 Later searches for "attention" or "BERT" will find this highlight
   with YOUR personal notes attached!
"""
    
    messagebox.showinfo("📝 Highlight Capture Feature", demo_text)

def demo_citations():
    """Demo the citation feature."""
    demo_text = """
📚 AUTOMATIC CITATIONS DEMO

When you drag search results, they now include citations:

BEFORE (old system):
"Vector embeddings capture semantic meaning"

AFTER (new system):
"Vector embeddings capture semantic meaning

(Source: Natural Language Processing Handbook, p. 127)"

🎯 Perfect for academic writing!
🔬 Proper attribution automatically included
📖 Works with PDFs, documents, web pages
✍️ Drop directly into Word, Google Docs, etc.

Example in your document:
"As noted in recent research, vector embeddings capture semantic meaning 
(Source: NLP Handbook, p. 127). This enables more intelligent search 
capabilities (Source: Modern Search Technologies)."

✨ No more manual citation formatting!
📝 Professional research workflow
🎓 Academic integrity maintained
"""
    
    messagebox.showinfo("📚 Automatic Citations Feature", demo_text)

def run_full_demo():
    """Run the full application to test features."""
    try:
        # Check if start_enhanced_admin.bat exists
        bat_file = Path("start_enhanced_admin.bat")
        if bat_file.exists():
            messagebox.showinfo("🚀 Starting Full Demo", 
                              "Starting the full application...\n\n"
                              "Features to test:\n"
                              "1. Global highlight capture (Ctrl+Shift+H)\n"
                              "2. Drag-and-drop with citations\n"
                              "3. Real-time search as you type\n\n"
                              "The application will open in a new window.")
            
            # Run the batch file
            subprocess.Popen([str(bat_file)], shell=True)
        else:
            messagebox.showerror("Error", "start_enhanced_admin.bat not found.\n\nRun this demo from the project directory.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")

def run_test_suite():
    """Run the test suite."""
    try:
        subprocess.Popen([sys.executable, "test_highlight_and_dragdrop.py"])
        messagebox.showinfo("🧪 Test Suite", "Test suite started!\n\nUse the test interface to try both features.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start test suite: {e}")

def main():
    """Main demo interface."""
    root = tk.Tk()
    root.title("✨ New Features Demo")
    root.geometry("600x500")
    root.configure(bg='#f8f9fa')
    
    # Header
    header = tk.Label(root, 
                     text="✨ NEW FEATURES DEMO",
                     font=('Arial', 20, 'bold'), 
                     bg='#f8f9fa', fg='#2c3e50')
    header.pack(pady=20)
    
    # Subtitle
    subtitle = tk.Label(root,
                       text="Highlight Capture + Automatic Citations",
                       font=('Arial', 14), 
                       bg='#f8f9fa', fg='#7f8c8d')
    subtitle.pack(pady=(0, 30))
    
    # Feature buttons
    button_frame = tk.Frame(root, bg='#f8f9fa')
    button_frame.pack(pady=20)
    
    # Highlight capture demo
    highlight_btn = tk.Button(button_frame,
                            text="📝 Highlight Capture Demo\n(Ctrl+Alt+H from any app)",
                            command=demo_highlight_capture,
                            bg='#3498db', fg='white', 
                            font=('Arial', 12, 'bold'),
                            padx=20, pady=15, relief='flat',
                            width=25, height=3)
    highlight_btn.pack(pady=10)
    
    # Citations demo
    citations_btn = tk.Button(button_frame,
                            text="📚 Automatic Citations Demo\n(Drag-drop with references)",
                            command=demo_citations,
                            bg='#e74c3c', fg='white', 
                            font=('Arial', 12, 'bold'),
                            padx=20, pady=15, relief='flat',
                            width=25, height=3)
    citations_btn.pack(pady=10)
    
    # Test suite
    test_btn = tk.Button(button_frame,
                       text="🧪 Interactive Test Suite\n(Try the features yourself)",
                       command=run_test_suite,
                       bg='#f39c12', fg='white', 
                       font=('Arial', 12, 'bold'),
                       padx=20, pady=15, relief='flat',
                       width=25, height=3)
    test_btn.pack(pady=10)
    
    # Full demo
    full_btn = tk.Button(button_frame,
                       text="🚀 Run Full Application\n(Complete working system)",
                       command=run_full_demo,
                       bg='#27ae60', fg='white', 
                       font=('Arial', 12, 'bold'),
                       padx=20, pady=15, relief='flat',
                       width=25, height=3)
    full_btn.pack(pady=10)
    
    # Instructions
    instructions_frame = tk.Frame(root, bg='#ecf0f1', relief='solid', borderwidth=1)
    instructions_frame.pack(fill=tk.X, padx=20, pady=20)
    
    instructions_title = tk.Label(instructions_frame,
                                text="💡 How to Test:",
                                font=('Arial', 12, 'bold'),
                                bg='#ecf0f1', fg='#2c3e50')
    instructions_title.pack(pady=(10, 5))
    
    instructions_text = tk.Label(instructions_frame,
                               text="1. Click demo buttons above to learn about features\n"
                                    "2. Use 'Interactive Test Suite' to try features safely\n"
                                    "3. Use 'Run Full Application' for real-world testing\n"
                                    "4. Test highlight capture: Select text anywhere + Ctrl+Alt+H\n"
                                    "5. Test citations: Drag search results to Word/Notepad",
                               font=('Arial', 10),
                               bg='#ecf0f1', fg='#34495e',
                               justify=tk.LEFT)
    instructions_text.pack(pady=(0, 15), padx=20)
    
    # Footer
    footer = tk.Label(root,
                     text="🎯 These features transform basic search into a powerful research tool",
                     font=('Arial', 10, 'italic'),
                     bg='#f8f9fa', fg='#95a5a6')
    footer.pack(side=tk.BOTTOM, pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
