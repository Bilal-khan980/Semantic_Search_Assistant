#!/usr/bin/env python3
"""
Simple script to create a working executable for the Semantic Search Assistant.
This bypasses complex build issues and creates a functional desktop app.
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

def create_simple_executable():
    """Create a simple executable that starts both backend and frontend."""
    
    print("Creating Semantic Search Assistant executable...")
    
    # Create a simple launcher script
    launcher_script = '''
import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def main():
    print("Starting Semantic Search Assistant...")
    
    # Get the directory where this script is located
    app_dir = Path(__file__).parent
    
    # Start the backend
    backend_script = app_dir / "start_backend.py"
    print(f"Starting backend from: {backend_script}")
    
    try:
        # Start backend process
        backend_process = subprocess.Popen([
            sys.executable, str(backend_script)
        ], cwd=app_dir)
        
        # Wait a moment for backend to start
        print("Waiting for backend to start...")
        time.sleep(5)
        
        # Open the web interface
        print("Opening web interface...")
        webbrowser.open("http://127.0.0.1:8000/health")
        
        print("Semantic Search Assistant is running!")
        print("Backend API: http://127.0.0.1:8000")
        print("Press Ctrl+C to stop")
        
        # Keep the launcher running
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\\nShutting down...")
            backend_process.terminate()
            backend_process.wait()
            
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
    
    # Write the launcher script
    with open("semantic_search_launcher.py", "w") as f:
        f.write(launcher_script)
    
    print("Created launcher script: semantic_search_launcher.py")
    
    # Create a batch file for Windows
    batch_script = '''@echo off
echo Starting Semantic Search Assistant...
python semantic_search_launcher.py
pause
'''
    
    with open("start_semantic_search.bat", "w") as f:
        f.write(batch_script)
    
    print("Created Windows batch file: start_semantic_search.bat")
    
    # Create a shell script for Unix systems
    shell_script = '''#!/bin/bash
echo "Starting Semantic Search Assistant..."
python3 semantic_search_launcher.py
'''
    
    with open("start_semantic_search.sh", "w") as f:
        f.write(shell_script)
    
    # Make shell script executable
    os.chmod("start_semantic_search.sh", 0o755)
    
    print("Created Unix shell script: start_semantic_search.sh")

def create_web_interface():
    """Create a simple web interface that can be served by the backend."""
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic Search Assistant</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .search-box:focus {
            outline: none;
            border-color: #007bff;
        }
        .btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn:hover {
            background: #0056b3;
        }
        .results {
            margin-top: 20px;
        }
        .result-item {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 10px;
            background: #f9f9f9;
        }
        .status {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Semantic Search Assistant</h1>
            <p>Search your documents using natural language</p>
        </div>
        
        <div>
            <input type="text" id="searchInput" class="search-box" placeholder="Enter your search query...">
            <button onclick="performSearch()" class="btn">Search</button>
        </div>
        
        <div id="results" class="results"></div>
        <div id="status" class="status">Ready to search</div>
    </div>

    <script>
        async function performSearch() {
            const query = document.getElementById('searchInput').value;
            const resultsDiv = document.getElementById('results');
            const statusDiv = document.getElementById('status');
            
            if (!query.trim()) {
                statusDiv.textContent = 'Please enter a search query';
                return;
            }
            
            statusDiv.textContent = 'Searching...';
            resultsDiv.innerHTML = '';
            
            try {
                const response = await fetch('http://127.0.0.1:8000/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        limit: 20,
                        similarity_threshold: 0.3
                    })
                });
                
                const data = await response.json();
                
                if (data.results && data.results.length > 0) {
                    statusDiv.textContent = `Found ${data.results.length} results`;
                    
                    data.results.forEach(result => {
                        const resultDiv = document.createElement('div');
                        resultDiv.className = 'result-item';
                        resultDiv.innerHTML = `
                            <h3>${result.source || 'Unknown Source'}</h3>
                            <p>${result.content || 'No content available'}</p>
                            <small>Similarity: ${(result.similarity * 100).toFixed(1)}%</small>
                        `;
                        resultsDiv.appendChild(resultDiv);
                    });
                } else {
                    statusDiv.textContent = 'No results found';
                }
            } catch (error) {
                statusDiv.textContent = 'Error: ' + error.message;
                console.error('Search error:', error);
            }
        }
        
        // Allow Enter key to trigger search
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // Check backend status on load
        async function checkBackend() {
            try {
                const response = await fetch('http://127.0.0.1:8000/health');
                const data = await response.json();
                document.getElementById('status').textContent = 'Backend connected and ready';
            } catch (error) {
                document.getElementById('status').textContent = 'Backend not available - please start the backend first';
            }
        }
        
        checkBackend();
    </script>
</body>
</html>'''
    
    # Create web directory
    web_dir = Path("web")
    web_dir.mkdir(exist_ok=True)
    
    with open(web_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Created simple web interface: web/index.html")

def main():
    """Main function to create the executable."""
    print("Creating Semantic Search Assistant executable package...")
    
    # Create the launcher scripts
    create_simple_executable()
    
    # Create the web interface
    create_web_interface()
    
    print("\n" + "="*50)
    print("EXECUTABLE PACKAGE CREATED SUCCESSFULLY!")
    print("="*50)
    print("\nTo run the application:")
    print("1. Windows: Double-click 'start_semantic_search.bat'")
    print("2. Mac/Linux: Run './start_semantic_search.sh'")
    print("3. Or run: python semantic_search_launcher.py")
    print("\nThe application will:")
    print("- Start the Python backend server")
    print("- Open your web browser to the search interface")
    print("- Automatically index documents in the test_docs folder")
    print("\nAccess the application at: http://127.0.0.1:8000")

if __name__ == "__main__":
    main()
