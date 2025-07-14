#!/usr/bin/env python3
"""
Startup script for the Semantic Search Assistant backend.
This script is used by the Electron app to start the Python backend.
"""

import sys
import os
import asyncio
import logging
import signal
import uvicorn
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main entry point for the backend."""
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Starting Semantic Search Assistant backend...")
        
        # Change to the script directory
        os.chdir(current_dir)
        
        # Start the FastAPI server
        uvicorn.run(
            "api_service:app",
            host="127.0.0.1",
            port=8000,
            log_level="info",
            access_log=True,
            reload=False  # Disable reload in production
        )
        
    except Exception as e:
        logger.error(f"Failed to start backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
