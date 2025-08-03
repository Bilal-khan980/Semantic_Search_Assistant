#!/usr/bin/env python3
"""
Diagnostic tool to figure out why copy isn't working with selected text
"""

import pyperclip
import keyboard
import time
import win32gui
import win32con
import win32api
import win32clipboard
import tkinter as tk
from tkinter import messagebox

class CopyDiagnostic:
    def __init__(self):
        self.test_count = 0
        
    def diagnose_copy_issue(self):
        """Comprehensive diagnosis of copy operation."""
        self.test_count += 1
        print(f"\n{'='*60}")
        print(f"🔍 COPY DIAGNOSTIC TEST #{self.test_count}")
        print(f"{'='*60}")
        
        # Get window information
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            print(f"🪟 Active window: '{window_title}' (class: {class_name})")
        except Exception as e:
            print(f"❌ Window info error: {e}")
        
        # Test 1: Check initial clipboard
        print(f"\n📋 TEST 1: Initial clipboard state")
        initial_clipboard = self.safe_get_clipboard()
        print(f"   Content: '{initial_clipboard[:50]}...' ({len(initial_clipboard)} chars)")
        
        # Test 2: Try pyperclip copy method
        print(f"\n📋 TEST 2: Pyperclip Ctrl+C method")
        keyboard.send('ctrl+c')
        time.sleep(0.5)
        pyperclip_result = self.safe_get_clipboard()
        print(f"   Result: '{pyperclip_result[:50]}...' ({len(pyperclip_result)} chars)")
        print(f"   Changed: {'✅ YES' if pyperclip_result != initial_clipboard else '❌ NO'}")
        
        # Test 3: Try Windows API method
        print(f"\n📋 TEST 3: Windows API WM_COPY method")
        try:
            hwnd = win32gui.GetForegroundWindow()
            win32api.SendMessage(hwnd, win32con.WM_COPY, 0, 0)
            time.sleep(0.3)
            api_result = self.safe_get_clipboard()
            print(f"   Result: '{api_result[:50]}...' ({len(api_result)} chars)")
            print(f"   Changed: {'✅ YES' if api_result != initial_clipboard else '❌ NO'}")
        except Exception as e:
            print(f"   ❌ API method failed: {e}")
        
        # Test 4: Try alternative keyboard shortcut
        print(f"\n📋 TEST 4: Ctrl+Insert method")
        keyboard.send('ctrl+insert')
        time.sleep(0.5)
        insert_result = self.safe_get_clipboard()
        print(f"   Result: '{insert_result[:50]}...' ({len(insert_result)} chars)")
        print(f"   Changed: {'✅ YES' if insert_result != initial_clipboard else '❌ NO'}")
        
        # Test 5: Try direct Windows clipboard API
        print(f"\n📋 TEST 5: Direct Windows clipboard API")
        try:
            win32clipboard.OpenClipboard()
            clipboard_data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
            win32clipboard.CloseClipboard()
            if isinstance(clipboard_data, bytes):
                clipboard_data = clipboard_data.decode('utf-8', errors='ignore')
            print(f"   Result: '{clipboard_data[:50]}...' ({len(clipboard_data)} chars)")
        except Exception as e:
            print(f"   ❌ Direct API failed: {e}")
        
        # Test 6: Multiple attempts with delays
        print(f"\n📋 TEST 6: Multiple copy attempts")
        for i in range(3):
            print(f"   Attempt {i+1}:")
            keyboard.send('ctrl+c')
            time.sleep(0.2 * (i+1))  # Increasing delays
            attempt_result = self.safe_get_clipboard()
            print(f"     Result: '{attempt_result[:30]}...' ({len(attempt_result)} chars)")
            if attempt_result != initial_clipboard:
                print(f"     ✅ Success on attempt {i+1}!")
                break
        
        # Summary and recommendations
        print(f"\n{'='*30}")
        print(f"📊 DIAGNOSTIC SUMMARY")
        print(f"{'='*30}")
        
        all_results = [pyperclip_result, api_result if 'api_result' in locals() else "", 
                      insert_result, attempt_result if 'attempt_result' in locals() else ""]
        
        successful_methods = []
        if pyperclip_result != initial_clipboard and pyperclip_result.strip():
            successful_methods.append("Ctrl+C (keyboard)")
        if 'api_result' in locals() and api_result != initial_clipboard and api_result.strip():
            successful_methods.append("Windows API")
        if insert_result != initial_clipboard and insert_result.strip():
            successful_methods.append("Ctrl+Insert")
        
        if successful_methods:
            print(f"✅ Working methods: {', '.join(successful_methods)}")
            print(f"💡 Recommendation: Use the working method(s)")
        else:
            print(f"❌ NO METHODS WORKED!")
            print(f"💡 Possible issues:")
            print(f"   • Text is not actually selectable in this application")
            print(f"   • Application blocks copy operations")
            print(f"   • Text selection was lost before copy")
            print(f"   • Application requires special copy method")
            print(f"   • Security software blocking clipboard access")
        
        print(f"{'='*60}")
        
        # Show results in GUI
        self.show_diagnostic_results(successful_methods, all_results)
    
    def safe_get_clipboard(self):
        """Safely get clipboard content."""
        try:
            return pyperclip.paste()
        except:
            return ""
    
    def show_diagnostic_results(self, successful_methods, results):
        """Show diagnostic results in a GUI."""
        def show_gui():
            root = tk.Tk()
            root.withdraw()
            
            if successful_methods:
                title = "✅ Copy Methods Found!"
                message = f"Good news! These copy methods worked:\n\n"
                message += f"• {chr(10).join(successful_methods)}\n\n"
                message += f"The highlight capture should work with these methods."
                messagebox.showinfo(title, message)
            else:
                title = "❌ Copy Issue Detected"
                message = f"No copy methods worked with the selected text.\n\n"
                message += f"Possible solutions:\n"
                message += f"• Try selecting text in a different application (like Notepad)\n"
                message += f"• Make sure text is actually selectable\n"
                message += f"• Check if the application allows copying\n"
                message += f"• Try manually pressing Ctrl+C to test\n\n"
                message += f"If manual Ctrl+C doesn't work, the application\n"
                message += f"may not support text copying."
                messagebox.showerror(title, message)
            
            root.quit()
        
        import threading
        threading.Thread(target=show_gui, daemon=True).start()

def main():
    """Main diagnostic function."""
    print("🔍 Copy Operation Diagnostic Tool")
    print("="*50)
    print("This tool will test different copy methods to see why")
    print("text selection isn't working with your highlight capture.")
    print()
    print("Instructions:")
    print("1. Go to the application where you selected text")
    print("2. Select the text again (make sure it's highlighted)")
    print("3. Come back here and press Ctrl+Alt+D")
    print("4. Check the diagnostic results")
    print()
    print("The tool will test multiple copy methods and show")
    print("which ones work with your selected text.")
    print()
    
    diagnostic = CopyDiagnostic()
    
    try:
        keyboard.add_hotkey('ctrl+alt+d', diagnostic.diagnose_copy_issue)
        print("✅ Diagnostic ready - Press Ctrl+Alt+D after selecting text")
        print("🛑 Press Ctrl+C here to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Diagnostic stopped")
        keyboard.unhook_all()

if __name__ == "__main__":
    main()
