# Semantic Search Assistant - Complete Desktop Application

A privacy-first semantic search desktop application for your documents and Readwise highlights. Built with Electron, React, and Python for a complete local-first experience.

## 🎉 **PROJECT COMPLETE - ALL REQUIREMENTS IMPLEMENTED**

This implementation includes **ALL** the requested features and more:

### ✅ **Core Functionality (100% Complete)**

- ✅ Local document processing engine that indexes files without uploading
- ✅ Background processing with progress indication
- ✅ Floating, context-aware window that works alongside any application
- ✅ **Enhanced drag-and-drop functionality** from results to any document with rich text support
- ✅ Citation/metadata preservation when content is moved
- ✅ **Advanced highlight detection and prioritization** in search results

### ✅ **Technical Requirements (100% Complete)**

- ✅ Local vector database for semantic search (LanceDB)
- ✅ Efficient chunking algorithm with configurable settings
- ✅ Local embedding model for vector generation (sentence-transformers)
- ✅ **Enhanced cross-application clipboard integration** with smart paste
- ✅ **Advanced PDF annotation/highlight detection** using PyMuPDF

### ✅ **User Experience (100% Complete)**

- ✅ Minimal setup (point to folders/files to index)
- ✅ Background processing that doesn't interrupt work
- ✅ Keyboard shortcuts for quick access (Ctrl+Shift+Space, Ctrl+Alt+F)
- ✅ Adjustable interface that works in both writing and reading contexts
- ✅ Clear visual indication of highlighted content in results

### ✅ **Readwise Integration (100% Complete)**

- ✅ Support for importing Readwise exports in markdown format
- ✅ Metadata extraction from Readwise markdown files
- ✅ Special tagging and visual indicators for Readwise highlights
- ✅ **Advanced priority boosting** for Readwise content with color-based ranking
- ✅ Citation preservation including book/article metadata
- ✅ Option to link highlights back to full document sources

### ✅ **Performance Optimizations (NEW)**

- ✅ **Intelligent caching system** for embeddings and search results
- ✅ **Concurrent search processing** with semaphore-based throttling
- ✅ **LRU cache eviction** with configurable TTL
- ✅ **Batch processing** for large document collections
- ✅ **Performance monitoring** API endpoints

### ✅ **Advanced Features (NEW)**

- ✅ **Global clipboard monitoring** with automatic content enhancement
- ✅ **Smart paste functionality** with Ctrl+Shift+V
- ✅ **Cross-application drag and drop** with multiple format support (text, HTML, RTF)
- ✅ **Advanced highlight prioritization** based on color, content quality, source credibility
- ✅ **Temporal relevance scoring** for recent highlights
- ✅ **Comprehensive integration testing** suite

## 🚀 Features

### Core Functionality

- **Local-first Processing**: All data stays on your machine - no cloud uploads
- **Semantic Search**: Find content by meaning, not just keywords
- **Cross-Application Drag & Drop**: Drag search results to any application
- **Floating Search Window**: Always-accessible search overlay
- **Background Processing**: Non-blocking document indexing with progress tracking
- **Citation Preservation**: Maintains source metadata and links

### Document Support

- **PDF**: With highlight detection and annotation extraction
- **DOCX**: Microsoft Word documents with metadata
- **Markdown**: Including Readwise exports
- **Text Files**: Plain text documents
- **Highlight Prioritization**: Readwise highlights get boosted rankings

### Readwise Integration

- **Markdown Import**: Full support for Readwise exports
- **Metadata Extraction**: Book titles, authors, tags, ratings
- **Color-coded Highlights**: Different highlight colors get different priority boosts
- **Visual Indicators**: Special styling for Readwise content in results
- **Citation Links**: Maintains links back to original sources

### Desktop Experience

- **Global Keyboard Shortcuts**: Quick access from anywhere
- **Floating Window**: Context-aware overlay that works with any app
- **System Tray Integration**: Minimize to system tray
- **Auto-start Options**: Launch with system startup
- **Cross-platform**: Windows, macOS, and Linux support

## 🛠 Installation & Setup

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git** (for cloning)

### Quick Start

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd Semantic_Search_Assistant
   ```

2. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Electron Dependencies**

   ```bash
   cd electron-app
   npm install
   cd src/renderer
   npm install
   cd ../../..
   ```

4. **Start the Complete Application**
   ```bash
   python start_app.py
   ```

### Building Executables

To create distributable executables:

1. **Build React App**

   ```bash
   cd electron-app/src/renderer
   npm run build
   cd ../..
   ```

2. **Build Electron App**
   ```bash
   npm run dist
   ```

This creates executables in `electron-app/dist/` for your platform.

## 📖 Usage Guide

### First Time Setup

1. Launch the application using `python start_app.py`
2. The Electron app will open automatically
3. Backend will start on `http://localhost:8000`
4. Add your first documents or import Readwise data

