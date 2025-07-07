#!/usr/bin/env python3
"""
Debug script to test database functionality directly.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import VectorStore
from document_processor import DocumentProcessor
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_database():
    """Debug database functionality."""
    
    print("🔍 Debugging Database")
    print("=" * 50)
    
    try:
        # Initialize components
        print("1. Initializing components...")
        config = Config()
        vector_store = VectorStore(config)
        document_processor = DocumentProcessor(config)
        
        await vector_store.initialize()
        await document_processor.initialize()
        print("✅ Components initialized")
        
        # Check table status
        print("\n2. Checking database table...")
        try:
            if vector_store.table is not None:
                count = vector_store.table.count_rows()
                print(f"📊 Current table has {count} rows")
            else:
                print("❌ No table found")
                return False
        except Exception as e:
            print(f"❌ Error checking table: {e}")
            return False
        
        # Process a test document
        print("\n3. Processing test document...")
        test_file = Path("test_docs/sample_document.md")
        
        if test_file.exists():
            # Process document
            chunks = await document_processor.process_file(str(test_file))
            print(f"📄 Created {len(chunks)} chunks")
            
            # Add to vector store
            document_id = await vector_store.add_document(str(test_file), chunks)
            print(f"💾 Added document with ID: {document_id}")
            
            # Check table count again
            count = vector_store.table.count_rows()
            print(f"📊 Table now has {count} rows")
            
            # Test search
            print("\n4. Testing search...")
            results = await vector_store.search("Programming", limit=5)
            print(f"🔍 Search for 'bilal' returned {len(results)} results")
            
            for i, result in enumerate(results[:3], 1):
                score = result.get('similarity', 0) * 100
                content = result.get('content', '')[:100] + '...'
                print(f"   {i}. Score: {score:.1f}% - {content}")
            
            return True
        else:
            print(f"❌ Test file not found: {test_file}")
            return False
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_database())
    sys.exit(0 if success else 1)
