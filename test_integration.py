#!/usr/bin/env python3
"""
Integration Testing Script for Semantic Search Assistant.
Tests all components and ensures seamless integration.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
import tempfile
import json
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_document_processor():
    """Test document processing functionality."""
    logger.info("🧪 Testing Document Processor...")

    try:
        from document_processor import DocumentProcessor

        # Create a simple config object that matches what DocumentProcessor expects
        class Config:
            def __init__(self):
                self.chunk_size = 500
                self.chunk_overlap = 50
                self.supported_formats = ['.txt', '.md', '.pdf', '.docx']

            def get(self, key, default=None):
                if key == 'chunking.separators':
                    return ["\n\n", "\n", " ", ""]
                return default

        config = Config()
        processor = DocumentProcessor(config)
        await processor.initialize()
        
        # Create a test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for semantic search. It contains important information about AI and machine learning.")
            test_file = f.name
        
        try:
            # Test document processing
            chunks = await processor.process_file(test_file)
            assert len(chunks) > 0, "No chunks generated"
            assert all('content' in chunk for chunk in chunks), "Missing content in chunks"
            
            logger.info(f"✅ Document processor test passed - Generated {len(chunks)} chunks")
            return True
            
        finally:
            Path(test_file).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"❌ Document processor test failed: {e}")
        return False

async def test_search_engine():
    """Test search engine functionality."""
    logger.info("🧪 Testing Search Engine...")

    try:
        from search_engine import SearchEngine
        from database import VectorDatabase

        config = {
            'search': {
                'model_name': 'all-MiniLM-L6-v2',
                'similarity_threshold': 0.3,
                'max_results': 10
            },
            'database': {
                'path': 'test_db',
                'table_name': 'test_documents'
            }
        }

        # Initialize vector database first
        vector_db = VectorDatabase(config)
        await vector_db.initialize()

        # Initialize search engine with vector database
        search_engine = SearchEngine(vector_db, config)
        
        # Test adding documents
        test_docs = [
            {
                'content': 'Artificial intelligence is transforming the world.',
                'source': 'test_doc_1.txt',
                'metadata': {'type': 'test'}
            },
            {
                'content': 'Machine learning algorithms can learn from data.',
                'source': 'test_doc_2.txt',
                'metadata': {'type': 'test'}
            }
        ]
        
        await search_engine.add_documents(test_docs)
        
        # Test search
        results = await search_engine.search('artificial intelligence', limit=5)
        assert len(results) > 0, "No search results returned"
        assert 'content' in results[0], "Missing content in search results"
        
        logger.info(f"✅ Search engine test passed - Found {len(results)} results")
        
        # Cleanup
        db_path = Path(config['database']['path'])
        if db_path.exists():
            shutil.rmtree(db_path)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Search engine test failed: {e}")
        return False

async def test_readwise_importer():
    """Test Readwise import functionality."""
    logger.info("🧪 Testing Readwise Importer...")
    
    try:
        from readwise_importer import ReadwiseImporter
        
        config = {
            'readwise': {
                'import_folder': 'test_readwise',
                'supported_formats': ['.md']
            }
        }
        
        importer = ReadwiseImporter(config)
        
        # Create test Readwise markdown file
        test_content = """# Test Book

## Metadata
- Author: Test Author
- Title: Test Book
- URL: https://example.com

## Highlights

> This is a test highlight about artificial intelligence.

> Another highlight about machine learning and data science.
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_book.md"
            test_file.write_text(test_content)
            
            # Test import
            highlights = await importer.import_from_file(str(test_file))
            assert len(highlights) > 0, "No highlights imported"
            assert all('content' in h for h in highlights), "Missing content in highlights"
            assert all(h.get('is_readwise') for h in highlights), "Missing Readwise flag"
            
            logger.info(f"✅ Readwise importer test passed - Imported {len(highlights)} highlights")
            return True
            
    except Exception as e:
        logger.error(f"❌ Readwise importer test failed: {e}")
        return False

async def test_citation_manager():
    """Test citation management functionality."""
    logger.info("🧪 Testing Citation Manager...")
    
    try:
        from citation_manager import CitationManager
        
        config = {
            'citation': {
                'default_style': 'apa',
                'database_path': 'test_citations.json'
            }
        }
        
        citation_manager = CitationManager(config)
        
        # Test source registration
        source_info = {
            'title': 'Test Article',
            'author': 'Test Author',
            'publication_date': '2024-01-01',
            'url': 'https://example.com/article'
        }
        
        source_id = citation_manager.register_source(source_info)
        assert source_id, "Source ID not generated"
        
        # Test citation creation
        citation = citation_manager.create_citation(
            content="This is a test quote from the article.",
            source_id=source_id,
            page="42"
        )
        
        assert citation['id'], "Citation ID not generated"
        assert citation['content'], "Citation content missing"
        
        # Test citation formatting
        formatted = citation_manager.format_citation(citation['id'], 'apa')
        assert formatted, "Citation not formatted"
        assert 'Test Author' in formatted, "Author missing from citation"
        
        logger.info("✅ Citation manager test passed")
        
        # Cleanup
        Path(config['citation']['database_path']).unlink(missing_ok=True)
        return True
        
    except Exception as e:
        logger.error(f"❌ Citation manager test failed: {e}")
        return False

