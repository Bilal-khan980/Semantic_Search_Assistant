#!/usr/bin/env python3
"""
Simple test for text capture functionality
"""

import tkinter as tk
import pyperclip
import keyboard
import time
import threading

class SimpleCaptureTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simple Capture Test")
        self.root.geometry("400x300")
        
        self.capture_active = False
        
        # UI
        title = tk.Label(self.root, text="Simple Text Capture Test", 
                        font=('Arial', 14, 'bold'))
        title.pack(pady=20)
        
        instructions = tk.Label(self.root, 
                              text="1. Click 'Start Capture'\n2. Go select text anywhere\n3. Text will be captured",
                              font=('Arial', 11))
        instructions.pack(pady=10)
        
        self.status_label = tk.Label(self.root, text="Ready", 
                                   font=('Arial', 12, 'bold'), fg='blue')
        self.status_label.pack(pady=10)
        
        self.start_btn = tk.Button(self.root, text="Start Capture", 
                                 command=self.start_capture,
                                 bg='green', fg='white', font=('Arial', 12, 'bold'))
        self.start_btn.pack(pady=10)
        
        self.stop_btn = tk.Button(self.root, text="Stop Capture", 
                                command=self.stop_capture,
                                bg='red', fg='white', font=('Arial', 12, 'bold'))
        self.stop_btn.pack(pady=5)
        
        self.result_text = tk.Text(self.root, height=8, width=50)
        self.result_text.pack(pady=10, padx=20, fill='both', expand=True)
        
    def start_capture(self):
        """Start capture mode."""
        self.capture_active = True
        self.status_label.config(text="🔍 Monitoring for text selection...", fg='orange')
        self.start_btn.config(state='disabled')
        
        # Start monitoring in background thread
        threading.Thread(target=self.monitor_selection, daemon=True).start()
        
    def stop_capture(self):
        """Stop capture mode."""
        self.capture_active = False
        self.status_label.config(text="Stopped", fg='red')
        self.start_btn.config(state='normal')
        
    def monitor_selection(self):
        """Monitor for text selection."""
        print("Starting selection monitoring...")
        
        while self.capture_active:
            try:
                # Save current clipboard
                original_clipboard = ""
                try:
                    original_clipboard = pyperclip.paste()
                except:
                    pass
                
                # Try to copy selected text
                try:
                    keyboard.send('ctrl+c')
                    time.sleep(0.2)
                    
                    new_clipboard = pyperclip.paste()
                    
                    # Check if clipboard changed
                    if (new_clipboard != original_clipboard and 
                        new_clipboard and 
                        len(new_clipboard.strip()) >= 3):
                        
                        # Text was captured!
                        self.root.after(0, lambda: self.text_captured(new_clipboard.strip()))
                        return
                    else:
                        # Restore original clipboard
                        try:
                            pyperclip.copy(original_clipboard)
                        except:
                            pass
                            
                except Exception as e:
                    print(f"Copy error: {e}")
                    try:
                        pyperclip.copy(original_clipboard)
                    except:
                        pass
                
                time.sleep(1)  # Wait 1 second before next check
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(2)
                
    def text_captured(self, text):
        """Handle captured text."""
        self.capture_active = False
        self.status_label.config(text=f"✅ Captured {len(text)} characters!", fg='green')
        self.start_btn.config(state='normal')
        
        # Show captured text
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, f"Captured Text:\n\n{text}")
        
        print(f"Captured: {text[:50]}...")
        
    def run(self):
        """Run the test."""
        self.root.mainloop()

if __name__ == "__main__":
    print("Simple Capture Test")
    print("===================")
    print("1. Click 'Start Capture'")
    print("2. Go to Word/Notepad/Browser")
    print("3. Select some text")
    print("4. Text should be captured automatically")
    print()
    
    app = SimpleCaptureTest()
    app.run()
