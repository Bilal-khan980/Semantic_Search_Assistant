#!/usr/bin/env python3
"""
Very simple test to isolate the text selection issue
"""

import pyperclip
import keyboard
import time

def test_copy():
    """Test basic copy functionality."""
    print("\n🎯 Copy test triggered!")
    print("="*40)
    
    # Get original clipboard
    try:
        original = pyperclip.paste()
        print(f"📋 Original clipboard: '{original}'")
    except Exception as e:
        print(f"❌ Error reading clipboard: {e}")
        original = ""
    
    # Send Ctrl+C
    print("📋 Sending Ctrl+C...")
    keyboard.send('ctrl+c')
    
    # Wait and check
    time.sleep(0.5)
    
    try:
        new_clipboard = pyperclip.paste()
        print(f"📋 New clipboard: '{new_clipboard}'")
        
        if new_clipboard != original:
            print(f"✅ SUCCESS! Detected change in clipboard")
            print(f"📝 Captured text: '{new_clipboard}'")
            print(f"📊 Length: {len(new_clipboard)} characters")
        else:
            print("❌ No change detected in clipboard")
            
    except Exception as e:
        print(f"❌ Error reading new clipboard: {e}")
    
    print("="*40)

def main():
    """Main test function."""
    print("🧪 Simple Copy Test")
    print("="*50)
    print("This test will help us understand why text selection isn't working.")
    print()
    print("Instructions:")
    print("1. Open Notepad (or any text editor)")
    print("2. Type some text: 'Hello World Test'")
    print("3. Select the text with your mouse (make sure it's highlighted)")
    print("4. Come back to this window")
    print("5. Press Ctrl+Alt+T to test copy")
    print()
    print("The test will show exactly what happens when we try to copy.")
    print()
    
    try:
        # Register test hotkey
        keyboard.add_hotkey('ctrl+alt+t', test_copy)
        print("✅ Test hotkey registered: Ctrl+Alt+T")
        print("🎯 Go select some text and press Ctrl+Alt+T")
        print("🛑 Press Ctrl+C here to stop the test")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped")
        keyboard.unhook_all()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
