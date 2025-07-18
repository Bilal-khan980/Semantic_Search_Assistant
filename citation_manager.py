"""
Citation and Metadata Management System for Semantic Search Assistant.
Handles citation formatting, metadata preservation, and source tracking.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import re
import hashlib
from urllib.parse import urlparse
import uuid

logger = logging.getLogger(__name__)

class CitationManager:
    """Manages citations and metadata for documents and highlights."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.citation_styles = {
            'apa': self._format_apa_citation,
            'mla': self._format_mla_citation,
            'chicago': self._format_chicago_citation,
            'harvard': self._format_harvard_citation,
            'ieee': self._format_ieee_citation
        }
        self.default_style = config.get('citation.default_style', 'apa')
        
        # Citation database
        self.citations_db_path = Path(config.get('citation.database_path', 'data/citations.json'))
        self.citations_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.citations_db = self._load_citations_database()
    
    def _load_citations_database(self) -> Dict[str, Any]:
        """Load the citations database."""
        try:
            if self.citations_db_path.exists():
                with open(self.citations_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading citations database: {e}")
        
        return {
            'sources': {},
            'citations': {},
            'metadata': {},
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def _save_citations_database(self):
        """Save the citations database."""
        try:
            self.citations_db['updated_at'] = datetime.now().isoformat()
            with open(self.citations_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.citations_db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving citations database: {e}")
    
    def register_source(self, source_info: Dict[str, Any]) -> str:
        """Register a new source and return its ID."""
        source_id = self._generate_source_id(source_info)
        
        # Enhanced source metadata
        enhanced_source = {
            'id': source_id,
            'title': source_info.get('title', ''),
            'author': source_info.get('author', ''),
            'authors': source_info.get('authors', []),
            'publication_date': source_info.get('publication_date', ''),
            'publisher': source_info.get('publisher', ''),
            'url': source_info.get('url', ''),
            'doi': source_info.get('doi', ''),
            'isbn': source_info.get('isbn', ''),
            'file_path': source_info.get('file_path', ''),
            'source_type': self._determine_source_type(source_info),
            'page_count': source_info.get('page_count', 0),
            'language': source_info.get('language', 'en'),
            'tags': source_info.get('tags', []),
            'notes': source_info.get('notes', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'access_date': datetime.now().isoformat(),
            'metadata': source_info.get('metadata', {})
        }
        
        self.citations_db['sources'][source_id] = enhanced_source
        self._save_citations_database()
        
        logger.info(f"Registered source: {enhanced_source['title']} (ID: {source_id})")
        return source_id
    
    def create_citation(self, content: str, source_id: str, **kwargs) -> Dict[str, Any]:
        """Create a citation for content from a source."""
        citation_id = str(uuid.uuid4())
        
        source = self.citations_db['sources'].get(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        citation = {
            'id': citation_id,
            'content': content,
            'source_id': source_id,
            'page': kwargs.get('page', ''),
            'location': kwargs.get('location', ''),
            'highlight_color': kwargs.get('highlight_color', ''),
            'user_note': kwargs.get('user_note', ''),
            'tags': kwargs.get('tags', []),
            'importance': kwargs.get('importance', 'medium'),
            'context': kwargs.get('context', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'citation_style': kwargs.get('citation_style', self.default_style),
            'metadata': kwargs.get('metadata', {})
        }
        
        self.citations_db['citations'][citation_id] = citation
        self._save_citations_database()
        
        return citation
    
    def format_citation(self, citation_id: str, style: Optional[str] = None) -> str:
        """Format a citation in the specified style."""
        citation = self.citations_db['citations'].get(citation_id)
        if not citation:
            raise ValueError(f"Citation {citation_id} not found")
        
        source = self.citations_db['sources'].get(citation['source_id'])
        if not source:
            raise ValueError(f"Source {citation['source_id']} not found")
        
        style = style or citation.get('citation_style', self.default_style)
        formatter = self.citation_styles.get(style, self.citation_styles[self.default_style])
        
        return formatter(source, citation)
    
    def format_content_with_citation(self, content: str, citation_id: str, 
                                   style: Optional[str] = None, 
                                   format_type: str = 'inline') -> str:
        """Format content with its citation."""
        citation_text = self.format_citation(citation_id, style)
        
        if format_type == 'inline':
            return f"{content}\n\n{citation_text}"
        elif format_type == 'footnote':
            return f"{content}¹\n\n¹ {citation_text}"
        elif format_type == 'parenthetical':
            # Extract author and year for parenthetical citation
            citation = self.citations_db['citations'].get(citation_id)
            source = self.citations_db['sources'].get(citation['source_id'])
            author = source.get('author', 'Unknown').split(',')[0]  # First author
            year = self._extract_year(source.get('publication_date', ''))
            page = citation.get('page', '')
            
            parenthetical = f"({author}, {year}"
            if page:
                parenthetical += f", p. {page}"
            parenthetical += ")"
            
            return f"{content} {parenthetical}\n\nReference:\n{citation_text}"
        else:
            return f"{content}\n\n{citation_text}"
    
    def _generate_source_id(self, source_info: Dict[str, Any]) -> str:
        """Generate a unique ID for a source."""
        # Create a hash based on key identifying information
        identifier_parts = [
            source_info.get('title', ''),
            source_info.get('author', ''),
            source_info.get('url', ''),
            source_info.get('file_path', ''),
            source_info.get('doi', '')
        ]
        
        identifier = '|'.join(str(part) for part in identifier_parts if part)
        return hashlib.md5(identifier.encode()).hexdigest()[:12]
    
    def _determine_source_type(self, source_info: Dict[str, Any]) -> str:
        """Determine the type of source."""
        if source_info.get('doi'):
            return 'journal_article'
        elif source_info.get('isbn'):
            return 'book'
        elif source_info.get('url'):
            if 'readwise' in source_info.get('url', '').lower():
                return 'readwise_highlight'
            else:
                return 'website'
        elif source_info.get('file_path'):
            file_path = Path(source_info['file_path'])
            if file_path.suffix.lower() == '.pdf':
                return 'pdf_document'
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                return 'word_document'
            elif file_path.suffix.lower() in ['.md', '.txt']:
                return 'text_document'
        
        return 'unknown'
    
    def _extract_year(self, date_string: str) -> str:
        """Extract year from a date string."""
        if not date_string:
            return 'n.d.'
        
        # Try to extract 4-digit year
        year_match = re.search(r'\b(19|20)\d{2}\b', date_string)
        if year_match:
            return year_match.group()
        
        return 'n.d.'
    
    def _format_apa_citation(self, source: Dict[str, Any], citation: Dict[str, Any]) -> str:
        """Format citation in APA style."""
        author = source.get('author', 'Unknown Author')
        year = self._extract_year(source.get('publication_date', ''))
        title = source.get('title', 'Untitled')
        
        # Basic APA format
        citation_text = f"{author} ({year}). {title}"
        
        # Add publisher if available
        if source.get('publisher'):
            citation_text += f". {source['publisher']}"
        
        # Add URL if available
        if source.get('url'):
            citation_text += f". Retrieved from {source['url']}"
        
        # Add page if specified in citation
        if citation.get('page'):
            citation_text += f" (p. {citation['page']})"
        
        return citation_text
    
    def _format_mla_citation(self, source: Dict[str, Any], citation: Dict[str, Any]) -> str:
        """Format citation in MLA style."""
        author = source.get('author', 'Unknown Author')
        title = source.get('title', 'Untitled')
        
        # Basic MLA format
        citation_text = f"{author}. \"{title}.\""
        
        # Add publisher and date
        if source.get('publisher'):
            citation_text += f" {source['publisher']},"
        
        year = self._extract_year(source.get('publication_date', ''))
        citation_text += f" {year}"
        
        # Add URL if available
        if source.get('url'):
            citation_text += f". Web. {datetime.now().strftime('%d %b %Y')}"
        
        return citation_text
    
    def _format_chicago_citation(self, source: Dict[str, Any], citation: Dict[str, Any]) -> str:
        """Format citation in Chicago style."""
        author = source.get('author', 'Unknown Author')
        title = source.get('title', 'Untitled')
        year = self._extract_year(source.get('publication_date', ''))
        
        # Basic Chicago format
        citation_text = f"{author}. \"{title}.\""
        
        if source.get('publisher'):
            citation_text += f" {source['publisher']}, {year}"
        else:
            citation_text += f" {year}"
        
        # Add URL if available
        if source.get('url'):
            citation_text += f". {source['url']}"
        
        return citation_text
    
    def _format_harvard_citation(self, source: Dict[str, Any], citation: Dict[str, Any]) -> str:
        """Format citation in Harvard style."""
        author = source.get('author', 'Unknown Author')
        year = self._extract_year(source.get('publication_date', ''))
        title = source.get('title', 'Untitled')
        
        # Basic Harvard format
        citation_text = f"{author} {year}, '{title}'"
        
        if source.get('publisher'):
            citation_text += f", {source['publisher']}"
        
        # Add URL if available
        if source.get('url'):
            citation_text += f", viewed {datetime.now().strftime('%d %B %Y')}, <{source['url']}>"
        
        return citation_text
    
    def _format_ieee_citation(self, source: Dict[str, Any], citation: Dict[str, Any]) -> str:
        """Format citation in IEEE style."""
        author = source.get('author', 'Unknown Author')
        title = source.get('title', 'Untitled')
        year = self._extract_year(source.get('publication_date', ''))
        
        # Basic IEEE format
        citation_text = f"{author}, \"{title},\" {year}"
        
        # Add URL if available
        if source.get('url'):
            citation_text += f". [Online]. Available: {source['url']}"
        
        return citation_text
    
    def get_source_info(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source information by ID."""
        return self.citations_db['sources'].get(source_id)
    
    def get_citation_info(self, citation_id: str) -> Optional[Dict[str, Any]]:
        """Get citation information by ID."""
        return self.citations_db['citations'].get(citation_id)
    
    def search_sources(self, query: str) -> List[Dict[str, Any]]:
        """Search sources by title, author, or content."""
        results = []
        query_lower = query.lower()
        
        for source in self.citations_db['sources'].values():
            if (query_lower in source.get('title', '').lower() or
                query_lower in source.get('author', '').lower() or
                any(query_lower in tag.lower() for tag in source.get('tags', []))):
                results.append(source)
        
        return results
    
    def export_bibliography(self, citation_ids: List[str], style: str = None) -> str:
        """Export a bibliography for the given citations."""
        style = style or self.default_style
        bibliography = []
        
        for citation_id in citation_ids:
            try:
                formatted_citation = self.format_citation(citation_id, style)
                bibliography.append(formatted_citation)
            except ValueError as e:
                logger.warning(f"Could not format citation {citation_id}: {e}")
        
        return '\n\n'.join(bibliography)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the citation database."""
        return {
            'total_sources': len(self.citations_db['sources']),
            'total_citations': len(self.citations_db['citations']),
            'source_types': self._count_source_types(),
            'citation_styles_used': self._count_citation_styles(),
            'most_cited_sources': self._get_most_cited_sources()
        }
    
    def _count_source_types(self) -> Dict[str, int]:
        """Count sources by type."""
        type_counts = {}
        for source in self.citations_db['sources'].values():
            source_type = source.get('source_type', 'unknown')
            type_counts[source_type] = type_counts.get(source_type, 0) + 1
        return type_counts
    
    def _count_citation_styles(self) -> Dict[str, int]:
        """Count citations by style."""
        style_counts = {}
        for citation in self.citations_db['citations'].values():
            style = citation.get('citation_style', self.default_style)
            style_counts[style] = style_counts.get(style, 0) + 1
        return style_counts
    
    def _get_most_cited_sources(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most frequently cited sources."""
        source_citation_counts = {}
        
        for citation in self.citations_db['citations'].values():
            source_id = citation['source_id']
            source_citation_counts[source_id] = source_citation_counts.get(source_id, 0) + 1
        
        # Sort by citation count
        sorted_sources = sorted(source_citation_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for source_id, count in sorted_sources[:limit]:
            source = self.citations_db['sources'].get(source_id)
            if source:
                result.append({
                    'source': source,
                    'citation_count': count
                })
        
        return result
