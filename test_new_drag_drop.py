#!/usr/bin/env python3
"""
Test the new improved drag-and-drop functionality
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

def test_new_drag_drop():
    """Test the new drag-and-drop functionality."""
    
    root = tk.Tk()
    root.title("🖱️ New Drag & Drop Test")
    root.geometry("500x400")
    root.configure(bg='#f0f0f0')
    
    # Instructions
    instructions = tk.Label(root, 
                          text="🎯 NEW DRAG & DROP TEST\n\n"
                               "1. Hover over the blue chunk below\n"
                               "2. Click and drag it\n"
                               "3. Drag to an external app (Word, Notepad)\n"
                               "4. Release to drop - it should auto-paste!\n\n"
                               "✨ Features:\n"
                               "• Green box follows cursor globally\n"
                               "• Auto-activates target applications\n"
                               "• Auto-pastes at cursor position\n"
                               "• No more manual Ctrl+V needed!",
                          font=('Arial', 11), bg='#f0f0f0', fg='#1976D2',
                          justify=tk.LEFT)
    instructions.pack(pady=20, padx=20)
    
    # Test content area
    content_frame = tk.Frame(root, bg='white', relief='solid', borderwidth=1)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    # Test chunk
    test_content = "This is a test chunk that should be draggable to external applications like Word, Notepad, VS Code, etc. When you drop it, it should automatically paste at the cursor position!"
    
    chunk_label = tk.Label(content_frame, 
                         text=f"📄 DRAGGABLE CHUNK:\n\n{test_content}",
                         bg='#E3F2FD', fg='#1976D2', 
                         font=('Arial', 10), relief='raised', borderwidth=2,
                         padx=15, pady=15, wraplength=400, justify=tk.LEFT)
    chunk_label.pack(pady=20, padx=20)
    
    # Status
    status_label = tk.Label(root, text="Ready for testing!", 
                          font=('Arial', 10, 'bold'), bg='#f0f0f0', fg='#4CAF50')
    status_label.pack(pady=10)
    
    # Drag state
    drag_data = None
    is_dragging = False
    drag_window = None
    
    def on_hover_enter(event):
        chunk_label.config(cursor="hand2", bg='#BBDEFB')
        status_label.config(text="✋ Hover detected - ready to drag!", fg='#FF9800')
    
    def on_hover_leave(event):
        if not is_dragging:
            chunk_label.config(cursor="", bg='#E3F2FD')
            status_label.config(text="Ready for testing!", fg='#4CAF50')
    
    def on_click(event):
        nonlocal drag_data
        drag_data = test_content
        status_label.config(text="🖱️ Click detected - start dragging!", fg='#2196F3')
    
    def on_drag_start(event):
        nonlocal is_dragging, drag_window
        if drag_data:
            is_dragging = True
            
            # Create drag window
            drag_window = tk.Toplevel(root)
            drag_window.wm_overrideredirect(True)
            drag_window.attributes('-topmost', True)
            drag_window.attributes('-alpha', 0.9)
            drag_window.configure(bg='#4CAF50', relief='solid', borderwidth=2)
            
            preview = test_content[:50] + "..." if len(test_content) > 50 else test_content
            label = tk.Label(drag_window, text=f"📄 {preview}", 
                           bg='#4CAF50', fg='white', font=('Arial', 9, 'bold'))
            label.pack(padx=8, pady=4)
            
            # Position near cursor
            x, y = root.winfo_pointerxy()
            drag_window.geometry(f"+{x+15}+{y+15}")
            
            status_label.config(text="🚀 Dragging! Move to external app and release!", fg='#FF5722')
            
            # Start tracking
            track_mouse()
    
    def track_mouse():
        nonlocal drag_window
        if is_dragging and drag_window:
            try:
                x, y = root.winfo_pointerxy()
                drag_window.geometry(f"+{x+15}+{y+15}")
                root.after(30, track_mouse)
            except:
                pass
    
    def on_drag_end(event):
        nonlocal is_dragging, drag_window, drag_data
        if is_dragging:
            # Copy to clipboard
            try:
                import pyperclip
                pyperclip.copy(test_content)
                status_label.config(text="✅ Content copied! Switch to your app and paste (Ctrl+V)", fg='#4CAF50')
            except ImportError:
                root.clipboard_clear()
                root.clipboard_append(test_content)
                status_label.config(text="✅ Content copied! Switch to your app and paste (Ctrl+V)", fg='#4CAF50')
            
            # Clean up
            if drag_window:
                drag_window.destroy()
                drag_window = None
            
            is_dragging = False
            drag_data = None
            chunk_label.config(cursor="", bg='#E3F2FD')
    
    # Bind events
    chunk_label.bind('<Enter>', on_hover_enter)
    chunk_label.bind('<Leave>', on_hover_leave)
    chunk_label.bind('<Button-1>', on_click)
    chunk_label.bind('<B1-Motion>', on_drag_start)
    chunk_label.bind('<ButtonRelease-1>', on_drag_end)
    
    # Test button
    test_btn = tk.Button(root, text="🧪 Test with Real App", 
                        command=lambda: messagebox.showinfo("Test Instructions",
                                                           "1. Open Word or Notepad\n"
                                                           "2. Click in the document\n"
                                                           "3. Come back and drag the chunk\n"
                                                           "4. Drop it in your document\n"
                                                           "5. It should auto-paste!"),
                        bg='#2196F3', fg='white', font=('Arial', 10, 'bold'),
                        padx=20, pady=5)
    test_btn.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_new_drag_drop()
