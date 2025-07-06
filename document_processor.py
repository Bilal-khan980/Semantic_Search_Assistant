"""
Document processing module for extracting text and metadata from various file formats.
Supports PDF, DOCX, Markdown, and plain text files.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import mimetypes
# Document processing libraries
import PyPDF2
from docx import Document
import markdown
from bs4 import BeautifulSoup

# Text processing
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentChunk:
    """Represents a chunk of processed document content."""
    
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata
        self.chunk_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique ID for this chunk."""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()
        return f"chunk_{content_hash[:12]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for storage."""
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'metadata': self.metadata
        }

class DocumentProcessor:
    """Main document processing class."""
    
    def __init__(self, config):
        self.config = config
        self.text_splitter = None
        self.supported_processors = {
            '.pdf': self._process_pdf,
            '.docx': self._process_docx,
            '.md': self._process_markdown,
            '.txt': self._process_text
        }
    
    async def initialize(self):
        """Initialize the document processor."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.get('chunking.separators', ["\n\n", "\n", " ", ""])
        )
        logger.info("Document processor initialized")
    
    async def process_file(self, file_path: str) -> List[DocumentChunk]:
        """Process a single file and return chunks."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        max_size = self.config.get('processing.max_file_size_mb', 100)
        if file_size_mb > max_size:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB > {max_size}MB")
        
        # Check file extension
        extension = file_path.suffix.lower()
        if extension not in self.config.supported_extensions:
            raise ValueError(f"Unsupported file type: {extension}")
        
        # Extract text and metadata
        text_content, metadata = await self._extract_content(file_path)
        
        # Create chunks
        chunks = await self._create_chunks(text_content, metadata)
        
        logger.info(f"Processed {file_path.name}: {len(chunks)} chunks created")
        return chunks
    
    async def _extract_content(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Extract text content and metadata from file."""
        extension = file_path.suffix.lower()
        processor = self.supported_processors.get(extension)
        
        if not processor:
            raise ValueError(f"No processor for file type: {extension}")
        
        # Base metadata
        metadata = {
            'source': str(file_path),
            'filename': file_path.name,
            'extension': extension,
            'file_size': file_path.stat().st_size,
            'modified_time': file_path.stat().st_mtime
        }
        
        # Extract content using appropriate processor
        content, extra_metadata = await processor(file_path)
        metadata.update(extra_metadata)
        
        return content, metadata
    
    async def _process_pdf(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Process PDF file and extract text."""
        content = ""
        metadata = {'pages': 0, 'highlights': []}
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata['pages'] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    
                    # Extract highlights if available
                    if self.config.get('processing.extract_highlights', True):
                        highlights = self._extract_pdf_highlights(page, page_num + 1)
                        metadata['highlights'].extend(highlights)
                
                # Extract PDF metadata
                if pdf_reader.metadata:
                    metadata.update({
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', '')
                    })
        
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise
        
        return content.strip(), metadata
    
    def _extract_pdf_highlights(self, page, page_num: int) -> List[Dict[str, Any]]:
        """Extract highlights from PDF page (simplified implementation)."""
        highlights = []
        
        # This is a simplified implementation
        # In a real application, you'd use more sophisticated PDF parsing
        # to extract actual annotations and highlights
        
        try:
            if '/Annots' in page:
                # PDF has annotations - could contain highlights
                # This would require more complex PDF parsing
                pass
        except:
            pass
        
        return highlights
    
    async def _process_docx(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Process DOCX file and extract text."""
        try:
            doc = Document(file_path)
            
            # Extract text from paragraphs
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            
            # Extract metadata
            metadata = {
                'paragraphs': len(doc.paragraphs),
                'title': doc.core_properties.title or '',
                'author': doc.core_properties.author or '',
                'subject': doc.core_properties.subject or '',
                'created': str(doc.core_properties.created) if doc.core_properties.created else ''
            }
            
            return content.strip(), metadata
            
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {str(e)}")
            raise
    
    async def _process_markdown(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Process Markdown file and extract text."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
            
            # Convert markdown to HTML then extract text
            html = markdown.markdown(md_content)
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            
            # Extract markdown-specific metadata
            metadata = {
                'format': 'markdown',
                'headers': self._extract_markdown_headers(md_content),
                'links': self._extract_markdown_links(md_content)
            }
            
            return text_content.strip(), metadata
            
        except Exception as e:
            logger.error(f"Error processing Markdown {file_path}: {str(e)}")
            raise
    
    async def _process_text(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Process plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            metadata = {
                'format': 'text',
                'lines': len(content.splitlines()),
                'words': len(content.split())
            }
            
            return content.strip(), metadata
            
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            raise
    
    def _extract_markdown_headers(self, content: str) -> List[Dict[str, Any]]:
        """Extract headers from markdown content."""
        headers = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            headers.append({
                'level': len(match.group(1)),
                'text': match.group(2).strip()
            })
        return headers
    
    def _extract_markdown_links(self, content: str) -> List[Dict[str, Any]]:
        """Extract links from markdown content."""
        links = []
        for match in re.finditer(r'\[([^\]]+)\]$$([^)]+)$$', content):
            links.append({
                'text': match.group(1),
                'url': match.group(2)
            })
        return links
    
    async def _create_chunks(self, content: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Split content into chunks."""
        if not content.strip():
            return []
        # Split text into chunks
        text_chunks = self.text_splitter.split_text(content)
        # Create DocumentChunk objects
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'total_chunks': len(text_chunks),
                'chunk_size': len(chunk_text)
            })
            chunk = DocumentChunk(chunk_text, chunk_metadata)
            chunks.append(chunk)
        return chunks
