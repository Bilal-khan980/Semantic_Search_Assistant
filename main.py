"""
Main entry point for the local document processing backend.
Handles document indexing, vector search, and Readwise integration.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
import json
import os
import re

from document_processor import DocumentProcessor
from database import VectorStore
from readwise_importer import ReadwiseImporter
from search_engine import SearchEngine
from folder_manager import FolderManager
from config import Config
from citation_manager import CitationManager
from background_processor import BackgroundProcessor
from auto_indexer import AutoIndexer
# from document_monitor import DocumentMonitor  # Removed - using client-side monitoring

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentSearchBackend:
    """Main backend class that orchestrates all components."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self.document_processor = DocumentProcessor(self.config)
        self.vector_store = VectorStore(self.config)
        self.readwise_importer = ReadwiseImporter(self.config)
        self.search_engine = SearchEngine(self.vector_store, self.config)
        self.folder_manager = FolderManager(self.config, self)

        # New enhanced components
        self.citation_manager = CitationManager(self.config.to_dict())
        self.background_processor = BackgroundProcessor(self.config.to_dict())
        self.auto_indexer = AutoIndexer(self.document_processor, self.search_engine, self.config.to_dict())
        # self.document_monitor = DocumentMonitor(self.search_engine, self.config.to_dict())  # Using client-side monitoring
        
    async def initialize(self):
        """Initialize all components."""
        logger.info("Initializing document search backend...")
        await self.vector_store.initialize()
        await self.document_processor.initialize()

        # Initialize new components
        await self.background_processor.start()
        logger.info("✅ Background processor started")

        # Start automatic file indexing and monitoring
        logger.info("🔍 Starting automatic file indexing...")
        indexed_count = await self.auto_indexer.initial_indexing()
        logger.info(f"✅ Auto-indexer: {indexed_count} files indexed")

        # Start file monitoring
        self.auto_indexer.start_monitoring()
        logger.info("✅ File monitoring started")

        # Setup document monitoring callbacks (disabled - using client-side monitoring)
        # self.document_monitor.add_context_callback(self._handle_context_event)
        logger.info("✅ Document monitor configured (client-side)")

        # Add test_docs folder to monitoring
        test_docs_path = Path("test_docs")
        if test_docs_path.exists():
            await self.folder_manager.add_folder(str(test_docs_path))
            logger.info(f"Added test_docs folder to monitoring: {test_docs_path.absolute()}")
        else:
            logger.warning("test_docs folder not found, creating it...")
            test_docs_path.mkdir(exist_ok=True)
            await self.folder_manager.add_folder(str(test_docs_path))

        # Start folder monitoring
        await self.folder_manager.start_monitoring()

        logger.info("✅ Document search backend initialized successfully")
        return True

    async def cleanup(self):
        """Cleanup resources and stop monitoring."""
        logger.info("🧹 Cleaning up backend...")

        try:
            # Stop folder monitoring
            if hasattr(self, 'folder_manager'):
                await self.folder_manager.stop_monitoring()
                logger.info("✅ Folder monitoring stopped")

            # Stop background processor
            if hasattr(self, 'background_processor'):
                await self.background_processor.stop()
                logger.info("✅ Background processor stopped")

            # Stop auto-indexer and file monitoring
            if hasattr(self, 'auto_indexer'):
                self.auto_indexer.stop_monitoring()
                logger.info("✅ Auto-indexer stopped")

            # Stop document monitoring (disabled - using client-side monitoring)
            # if hasattr(self, 'document_monitor'):
            #     await self.document_monitor.stop_monitoring()
            logger.info("✅ Document monitoring stopped (client-side)")

            # Cleanup old tasks
            if hasattr(self, 'background_processor'):
                await self.background_processor.cleanup_old_tasks()
                logger.info("✅ Old tasks cleaned up")

            logger.info("✅ Backend cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _handle_context_event(self, context_event: Dict[str, Any]):
        """Handle context events from document monitoring."""
        try:
            event_type = context_event.get('type')
            suggestions = context_event.get('suggestions', [])

            logger.info(f"📋 Context event: {event_type} with {len(suggestions)} suggestions")

            # Here you could add logic to:
            # - Store context events for analytics
            # - Trigger additional processing
            # - Send notifications to connected clients

        except Exception as e:
            logger.error(f"Error handling context event: {e}")

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            status = {
                'backend_initialized': True,
                'components': {
                    'vector_store': hasattr(self, 'vector_store') and self.vector_store is not None,
                    'document_processor': hasattr(self, 'document_processor') and self.document_processor is not None,
                    'search_engine': hasattr(self, 'search_engine') and self.search_engine is not None,
                    'citation_manager': hasattr(self, 'citation_manager') and self.citation_manager is not None,
                    'background_processor': hasattr(self, 'background_processor') and self.background_processor is not None,
                    'auto_indexer': hasattr(self, 'auto_indexer') and self.auto_indexer is not None,
                    'document_monitor': False,  # Using client-side monitoring
                },
                'auto_indexer': self.auto_indexer.get_status() if hasattr(self, 'auto_indexer') else {},
                'statistics': {}
            }

            # Add component-specific statistics
            if hasattr(self, 'background_processor'):
                status['statistics']['background_processing'] = self.background_processor.get_statistics()

            if hasattr(self, 'citation_manager'):
                status['statistics']['citations'] = self.citation_manager.get_statistics()

            # Add search statistics
            search_stats = await self.get_search_statistics()
            status['statistics']['search'] = search_stats

            return status

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}

    async def get_search_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        try:
            # Get vector store statistics
            stats = await self.vector_store.get_stats()

            # Add search-specific statistics
            search_stats = {
                'total_documents': stats.get('total_documents', 0),
                'total_chunks': stats.get('total_chunks', 0),
                'vector_dimensions': stats.get('vector_dimensions', 0),
                'index_size': stats.get('index_size', 0)
            }

            return search_stats

        except Exception as e:
            logger.error(f"Error getting search statistics: {e}")
            return {'error': str(e)}

    async def process_documents(self, file_paths: List[str], progress_callback=None):
        """Process multiple documents and add them to the vector store."""
        results = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                logger.info(f"Processing document {i+1}/{total_files}: {file_path}")
                
                # Check if file exists
                if not Path(file_path).exists():
                    logger.warning(f"File not found: {file_path}")
                    results.append({
                        'file_path': file_path,
                        'error': 'File not found',
                        'status': 'error'
                    })
                    continue
                
                # Process document
                chunks = await self.document_processor.process_file(file_path)
                logger.info(f"Processed {file_path}: {len(chunks)} chunks, type: {type(chunks)}")
                if chunks:
                    logger.info(f"First chunk type: {type(chunks[0])}, has content: {hasattr(chunks[0], 'content') if chunks else 'N/A'}")

                # Generate embeddings and store
                document_id = await self.vector_store.add_document(file_path, chunks)
                
                results.append({
                    'file_path': file_path,
                    'document_id': document_id,
                    'chunks_count': len(chunks),
                    'status': 'success',
                    'chunks': chunks  # Include chunks for query generation
                })
                
                # Report progress
                if progress_callback:
                    progress = (i + 1) / total_files * 100
                    await progress_callback(progress, f"Processed {Path(file_path).name}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                results.append({
                    'file_path': file_path,
                    'error': str(e),
                    'status': 'error'
                })
                
        return results
    
    async def import_readwise_data(self, markdown_content: str, progress_callback=None):
        """Import Readwise highlights from markdown content."""
        try:
            highlights = await self.readwise_importer.parse_markdown(markdown_content)
            
            total_highlights = len(highlights)
            processed_highlights = []
            
            for i, highlight in enumerate(highlights):
                # Process highlight as a document chunk
                document_id = await self.vector_store.add_readwise_highlight(highlight)
                processed_highlights.append({
                    'highlight_id': document_id,
                    'book': highlight.get('book', 'Unknown'),
                    'author': highlight.get('author', 'Unknown'),
                    'text': highlight.get('text', '')[:100] + '...',
                    'status': 'success',
                    'full_highlight': highlight  # Include full highlight for query generation
                })
                
                # Report progress
                if progress_callback:
                    progress = (i + 1) / total_highlights * 100
                    await progress_callback(progress, f"Imported highlight from {highlight.get('book', 'Unknown')}")
            
            logger.info(f"Successfully imported {len(processed_highlights)} Readwise highlights")
            return processed_highlights
            
        except Exception as e:
            logger.error(f"Error importing Readwise data: {str(e)}")
            raise
    
    async def search(self, query: str, limit: int = 20, similarity_threshold: float = 0.7):
        """Perform semantic search across all indexed documents."""
        try:
            results = await self.search_engine.search(
                query=query,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise
    
    async def get_stats(self):
        """Get statistics about indexed documents."""
        return await self.vector_store.get_stats()
    
    async def generate_test_queries(self, processed_results, readwise_results=None):
        """Generate test queries based on actual document content."""
        queries = []
        
        # Extract key terms from processed documents
        all_content = []
        
        # Get content from document chunks
        for result in processed_results:
            if result['status'] == 'success' and 'chunks' in result:
                for chunk in result['chunks']:
                    all_content.append(chunk.content.lower())
        
        # Get content from Readwise highlights
        if readwise_results:
            for result in readwise_results:
                if result['status'] == 'success' and 'full_highlight' in result:
                    highlight_text = result['full_highlight'].get('text', '')
                    if highlight_text:
                        all_content.append(highlight_text.lower())
        
        # Combine all content
        combined_content = ' '.join(all_content)
        
        # Extract meaningful terms and phrases
        # Look for important keywords (2-3 word phrases)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', combined_content)
        word_freq = {}
        for word in words:
            if word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'what', 'when', 'with']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get most common meaningful words
        common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Generate queries based on actual content
        if 'artificial intelligence' in combined_content or 'machine learning' in combined_content:
            queries.extend([
                "artificial intelligence",
                "machine learning",
                "AI and ML applications",
                "supervised learning",
                "neural networks"
            ])
        
        if 'ethics' in combined_content or 'ethical' in combined_content:
            queries.extend([
                "AI ethics",
                "ethical framework",
                "algorithmic bias"
            ])
        
        if 'focus' in combined_content or 'concentration' in combined_content:
            queries.extend([
                "focus and concentration",
                "deep work",
                "cognitive demanding"
            ])
        
        # Add queries based on most frequent terms
        for word, freq in common_words[:5]:
            if len(word) > 4 and freq > 2:  # Only meaningful, frequent terms
                queries.append(word)
        
        # Add some combination queries
        if len(common_words) >= 2:
            queries.append(f"{common_words[0][0]} {common_words[1][0]}")
        
        # Remove duplicates and return
        return list(set(queries))[:8]  # Limit to 8 queries
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.vector_store.close()

