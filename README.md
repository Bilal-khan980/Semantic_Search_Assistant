# Semantic Search Assistant

A professional desktop application for intelligent document search with highlight capture and drag-and-drop functionality.

## 🚀 Quick Start

### For Development
1. Run `start_enhanced_admin.bat` to launch the application
2. The app will automatically create and monitor `Desktop/SemanticFiles` folder
3. Add your documents (PDF, Word, Text, Markdown) to the SemanticFiles folder

### For Client Distribution
1. Run `build_exe.bat` to create executable
2. Share the generated `build/exe.win-amd64-3.x` folder with client
3. Client follows instructions in `CLIENT_SETUP_INSTRUCTIONS.md`

## ✨ Features

### 🔍 **Smart Semantic Search**
- Searches through all documents in SemanticFiles folder
- AI-powered semantic matching (finds relevant content even without exact word matches)
- Real-time indexing of new documents

### ✨ **Highlight Text Capture**
- Click "Highlight Text" button, then select text anywhere
- Works with web browsers, PDFs, Word documents, etc.
- Add custom tags and notes to captured highlights
- Captured highlights get priority in search results

### 📝 **Drag & Drop Integration**
- Drag search results directly into Word, email, or any text editor
- Automatic citation formatting: "content (Source: Document Name, p. 42)"
- Works with active cursor position in documents

### 🎯 **Context-Aware Suggestions**
- Monitors typing in Word documents
- Provides real-time content suggestions based on what you're writing
- Floating window stays above all applications

## 📁 File Structure

### Core Application Files
- `enhanced_global_monitor.py` - Main application with GUI
- `main.py` - Backend service with document processing
- `search_engine.py` - Semantic search functionality
- `document_processor.py` - Document parsing and indexing
- `folder_manager.py` - File monitoring and management

### Configuration
- `config.json` - Application settings
- `requirements.txt` - Python dependencies
- `start_enhanced_admin.bat` - Launch script

### Build & Distribution
- `setup.py` - Executable build configuration
- `build_exe.bat` - Build script for creating .exe
- `CLIENT_SETUP_INSTRUCTIONS.md` - Client setup guide

## 🛠 Technical Details

### Supported File Types
- PDF files (.pdf)
- Word documents (.docx, .doc)
- Text files (.txt)
- Markdown files (.md)

### Dependencies
- **AI/ML**: sentence-transformers, lancedb
- **Document Processing**: PyPDF2, PyMuPDF, python-docx
- **Desktop Integration**: pywin32, pyautogui, keyboard
- **Backend**: FastAPI, uvicorn
- **File Monitoring**: watchdog

### Data Storage
- Vector database: LanceDB (stored in `data/vector_db`)
- Highlights: JSON files in `highlights/` folder
- Configuration: `connected_folders.json`

## 🎯 Client Deployment

1. **Build executable**: Run `build_exe.bat`
2. **Package for client**: Copy entire `build/exe.win-amd64-3.x` folder
3. **Client setup**: 
   - Create `SemanticFiles` folder on Desktop
   - Run `SemanticSearchAssistant.exe`
   - Add documents to SemanticFiles folder

## 🔧 Development

### Running in Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Start application
start_enhanced_admin.bat
```

### Building Executable
```bash
# Install build tools
pip install cx_Freeze

# Build executable
python setup.py build
```

## 📋 System Requirements
- Windows 10/11
- Python 3.8+ (for development)
- 4GB RAM minimum
- 1GB free disk space

## 🆘 Troubleshooting

**Application won't start:**
- Ensure SemanticFiles folder exists on Desktop
- Run as Administrator
- Check Windows Defender settings

**No search results:**
- Verify documents are in Desktop/SemanticFiles
- Wait for initial indexing to complete
- Check supported file formats

**Drag & drop issues:**
- Ensure target application is active
- Click in target document first
- Position cursor where you want text inserted
