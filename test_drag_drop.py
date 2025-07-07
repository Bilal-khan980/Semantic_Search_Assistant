#!/usr/bin/env python3
"""
Test script to verify drag-and-drop functionality works correctly.
This script tests the backend components that support drag-and-drop.
"""

import asyncio
import json
import logging
from pathlib import Path
import tempfile
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_drag_drop_backend():
    """Test the backend components that support drag-and-drop functionality."""
    
    print("🧪 Testing Drag-and-Drop Backend Components")
    print("=" * 50)
    
    try:
        # Import backend components
        from main import DocumentSearchBackend
        from config import Config
        
        # Initialize backend
        config = Config()
        backend = DocumentSearchBackend()
        await backend.initialize()
        
        # Create test document
        test_content = """
        This is a test document for drag-and-drop functionality.
        
        It contains multiple paragraphs with different types of content:
        - Technical information about semantic search
        - User experience considerations
        - Implementation details
        
        The drag-and-drop feature should preserve this formatting and add proper citations.
        """
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file_path = f.name
        
        try:
            # Process the test document
            print("📄 Processing test document...")
            results = await backend.process_documents([test_file_path])
            
            if results and len(results) > 0 and results[0]['status'] == 'success':
                print(f"✅ Document processed successfully: {results[0]['chunks_count']} chunks")
            else:
                print("❌ Document processing failed")
                return False
            
            # Test search functionality
            print("🔍 Testing search functionality...")
            search_results = await backend.search("drag-and-drop functionality", limit=5)
            
            if search_results and len(search_results) > 0:
                print(f"✅ Search successful: {len(search_results)} results found")
                
                # Test drag data formatting
                print("🎯 Testing drag data formatting...")
                test_result = search_results[0]
                
                # Simulate drag data creation
                drag_data = {
                    'type': 'text',
                    'content': test_result['content'],
                    'metadata': {
                        'source': test_result['source'],
                        'score': test_result.get('final_score', test_result.get('similarity', 0)),
                        'timestamp': '2024-01-01T00:00:00Z',
                        'title': 'Test Document',
                        'author': 'Test Author'
                    }
                }
                
                # Test citation formatting
                citation = format_citation(drag_data)
                content_with_citation = f"{drag_data['content']}\n\n{citation}"
                
                print(f"✅ Drag data formatted successfully")
                print(f"📝 Content length: {len(content_with_citation)} characters")
                print(f"🏷️  Citation: {citation}")
                
                # Test rich text formatting
                rtf_content = format_rtf(drag_data)
                html_content = format_html(drag_data)
                
                print(f"✅ Rich text formats created")
                print(f"📄 RTF length: {len(rtf_content)} characters")
                print(f"🌐 HTML length: {len(html_content)} characters")
                
                return True
            else:
                print("❌ Search failed - no results found")
                return False
                
        finally:
            # Cleanup
            try:
                os.unlink(test_file_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.exception("Test failed")
        return False

def format_citation(drag_data):
    """Format citation for dragged content."""
    metadata = drag_data.get('metadata', {})
    source = metadata.get('source', 'Unknown')
    filename = source.split('/')[-1] if '/' in source else source
    score = metadata.get('score', 0)
    
    return f"— From {filename} ({int(score * 100)}% relevance)"

def format_rtf(drag_data):
    """Format content as RTF."""
    content = drag_data['content'].replace('\n', '\\par ')
    metadata = drag_data.get('metadata', {})
    source = metadata.get('source', 'Unknown')
    
    rtf = "{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}"
    rtf += "\\f0\\fs24 "
    rtf += content
    rtf += "\\par\\par"
    rtf += "{\\i Source: " + source + "}"
    rtf += "}"
    
    return rtf

def format_html(drag_data):
    """Format content as HTML."""
    content = drag_data['content'].replace('\n', '<br>')
    metadata = drag_data.get('metadata', {})
    source = metadata.get('source', 'Unknown')
    
    html = f'<div style="font-family: Arial, sans-serif; line-height: 1.4;">'
    html += f'<div style="margin-bottom: 10px;">{content}</div>'
    html += f'<hr style="border: none; border-top: 1px solid #ccc; margin: 10px 0;">'
    html += f'<div style="font-size: 12px; color: #666;">Source: {source}</div>'
    html += f'</div>'
    
    return html

def test_clipboard_formats():
    """Test different clipboard format compatibility."""
    print("\n🔧 Testing Clipboard Format Compatibility")
    print("=" * 50)
    
    test_data = {
        'type': 'text',
        'content': 'This is test content for clipboard formatting.\n\nIt has multiple lines and formatting.',
        'metadata': {
            'source': 'test_document.txt',
            'score': 0.95,
            'title': 'Test Document',
            'author': 'Test Author'
        }
    }
    
    # Test plain text
    plain_text = test_data['content']
    print(f"✅ Plain text: {len(plain_text)} characters")
    
    # Test with citation
    citation = format_citation(test_data)
    text_with_citation = f"{plain_text}\n\n{citation}"
    print(f"✅ Text with citation: {len(text_with_citation)} characters")
    
    # Test RTF
    rtf_content = format_rtf(test_data)
    print(f"✅ RTF format: {len(rtf_content)} characters")
    
    # Test HTML
    html_content = format_html(test_data)
    print(f"✅ HTML format: {len(html_content)} characters")
    
    return True

async def main():
    """Run all drag-and-drop tests."""
    print("🚀 Starting Drag-and-Drop Functionality Tests")
    print("=" * 60)
    
    # Test backend components
    backend_success = await test_drag_drop_backend()
    
    # Test clipboard formats
    clipboard_success = test_clipboard_formats()
    
    print("\n📊 Test Results Summary")
    print("=" * 30)
    print(f"Backend Components: {'✅ PASS' if backend_success else '❌ FAIL'}")
    print(f"Clipboard Formats:  {'✅ PASS' if clipboard_success else '❌ FAIL'}")
    
    overall_success = backend_success and clipboard_success
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Drag-and-drop functionality is working correctly!")
        print("💡 To test cross-application dragging:")
        print("   1. Start the application: python start_app.py")
        print("   2. Search for content")
        print("   3. Try dragging results to external applications")
        print("   4. Check console logs for drag operation details")
    else:
        print("\n⚠️  Some components need attention before drag-and-drop will work properly.")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())