# Example usage and testing
async def main():
    """Example usage of the backend."""
    backend = DocumentSearchBackend()
    
    try:
        await backend.initialize()
        
        # Check if we have any sample documents
        sample_files = []
        possible_locations = [
            "sample_documents/",
            "documents/",
            "test_documents/",
            "./"
        ]
        
        # Look for any text files to process
        for location in possible_locations:
            location_path = Path(location)
            if location_path.exists():
                # Find any supported files
                for ext in [".pdf", ".docx", ".md", ".txt"]:
                    files = list(location_path.glob(f"*{ext}"))
                    sample_files.extend([str(f) for f in files])
                
                if sample_files:
                    break
        
        if not sample_files:
            # Create a simple test document
            test_dir = Path("test_documents")
            test_dir.mkdir(exist_ok=True)
            
            test_file = test_dir / "sample.txt"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("""
# Sample Document for Testing

This is a sample document to test the semantic search functionality.

## About Productivity

Productivity is about getting things done efficiently. Deep work, as described by Cal Newport, 
is the ability to focus without distraction on cognitively demanding tasks.

## Key Concepts

- Focus and concentration are essential for knowledge work
- Eliminating distractions improves output quality
- Time blocking can help manage attention
- Regular breaks prevent mental fatigue

## Learning and Growth

Continuous learning is important for personal and professional development. 
Taking notes and building a knowledge management system helps retain information.

The key to effective learning is active engagement with the material, 
not passive consumption.
                """)
            
            sample_files = [str(test_file)]
            logger.info(f"Created test document: {test_file}")
        
        async def progress_callback(progress, message):
            print(f"Progress: {progress:.1f}% - {message}")
        
        # Process documents if we have any
        processed_results = []
        if sample_files:
            print(f"\nProcessing {len(sample_files)} documents...")
            processed_results = await backend.process_documents(sample_files, progress_callback)
            
            successful = [r for r in processed_results if r['status'] == 'success']
            print(f"Successfully processed {len(successful)} documents")
        
        # Test Readwise import with sample data
        print("\n" + "="*50)
        print("TESTING READWISE IMPORT")
        print("="*50)
        
        sample_readwise = """
## Deep Work - Cal Newport

> The ability to focus without distraction on a cognitively demanding task is becoming increasingly valuable—and increasingly rare.

Author: Cal Newport
Tags: productivity, focus, deep-work

> Human beings, it seems, are at their best when immersed deeply in something challenging.

Note: This resonates with the concept of flow state

> Clarity about what matters provides clarity about what does not.

Note: Important principle for prioritization
        """
        
        print("Importing sample Readwise data...")
        readwise_results = await backend.import_readwise_data(sample_readwise, progress_callback)
        print(f"Imported {len(readwise_results)} highlights")
        
        # Generate test queries based on actual content
        print("\n" + "="*50)
        print("GENERATING TEST QUERIES FROM CONTENT")
        print("="*50)
        test_queries = await backend.generate_test_queries(processed_results, readwise_results)
        print(f"Generated {len(test_queries)} test queries based on document content:")
        for i, query in enumerate(test_queries, 1):
            print(f"  {i}. {query}")
        
        # Test search functionality with generated queries
        if test_queries:
            print("\n" + "="*50)
            print("TESTING SEARCH FUNCTIONALITY")
            print("="*50)
            
            # Lower the similarity threshold for testing
            similarity_threshold = 0.3
            
            for query in test_queries:
                print(f"\nSearching for: '{query}'")
                search_results = await backend.search(query, limit=3, similarity_threshold=similarity_threshold)
                
                if search_results:
                    for i, result in enumerate(search_results, 1):
                        readwise_indicator = " [READWISE]" if result.get('is_readwise') else ""
                        print(f"\n  Result {i}{readwise_indicator}: {result['similarity']:.3f} - {result['content'][:150]}...")
                        if result.get('metadata', {}).get('note'):
                            print(f"    Note: {result['metadata']['note']}")
                else:
                    print("    No results found")
        
        # Test with some manual queries that should definitely work
        print("\n" + "="*50)
        print("TESTING WITH BROAD QUERIES")
        print("="*50)
        broad_queries = [
            "learning",
            "intelligence", 
            "focus",
            "data",
            "system"
        ]
        for query in broad_queries:
            print(f"\nSearching for: '{query}' (threshold: 0.2)")
            search_results = await backend.search(query, limit=2, similarity_threshold=0.2)
            if search_results:
                for i, result in enumerate(search_results, 1):
                    readwise_indicator = " [READWISE]" if result.get('is_readwise') else ""
                    print(f"  Result {i}{readwise_indicator}: {result['similarity']:.3f} - {result['content'][:100]}...")
            else:
                print("No results found")
        # Get final stats
        print("\n" + "="*50)
        print("FINAL STATISTICS")
        print("="*50)
        stats = await backend.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print(f"\n✅ Backend testing completed successfully!")
        print(f"📁 Database location: {backend.config.db_path}")
        print(f"⚙️  Configuration: {backend.config.config_path}")
        # Debug: Show some actual content from the database
        print(f"\n🔍 DEBUG: Sample content from database:")
        debug_results = await backend.search("the", limit=2, similarity_threshold=0.1)
        for i, result in enumerate(debug_results, 1):
            print(f"  Sample {i}: {result['content'][:200]}...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise
    finally:
        await backend.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
