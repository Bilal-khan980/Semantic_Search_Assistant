# Semantic Search Assistant - Complete Executable

A privacy-first desktop application for semantic search across your documents and Readwise highlights.

## 🚀 Quick Start

### For End Users (Ready-to-Run Application)

1. **Run the application**:

   - **Windows**: Double-click `start_semantic_search.bat`
   - **Mac/Linux**: Run `./start_semantic_search.sh` in terminal
   - **Manual**: Run `python semantic_search_launcher.py`

2. **The application will automatically**:

   - Start the Python backend server
   - Index documents in the `test_docs` folder
   - Open the web interface in your browser
   - Begin monitoring for new files

3. **Start using**:
   - **Search**: Use the web interface to search your documents
   - **Add documents**: Copy files to the `test_docs` folder
   - **Import Readwise**: Use the import feature for your highlights

### For Developers (Build from Source)

1. **Prerequisites**:

   - Python 3.8+ with pip
   - Node.js 16+ with npm
   - Git

2. **Clone and Build**:

   ```bash
   git clone <repository-url>
   cd Semantic_Search_Assistant
   python build_app.py
   ```

3. **Find your executable** in `electron-app/dist/`

## ✨ Features

### 🔍 Semantic Search

- **Natural language queries** - Search using everyday language
- **Intelligent ranking** - Results ranked by relevance and context
- **Real-time suggestions** - Get search suggestions as you type
- **Multiple file formats** - PDF, DOCX, Markdown, TXT support

### 📁 Automatic Indexing

- **Folder monitoring** - Automatically indexes new files
- **Background processing** - Non-blocking document processing
- **Real-time updates** - See indexing progress in real-time
- **Smart chunking** - Optimized text segmentation for better search

### 📚 Readwise Integration

- **Import highlights** - Import your Readwise markdown exports
- **Preserve metadata** - Maintains book titles, authors, and tags
- **Enhanced search** - Highlights get special ranking boost
- **Easy setup** - Simple folder selection for import

### ⚙️ Settings & Configuration

- **Customizable chunking** - Adjust chunk size and overlap
- **Search parameters** - Fine-tune similarity thresholds
- **Theme options** - Light, dark, or system theme
- **Notification preferences** - Control processing notifications

### 🖥️ Desktop Experience

- **Native desktop app** - Built with Electron for cross-platform support
- **Floating search window** - Quick access with global shortcuts
- **Drag & drop support** - Easy file management
- **System integration** - Native file dialogs and notifications

## 🎯 How to Use

### Initial Setup

1. **Launch the application** - The backend starts automatically
2. **Wait for indexing** - The app will index the `test_docs` folder
3. **Add your documents** - Copy files to `test_docs` or connect folders
4. **Import Readwise** (optional) - Use the Readwise tab to import highlights

### Searching

1. **Open search** - Use the search tab or press `Ctrl+K`
2. **Type your query** - Use natural language (e.g., "productivity tips")
3. **Browse results** - Click results to see full content
4. **Refine search** - Adjust similarity threshold if needed

### Managing Documents

1. **Connect folders** - Use the Folders tab to add document directories
2. **Monitor indexing** - See real-time progress in the status bar
3. **View documents** - Browse indexed documents in the Documents tab
4. **Remove documents** - Delete unwanted documents from the index

### Readwise Integration

1. **Export from Readwise** - Go to Readwise → Export → Markdown
2. **Download and extract** - Save the export to a folder
3. **Import in app** - Use the Readwise tab to select the folder
4. **Search highlights** - Your highlights are now searchable

## 🔧 Configuration

### Settings Panel

Access via the Settings tab to configure:

- **Appearance** - Theme and UI preferences
- **Search & Processing** - Chunk size, overlap, auto-indexing
- **Floating Window** - Always on top, auto-hide behavior
- **Notifications** - Processing and error notifications

### Advanced Configuration

Edit `config.json` for advanced settings:

- **Embedding model** - Change the AI model used for search
- **Search ranking** - Adjust ranking weights and boosts
- **File processing** - Modify supported file types and limits
- **API settings** - Change server host and port

## 🛠️ Technical Details

### Architecture

- **Backend**: Python with FastAPI, LanceDB, SentenceTransformers
- **Frontend**: React with Tailwind CSS and Framer Motion
- **Desktop**: Electron for native desktop integration
- **Search**: Vector similarity search with semantic understanding

### File Processing

- **PDF**: Text extraction with metadata preservation
- **DOCX**: Full document parsing including formatting
- **Markdown**: Native support with syntax highlighting
- **TXT**: Plain text with encoding detection

### Privacy & Security

- **Local processing** - All data stays on your machine
- **No cloud dependencies** - Works completely offline
- **Encrypted storage** - Vector embeddings stored locally
- **No telemetry** - No data collection or tracking

## 📋 System Requirements

### Minimum Requirements

- **OS**: Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **CPU**: 64-bit processor

### Recommended

- **RAM**: 8GB or more for large document collections
- **Storage**: SSD for faster indexing and search
- **CPU**: Multi-core processor for faster processing

## 🐛 Troubleshooting

### Common Issues

**Backend won't start**

- Check if Python is installed and accessible
- Verify all dependencies are installed
- Check the backend.log file for errors

**Indexing is slow**

- Reduce chunk size in settings
- Close other applications to free up RAM
- Check if antivirus is scanning files

**Search results are poor**

- Lower the similarity threshold
- Try different query phrasing
- Ensure documents are properly indexed

**Readwise import fails**

- Verify the export folder contains .md files
- Check file permissions
- Try importing smaller batches

### Getting Help

1. Check the application logs in the installation directory
2. Review the troubleshooting section in the full README
3. Create an issue on the project repository

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- **SentenceTransformers** for semantic embeddings
- **LanceDB** for vector storage
- **Electron** for desktop framework
- **React** for the user interface
- **Readwise** for highlight management inspiration
