#!/usr/bin/env python3
"""
Setup Test Documents Script
Automatically indexes all files in test_docs and sample_documents directories
"""

import os
import sys
import asyncio
import logging
import requests
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestDocumentSetup:
    """Setup and index test documents for the semantic search system."""

    def __init__(self):
        self.api_base_url = "http://127.0.0.1:8000"
        self.session = requests.Session()

    def check_backend_health(self):
        """Check if the backend API is running."""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Backend API is running and healthy")
                return True
            else:
                logger.error(f"❌ Backend API returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cannot connect to backend API: {e}")
            logger.error("💡 Make sure the backend server is running with: python start_server.py")
            return False

    def setup_test_documents(self):
        """Process and index all test documents."""
        logger.info("🚀 Setting up test documents for semantic search...")

        # Check backend health first
        if not self.check_backend_health():
            return False

        # Define directories to process
        test_directories = [
            Path("test_docs"),
            Path("sample_documents")
        ]

        total_processed = 0

        for directory in test_directories:
            if directory.exists():
                logger.info(f"📁 Processing directory: {directory}")
                processed_count = self.process_directory(directory)
                total_processed += processed_count
            else:
                logger.warning(f"⚠️ Directory not found: {directory}")

        logger.info(f"✅ Setup complete! Processed {total_processed} documents")
        logger.info("🔍 Documents are now available for semantic search")

        # Display some statistics
        self.show_database_stats()
        return True

    def process_directory(self, directory_path):
        """Process all supported files in a directory."""
        supported_extensions = {'.txt', '.md', '.pdf', '.docx'}
        processed_count = 0

        # Collect all files to process
        files_to_process = []
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files_to_process.append(str(file_path.absolute()))

        if not files_to_process:
            logger.info(f"No supported files found in {directory_path}")
            return 0

        logger.info(f"Found {len(files_to_process)} files to process")

        # Process files using the backend API
        try:
            response = self.session.post(
                f"{self.api_base_url}/documents/upload",
                json={"file_paths": files_to_process},
                timeout=300  # 5 minutes timeout for processing
            )

            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')

                if task_id:
                    # Poll for completion
                    processed_count = self.wait_for_processing_completion(task_id)
                else:
                    # Immediate processing
                    processed_count = len(files_to_process)
                    logger.info(f"✅ Successfully processed {processed_count} files")
            else:
                logger.error(f"❌ Failed to process files: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error calling backend API: {e}")

        return processed_count

    def wait_for_processing_completion(self, task_id):
        """Wait for document processing to complete and return count of processed files."""
        logger.info(f"⏳ Waiting for processing completion (Task ID: {task_id})")
        processed_count = 0

        while True:
            try:
                response = self.session.get(f"{self.api_base_url}/documents/processing/{task_id}")

                if response.status_code == 200:
                    status = response.json()

                    if status.get('status') == 'completed':
                        processed_count = status.get('processed_count', 0)
                        logger.info(f"✅ Processing completed! {processed_count} files processed")
                        break
                    elif status.get('status') == 'failed':
                        logger.error(f"❌ Processing failed: {status.get('error', 'Unknown error')}")
                        break
                    else:
                        # Still processing
                        progress = status.get('progress', 0)
                        message = status.get('message', 'Processing...')
                        logger.info(f"⏳ Progress: {progress:.1f}% - {message}")
                        time.sleep(2)
                else:
                    logger.error(f"❌ Error checking status: {response.status_code}")
                    break

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error checking processing status: {e}")
                break

        return processed_count

    def show_database_stats(self):
        """Display database statistics."""
        try:
            response = self.session.get(f"{self.api_base_url}/stats")

            if response.status_code == 200:
                stats = response.json()
                logger.info("📊 Database Statistics:")
                logger.info(f"   - Total documents: {stats.get('total_documents', 0)}")
                logger.info(f"   - Total chunks: {stats.get('total_chunks', 0)}")
                logger.info(f"   - Database size: {stats.get('database_size', 'Unknown')}")
            else:
                logger.warning(f"Could not retrieve database stats: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not retrieve database stats: {e}")

    def test_search(self):
        """Test the search functionality with sample queries."""
        logger.info("🔍 Testing search functionality...")

        test_queries = [
            "productivity techniques",
            "semantic search features",
            "document processing",
            "time management"
        ]

        for query in test_queries:
            try:
                logger.info(f"🔎 Testing query: '{query}'")

                response = self.session.post(
                    f"{self.api_base_url}/search",
                    json={"query": query, "limit": 3}
                )

                if response.status_code == 200:
                    results = response.json().get('results', [])

                    if results:
                        logger.info(f"   ✅ Found {len(results)} results")
                        for i, result in enumerate(results, 1):
                            score = result.get('score', 0)
                            source = result.get('source', 'Unknown')
                            logger.info(f"   {i}. Score: {score:.3f} | Source: {Path(source).name}")
                    else:
                        logger.info("   ❌ No results found")
                else:
                    logger.error(f"   ❌ Search failed: {response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.error(f"   ❌ Search failed: {e}")

def main():
    """Main function to run the test document setup."""
    try:
        setup = TestDocumentSetup()

        # Setup test documents
        success = setup.setup_test_documents()

        if success:
            # Test search functionality
            setup.test_search()

            logger.info("🎉 Test document setup completed successfully!")
            logger.info("💡 You can now search for documents in the application")
            logger.info("🖥️ Open the desktop application to see the indexed documents")
        else:
            logger.error("❌ Setup failed - please check the backend server")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