async def test_background_processor():
    """Test background processing functionality."""
    logger.info("🧪 Testing Background Processor...")
    
    try:
        from background_processor import BackgroundProcessor, TaskPriority
        
        config = {
            'processing': {
                'max_workers': 2,
                'max_queue_size': 10
            }
        }
        
        processor = BackgroundProcessor(config)
        await processor.start()
        
        # Test task submission
        async def test_task(progress_callback=None, **kwargs):
            if progress_callback:
                progress_callback(50.0)
            await asyncio.sleep(0.1)  # Simulate work
            if progress_callback:
                progress_callback(100.0)
            return "Task completed successfully"
        
        task_id = await processor.submit_task(
            test_task,
            "Test Task",
            "Testing background processing",
            priority=TaskPriority.HIGH
        )
        
        # Wait for task completion
        for _ in range(50):  # 5 second timeout
            task = processor.get_task(task_id)
            if task and task.status.value in ['completed', 'failed']:
                break
            await asyncio.sleep(0.1)
        
        task = processor.get_task(task_id)
        assert task, "Task not found"
        assert task.status.value == 'completed', f"Task failed: {task.error_message}"
        assert task.result == "Task completed successfully", "Incorrect task result"
        
        await processor.stop()
        
        logger.info("✅ Background processor test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Background processor test failed: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints."""
    logger.info("🧪 Testing API Endpoints...")
    
    try:
        # Import API components
        from api_service import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200, "Health endpoint failed"
        
        # Test search endpoint (may fail if no documents indexed)
        search_data = {
            "query": "test query",
            "limit": 5,
            "similarity_threshold": 0.3
        }
        
        response = client.post("/search", json=search_data)
        assert response.status_code == 200, "Search endpoint failed"
        
        logger.info("✅ API endpoints test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ API endpoints test failed: {e}")
        return False

async def test_integration():
    """Test full integration workflow."""
    logger.info("🧪 Testing Full Integration...")
    
    try:
        # Test the complete workflow
        from document_processor import DocumentProcessor
        from search_engine import SearchEngine
        from citation_manager import CitationManager
        
        # Initialize components
        config = {
            'processing': {'chunk_size': 500, 'chunk_overlap': 50},
            'search': {'model_name': 'all-MiniLM-L6-v2', 'similarity_threshold': 0.3},
            'database': {'path': 'integration_test_db', 'table_name': 'test_docs'},
            'citation': {'default_style': 'apa', 'database_path': 'integration_citations.json'}
        }
        
        processor = DocumentProcessor(config)
        search_engine = SearchEngine(config)
        citation_manager = CitationManager(config)
        
        await search_engine.initialize()
        
        # Create test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Artificial intelligence and machine learning are revolutionizing technology. Deep learning models can process vast amounts of data.")
            test_file = f.name
        
        try:
            # Process document
            chunks = await processor.process_file(test_file)
            assert len(chunks) > 0, "No chunks generated"
            
            # Add to search engine
            await search_engine.add_documents(chunks)
            
            # Search for content
            results = await search_engine.search("artificial intelligence", limit=3)
            assert len(results) > 0, "No search results"
            
            # Create citation
            source_info = {
                'title': 'Test Document',
                'author': 'Test Author',
                'file_path': test_file
            }
            source_id = citation_manager.register_source(source_info)
            
            citation = citation_manager.create_citation(
                content=results[0]['content'][:100],
                source_id=source_id
            )
            
            formatted_citation = citation_manager.format_citation(citation['id'])
            assert formatted_citation, "Citation formatting failed"
            
            logger.info("✅ Full integration test passed")
            return True
            
        finally:
            # Cleanup
            Path(test_file).unlink(missing_ok=True)
            db_path = Path(config['database']['path'])
            if db_path.exists():
                shutil.rmtree(db_path)
            Path(config['citation']['database_path']).unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"❌ Full integration test failed: {e}")
        return False

async def main():
    """Run all tests."""
    logger.info("🚀 Starting Semantic Search Assistant Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Document Processor", test_document_processor),
        ("Search Engine", test_search_engine),
        ("Readwise Importer", test_readwise_importer),
        ("Citation Manager", test_citation_manager),
        ("Background Processor", test_background_processor),
        ("API Endpoints", test_api_endpoints),
        ("Full Integration", test_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Test Results Summary")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📊 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        logger.info("🎉 All tests passed! The Semantic Search Assistant is ready to use.")
        logger.info("\n📋 Next Steps:")
        logger.info("1. Install Node.js from https://nodejs.org/ (required for desktop app)")
        logger.info("2. Run 'python build_desktop_app.py' to build the desktop application")
        logger.info("3. Run 'python start_desktop_app.py' to launch the application")
        logger.info("4. Use 'start_desktop_app.bat' for easy Windows launching")
    else:
        logger.info("⚠️ Some tests failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
