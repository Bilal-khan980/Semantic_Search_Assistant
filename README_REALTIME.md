# Real-time Semantic Search Assistant

A **desktop application** that provides **real-time text suggestions** as you type in any text editor. Features **letter-by-letter search** and **spacebar clearing** functionality.

## 🚀 Quick Start

**Run the application:**

```bash
python run_realtime_app.py
```

**Or use the Windows batch file:**
```bash
start_realtime_app.bat
```

## ✨ Key Features

### 🔍 **Real-time Text Monitoring**
- Monitors typing in **any text application** (Notepad, Word, VS Code, etc.)
- Triggers search on **every letter** you type
- Works across all text editors and word processors

### ⌨️ **Smart Search Behavior**
- **Letter-by-letter search**: Each character triggers an instant search
- **Spacebar clearing**: Press space to clear search and start new word
- **Backspace support**: Remove letters to refine search
- **Instant results**: See suggestions appear as you type

### 📋 **Easy Copy & Paste**
- Double-click any result to copy to clipboard
- Results include similarity scores and source information
- One-click copying for seamless workflow

### 🌐 **Dual Interface**
- **Desktop GUI**: Native Windows application with real-time monitoring
- **Web Interface**: Full-featured web UI at `http://127.0.0.1:8000/static/app.html`

## 📖 How to Use

### 1. **Start the Application**
```bash
python run_realtime_app.py
```

### 2. **Add Your Documents**
- Click "Add Documents" in the GUI
- Select your text files, PDFs, Word docs, or Markdown files
- Documents will be indexed automatically

### 3. **Start Real-time Monitoring**
- Click "Start Monitoring" button
- The app will now monitor your typing

### 4. **Type in Any Text Editor**
- Open Notepad, Word, VS Code, or any text application
- Start typing a word
- Watch suggestions appear for each letter!

### 5. **Use the Results**
- See real-time suggestions in the app window
- Double-click any result to copy it to clipboard
- Press **SPACEBAR** to clear search and start a new word

## 🎯 Example Workflow

1. **Type "artif"** → See results about "artificial intelligence"
2. **Type "i"** → Results refine to "artificial intelligence" content
3. **Type "c"** → Results show "artificial" content
4. **Press SPACEBAR** → Search clears, ready for next word
5. **Type "mach"** → See results about "machine learning"

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Windows OS (for keyboard monitoring)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Test Installation
```bash
python test_realtime_app.py
```

## 🏗️ Build Desktop Executable

Create a standalone executable:

```bash
python build_executable.py
```

This creates a portable package in `SemanticSearchAssistant_Portable/` with:
- `SemanticSearchAssistant.exe` - The main executable
- All necessary files and dependencies
- Sample documents for testing

## 📁 Project Structure

```
Semantic_Search_Assistant/
├── 🚀 Main Application
│   ├── app.py                    # Main GUI application
│   ├── run_realtime_app.py       # Simple launcher
│   └── start_realtime_app.bat    # Windows batch launcher
│
├── 🔧 Backend Components
│   ├── api_service.py            # FastAPI backend
│   ├── document_processor.py     # Document processing
│   ├── search_engine.py          # Vector search engine
│   └── database.py               # Vector database
│
├── 🌐 Web Interface
│   ├── web/app.html              # Complete web UI
│   └── web/index.html            # Simple web UI
│
├── 🛠️ Build Tools
│   ├── build_executable.py       # Create desktop executable
│   ├── test_realtime_app.py      # Test all components
│   └── cleanup_project.py        # Remove unnecessary files
│
└── 📄 Configuration
    ├── config.json               # App configuration
    ├── requirements.txt          # Python dependencies
    └── test_docs/                # Sample documents
```

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "search": {
    "similarity_threshold": 0.3,
    "max_results": 10
  },
  "monitoring": {
    "enabled_applications": ["notepad", "word", "code", "sublime"]
  }
}
```

## 🔧 Supported Applications

The real-time monitoring works with:

- **Text Editors**: Notepad, Notepad++, Sublime Text, VS Code, Atom
- **Word Processors**: Microsoft Word, WordPad, LibreOffice Writer
- **Note Apps**: Obsidian, Notion, Typora, Bear
- **IDEs**: Visual Studio Code, Vim, Emacs
- **Any text input field** in most applications

## 🐛 Troubleshooting

### App Won't Start
- Run as administrator
- Check if Python is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`

### Monitoring Not Working
- Make sure you clicked "Start Monitoring"
- Try running as administrator
- Check if antivirus is blocking keyboard monitoring

### No Search Results
- Add documents first using "Add Documents"
- Wait for indexing to complete
- Check that documents contain text content

### Port 8000 Already in Use
- Close other applications using port 8000
- Or change port in `api_service.py`

## 🎯 Performance Tips

1. **Start with small document collections** (< 100 files)
2. **Use SSD storage** for better vector database performance
3. **Close unnecessary applications** during heavy indexing
4. **Run as administrator** for best keyboard monitoring

## 🔒 Privacy & Security

- **100% Local Processing**: No data sent to external servers
- **Offline Capable**: Works completely offline
- **Your Data Stays Local**: All processing happens on your computer
- **Open Source**: Full transparency of all operations

## 🚀 Next Steps

1. **Test the app**: `python test_realtime_app.py`
2. **Run the app**: `python run_realtime_app.py`
3. **Add your documents** and start typing!
4. **Build executable**: `python build_executable.py`
5. **Clean up project**: `python cleanup_project.py`

## 📞 Support

If you encounter issues:

1. Run the test script: `python test_realtime_app.py`
2. Check the logs in `app.log`
3. Make sure all dependencies are installed
4. Try running as administrator

---

**Enjoy your real-time semantic search experience! 🎉**
