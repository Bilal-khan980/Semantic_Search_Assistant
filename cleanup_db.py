"""
Simple script to clean up the database if there are schema issues.
"""

import shutil
from pathlib import Path
from config import Config

def cleanup_database():
    """Remove the existing database to start fresh."""
    config = Config()
    db_path = Path(config.db_path)
    
    if db_path.exists():
        print(f"Removing existing database at: {db_path}")
        shutil.rmtree(db_path)
        print("Database cleaned up successfully!")
    else:
        print("No existing database found.")

if __name__ == "__main__":
    cleanup_database()
