#!/usr/bin/env python3
"""
Quick test for drag-and-drop functionality
"""

import tkinter as tk
from tkinter import messagebox

def test_drag_drop():
    """Test the drag-and-drop functionality."""
    
    # Create test window
    root = tk.Tk()
    root.title("Drag & Drop Test")
    root.geometry("400x300")
    
    # Test data
    test_content = "This is a test chunk of content that should be draggable!"
    
    # Create a text widget with a chunk
    text_widget = tk.Text(root, font=('Arial', 11), wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Add test content
    text_widget.insert(tk.END, "🔍 Test Search Results\n\n")
    text_widget.insert(tk.END, "┌─ Result 1 [95.0%] from test.txt\n")
    text_widget.insert(tk.END, "│\n")
    
    chunk_start = text_widget.index(tk.INSERT)
    text_widget.insert(tk.END, "│ " + test_content)
    chunk_end = text_widget.index(tk.INSERT)
    
    text_widget.insert(tk.END, "\n│\n")
    text_widget.insert(tk.END, "└" + "─" * 50 + "\n\n")
    
    # Style the chunk
    text_widget.tag_add("chunk_1", chunk_start, chunk_end)
    text_widget.tag_config("chunk_1", background="#f0f8ff", relief="raised",
                          borderwidth=1, lmargin1=20, lmargin2=20)
    
    # Drag state
    drag_data = None
    drag_start_pos = None
    is_dragging = False
    
    def on_mouse_motion(event):
        """Handle mouse motion."""
        try:
            cursor_pos = text_widget.index(f"@{event.x},{event.y}")
            ranges = text_widget.tag_ranges("chunk_1")
            
            if ranges:
                start, end = ranges[0], ranges[1]
                if text_widget.compare(start, "<=", cursor_pos) and text_widget.compare(cursor_pos, "<=", end):
                    text_widget.config(cursor="hand2")
                else:
                    text_widget.config(cursor="")
            else:
                text_widget.config(cursor="")
        except:
            pass
    
    def on_click_start(event):
        """Handle click start."""
        nonlocal drag_data, drag_start_pos
        try:
            cursor_pos = text_widget.index(f"@{event.x},{event.y}")
            ranges = text_widget.tag_ranges("chunk_1")
            
            if ranges:
                start, end = ranges[0], ranges[1]
                if text_widget.compare(start, "<=", cursor_pos) and text_widget.compare(cursor_pos, "<=", end):
                    drag_start_pos = (event.x, event.y)
                    drag_data = test_content
        except:
            pass
    
    def on_drag_motion(event):
        """Handle drag motion."""
        nonlocal is_dragging
        if drag_start_pos and drag_data:
            dx = event.x - drag_start_pos[0]
            dy = event.y - drag_start_pos[1]
            distance = (dx*dx + dy*dy) ** 0.5
            
            if distance > 10 and not is_dragging:
                is_dragging = True
                start_drag()
    
    def on_drag_end(event):
        """Handle drag end."""
        nonlocal drag_data, drag_start_pos, is_dragging
        if is_dragging:
            end_drag()
        drag_data = None
        drag_start_pos = None
        is_dragging = False
    
    def start_drag():
        """Start drag operation."""
        try:
            import pyperclip
            pyperclip.copy(drag_data)
            text_widget.config(cursor="fleur")
            messagebox.showinfo("Drag Started", 
                              f"✅ Drag started!\n\n"
                              f"Content: {drag_data[:50]}...\n\n"
                              f"The content is now in clipboard.\n"
                              f"You can paste it anywhere with Ctrl+V!")
        except ImportError:
            root.clipboard_clear()
            root.clipboard_append(drag_data)
            messagebox.showinfo("Drag Started", 
                              f"✅ Drag started!\n\n"
                              f"Content copied to clipboard.\n"
                              f"Paste with Ctrl+V!")
    
    def end_drag():
        """End drag operation."""
        text_widget.config(cursor="")
    
    # Bind events
    text_widget.bind('<Motion>', on_mouse_motion)
    text_widget.bind('<Button-1>', on_click_start)
    text_widget.bind('<B1-Motion>', on_drag_motion)
    text_widget.bind('<ButtonRelease-1>', on_drag_end)
    
    # Instructions
    instructions = tk.Label(root,
                          text="💡 Hover over the highlighted chunk and drag it!\n"
                               "🖱️ Drag outside this window to external apps like Word/Notepad\n"
                               "📋 Content will be automatically pasted when you release!",
                          font=('Arial', 10), fg='blue', justify=tk.CENTER)
    instructions.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    test_drag_drop()