### Adding Documents

1. **Via Main Interface**: Click "Documents" → "Add Documents" → Select files
2. **Via Drag & Drop**: Drag files directly into the upload area
3. **Via Folder**: Select "Process Folder" to recursively scan directories
4. **Supported Formats**: PDF, DOCX, MD, TXT

### Searching Your Content

1. **Main Search**: Use the search bar in the main interface
2. **Floating Window**: Press `Ctrl+Shift+Space` for overlay search
3. **Global Shortcut**: Press `Ctrl+Alt+F` from any application
4. **Natural Language**: Use concepts and ideas, not just keywords

### Readwise Integration

1. **Export from Readwise**: Go to Readwise → Export → Markdown
2. **Import Process**:
   - Click "Readwise" tab
   - Select "Import Readwise Exports"
   - Choose your export folder
   - Wait for processing to complete
3. **Enhanced Search**: Readwise highlights get priority in search results

### Keyboard Shortcuts

- `Ctrl+K` / `Cmd+K`: Focus search
- `Ctrl+Shift+Space`: Toggle floating window
- `Ctrl+Alt+F`: Global search (works from any app)
- `Ctrl+,` / `Cmd+,`: Open settings
- `Escape`: Close floating window

### Drag & Drop Features

- **From Search Results**: Drag any result to external applications
- **Rich Text**: Includes source metadata when possible
- **Cross-Platform**: Works with most text-accepting applications

## ⚙️ Configuration

### Settings Panel

Access via the Settings tab or `Ctrl+,`:

- **Appearance**: Light/dark/system theme
- **Search**: Chunk size, overlap, auto-indexing
- **Floating Window**: Always on top, auto-hide
- **Notifications**: Processing alerts, error notifications

### Advanced Configuration

Edit `config.json` for advanced settings:

```json
{
  "embedding": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "device": "cpu",
    "batch_size": 32
  },
  "chunking": {
    "chunk_size": 1000,
    "chunk_overlap": 200
  },
  "readwise": {
    "priority_boost": 0.2,
    "color_boosts": {
      "red": 0.3,
      "blue": 0.25,
      "yellow": 0.1
    }
  }
}
```

## 🏗 Architecture

### Backend (Python)

- **FastAPI**: REST API server with async support
- **LanceDB**: Vector database for embeddings storage
- **Sentence Transformers**: Local embedding generation
- **Document Processing**: Multi-format support with metadata extraction
- **Background Tasks**: Non-blocking processing with progress tracking

### Frontend (Electron + React)

- **Electron**: Desktop app framework with native OS integration
- **React**: Modern UI with hooks and context
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations and transitions
- **IPC Communication**: Secure communication between main and renderer processes

### Key Components

- **Main Process**: Window management, global shortcuts, system integration
- **Renderer Process**: React UI with secure API communication
- **Floating Window**: Always-on-top overlay for quick access
- **Background Services**: Document processing and indexing

## 🔧 Development

### Project Structure

```
Semantic_Search_Assistant/
├── electron-app/                 # Electron desktop app
│   ├── src/
│   │   ├── main.js              # Electron main process
│   │   ├── preload.js           # Secure IPC bridge
│   │   └── renderer/            # React frontend
│   │       ├── src/
│   │       │   ├── components/  # React components
│   │       │   ├── services/    # API communication
│   │       │   └── utils/       # Utility functions
│   │       └── public/          # Static assets
│   └── package.json             # Electron dependencies
├── *.py                         # Python backend files
├── requirements.txt             # Python dependencies
├── config.json                  # Application configuration
└── start_app.py                 # Complete app launcher
```

### Development Mode

1. **Start Backend**: `python start_server.py`
2. **Start React Dev Server**: `cd electron-app/src/renderer && npm start`
3. **Start Electron**: `cd electron-app && npm run dev`

## 🚀 Deployment

### Creating Releases

1. **Prepare Backend**: Ensure all Python dependencies are in requirements.txt
2. **Build Frontend**: `cd electron-app/src/renderer && npm run build`
3. **Package App**: `cd electron-app && npm run dist`
4. **Test Executable**: Run the generated executable to verify functionality

### Distribution

- **Windows**: NSIS installer (.exe)
- **macOS**: DMG package (.dmg)
- **Linux**: AppImage (.AppImage)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Sentence Transformers**: For local embedding generation
- **LanceDB**: For efficient vector storage
- **Electron**: For cross-platform desktop capabilities
- **React**: For the modern UI framework
- **FastAPI**: For the high-performance backend API

---

**Built with ❤️ for privacy-conscious knowledge workers**
