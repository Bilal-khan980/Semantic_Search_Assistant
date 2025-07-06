#!/usr/bin/env python3
"""
Simple script to start the API server
"""

import uvicorn

if __name__ == "__main__":
    print("Starting Semantic Search Assistant API Server...")
    print("Server will be available at: http://127.0.0.1:8000")
    print("API docs will be available at: http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "api_service:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
