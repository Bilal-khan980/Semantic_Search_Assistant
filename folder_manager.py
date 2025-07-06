"""
Folder Manager for automatic document discovery and processing.
Handles folder connections, monitoring, and background processing.
"""

import asyncio
import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
import hashlib
import time
from datetime import datetime
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class DocumentFolderHandler(FileSystemEventHandler):
    """File system event handler for document folders."""
    
    def __init__(self, folder_manager):
        self.folder_manager = folder_manager
        
    def on_created(self, event):
        if not event.is_directory:
            self.folder_manager.queue_file_for_processing(event.src_path, 'created')
    
    def on_modified(self, event):
        if not event.is_directory:
            self.folder_manager.queue_file_for_processing(event.src_path, 'modified')
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.folder_manager.queue_file_for_removal(event.src_path)

class FolderManager:
    """Manages folder connections and automatic document processing."""
    
    def __init__(self, config, document_processor=None):
        self.config = config
        self.document_processor = document_processor
        self.connected_folders = set()
        self.folder_observers = {}
        self.processing_queue = asyncio.Queue()
        self.removal_queue = asyncio.Queue()
        self.processed_files = {}  # file_path -> {hash, last_modified, status}
        self.is_monitoring = False
        self.processing_task = None
        
        # Load connected folders from config
        self.folders_config_path = Path(config.get('folders.config_path', 'connected_folders.json'))
        self.load_connected_folders()
        
        # Supported file extensions
        self.supported_extensions = set(config.get('processing.supported_extensions', [
            '.pdf', '.docx', '.md', '.txt', '.doc', '.rtf'
        ]))
        
        # Processing settings
        self.batch_size = config.get('folders.batch_size', 10)
        self.scan_interval = config.get('folders.scan_interval_hours', 24)
        
    def load_connected_folders(self):
        """Load connected folders from configuration file."""
        try:
            if self.folders_config_path.exists():
                with open(self.folders_config_path, 'r') as f:
                    data = json.load(f)
                    self.connected_folders = set(data.get('folders', []))
                    self.processed_files = data.get('processed_files', {})
                logger.info(f"Loaded {len(self.connected_folders)} connected folders")
        except Exception as e:
            logger.warning(f"Failed to load connected folders: {e}")
            self.connected_folders = set()
            self.processed_files = {}
    
    def save_connected_folders(self):
        """Save connected folders to configuration file."""
        try:
            # Ensure directory exists
            self.folders_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'folders': list(self.connected_folders),
                'processed_files': self.processed_files,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.folders_config_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save connected folders: {e}")
    
    async def add_folder(self, folder_path: str) -> Dict[str, Any]:
        """Add a folder to be monitored and processed."""
        folder_path = os.path.abspath(folder_path)
        
        if not os.path.exists(folder_path):
            return {'success': False, 'error': 'Folder does not exist'}
        
        if not os.path.isdir(folder_path):
            return {'success': False, 'error': 'Path is not a directory'}
        
        if folder_path in self.connected_folders:
            return {'success': False, 'error': 'Folder already connected'}
        
        try:
            # Add folder to connected set
            self.connected_folders.add(folder_path)
            
            # Start monitoring if we're already running
            if self.is_monitoring:
                await self.start_folder_monitoring(folder_path)
            
            # Scan folder for existing documents
            discovered_files = await self.scan_folder(folder_path)
            
            # Save configuration
            self.save_connected_folders()
            
            logger.info(f"Added folder: {folder_path} ({len(discovered_files)} documents found)")
            
            return {
                'success': True,
                'folder_path': folder_path,
                'documents_found': len(discovered_files),
                'files': discovered_files
            }
            
        except Exception as e:
            logger.error(f"Failed to add folder {folder_path}: {e}")
            self.connected_folders.discard(folder_path)
            return {'success': False, 'error': str(e)}
    
    async def remove_folder(self, folder_path: str) -> Dict[str, Any]:
        """Remove a folder from monitoring."""
        folder_path = os.path.abspath(folder_path)
        
        if folder_path not in self.connected_folders:
            return {'success': False, 'error': 'Folder not connected'}
        
        try:
            # Stop monitoring
            if folder_path in self.folder_observers:
                self.folder_observers[folder_path].stop()
                del self.folder_observers[folder_path]
            
            # Remove from connected folders
            self.connected_folders.remove(folder_path)
            
            # Remove processed files from this folder
            files_to_remove = [f for f in self.processed_files.keys() if f.startswith(folder_path)]
            for file_path in files_to_remove:
                del self.processed_files[file_path]
            
            # Save configuration
            self.save_connected_folders()
            
            logger.info(f"Removed folder: {folder_path}")
            
            return {'success': True, 'folder_path': folder_path}
            
        except Exception as e:
            logger.error(f"Failed to remove folder {folder_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def scan_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """Scan a folder for documents and return file information."""
        discovered_files = []
        
        try:
            folder_path = Path(folder_path)
            
            # Recursively find all supported files
            for file_path in folder_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    try:
                        stat = file_path.stat()
                        file_info = {
                            'path': str(file_path),
                            'name': file_path.name,
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'extension': file_path.suffix.lower(),
                            'relative_path': str(file_path.relative_to(folder_path))
                        }
                        
                        # Check if file needs processing
                        needs_processing = self.file_needs_processing(str(file_path), stat.st_mtime)
                        file_info['needs_processing'] = needs_processing
                        
                        if needs_processing:
                            # Queue for processing
                            await self.processing_queue.put({
                                'file_path': str(file_path),
                                'action': 'process',
                                'priority': 'normal'
                            })
                        
                        discovered_files.append(file_info)
                        
                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error scanning folder {folder_path}: {e}")
        
        return discovered_files
    
    def file_needs_processing(self, file_path: str, modified_time: float) -> bool:
        """Check if a file needs to be processed or reprocessed."""
        if file_path not in self.processed_files:
            return True
        
        processed_info = self.processed_files[file_path]
        
        # Check if file was modified since last processing
        if modified_time > processed_info.get('last_modified', 0):
            return True
        
        # Check if processing failed last time
        if processed_info.get('status') != 'success':
            return True
        
        return False
    
    def queue_file_for_processing(self, file_path: str, action: str):
        """Queue a file for processing (called by file system events)."""
        if Path(file_path).suffix.lower() in self.supported_extensions:
            try:
                asyncio.create_task(self.processing_queue.put({
                    'file_path': file_path,
                    'action': 'process',
                    'priority': 'high',  # Real-time changes get high priority
                    'trigger': action
                }))
            except Exception as e:
                logger.warning(f"Failed to queue file for processing: {e}")
    
    def queue_file_for_removal(self, file_path: str):
        """Queue a file for removal from the vector store."""
        try:
            asyncio.create_task(self.removal_queue.put({
                'file_path': file_path,
                'action': 'remove'
            }))
        except Exception as e:
            logger.warning(f"Failed to queue file for removal: {e}")
    
    async def start_monitoring(self):
        """Start folder monitoring and background processing."""
        if self.is_monitoring:
            return
        
        logger.info("Starting folder monitoring...")
        self.is_monitoring = True
        
        # Start monitoring all connected folders
        for folder_path in self.connected_folders:
            await self.start_folder_monitoring(folder_path)
        
        # Start background processing task
        self.processing_task = asyncio.create_task(self.background_processor())
        
        logger.info(f"Monitoring {len(self.connected_folders)} folders")
    
    async def start_folder_monitoring(self, folder_path: str):
        """Start monitoring a specific folder."""
        try:
            if folder_path not in self.folder_observers:
                event_handler = DocumentFolderHandler(self)
                observer = Observer()
                observer.schedule(event_handler, folder_path, recursive=True)
                observer.start()
                
                self.folder_observers[folder_path] = observer
                logger.info(f"Started monitoring folder: {folder_path}")
                
        except Exception as e:
            logger.error(f"Failed to start monitoring folder {folder_path}: {e}")
    
    async def stop_monitoring(self):
        """Stop folder monitoring."""
        logger.info("Stopping folder monitoring...")
        self.is_monitoring = False
        
        # Stop all folder observers
        for observer in self.folder_observers.values():
            observer.stop()
            observer.join()
        
        self.folder_observers.clear()
        
        # Cancel processing task
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Folder monitoring stopped")
    
    async def background_processor(self):
        """Background task that processes queued files."""
        logger.info("Starting background document processor...")
        
        while self.is_monitoring:
            try:
                # Process files from queue
                await self.process_queued_files()
                
                # Process removals
                await self.process_queued_removals()
                
                # Brief pause to prevent excessive CPU usage
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background processor: {e}")
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info("Background processor stopped")

    async def process_queued_files(self):
        """Process files from the processing queue."""
        batch = []

        # Collect a batch of files to process
        try:
            while len(batch) < self.batch_size:
                try:
                    item = await asyncio.wait_for(self.processing_queue.get(), timeout=0.1)
                    batch.append(item)
                except asyncio.TimeoutError:
                    break
        except Exception as e:
            logger.warning(f"Error collecting batch: {e}")

        if not batch:
            return

        # Process the batch
        for item in batch:
            await self.process_single_file(item)

    async def process_single_file(self, item: Dict[str, Any]):
        """Process a single file."""
        file_path = item['file_path']

        try:
            if not os.path.exists(file_path):
                logger.warning(f"File no longer exists: {file_path}")
                return

            # Check if file is still supported
            if Path(file_path).suffix.lower() not in self.supported_extensions:
                return

            logger.info(f"Processing file: {file_path}")

            # Get file stats
            stat = os.stat(file_path)
            file_hash = self.calculate_file_hash(file_path)

            # Process the document
            if self.document_processor:
                try:
                    results = await self.document_processor.process_documents([file_path])

                    if results and len(results) > 0:
                        result = results[0]

                        # Update processed files record
                        self.processed_files[file_path] = {
                            'hash': file_hash,
                            'last_modified': stat.st_mtime,
                            'status': result.get('status', 'unknown'),
                            'processed_at': time.time(),
                            'chunks': result.get('chunks_created', 0),
                            'highlights': len(result.get('highlights', [])),
                            'error': result.get('error', None)
                        }

                        logger.info(f"Successfully processed: {file_path} ({result.get('chunks_created', 0)} chunks)")
                    else:
                        # Processing failed
                        self.processed_files[file_path] = {
                            'hash': file_hash,
                            'last_modified': stat.st_mtime,
                            'status': 'failed',
                            'processed_at': time.time(),
                            'error': 'No results returned'
                        }
                        logger.warning(f"Processing failed: {file_path}")

                except Exception as e:
                    # Processing error
                    self.processed_files[file_path] = {
                        'hash': file_hash,
                        'last_modified': stat.st_mtime,
                        'status': 'error',
                        'processed_at': time.time(),
                        'error': str(e)
                    }
                    logger.error(f"Error processing {file_path}: {e}")

            # Save progress periodically
            if len(self.processed_files) % 10 == 0:
                self.save_connected_folders()

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")

    async def process_queued_removals(self):
        """Process file removals from the removal queue."""
        try:
            while True:
                try:
                    item = await asyncio.wait_for(self.removal_queue.get(), timeout=0.1)
                    await self.remove_file_from_store(item['file_path'])
                except asyncio.TimeoutError:
                    break
        except Exception as e:
            logger.warning(f"Error processing removals: {e}")

    async def remove_file_from_store(self, file_path: str):
        """Remove a file from the vector store."""
        try:
            # Remove from processed files
            if file_path in self.processed_files:
                del self.processed_files[file_path]

            # Remove from vector store (if document processor supports it)
            if hasattr(self.document_processor, 'remove_document'):
                await self.document_processor.remove_document(file_path)

            logger.info(f"Removed file from store: {file_path}")

        except Exception as e:
            logger.error(f"Failed to remove file {file_path}: {e}")

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of file for change detection."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    async def rescan_all_folders(self) -> Dict[str, Any]:
        """Rescan all connected folders for new/changed documents."""
        logger.info("Rescanning all connected folders...")

        total_files = 0
        new_files = 0

        for folder_path in self.connected_folders:
            try:
                discovered_files = await self.scan_folder(folder_path)
                folder_new_files = sum(1 for f in discovered_files if f.get('needs_processing', False))

                total_files += len(discovered_files)
                new_files += folder_new_files

                logger.info(f"Scanned {folder_path}: {len(discovered_files)} files, {folder_new_files} new")

            except Exception as e:
                logger.error(f"Failed to rescan folder {folder_path}: {e}")

        # Save updated state
        self.save_connected_folders()

        return {
            'total_files': total_files,
            'new_files': new_files,
            'connected_folders': len(self.connected_folders)
        }

    def get_folder_stats(self) -> Dict[str, Any]:
        """Get statistics about connected folders and processed files."""
        stats = {
            'connected_folders': len(self.connected_folders),
            'total_processed_files': len(self.processed_files),
            'successful_files': sum(1 for f in self.processed_files.values() if f.get('status') == 'success'),
            'failed_files': sum(1 for f in self.processed_files.values() if f.get('status') in ['failed', 'error']),
            'total_chunks': sum(f.get('chunks', 0) for f in self.processed_files.values()),
            'total_highlights': sum(f.get('highlights', 0) for f in self.processed_files.values()),
            'folders': []
        }

        # Get stats per folder
        for folder_path in self.connected_folders:
            folder_files = [f for f in self.processed_files.keys() if f.startswith(folder_path)]
            folder_stats = {
                'path': folder_path,
                'files_count': len(folder_files),
                'successful_files': sum(1 for f in folder_files if self.processed_files[f].get('status') == 'success'),
                'exists': os.path.exists(folder_path)
            }
            stats['folders'].append(folder_stats)

        return stats

    def get_connected_folders(self) -> List[str]:
        """Get list of connected folders."""
        return list(self.connected_folders)

    def get_processed_files(self) -> Dict[str, Any]:
        """Get information about processed files."""
        return self.processed_files.copy()

    async def force_reprocess_folder(self, folder_path: str) -> Dict[str, Any]:
        """Force reprocessing of all files in a folder."""
        if folder_path not in self.connected_folders:
            return {'success': False, 'error': 'Folder not connected'}

        try:
            # Remove all processed files records for this folder
            files_to_remove = [f for f in self.processed_files.keys() if f.startswith(folder_path)]
            for file_path in files_to_remove:
                del self.processed_files[file_path]

            # Rescan the folder
            discovered_files = await self.scan_folder(folder_path)

            logger.info(f"Queued {len(discovered_files)} files for reprocessing in {folder_path}")

            return {
                'success': True,
                'files_queued': len(discovered_files),
                'folder_path': folder_path
            }

        except Exception as e:
            logger.error(f"Failed to force reprocess folder {folder_path}: {e}")
            return {'success': False, 'error': str(e)}
