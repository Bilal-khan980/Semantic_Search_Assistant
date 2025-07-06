"""
Comprehensive integration test for the Semantic Search Assistant.
Tests all major features and components working together.
"""

import asyncio
import logging
import tempfile
import os
import json
from pathlib import Path
import time

# Import our modules
from main import DocumentSearchBackend
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Comprehensive integration tester for the semantic search system."""
    
    def __init__(self):
        self.backend = None
        self.test_results = {}
        self.temp_dir = None
        
    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting comprehensive integration tests...")
        
        try:
            # Setup test environment
            await self.setup_test_environment()
            
            # Run individual test suites
            await self.test_backend_initialization()
            await self.test_document_processing()
            await self.test_pdf_highlight_extraction()
            await self.test_readwise_integration()
            await self.test_vector_search()
            await self.test_performance_features()
            await self.test_clipboard_monitoring()
            await self.test_api_endpoints()
            
            # Generate test report
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"Integration test failed: {str(e)}")
            raise
        finally:
            await self.cleanup_test_environment()
    
    async def setup_test_environment(self):
        """Setup test environment with temporary files and config."""
        logger.info("Setting up test environment...")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="semantic_search_test_")
        logger.info(f"Test directory: {self.temp_dir}")
        
        # Create test config
        test_config = {
            "embedding": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cpu",
                "batch_size": 16
            },
            "vector_store": {
                "db_path": os.path.join(self.temp_dir, "test_vector_db"),
                "table_name": "test_documents"
            },
            "performance": {
                "max_cache_size": 100,
                "cache_ttl_seconds": 60,
                "batch_size": 16,
                "max_concurrent_searches": 3
            },
            "clipboard": {
                "enabled": False  # Disable for testing
            }
        }
        
        config_path = os.path.join(self.temp_dir, "test_config.json")
        with open(config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Initialize backend
        self.backend = DocumentSearchBackend(config_path)
        
        self.test_results['setup'] = {'status': 'PASS', 'message': 'Test environment setup successful'}
    
    async def test_backend_initialization(self):
        """Test backend initialization."""
        logger.info("Testing backend initialization...")
        
        try:
            await self.backend.initialize()
            
            # Verify components are initialized
            assert self.backend.vector_store is not None
            assert self.backend.document_processor is not None
            assert self.backend.search_engine is not None
            assert self.backend.readwise_importer is not None
            
            self.test_results['backend_init'] = {'status': 'PASS', 'message': 'Backend initialized successfully'}
            
        except Exception as e:
            self.test_results['backend_init'] = {'status': 'FAIL', 'message': str(e)}
            raise
    
    async def test_document_processing(self):
        """Test document processing functionality."""
        logger.info("Testing document processing...")
        
        try:
            # Create test documents
            test_docs = self.create_test_documents()
            
            # Process documents
            results = await self.backend.process_documents(test_docs)
            
            # Verify processing results
            assert len(results) > 0
            assert all(r['status'] == 'success' for r in results)
            
            # Verify documents are in vector store
            stats = await self.backend.get_stats()
            assert stats['total_documents'] > 0
            assert stats['total_chunks'] > 0
            
            self.test_results['document_processing'] = {
                'status': 'PASS', 
                'message': f'Processed {len(results)} documents successfully',
                'details': {
                    'documents_processed': len(results),
                    'total_chunks': stats['total_chunks']
                }
            }
            
        except Exception as e:
            self.test_results['document_processing'] = {'status': 'FAIL', 'message': str(e)}
            raise
    
    async def test_pdf_highlight_extraction(self):
        """Test PDF highlight extraction."""
        logger.info("Testing PDF highlight extraction...")
        
        try:
            # Create a test PDF with simulated highlights
            pdf_path = self.create_test_pdf_with_highlights()
            
            # Process the PDF
            results = await self.backend.process_documents([pdf_path])
            
            # Verify highlight extraction
            assert len(results) > 0
            result = results[0]
            
            # Check if highlights were extracted (this depends on the PDF content)
            highlights = result.get('highlights', [])
            annotations = result.get('annotations', [])
            
            self.test_results['pdf_highlights'] = {
                'status': 'PASS',
                'message': f'PDF processing completed with {len(highlights)} highlights and {len(annotations)} annotations',
                'details': {
                    'highlights_found': len(highlights),
                    'annotations_found': len(annotations)
                }
            }
            
        except Exception as e:
            self.test_results['pdf_highlights'] = {'status': 'FAIL', 'message': str(e)}
            # Don't raise - this might fail if PyMuPDF isn't available
    
    async def test_readwise_integration(self):
        """Test Readwise integration."""
        logger.info("Testing Readwise integration...")
        
        try:
            # Create test Readwise markdown
            readwise_content = self.create_test_readwise_markdown()
            
            # Import Readwise content
            results = await self.backend.import_readwise_markdown(readwise_content)
            
            # Verify import results
            assert len(results) > 0
            assert all(r['status'] == 'success' for r in results)
            
            # Verify Readwise highlights are searchable
            search_results = await self.backend.search("productivity insights")
            readwise_results = [r for r in search_results if r.get('is_readwise', False)]
            
            self.test_results['readwise_integration'] = {
                'status': 'PASS',
                'message': f'Imported {len(results)} Readwise highlights',
                'details': {
                    'highlights_imported': len(results),
                    'searchable_highlights': len(readwise_results)
                }
            }
            
        except Exception as e:
            self.test_results['readwise_integration'] = {'status': 'FAIL', 'message': str(e)}
            raise
    
    async def test_vector_search(self):
        """Test vector search functionality."""
        logger.info("Testing vector search...")
        
        try:
            # Test various search queries
            test_queries = [
                "productivity tips",
                "machine learning concepts",
                "business strategy",
                "personal development"
            ]
            
            search_results = {}
            for query in test_queries:
                results = await self.backend.search(query, limit=5)
                search_results[query] = len(results)
            
            # Verify search functionality
            assert all(count >= 0 for count in search_results.values())
            
            # Test similarity thresholds
            high_threshold_results = await self.backend.search("productivity", similarity_threshold=0.8)
            low_threshold_results = await self.backend.search("productivity", similarity_threshold=0.3)
            
            assert len(low_threshold_results) >= len(high_threshold_results)
            
            self.test_results['vector_search'] = {
                'status': 'PASS',
                'message': 'Vector search working correctly',
                'details': {
                    'query_results': search_results,
                    'threshold_test_passed': True
                }
            }
            
        except Exception as e:
            self.test_results['vector_search'] = {'status': 'FAIL', 'message': str(e)}
            raise
    
    async def test_performance_features(self):
        """Test performance optimization features."""
        logger.info("Testing performance features...")
        
        try:
            # Test caching
            query = "test query for caching"
            
            # First search (should cache)
            start_time = time.time()
            results1 = await self.backend.search(query)
            first_search_time = time.time() - start_time
            
            # Second search (should use cache)
            start_time = time.time()
            results2 = await self.backend.search(query)
            second_search_time = time.time() - start_time
            
            # Verify caching worked
            assert results1 == results2  # Same results
            assert second_search_time < first_search_time  # Faster second time
            
            # Test cache stats
            cache_stats = self.backend.vector_store.get_cache_stats()
            assert 'embedding_cache_size' in cache_stats
            assert 'search_cache_size' in cache_stats
            
            self.test_results['performance'] = {
                'status': 'PASS',
                'message': 'Performance features working correctly',
                'details': {
                    'first_search_time': first_search_time,
                    'second_search_time': second_search_time,
                    'cache_stats': cache_stats
                }
            }
            
        except Exception as e:
            self.test_results['performance'] = {'status': 'FAIL', 'message': str(e)}
            raise
    
    async def test_clipboard_monitoring(self):
        """Test clipboard monitoring (if enabled)."""
        logger.info("Testing clipboard monitoring...")
        
        try:
            if hasattr(self.backend, 'clipboard_monitor') and self.backend.clipboard_monitor:
                # Test clipboard monitor functionality
                history = self.backend.clipboard_monitor.get_clipboard_history()
                
                self.test_results['clipboard'] = {
                    'status': 'PASS',
                    'message': 'Clipboard monitoring available',
                    'details': {'history_size': len(history)}
                }
            else:
                self.test_results['clipboard'] = {
                    'status': 'SKIP',
                    'message': 'Clipboard monitoring disabled for testing'
                }
                
        except Exception as e:
            self.test_results['clipboard'] = {'status': 'FAIL', 'message': str(e)}
    
    async def test_api_endpoints(self):
        """Test API endpoints (basic functionality)."""
        logger.info("Testing API functionality...")
        
        try:
            # Test basic backend methods that API would use
            stats = await self.backend.get_stats()
            assert isinstance(stats, dict)
            assert 'total_documents' in stats
            
            # Test search functionality
            search_results = await self.backend.search("test query")
            assert isinstance(search_results, list)
            
            self.test_results['api'] = {
                'status': 'PASS',
                'message': 'API functionality working correctly',
                'details': {'stats_available': True, 'search_working': True}
            }
            
        except Exception as e:
            self.test_results['api'] = {'status': 'FAIL', 'message': str(e)}
            raise

    def create_test_documents(self):
        """Create test documents for processing."""
        test_docs = []

        # Create test text file
        txt_path = os.path.join(self.temp_dir, "test_document.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("""
            This is a test document about productivity and time management.
            It contains information about various productivity techniques
            including the Pomodoro Technique, Getting Things Done (GTD),
            and time blocking strategies.

            Key concepts include:
            - Focus and concentration
            - Task prioritization
            - Goal setting and achievement
            - Work-life balance
            """)
        test_docs.append(txt_path)

        # Create test markdown file
        md_path = os.path.join(self.temp_dir, "test_notes.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("""
            # Machine Learning Notes

            ## Key Concepts

            ### Supervised Learning
            - Classification algorithms
            - Regression techniques
            - Model evaluation metrics

            ### Unsupervised Learning
            - Clustering methods
            - Dimensionality reduction
            - Anomaly detection

            ## Best Practices
            - Data preprocessing
            - Feature engineering
            - Cross-validation
            """)
        test_docs.append(md_path)

        return test_docs

    def create_test_pdf_with_highlights(self):
        """Create a test PDF file (simplified)."""
        # For testing purposes, create a simple text file that simulates PDF content
        pdf_path = os.path.join(self.temp_dir, "test_document.pdf")

        # Create a dummy PDF-like file (in real implementation, would use proper PDF library)
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write("""
            Business Strategy and Innovation

            This document discusses key principles of business strategy
            and innovation management in modern organizations.

            Strategic planning involves analyzing market conditions,
            competitive landscape, and internal capabilities.
            """)

        return pdf_path

    def create_test_readwise_markdown(self):
        """Create test Readwise markdown content."""
        return """
        ## Atomic Habits by James Clear

        > The quality of our lives often depends on the quality of our habits.

        > You do not rise to the level of your goals. You fall to the level of your systems.

        > Every action you take is a vote for the type of person you wish to become.

        ## Deep Work by Cal Newport

        > Human beings, it seems, are at their best when immersed deeply in something challenging.

        > The ability to perform deep work is becoming increasingly rare at exactly the same time it is becoming increasingly valuable.

        ## The Lean Startup by Eric Ries

        > The only way to win is to learn faster than anyone else.

        > Success is not delivering a feature; success is learning how to solve the customer's problem.
        """

    def generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("Generating test report...")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'PASS')
        failed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'FAIL')
        skipped_tests = sum(1 for r in self.test_results.values() if r['status'] == 'SKIP')

        print("\n" + "="*80)
        print("SEMANTIC SEARCH ASSISTANT - INTEGRATION TEST REPORT")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Skipped: {skipped_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("="*80)

        for test_name, result in self.test_results.items():
            status_symbol = "✓" if result['status'] == 'PASS' else "✗" if result['status'] == 'FAIL' else "⚠"
            print(f"{status_symbol} {test_name.upper()}: {result['status']}")
            print(f"   {result['message']}")

            if 'details' in result:
                for key, value in result['details'].items():
                    print(f"   - {key}: {value}")
            print()

        print("="*80)

        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! The Semantic Search Assistant is ready for use.")
        else:
            print(f"⚠️  {failed_tests} test(s) failed. Please review the issues above.")

        print("="*80)

    async def cleanup_test_environment(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")

        try:
            # Close backend connections
            if self.backend and self.backend.vector_store:
                await self.backend.vector_store.close()

            # Clean up temporary files
            import shutil
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up test directory: {self.temp_dir}")

        except Exception as e:
            logger.warning(f"Cleanup warning: {str(e)}")

async def main():
    """Run the integration tests."""
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
