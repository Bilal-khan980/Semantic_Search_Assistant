# Semantic Search Assistant

A **privacy-first semantic search application** that allows you to upload documents, import Readwise highlights, and perform intelligent semantic search across all your content using AI embeddings - all processed locally on your machine.

## 🌟 Features

- **📄 Document Processing**: Upload and process PDF, DOCX, Markdown, and text files
- **📚 Readwise Integration**: Import highlights from Readwise markdown exports
- **🔍 Semantic Search**: AI-powered search using sentence transformers
- **🔒 Privacy-First**: All processing happens locally - no data sent to external services
- **⚡ Fast API**: RESTful API built with FastAPI
- **🎨 Modern UI**: React frontend with Tailwind CSS
- **🖥️ Desktop App**: Tauri integration for desktop application capabilities

## 🏗️ Architecture

### Backend (Python)

- **FastAPI** REST API server
- **LanceDB** vector database for embeddings storage
- **Sentence Transformers** for generating embeddings (all-MiniLM-L6-v2 model)
- **Document processing** pipeline for multiple file formats
- **Readwise integration** for importing highlights

### Frontend (React)

- **React + Vite** development setup
- **Tailwind CSS** for styling
- **Tauri** integration for desktop app capabilities
- **Axios** for API communication
- **Lucide React** for icons

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git** (for cloning the repository)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Semantic_Search_Assistant
   ```

2. **Set up Python backend**

   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   ```

3. **Set up React frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the Application

1. **Start the Backend API Server**

   ```bash
   python start_server.py
   ```

   The API will be available at: http://127.0.0.1:8000
   API documentation: http://127.0.0.1:8000/docs

2. **Start the Frontend Development Server**
   ```bash
   cd frontend
   npm start
   ```
   The frontend will be available at: http://127.0.0.1:1420

## 📖 Usage Guide

### Document Upload

1. Navigate to the "Documents" tab
2. Click "Upload Documents" or drag and drop files
3. Supported formats: PDF, DOCX, MD, TXT
4. Wait for processing to complete

### Readwise Import

1. Export your highlights from Readwise as Markdown
2. Navigate to the "Readwise" tab
3. Paste the markdown content
4. Click "Import Highlights"

### Semantic Search

1. Navigate to the "Search" tab
2. Enter your search query
3. Adjust similarity threshold if needed
4. View results with relevance scores

## 🔧 Configuration

The application uses `config.json` for configuration:

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
  "vector_store": {
    "db_path": "./data/vector_db",
    "similarity_threshold": 0.7
  }
}
```

## 🛠️ API Endpoints

The backend provides the following REST API endpoints:

### Health Check

- `GET /` - Basic status check
- `GET /health` - Detailed health check with database stats

### Document Management

- `POST /documents/upload` - Upload and process documents
- `GET /documents/processing/{task_id}` - Check processing status

### Search

- `POST /search` - Perform semantic search
- `GET /suggestions` - Get search suggestions

### Readwise Integration

- `POST /readwise/import` - Import Readwise highlights

### Statistics

- `GET /stats` - Get database statistics

## 📁 Project Structure

```
Semantic_Search_Assistant/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.json              # Application configuration
├── start_server.py          # Server startup script
├── main.py                  # Main backend logic
├── api_service.py           # FastAPI application
├── database.py              # Vector database operations
├── document_processor.py    # Document processing pipeline
├── search_engine.py         # Search functionality
├── readwise_importer.py     # Readwise integration
├── config.py               # Configuration management
├── data/                   # Database storage
│   └── vector_db/         # LanceDB files
├── sample_documents/       # Sample files for testing
└── frontend/              # React frontend
    ├── package.json       # Node.js dependencies
    ├── vite.config.js     # Vite configuration
    ├── src/              # React source code
    │   ├── App.js        # Main React component
    │   ├── components/   # React components
    │   └── services/     # API service layer
    └── public/           # Static assets
```

## 🧪 Testing

### Backend Testing

```bash
# Test backend functionality
python test_backend.py

# Test specific components
python main.py
```

### API Testing

```bash
# Test health endpoint
curl http://127.0.0.1:8000/health

# Test search endpoint
curl -X POST "http://127.0.0.1:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "productivity", "limit": 5}'
```

## 🔍 How It Works

1. **Document Processing**: Files are parsed and split into chunks using LangChain's text splitters
2. **Embedding Generation**: Each chunk is converted to a vector using Sentence Transformers
3. **Vector Storage**: Embeddings are stored in LanceDB for fast similarity search
4. **Semantic Search**: Query embeddings are compared with stored vectors using cosine similarity
5. **Result Ranking**: Results are ranked by similarity score and returned with metadata

## 🚨 Troubleshooting

### Common Issues

**Backend won't start:**

- Check Python version (3.8+ required)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is not in use

**Frontend won't start:**

- Check Node.js version (16+ required)
- Install dependencies: `cd frontend && npm install`
- Check port 1420 is not in use

**Search returns no results:**

- Ensure documents are processed successfully
- Lower similarity threshold in search
- Check embedding model is loaded correctly

**Memory issues:**

- Reduce batch_size in config.json
- Process fewer documents at once
- Use CPU instead of GPU if having issues

## 📝 License

This project is open source. Please check the license file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📞 Support

For support and questions, please open an issue in the repository.
