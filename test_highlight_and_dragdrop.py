#!/usr/bin/env python3
"""
Test script for both Highlight Capture and Enhanced Drag-and-Drop features
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import sys
import os
from pathlib import Path

def test_highlight_capture():
    """Test the highlight capture feature."""
    try:
        from highlight_capture import HighlightCapture
        
        # Create test window
        test_window = tk.Toplevel()
        test_window.title("🎯 Highlight Capture Test")
        test_window.geometry("600x500")
        test_window.attributes('-topmost', True)
        
        # Instructions
        instructions = tk.Label(test_window,
                              text="📝 HIGHLIGHT CAPTURE TEST\n\n"
                                   "1. Open any document (PDF, Word, web page)\n"
                                   "2. Select some text with your mouse\n"
                                   "3. Press Ctrl+Alt+H\n"
                                   "4. Add tags and notes in the dialog\n"
                                   "5. Click 'Save Highlight'\n\n"
                                   "✨ Your highlight will be added to the searchable database!",
                              font=('Arial', 12), justify=tk.LEFT, wraplength=550)
        instructions.pack(pady=20, padx=20)
        
        # Start capture system
        capture = HighlightCapture()
        if capture.start_global_listener():
            status_label = tk.Label(test_window,
                                  text="✅ Highlight capture is ACTIVE!\nPress Ctrl+Alt+H after selecting text",
                                  font=('Arial', 11, 'bold'), fg='green')
            status_label.pack(pady=10)
        else:
            status_label = tk.Label(test_window, 
                                  text="❌ Failed to start highlight capture",
                                  font=('Arial', 11, 'bold'), fg='red')
            status_label.pack(pady=10)
        
        # Test text area
        test_frame = tk.LabelFrame(test_window, text="Test Text (select and press Ctrl+Alt+H)",
                                 font=('Arial', 10, 'bold'))
        test_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        test_text = scrolledtext.ScrolledText(test_frame, height=8, wrap=tk.WORD, 
                                            font=('Arial', 11))
        test_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        sample_text = """Vector embeddings are mathematical representations of text that capture semantic meaning. 
They allow computers to understand that "car" and "automobile" are similar concepts, even though they are different words.

In semantic search systems, documents are converted into high-dimensional vectors using neural networks. 
These vectors preserve the contextual relationships between words and concepts.

When you search for "machine learning algorithms", the system can find relevant content about "neural networks" 
or "artificial intelligence" because their vector representations are close in the embedding space.

