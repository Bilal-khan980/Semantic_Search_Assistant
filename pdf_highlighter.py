#!/usr/bin/env python3
"""
PDF Highlighting System with Metadata Support.
Allows users to highlight PDFs and add custom metadata (tags, notes).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import fitz  # PyMuPDF
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests

logger = logging.getLogger(__name__)

class PDFHighlighter:
    """PDF highlighting application with metadata support."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF Highlighter - Semantic Search Assistant")
        self.root.geometry("1200x800")
        
        # State
        self.current_pdf = None
        self.pdf_document = None
        self.current_page = 0
        self.highlights = []
        self.backend_url = "http://127.0.0.1:8000"
        
        # Highlight colors
        self.highlight_colors = {
            "Yellow": (1, 1, 0),
            "Green": (0, 1, 0),
            "Blue": (0, 0, 1),
            "Pink": (1, 0.75, 0.8),
            "Orange": (1, 0.65, 0)
        }
        self.current_color = "Yellow"
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="Open PDF", command=self.open_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Save Highlights", command=self.save_highlights).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export to Backend", command=self.export_to_backend).pack(side=tk.LEFT, padx=5)
        
        # Color selection
        ttk.Label(toolbar, text="Highlight Color:").pack(side=tk.LEFT, padx=(20, 5))
        self.color_var = tk.StringVar(value=self.current_color)
        color_combo = ttk.Combobox(toolbar, textvariable=self.color_var, values=list(self.highlight_colors.keys()), width=10)
        color_combo.pack(side=tk.LEFT, padx=5)
        color_combo.bind("<<ComboboxSelected>>", self.on_color_change)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # PDF viewer (left side)
        pdf_frame = ttk.LabelFrame(content_frame, text="PDF Viewer")
        pdf_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # PDF canvas
        self.pdf_canvas = tk.Canvas(pdf_frame, bg="white")
        pdf_scrollbar_v = ttk.Scrollbar(pdf_frame, orient=tk.VERTICAL, command=self.pdf_canvas.yview)
        pdf_scrollbar_h = ttk.Scrollbar(pdf_frame, orient=tk.HORIZONTAL, command=self.pdf_canvas.xview)
        self.pdf_canvas.configure(yscrollcommand=pdf_scrollbar_v.set, xscrollcommand=pdf_scrollbar_h.set)
        
        self.pdf_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pdf_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        pdf_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Page navigation
        nav_frame = ttk.Frame(pdf_frame)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        ttk.Button(nav_frame, text="Previous", command=self.prev_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="Page: 0/0")
        self.page_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(nav_frame, text="Next", command=self.next_page).pack(side=tk.LEFT)
        
        # Highlights panel (right side)
        highlights_frame = ttk.LabelFrame(content_frame, text="Highlights & Metadata")
        highlights_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        highlights_frame.configure(width=300)
        
        # Highlights list
        self.highlights_tree = ttk.Treeview(highlights_frame, columns=("content", "tags", "notes"), show="tree headings")
        self.highlights_tree.heading("#0", text="Page")
        self.highlights_tree.heading("content", text="Content")
        self.highlights_tree.heading("tags", text="Tags")
        self.highlights_tree.heading("notes", text="Notes")
        
        self.highlights_tree.column("#0", width=50)
        self.highlights_tree.column("content", width=100)
        self.highlights_tree.column("tags", width=80)
        self.highlights_tree.column("notes", width=70)
        
        self.highlights_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Highlight details
        details_frame = ttk.LabelFrame(highlights_frame, text="Highlight Details")
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Tags entry
        ttk.Label(details_frame, text="Tags:").pack(anchor=tk.W)
        self.tags_entry = ttk.Entry(details_frame)
        self.tags_entry.pack(fill=tk.X, pady=(0, 5))
        
        # Notes text
        ttk.Label(details_frame, text="Notes:").pack(anchor=tk.W)
        self.notes_text = tk.Text(details_frame, height=4)
        self.notes_text.pack(fill=tk.X, pady=(0, 5))
        
        # Importance level
        ttk.Label(details_frame, text="Importance:").pack(anchor=tk.W)
        self.importance_var = tk.StringVar(value="Medium")
        importance_combo = ttk.Combobox(details_frame, textvariable=self.importance_var, 
                                      values=["Low", "Medium", "High", "Critical"], width=10)
        importance_combo.pack(fill=tk.X, pady=(0, 5))
        
        # Buttons
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Update Highlight", command=self.update_highlight).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Highlight", command=self.delete_highlight).pack(side=tk.LEFT)
        
        # Bind events
        self.pdf_canvas.bind("<Button-1>", self.start_highlight)
        self.pdf_canvas.bind("<B1-Motion>", self.drag_highlight)
        self.pdf_canvas.bind("<ButtonRelease-1>", self.end_highlight)
        self.highlights_tree.bind("<<TreeviewSelect>>", self.on_highlight_select)
        
        # Selection state
        self.selection_start = None
        self.selection_rect = None
        
    def open_pdf(self):
        """Open a PDF file."""
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if file_path:
            try:
                self.pdf_document = fitz.open(file_path)
                self.current_pdf = file_path
                self.current_page = 0
                self.load_existing_highlights()
                self.display_page()
                logger.info(f"Opened PDF: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF: {e}")
    
    def load_existing_highlights(self):
        """Load existing highlights from the PDF."""
        if not self.pdf_document:
            return
        
        self.highlights = []
        
        for page_num in range(len(self.pdf_document)):
            page = self.pdf_document[page_num]
            
            # Get existing annotations
            for annot in page.annots():
                if annot.type[1] == "Highlight":
                    # Extract highlight data
                    content = annot.info.get("content", "")
                    rect = annot.rect
                    
                    highlight = {
                        "page": page_num,
                        "rect": [rect.x0, rect.y0, rect.x1, rect.y1],
                        "content": content,
                        "color": self.current_color,
                        "tags": [],
                        "notes": "",
                        "importance": "Medium",
                        "created_at": datetime.now().isoformat()
                    }
                    
                    self.highlights.append(highlight)
        
        self.update_highlights_tree()
    
    def display_page(self):
        """Display the current page."""
        if not self.pdf_document:
            return
        
        page = self.pdf_document[self.current_page]
        
        # Render page to image
        mat = fitz.Matrix(2, 2)  # 2x zoom
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        
        # Display in canvas
        self.pdf_canvas.delete("all")
        self.page_image = tk.PhotoImage(data=img_data)
        self.pdf_canvas.create_image(0, 0, anchor=tk.NW, image=self.page_image)
        
        # Update canvas scroll region
        self.pdf_canvas.configure(scrollregion=self.pdf_canvas.bbox("all"))
        
        # Draw existing highlights for this page
        self.draw_highlights()
        
        # Update page label
        self.page_label.config(text=f"Page: {self.current_page + 1}/{len(self.pdf_document)}")
    
    def draw_highlights(self):
        """Draw existing highlights on the current page."""
        for highlight in self.highlights:
            if highlight["page"] == self.current_page:
                rect = highlight["rect"]
                color = highlight.get("color", "Yellow").lower()
                
                # Draw highlight rectangle
                self.pdf_canvas.create_rectangle(
                    rect[0] * 2, rect[1] * 2, rect[2] * 2, rect[3] * 2,
                    fill=color, stipple="gray50", outline=""
                )
    
    def start_highlight(self, event):
        """Start highlighting selection."""
        self.selection_start = (self.pdf_canvas.canvasx(event.x), self.pdf_canvas.canvasy(event.y))
    
    def drag_highlight(self, event):
        """Drag highlighting selection."""
        if self.selection_start:
            current_pos = (self.pdf_canvas.canvasx(event.x), self.pdf_canvas.canvasy(event.y))
            
            # Remove previous selection rectangle
            if self.selection_rect:
                self.pdf_canvas.delete(self.selection_rect)
            
            # Draw new selection rectangle
            self.selection_rect = self.pdf_canvas.create_rectangle(
                self.selection_start[0], self.selection_start[1],
                current_pos[0], current_pos[1],
                outline="red", width=2
            )
    
    def end_highlight(self, event):
        """End highlighting selection."""
        if self.selection_start:
            end_pos = (self.pdf_canvas.canvasx(event.x), self.pdf_canvas.canvasy(event.y))
            
            # Calculate rectangle
            x1, y1 = self.selection_start
            x2, y2 = end_pos
            
            # Ensure proper rectangle
            rect = [min(x1, x2) / 2, min(y1, y2) / 2, max(x1, x2) / 2, max(y1, y2) / 2]
            
            # Extract text from selection
            content = self.extract_text_from_rect(rect)
            
            if content.strip():
                # Create highlight
                highlight = {
                    "page": self.current_page,
                    "rect": rect,
                    "content": content.strip(),
                    "color": self.current_color,
                    "tags": [],
                    "notes": "",
                    "importance": "Medium",
                    "created_at": datetime.now().isoformat()
                }
                
                self.highlights.append(highlight)
                self.update_highlights_tree()
                self.display_page()  # Refresh to show new highlight
                
                # Show metadata dialog
                self.show_metadata_dialog(highlight)
            
            # Clean up
            if self.selection_rect:
                self.pdf_canvas.delete(self.selection_rect)
            self.selection_start = None
            self.selection_rect = None
    
    def extract_text_from_rect(self, rect):
        """Extract text from a rectangle on the current page."""
        if not self.pdf_document:
            return ""
        
        page = self.pdf_document[self.current_page]
        fitz_rect = fitz.Rect(rect[0], rect[1], rect[2], rect[3])
        
        try:
            text = page.get_text("text", clip=fitz_rect)
            return text
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def show_metadata_dialog(self, highlight):
        """Show dialog to add metadata to highlight."""
        dialog = MetadataDialog(self.root, highlight)
        self.root.wait_window(dialog.window)
        
        if dialog.result:
            highlight.update(dialog.result)
            self.update_highlights_tree()
    
    def update_highlights_tree(self):
        """Update the highlights tree view."""
        # Clear existing items
        for item in self.highlights_tree.get_children():
            self.highlights_tree.delete(item)
        
        # Add highlights
        for i, highlight in enumerate(self.highlights):
            content = highlight["content"][:50] + "..." if len(highlight["content"]) > 50 else highlight["content"]
            tags = ", ".join(highlight.get("tags", []))
            notes = highlight.get("notes", "")[:30] + "..." if len(highlight.get("notes", "")) > 30 else highlight.get("notes", "")
            
            self.highlights_tree.insert("", tk.END, iid=str(i), text=str(highlight["page"] + 1),
                                      values=(content, tags, notes))
    
    def on_highlight_select(self, event):
        """Handle highlight selection."""
        selection = self.highlights_tree.selection()
        if selection:
            index = int(selection[0])
            highlight = self.highlights[index]
            
            # Update details panel
            self.tags_entry.delete(0, tk.END)
            self.tags_entry.insert(0, ", ".join(highlight.get("tags", [])))
            
            self.notes_text.delete(1.0, tk.END)
            self.notes_text.insert(tk.END, highlight.get("notes", ""))
            
            self.importance_var.set(highlight.get("importance", "Medium"))
            
            # Navigate to page
            if highlight["page"] != self.current_page:
                self.current_page = highlight["page"]
                self.display_page()
    
    def update_highlight(self):
        """Update the selected highlight with new metadata."""
        selection = self.highlights_tree.selection()
        if selection:
            index = int(selection[0])
            highlight = self.highlights[index]
            
            # Update metadata
            tags_text = self.tags_entry.get().strip()
            highlight["tags"] = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            highlight["notes"] = self.notes_text.get(1.0, tk.END).strip()
            highlight["importance"] = self.importance_var.get()
            
            self.update_highlights_tree()
            messagebox.showinfo("Updated", "Highlight metadata updated!")
    
    def delete_highlight(self):
        """Delete the selected highlight."""
        selection = self.highlights_tree.selection()
        if selection:
            if messagebox.askyesno("Confirm", "Delete this highlight?"):
                index = int(selection[0])
                del self.highlights[index]
                self.update_highlights_tree()
                self.display_page()
    
    def save_highlights(self):
        """Save highlights to a JSON file."""
        if not self.highlights:
            messagebox.showwarning("Warning", "No highlights to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save highlights",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                data = {
                    "pdf_file": self.current_pdf,
                    "highlights": self.highlights,
                    "exported_at": datetime.now().isoformat()
                }
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Saved", f"Highlights saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save highlights: {e}")
    
    def export_to_backend(self):
        """Export highlights to the semantic search backend."""
        if not self.highlights:
            messagebox.showwarning("Warning", "No highlights to export.")
            return
        
        try:
            # Prepare highlights for backend
            documents = []
            for highlight in self.highlights:
                doc = {
                    "content": highlight["content"],
                    "source": f"{Path(self.current_pdf).name} (Page {highlight['page'] + 1})",
                    "metadata": {
                        "file_path": self.current_pdf,
                        "page": highlight["page"] + 1,
                        "tags": highlight.get("tags", []),
                        "notes": highlight.get("notes", ""),
                        "importance": highlight.get("importance", "Medium"),
                        "highlight_color": highlight.get("color", "Yellow"),
                        "created_at": highlight.get("created_at"),
                        "is_user_highlight": True,
                        "content_type": "pdf_highlight"
                    }
                }
                documents.append(doc)
            
            # Send to backend
            response = requests.post(
                f"{self.backend_url}/documents/add_batch",
                json={"documents": documents},
                timeout=30
            )
            
            if response.status_code == 200:
                messagebox.showinfo("Success", f"Exported {len(documents)} highlights to backend!")
            else:
                messagebox.showerror("Error", f"Failed to export: {response.text}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export highlights: {e}")
    
    def on_color_change(self, event):
        """Handle color change."""
        self.current_color = self.color_var.get()
    
    def prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    
    def next_page(self):
        """Go to next page."""
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.display_page()
    
    def run(self):
        """Run the application."""
        self.root.mainloop()

class MetadataDialog:
    """Dialog for adding metadata to highlights."""
    
    def __init__(self, parent, highlight):
        self.window = tk.Toplevel(parent)
        self.window.title("Add Metadata")
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.highlight = highlight
        self.result = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI."""
        # Content preview
        ttk.Label(self.window, text="Highlighted Text:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        content_text = tk.Text(self.window, height=4, wrap=tk.WORD)
        content_text.pack(fill=tk.X, padx=10, pady=5)
        content_text.insert(tk.END, self.highlight["content"])
        content_text.config(state=tk.DISABLED)
        
        # Tags
        ttk.Label(self.window, text="Tags (comma-separated):").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.tags_entry = ttk.Entry(self.window)
        self.tags_entry.pack(fill=tk.X, padx=10, pady=5)
        
        # Notes
        ttk.Label(self.window, text="Notes:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.notes_text = tk.Text(self.window, height=4)
        self.notes_text.pack(fill=tk.X, padx=10, pady=5)
        
        # Importance
        ttk.Label(self.window, text="Importance:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.importance_var = tk.StringVar(value="Medium")
        importance_combo = ttk.Combobox(self.window, textvariable=self.importance_var, 
                                      values=["Low", "Medium", "High", "Critical"])
        importance_combo.pack(fill=tk.X, padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)
    
    def save(self):
        """Save metadata."""
        tags_text = self.tags_entry.get().strip()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        
        self.result = {
            "tags": tags,
            "notes": self.notes_text.get(1.0, tk.END).strip(),
            "importance": self.importance_var.get()
        }
        
        self.window.destroy()
    
    def cancel(self):
        """Cancel dialog."""
        self.window.destroy()

def main():
    """Main entry point."""
    app = PDFHighlighter()
    app.run()

if __name__ == "__main__":
    main()
