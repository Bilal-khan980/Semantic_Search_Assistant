#!/usr/bin/env python3
"""
Automatic File Indexer and Monitor
Automatically indexes all files when backend starts and monitors for new files.
"""

import asyncio
import os
import time
import logging
import threading
from pathlib import Path
from typing import List, Dict, Set
import hashlib
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logger = logging.getLogger(__name__)

class AutoIndexer:
    """Automatic file indexer with real-time monitoring."""
    
    def __init__(self, document_processor, search_engine, config):
        self.document_processor = document_processor
        self.search_engine = search_engine
        self.config = config
        
        # Monitoring settings
        self.watch_folders = [
            "test_docs",
            "data/documents",
            "documents"
        ]
        
        # File tracking
        self.indexed_files = {}  # file_path -> {hash, timestamp, size}
        self.index_file = "data/indexed_files.json"
        
        # Supported file types
        self.supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.doc'}
        
        # Observer for file monitoring
        self.observer = None
        self.is_monitoring = False
        
        # Load existing index
        self.load_index_state()
        
    def load_index_state(self):
        """Load the state of indexed files."""
        try:
            if Path(self.index_file).exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.indexed_files = json.load(f)
                logger.info(f"📋 Loaded index state: {len(self.indexed_files)} files tracked")
            else:
                logger.info("📋 No previous index state found")
        except Exception as e:
            logger.error(f"❌ Error loading index state: {e}")
            self.indexed_files = {}
            
    def save_index_state(self):
        """Save the state of indexed files."""
        try:
            os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.indexed_files, f, indent=2)
            logger.debug(f"💾 Saved index state: {len(self.indexed_files)} files")
        except Exception as e:
            logger.error(f"❌ Error saving index state: {e}")
            
    def get_file_hash(self, file_path: str) -> str:
        """Get hash of file content for change detection."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"❌ Error hashing file {file_path}: {e}")
            return ""
            
    def get_file_info(self, file_path: str) -> Dict:
        """Get file information for tracking."""
        try:
            stat = os.stat(file_path)
            return {
                'hash': self.get_file_hash(file_path),
                'timestamp': stat.st_mtime,
                'size': stat.st_size
            }
        except Exception as e:
            logger.error(f"❌ Error getting file info {file_path}: {e}")
            return {}
            
    def should_index_file(self, file_path: str) -> bool:
        """Check if file should be indexed."""
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() not in self.supported_extensions:
            return False
            
        # Check if file exists
        if not path.exists():
            return False
            
        # Check if file has changed
        current_info = self.get_file_info(file_path)
        if not current_info:
            return False
            
        stored_info = self.indexed_files.get(file_path, {})
        
        # Index if new file or changed
        if (not stored_info or 
            stored_info.get('hash') != current_info['hash'] or
            stored_info.get('size') != current_info['size']):
            return True
            
        return False
        
    async def index_file(self, file_path: str) -> bool:
        """Index a single file."""
        try:
            logger.info(f"📄 Indexing: {file_path}")
            
            # Process the file
            success = await self.document_processor.process_file(file_path)
            
            if success:
                # Update tracking
                self.indexed_files[file_path] = self.get_file_info(file_path)
                self.save_index_state()
                logger.info(f"✅ Indexed: {file_path}")
                return True
            else:
                logger.error(f"❌ Failed to index: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error indexing {file_path}: {e}")
            return False
            
    async def scan_and_index_folder(self, folder_path: str) -> int:
        """Scan folder and index all files that need indexing."""
        indexed_count = 0
        
        if not Path(folder_path).exists():
            logger.warning(f"⚠️ Folder not found: {folder_path}")
            return 0
            
        logger.info(f"🔍 Scanning folder: {folder_path}")
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if self.should_index_file(file_path):
                        success = await self.index_file(file_path)
                        if success:
                            indexed_count += 1
                            
        except Exception as e:
            logger.error(f"❌ Error scanning folder {folder_path}: {e}")
            
        return indexed_count
        
    async def initial_indexing(self):
        """Perform initial indexing of all watch folders."""
        logger.info("🚀 Starting initial indexing...")

        # First, cleanup deleted files
        await self.cleanup_deleted_files()

        # Check if any files exist in watch folders
        total_files_found = 0
        total_indexed = 0

        for folder in self.watch_folders:
            if Path(folder).exists():
                # Count existing files
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if Path(file_path).suffix.lower() in self.supported_extensions:
                            total_files_found += 1

                count = await self.scan_and_index_folder(folder)
                total_indexed += count
                logger.info(f"📁 {folder}: {count} files indexed")
            else:
                logger.info(f"📁 {folder}: folder not found, skipping")

        # If no files found anywhere, clear all data
        if total_files_found == 0 and len(self.indexed_files) > 0:
            logger.info("🗑️ No files found in any watch folder, clearing all data...")
            await self.clear_all_data()

        logger.info(f"✅ Initial indexing complete: {total_indexed} files indexed")
        return total_indexed
        
    def start_monitoring(self):
        """Start file system monitoring."""
        if self.is_monitoring:
            return
            
        try:
            self.observer = Observer()
            
            # Add watchers for each folder
            for folder in self.watch_folders:
                if Path(folder).exists():
                    event_handler = FileChangeHandler(self)
                    self.observer.schedule(event_handler, folder, recursive=True)
                    logger.info(f"👁️ Monitoring: {folder}")
                    
            self.observer.start()
            self.is_monitoring = True
            logger.info("✅ File monitoring started")
            
        except Exception as e:
            logger.error(f"❌ Error starting file monitoring: {e}")
            
    def stop_monitoring(self):
        """Stop file system monitoring."""
        if self.observer and self.is_monitoring:
            try:
                self.observer.stop()
                self.observer.join()
                self.is_monitoring = False
                logger.info("🛑 File monitoring stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping file monitoring: {e}")
                
    async def handle_file_change(self, file_path: str):
        """Handle file change event."""
        try:
            # Small delay to ensure file is fully written
            await asyncio.sleep(1)

            if self.should_index_file(file_path):
                logger.info(f"🔄 File changed, re-indexing: {file_path}")
                await self.index_file(file_path)

        except Exception as e:
            logger.error(f"❌ Error handling file change {file_path}: {e}")

    async def handle_file_deletion(self, file_path: str):
        """Handle file deletion event."""
        try:
            if file_path in self.indexed_files:
                logger.info(f"🗑️ Removing deleted file from index: {file_path}")

                # Remove from vector database
                await self._remove_file_from_database(file_path)

                # Remove from index tracking
                del self.indexed_files[file_path]
                self.save_index_state()

                logger.info(f"✅ Successfully removed: {file_path}")
            else:
                logger.debug(f"🔍 File not in index, skipping: {file_path}")

        except Exception as e:
            logger.error(f"❌ Error handling file deletion {file_path}: {e}")
            
    async def cleanup_deleted_files(self):
        """Remove deleted files from index and vector database."""
        deleted_files = []

        for file_path in list(self.indexed_files.keys()):
            if not Path(file_path).exists():
                deleted_files.append(file_path)

        if deleted_files:
            logger.info(f"🗑️ Cleaning up {len(deleted_files)} deleted files from index and database")

            for file_path in deleted_files:
                # Remove from vector database
                await self._remove_file_from_database(file_path)

                # Remove from index tracking
                del self.indexed_files[file_path]
                logger.info(f"🗑️ Removed: {file_path}")

            self.save_index_state()
            logger.info(f"✅ Cleanup complete: {len(deleted_files)} files removed")

    async def _remove_file_from_database(self, file_path: str):
        """Remove all chunks of a file from the vector database."""
        try:
            # Get the vector store
            vector_store = self.document_processor.vector_store

            if hasattr(vector_store, 'delete_document'):
                # Use the vector store's delete method
                await vector_store.delete_document(file_path)
                logger.debug(f"🗑️ Removed chunks from database: {file_path}")
            elif hasattr(vector_store, 'table') and vector_store.table is not None:
                # For LanceDB, delete by source filter
                try:
                    # Normalize file path for comparison
                    normalized_path = file_path.replace('\\', '/')

                    # Try different path formats to ensure we catch all variations
                    delete_conditions = [
                        f"source = '{file_path}'",
                        f"source = '{normalized_path}'",
                        f"source LIKE '%{Path(file_path).name}%'"
                    ]

                    deleted_count = 0
                    for condition in delete_conditions:
                        try:
                            # Check if any rows match before deleting
                            df = vector_store.table.search().where(condition).limit(1).to_pandas()
                            if not df.empty:
                                vector_store.table.delete(condition)
                                deleted_count += len(df)
                                logger.debug(f"🗑️ Deleted {len(df)} chunks with condition: {condition}")
                                break
                        except Exception as e:
                            logger.debug(f"Delete condition failed: {condition} - {e}")
                            continue

                    if deleted_count > 0:
                        logger.info(f"🗑️ Removed {deleted_count} chunks from LanceDB: {file_path}")
                    else:
                        logger.warning(f"⚠️ No chunks found to delete for: {file_path}")

                except Exception as e:
                    logger.warning(f"⚠️ Could not delete from LanceDB for {file_path}: {e}")
            else:
                logger.warning(f"⚠️ Vector store doesn't support deletion for {file_path}")

        except Exception as e:
            logger.error(f"❌ Error removing {file_path} from database: {e}")

    async def clear_all_data(self):
        """Clear all indexed data and vector database."""
        try:
            logger.info("🗑️ Clearing all indexed data...")

            # Clear vector database
            vector_store = self.document_processor.vector_store
            if hasattr(vector_store, 'clear'):
                await vector_store.clear()
                logger.info("🗑️ Cleared vector database using clear() method")
            elif hasattr(vector_store, 'table') and vector_store.table is not None:
                # For LanceDB, delete all rows
                try:
                    # Check current count
                    current_count = vector_store.table.count_rows()
                    logger.info(f"🗑️ Current database has {current_count} rows")

                    if current_count > 0:
                        # Delete all rows - use a condition that matches all rows
                        vector_store.table.delete("id IS NOT NULL")

                        # Verify deletion
                        new_count = vector_store.table.count_rows()
                        logger.info(f"🗑️ Cleared LanceDB table: {current_count} → {new_count} rows")
                    else:
                        logger.info("🗑️ LanceDB table already empty")

                except Exception as e:
                    logger.warning(f"⚠️ Could not clear LanceDB: {e}")
            else:
                logger.warning("⚠️ Vector store doesn't support clearing")

            # Clear index tracking
            self.indexed_files.clear()
            self.save_index_state()

            logger.info("✅ All data cleared successfully")

        except Exception as e:
            logger.error(f"❌ Error clearing all data: {e}")
            
    async def periodic_check(self):
        """Periodic check for new/changed files."""
        while self.is_monitoring:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Cleanup deleted files
                await self.cleanup_deleted_files()
                
                # Quick scan for new files
                for folder in self.watch_folders:
                    if Path(folder).exists():
                        await self.scan_and_index_folder(folder)
                        
            except Exception as e:
                logger.error(f"❌ Error in periodic check: {e}")
                
    def get_status(self) -> Dict:
        """Get indexer status."""
        return {
            'is_monitoring': self.is_monitoring,
            'indexed_files_count': len(self.indexed_files),
            'watch_folders': self.watch_folders,
            'supported_extensions': list(self.supported_extensions)
        }

class FileChangeHandler(FileSystemEventHandler):
    """Handle file system events."""

    def __init__(self, auto_indexer):
        self.auto_indexer = auto_indexer

    def on_created(self, event):
        """Handle file creation."""
        if not event.is_directory:
            logger.info(f"📄 File created: {event.src_path}")
            asyncio.create_task(self.auto_indexer.handle_file_change(event.src_path))

    def on_modified(self, event):
        """Handle file modification."""
        if not event.is_directory:
            logger.info(f"📝 File modified: {event.src_path}")
            asyncio.create_task(self.auto_indexer.handle_file_change(event.src_path))

    def on_deleted(self, event):
        """Handle file deletion."""
        if not event.is_directory:
            logger.info(f"🗑️ File deleted: {event.src_path}")
            asyncio.create_task(self.auto_indexer.handle_file_deletion(event.src_path))

    def on_moved(self, event):
        """Handle file move/rename."""
        if not event.is_directory:
            logger.info(f"📦 File moved: {event.src_path} → {event.dest_path}")
            # Handle as deletion of old path and creation of new path
            asyncio.create_task(self.auto_indexer.handle_file_deletion(event.src_path))
            asyncio.create_task(self.auto_indexer.handle_file_change(event.dest_path))

async def main():
    """Test the auto indexer."""
    print("🧪 Testing Auto Indexer...")
    
    # Mock objects for testing
    class MockProcessor:
        async def process_file(self, file_path):
            print(f"Mock processing: {file_path}")
            return True
            
    class MockSearchEngine:
        pass
        
    class MockConfig:
        pass
        
    # Create and test indexer
    indexer = AutoIndexer(MockProcessor(), MockSearchEngine(), MockConfig())
    
    # Initial indexing
    await indexer.initial_indexing()
    
    # Start monitoring
    indexer.start_monitoring()
    
    print("✅ Auto indexer test complete")
    print(f"📊 Status: {indexer.get_status()}")

if __name__ == "__main__":
    asyncio.run(main())
