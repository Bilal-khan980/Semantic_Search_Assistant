#!/usr/bin/env python3
"""
Test script for the Real-time Semantic Search Assistant.
"""

import asyncio
import time
import sys
import requests
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_dependencies():
    """Test if all required dependencies are available."""
    print("🔍 Testing dependencies...")
    
    required_modules = [
        'fastapi',
        'uvicorn',
        'lancedb',
        'sentence_transformers',
        'keyboard',
        'pyperclip',
        'win32gui',
        'tkinter'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} (missing)")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing dependencies: {', '.join(missing_modules)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available")
    return True

def test_backend_components():
    """Test if backend components can be imported."""
    print("\n🔍 Testing backend components...")
    
    components = [
        'api_service',
        'document_processor',
        'search_engine',
        'database',
        'config'
    ]
    
    for component in components:
        try:
            __import__(component)
            print(f"   ✅ {component}")
        except ImportError as e:
            print(f"   ❌ {component}: {e}")
            return False
    
    print("✅ All backend components available")
    return True

def test_config_files():
    """Test if required configuration files exist."""
    print("\n🔍 Testing configuration files...")
    
    required_files = [
        'config.json',
        'web/app.html',
        'test_docs'
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")
            return False
    
    print("✅ All configuration files present")
    return True

async def test_backend_startup():
    """Test if backend can start properly."""
    print("\n🔍 Testing backend startup...")
    
    try:
        from api_service import initialize_backend
        await initialize_backend()
        print("   ✅ Backend initialization successful")
        return True
    except Exception as e:
        print(f"   ❌ Backend initialization failed: {e}")
        return False

def test_document_processing():
    """Test document processing with test files."""
    print("\n🔍 Testing document processing...")
    
    test_docs_dir = Path("test_docs")
    if not test_docs_dir.exists():
        print("   ❌ test_docs directory not found")
        return False
    
    test_files = list(test_docs_dir.glob("*.txt"))
    if not test_files:
        print("   ❌ No test files found in test_docs/")
        return False
    
    print(f"   ✅ Found {len(test_files)} test files")
    for file in test_files:
        print(f"      • {file.name}")
    
    return True

def create_test_document():
    """Create a test document if none exist."""
    test_docs_dir = Path("test_docs")
    test_docs_dir.mkdir(exist_ok=True)
    
    test_file = test_docs_dir / "realtime_test.txt"
    
    test_content = """Real-time Semantic Search Test Document

This document contains sample content for testing the real-time semantic search functionality.

Key features to test:
- Letter-by-letter search triggering
- Spacebar clearing functionality
- Instant result display
- Copy to clipboard feature

Sample topics:
- Artificial intelligence and machine learning
- Natural language processing
- Vector databases and embeddings
- Real-time text monitoring
- Desktop application development

This content should provide good test material for the semantic search engine.
The system should be able to find relevant content as you type each letter.

Test phrases:
- "artificial" should find AI-related content
- "real-time" should find monitoring content
- "vector" should find database content
- "desktop" should find application content

End of test document.
"""
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"   ✅ Created test document: {test_file}")
    return True

async def main():
    """Run all tests."""
    print("🚀 Testing Real-time Semantic Search Assistant")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Backend Components", test_backend_components),
        ("Configuration Files", test_config_files),
        ("Document Processing", test_document_processing),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test crashed: {e}")
            failed += 1
    
    # Test backend startup separately
    print(f"\n📋 Running Backend Startup test...")
    try:
        result = await test_backend_startup()
        if result:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print(f"   ❌ Backend startup test crashed: {e}")
        failed += 1
    
    # Create test document if needed
    print(f"\n📋 Setting up test environment...")
    create_test_document()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! The application is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Run: python run_realtime_app.py")
        print("2. Or use: start_realtime_app.bat")
        print("3. Click 'Start Monitoring' in the GUI")
        print("4. Open any text editor and start typing!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
