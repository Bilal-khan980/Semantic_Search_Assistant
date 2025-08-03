#!/usr/bin/env python3
"""
Super simple clipboard test - just shows what's in clipboard when you press hotkey
"""

import pyperclip
import keyboard
import time

def show_clipboard():
    """Show exactly what's in the clipboard right now."""
    print("\n" + "="*50)
    print("🔍 CLIPBOARD CONTENT CHECK")
    print("="*50)
    
    try:
        clipboard_content = pyperclip.paste()
        
        print(f"📋 Clipboard contains:")
        print(f"   Content: '{clipboard_content}'")
        print(f"   Length: {len(clipboard_content)} characters")
        print(f"   Type: {type(clipboard_content)}")
        print(f"   Stripped: '{clipboard_content.strip()}'")
        print(f"   Stripped length: {len(clipboard_content.strip())}")
        
        if clipboard_content.strip():
            print("✅ Clipboard has content!")
        else:
            print("❌ Clipboard is empty or whitespace only")
            
    except Exception as e:
        print(f"❌ Error reading clipboard: {e}")
    
    print("="*50)

def main():
    """Main test."""
    print("📋 Simple Clipboard Test")
    print("="*40)
    print("This will show EXACTLY what's in your clipboard")
    print()
    print("Instructions:")
    print("1. Go to any app (Notepad recommended)")
    print("2. Select some text")
    print("3. Press Ctrl+C manually")
    print("4. Come back here and press Ctrl+Alt+C")
    print("5. See exactly what's in clipboard")
    print()
    
    try:
        keyboard.add_hotkey('ctrl+alt+c', show_clipboard)
        print("✅ Hotkey registered: Ctrl+Alt+C")
        print("🎯 Select text, copy it (Ctrl+C), then press Ctrl+Alt+C")
        print("🛑 Press Ctrl+C here to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
        keyboard.unhook_all()

if __name__ == "__main__":
    main()
