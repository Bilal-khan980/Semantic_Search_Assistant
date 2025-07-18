#!/usr/bin/env python3
"""
Clear All Indexed Data Script
Removes all previously indexed files, vector database, and tracking data.
"""

import os
import shutil
import json
from pathlib import Path

def clear_all_data():
    """Clear all indexed data and reset the system."""
    print("🗑️ Clearing All Previously Indexed Data...")
    print("=" * 50)
    
    # 1. Clear LanceDB data
    lancedb_path = "data/lancedb"
    if Path(lancedb_path).exists():
        try:
            shutil.rmtree(lancedb_path)
            print(f"✅ Removed LanceDB data: {lancedb_path}")
        except Exception as e:
            print(f"❌ Error removing LanceDB: {e}")
    else:
        print(f"📁 LanceDB data not found: {lancedb_path}")
    
    # 2. Clear vector database files
    vector_db_files = [
        "data/documents.lance",
        "data/vector_store.db",
        "data/embeddings.db"
    ]
    
    for db_file in vector_db_files:
        if Path(db_file).exists():
            try:
                if Path(db_file).is_dir():
                    shutil.rmtree(db_file)
                else:
                    os.remove(db_file)
                print(f"✅ Removed database file: {db_file}")
            except Exception as e:
                print(f"❌ Error removing {db_file}: {e}")
        else:
            print(f"📁 Database file not found: {db_file}")
    
    # 3. Clear auto-indexer tracking
    index_files = [
        "data/indexed_files.json",
        "data/file_index.json",
        "indexed_files.json"
    ]
    
    for index_file in index_files:
        if Path(index_file).exists():
            try:
                os.remove(index_file)
                print(f"✅ Removed index tracking: {index_file}")
            except Exception as e:
                print(f"❌ Error removing {index_file}: {e}")
        else:
            print(f"📁 Index file not found: {index_file}")
    
    # 4. Clear document chunks cache
    cache_dirs = [
        "data/chunks",
        "data/cache",
        "cache"
    ]
    
    for cache_dir in cache_dirs:
        if Path(cache_dir).exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Removed cache directory: {cache_dir}")
            except Exception as e:
                print(f"❌ Error removing {cache_dir}: {e}")
        else:
            print(f"📁 Cache directory not found: {cache_dir}")
    
    # 5. Clear any temporary files
    temp_files = [
        "temp_embeddings.npy",
        "temp_index.faiss",
        "document_store.pkl"
    ]
    
    for temp_file in temp_files:
        if Path(temp_file).exists():
            try:
                os.remove(temp_file)
                print(f"✅ Removed temp file: {temp_file}")
            except Exception as e:
                print(f"❌ Error removing {temp_file}: {e}")
    
    # 6. Clear logs (optional)
    log_files = [
        "app.log",
        "backend.log",
        "indexer.log"
    ]
    
    for log_file in log_files:
        if Path(log_file).exists():
            try:
                os.remove(log_file)
                print(f"✅ Removed log file: {log_file}")
            except Exception as e:
                print(f"❌ Error removing {log_file}: {e}")
    
    # 7. Recreate necessary directories
    necessary_dirs = [
        "data",
        "test_docs"
    ]
    
    for dir_path in necessary_dirs:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"📁 Ensured directory exists: {dir_path}")
    
    print("\n" + "=" * 50)
    print("✅ ALL DATA CLEARED SUCCESSFULLY!")
    print("🚀 System is now ready for fresh start")
    print("📄 Add your documents to test_docs/ folder")
    print("🔄 Start the backend to begin auto-indexing")

if __name__ == "__main__":
    # Confirm before clearing
    print("⚠️  WARNING: This will delete ALL indexed data!")
    print("📋 This includes:")
    print("   • Vector database")
    print("   • Index tracking files") 
    print("   • Cached embeddings")
    print("   • All processed chunks")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        clear_all_data()
    else:
        print("❌ Operation cancelled")