This technology enables more intelligent search that goes beyond simple keyword matching to understand intent and meaning."""
        
        test_text.insert('1.0', sample_text)
        
        def cleanup():
            capture.stop_global_listener()
            test_window.destroy()
        
        test_window.protocol("WM_DELETE_WINDOW", cleanup)
        
    except ImportError:
        messagebox.showerror("Error", "Highlight capture module not available.\nMake sure highlight_capture.py exists.")

def test_drag_drop_with_citations():
    """Test the enhanced drag-and-drop with citations."""
    
    test_window = tk.Toplevel()
    test_window.title("🖱️ Drag & Drop with Citations Test")
    test_window.geometry("700x600")
    test_window.attributes('-topmost', True)
    
    # Instructions
    instructions = tk.Label(test_window,
                          text="🎯 DRAG & DROP WITH CITATIONS TEST\n\n"
                               "1. Drag any blue chunk below to an external app\n"
                               "2. Notice it includes citation information\n"
                               "3. The format: 'Content (Source: Document, p. 42)'\n"
                               "4. Perfect for academic writing and research!",
                          font=('Arial', 12), justify=tk.LEFT, wraplength=650)
    instructions.pack(pady=20, padx=20)
    
    # Sample search results with citations
    results_frame = tk.LabelFrame(test_window, text="Sample Search Results (Drag to test)", 
                                font=('Arial', 10, 'bold'))
    results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    results_text = tk.Text(results_frame, height=15, wrap=tk.WORD, 
                         font=('Arial', 10), bg='#f8f9fa')
    results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Sample results with different citation formats
    sample_results = [
        {
            'content': 'Machine learning algorithms can automatically identify patterns in large datasets without explicit programming.',
            'source': 'Introduction to AI Research',
            'page': '15',
            'similarity': 0.95
        },
        {
            'content': 'Vector embeddings transform text into numerical representations that preserve semantic relationships between words.',
            'source': 'Natural Language Processing Handbook',
            'page': '127',
            'similarity': 0.89
        },
        {
            'content': 'Semantic search goes beyond keyword matching to understand the intent and context of user queries.',
            'source': 'Modern Search Technologies',
            'page': '',  # No page number
            'similarity': 0.87
        }
    ]
    
    # Display results with highlighting
    for i, result in enumerate(sample_results):
        # Add result content
        start_pos = results_text.index(tk.INSERT)
        
        content = result['content']
        source = result['source']
        page = result.get('page', '')
        
        # Create citation
        if page:
            citation = f"(Source: {source}, p. {page})"
        else:
            citation = f"(Source: {source})"
        
        # Full content with citation for drag-drop
        full_content = f"{content}\n\n{citation}"
        
        results_text.insert(tk.END, f"📄 Result {i+1}:\n")
        results_text.insert(tk.END, f"{content}\n")
        results_text.insert(tk.END, f"📚 {citation}\n")
        results_text.insert(tk.END, f"🎯 Similarity: {result['similarity']:.2f}\n\n")
        
        end_pos = results_text.index(tk.INSERT)
        
        # Highlight the content area
        content_start = f"{start_pos.split('.')[0]}.{int(start_pos.split('.')[1]) + len('📄 Result X:')}"
        similarity_text = f"🎯 Similarity: {result['similarity']:.2f}"
        content_end = f"{end_pos.split('.')[0]}.{int(end_pos.split('.')[1]) - len(similarity_text) - 2}"
        
        results_text.tag_add(f"chunk_{i}", content_start, content_end)
        results_text.tag_config(f"chunk_{i}", background='#e3f2fd', relief='raised', borderwidth=1)
        
        # Bind drag events
        def create_drag_handler(content, citation, full_content):
            def on_click(event):
                # Store drag data
                results_text.drag_data = {
                    'content': content,
                    'content_with_citation': full_content,
                    'citation': citation
                }
                results_text.drag_start = (event.x, event.y)
                
            def on_drag(event):
                if hasattr(results_text, 'drag_data'):
                    # Create drag window
                    if not hasattr(results_text, 'drag_window'):
                        results_text.drag_window = tk.Toplevel()
                        results_text.drag_window.wm_overrideredirect(True)
                        results_text.drag_window.attributes('-topmost', True)
                        results_text.drag_window.configure(bg='#4CAF50', relief='solid', borderwidth=2)
                        
                        preview = content[:50] + "..." if len(content) > 50 else content
                        label = tk.Label(results_text.drag_window, 
                                       text=f"📄 {preview}\n📚 With citation!",
                                       bg='#4CAF50', fg='white', font=('Arial', 9, 'bold'))
                        label.pack(padx=8, pady=4)
                    
                    # Update position
                    x, y = test_window.winfo_pointerxy()
                    results_text.drag_window.geometry(f"+{x+15}+{y+15}")
                    
            def on_release(event):
                if hasattr(results_text, 'drag_window'):
                    results_text.drag_window.destroy()
                    delattr(results_text, 'drag_window')
                
                if hasattr(results_text, 'drag_data'):
                    # Copy to clipboard with citation
                    try:
                        import pyperclip
                        pyperclip.copy(results_text.drag_data['content_with_citation'])
                        messagebox.showinfo("Success", 
                                          f"Content with citation copied!\n\n"
                                          f"Content: {content[:50]}...\n"
                                          f"Citation: {citation}\n\n"
                                          f"Switch to your app and press Ctrl+V")
                    except ImportError:
                        test_window.clipboard_clear()
                        test_window.clipboard_append(results_text.drag_data['content_with_citation'])
                        messagebox.showinfo("Success", "Content with citation copied to clipboard!")
                    
                    delattr(results_text, 'drag_data')
            
            return on_click, on_drag, on_release
        
        on_click, on_drag, on_release = create_drag_handler(content, citation, full_content)
        
        results_text.tag_bind(f"chunk_{i}", '<Button-1>', on_click)
        results_text.tag_bind(f"chunk_{i}", '<B1-Motion>', on_drag)
        results_text.tag_bind(f"chunk_{i}", '<ButtonRelease-1>', on_release)
        results_text.tag_bind(f"chunk_{i}", '<Enter>', 
                            lambda e, tag=f"chunk_{i}": results_text.config(cursor="hand2"))
        results_text.tag_bind(f"chunk_{i}", '<Leave>', 
                            lambda e: results_text.config(cursor=""))

def main():
    """Main test interface."""
    root = tk.Tk()
    root.title("🧪 Highlight Capture & Drag-Drop Test Suite")
    root.geometry("500x400")
    
    # Main title
    title = tk.Label(root, text="🧪 Feature Test Suite", 
                    font=('Arial', 18, 'bold'), fg='#2c3e50')
    title.pack(pady=20)
    
    # Description
    desc = tk.Label(root, 
                   text="Test the new highlight capture and enhanced drag-drop features.\n"
                        "Both features work together to create a powerful research workflow.",
                   font=('Arial', 11), justify=tk.CENTER, wraplength=450)
    desc.pack(pady=10)
    
    # Test buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=30)
    
    highlight_btn = tk.Button(button_frame, 
                            text="📝 Test Highlight Capture\n(Ctrl+Shift+H)",
                            command=test_highlight_capture,
                            bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                            padx=20, pady=15, relief='flat')
    highlight_btn.pack(side=tk.LEFT, padx=10)
    
    dragdrop_btn = tk.Button(button_frame, 
                           text="🖱️ Test Drag & Drop\n(with Citations)",
                           command=test_drag_drop_with_citations,
                           bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                           padx=20, pady=15, relief='flat')
    dragdrop_btn.pack(side=tk.LEFT, padx=10)
    
    # Instructions
    instructions = tk.Label(root,
                          text="💡 Instructions:\n\n"
                               "1. Test highlight capture by selecting text in any app and pressing Ctrl+Shift+H\n"
                               "2. Test drag-drop by dragging blue chunks to external applications\n"
                               "3. Notice how citations are automatically included in drag-drop\n"
                               "4. Run the main app with start_enhanced_admin.bat for full functionality",
                          font=('Arial', 10), justify=tk.LEFT, wraplength=450)
    instructions.pack(pady=20, padx=20)
    
    # Status
    status = tk.Label(root, text="Ready to test! Click a button above to start.", 
                     font=('Arial', 10, 'italic'), fg='#7f8c8d')
    status.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
