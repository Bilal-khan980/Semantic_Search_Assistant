"""
Readwise markdown import functionality.
Parses Readwise exports and extracts highlights with metadata.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ReadwiseImporter:
    """Handles importing and parsing Readwise markdown exports."""
    
    def __init__(self, config):
        self.config = config
        
    async def parse_markdown(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Parse Readwise markdown export and extract highlights."""
        highlights = []
        
        try:
            # Split content by books/articles
            books = self._split_by_books(markdown_content)
            
            for book_content in books:
                book_highlights = await self._parse_book_highlights(book_content)
                highlights.extend(book_highlights)
            
            logger.info(f"Parsed {len(highlights)} highlights from Readwise export")
            return highlights
            
        except Exception as e:
            logger.error(f"Error parsing Readwise markdown: {str(e)}")
            raise
    
    def _split_by_books(self, content: str) -> List[str]:
        """Split markdown content by books/articles."""
        # Readwise exports typically use ## for book titles
        book_sections = re.split(r'^## ', content, flags=re.MULTILINE)
        
        # Remove empty sections and add back the ## prefix
        books = []
        for i, section in enumerate(book_sections):
            if section.strip():
                if i > 0:  # Add back the ## prefix (except for first section which might be metadata)
                    section = "## " + section
                books.append(section)
        
        return books
    
    async def _parse_book_highlights(self, book_content: str) -> List[Dict[str, Any]]:
        """Parse highlights from a single book section."""
        highlights = []
        
        # Extract book metadata
        book_info = self._extract_book_info(book_content)
        
        # Find all highlights in the book
        highlight_patterns = [
            r'> (.+?)(?=\n\n|\n- |\n> |\Z)',  # Blockquotes
            r'- (.+?)(?=\n\n|\n- |\n> |\Z)',  # List items
        ]
        
        for pattern in highlight_patterns:
            matches = re.finditer(pattern, book_content, re.DOTALL)
            
            for match in matches:
                highlight_text = match.group(1).strip()
                
                if highlight_text and len(highlight_text) > 10:  # Filter out very short matches
                    highlight = await self._create_highlight_object(
                        highlight_text, 
                        book_info, 
                        book_content
                    )
                    if highlight:
                        highlights.append(highlight)
        
        return highlights
    
    def _extract_book_info(self, book_content: str) -> Dict[str, Any]:
        """Extract book metadata from the content."""
        book_info = {
            'title': 'Unknown',
            'author': 'Unknown',
            'url': '',
            'tags': []
        }
        
        # Extract title (first line after ##)
        title_match = re.search(r'^## (.+?)$', book_content, re.MULTILINE)
        if title_match:
            title_line = title_match.group(1).strip()
            
            # Check if title contains author info
            if ' - ' in title_line:
                parts = title_line.split(' - ', 1)
                book_info['title'] = parts[0].strip()
                book_info['author'] = parts[1].strip()
            else:
                book_info['title'] = title_line
        
        # Extract author if not already found
        if book_info['author'] == 'Unknown':
            author_match = re.search(r'Author: (.+?)$', book_content, re.MULTILINE)
            if author_match:
                book_info['author'] = author_match.group(1).strip()
        
        # Extract URL
        url_match = re.search(r'URL: (.+?)$', book_content, re.MULTILINE)
        if url_match:
            book_info['url'] = url_match.group(1).strip()
        
        # Extract tags
        tags_match = re.search(r'Tags: (.+?)$', book_content, re.MULTILINE)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            book_info['tags'] = [tag.strip() for tag in tags_str.split(',')]
        
        return book_info
    
    async def _create_highlight_object(self, highlight_text: str, book_info: Dict[str, Any], full_content: str) -> Optional[Dict[str, Any]]:
        """Create a structured highlight object."""
        
        # Clean up the highlight text
        highlight_text = self._clean_highlight_text(highlight_text)
        
        if not highlight_text or len(highlight_text.strip()) < 10:
            return None
        
        # Extract note if present (usually follows the highlight)
        note = self._extract_note_for_highlight(highlight_text, full_content)
        
        # Extract location/page info
        location = self._extract_location_info(highlight_text, full_content)
        
        # Determine highlight color (if specified in Readwise export)
        color = self._extract_highlight_color(highlight_text, full_content)
        
        # Extract tags specific to this highlight
        highlight_tags = self._extract_highlight_tags(highlight_text, full_content)
        all_tags = list(set(book_info.get('tags', []) + highlight_tags))
        
        # Calculate enhanced metadata
        importance_score = self._calculate_highlight_importance(highlight_text, book_info)
        category = self._categorize_highlight(highlight_text, book_info)
        complexity_score = self._calculate_complexity_score(highlight_text)

        highlight = {
            'id': f"readwise_{hash(highlight_text)}",
            'content': highlight_text,  # Use 'content' for consistency with other parts
            'text': highlight_text,     # Keep 'text' for backward compatibility
            'source': book_info.get('title', 'Unknown'),
            'book': book_info.get('title', 'Unknown'),
            'author': book_info.get('author', 'Unknown'),
            'url': book_info.get('url', ''),
            'location': location,
            'note': note,
            'tags': all_tags,
            'color': color,
            'highlight_color': color,
            'highlighted_at': datetime.now().isoformat(),
            'imported_at': datetime.now().isoformat(),
            'source_type': 'readwise',
            'is_readwise': True,
            'importance_score': importance_score,
            'category': category,
            'metadata': {
                'book_title': book_info.get('title', 'Unknown'),
                'book_author': book_info.get('author', 'Unknown'),
                'book_url': book_info.get('url', ''),
                'book_tags': book_info.get('tags', []),
                'highlight_type': 'readwise',
                'word_count': len(highlight_text.split()),
                'char_count': len(highlight_text),
                'sentence_count': len(re.split(r'[.!?]+', highlight_text)),
                'reading_time_seconds': len(highlight_text.split()) * 0.25,  # ~240 WPM
                'complexity_score': complexity_score,
                'contains_question': '?' in highlight_text,
                'contains_numbers': bool(re.search(r'\d+', highlight_text)),
                'contains_quotes': '"' in highlight_text or "'" in highlight_text,
                'language_detected': self._detect_language(highlight_text),
                'has_personal_note': bool(note),
                'tag_count': len(all_tags),
                'location_info': location
            }
        }
        
        return highlight
    
    def _clean_highlight_text(self, text: str) -> str:
        """Clean and normalize highlight text."""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.+?)`', r'\1', text)        # Code
        
        # Remove location markers that might be embedded
        text = re.sub(r'$$Location \d+$$', '', text)
        text = re.sub(r'$$Page \d+$$', '', text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _extract_note_for_highlight(self, highlight_text: str, full_content: str) -> str:
        """Extract personal note associated with a highlight."""
        # Look for notes that follow highlights
        # This is a simplified implementation - real Readwise exports have specific formatting
        
        # Common patterns for notes in Readwise exports
        note_patterns = [
            r'Note: (.+?)(?=\n\n|\n> |\Z)',
            r'My note: (.+?)(?=\n\n|\n> |\Z)',
            r'Comment: (.+?)(?=\n\n|\n> |\Z)'
        ]
        
        for pattern in note_patterns:
            match = re.search(pattern, full_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""

    def _calculate_highlight_importance(self, highlight_text: str, book_info: Dict[str, Any]) -> float:
        """Calculate importance score for a highlight (0.0 to 1.0)."""
        score = 0.5  # Base score

        # Length-based scoring
        word_count = len(highlight_text.split())
        if word_count > 50:
            score += 0.2  # Longer highlights might be more important
        elif word_count < 10:
            score -= 0.1  # Very short highlights might be less important

        # Content-based scoring
        importance_indicators = [
            r'\b(important|crucial|key|essential|fundamental|critical)\b',
            r'\b(remember|note|significant|major|primary)\b',
            r'\b(conclusion|summary|result|finding)\b',
            r'\b(principle|rule|law|theory|concept)\b'
        ]

        for pattern in importance_indicators:
            if re.search(pattern, highlight_text, re.IGNORECASE):
                score += 0.1

        # Question marks often indicate important concepts
        if '?' in highlight_text:
            score += 0.1

        # Numbers and statistics might be important
        if re.search(r'\d+%|\$\d+|\d+\.\d+', highlight_text):
            score += 0.1

        # Quotes might indicate key insights
        if '"' in highlight_text or "'" in highlight_text:
            score += 0.05

        # Cap the score
        return min(score, 1.0)

    def _categorize_highlight(self, highlight_text: str, book_info: Dict[str, Any]) -> str:
        """Categorize the highlight based on content."""
        text_lower = highlight_text.lower()

        # Question or inquiry
        if '?' in highlight_text:
            return 'question'

        # Definition or explanation
        if any(word in text_lower for word in ['is defined as', 'means', 'refers to', 'is the']):
            return 'definition'

        # Action or instruction
        if any(word in text_lower for word in ['should', 'must', 'need to', 'have to', 'ought to']):
            return 'instruction'

        # Insight or conclusion
        if any(word in text_lower for word in ['therefore', 'thus', 'consequently', 'as a result']):
            return 'insight'

        # Example or illustration
        if any(word in text_lower for word in ['for example', 'such as', 'like', 'including']):
            return 'example'

        # Quote or citation
        if '"' in highlight_text or "'" in highlight_text:
            return 'quote'

        # Statistical or numerical
        if re.search(r'\d+%|\$\d+|\d+\.\d+', highlight_text):
            return 'statistic'

        return 'general'

    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate text complexity score (0.0 to 1.0)."""
        words = text.split()
        if not words:
            return 0.0

        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Sentence length
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = len(words) / max(len(sentences), 1)

        # Complex punctuation
        complex_punct_count = text.count(';') + text.count(':') + text.count('—')

        # Combine factors
        complexity = (
            (avg_word_length - 4) / 6 +  # Normalize around 4-letter average
            (avg_sentence_length - 15) / 20 +  # Normalize around 15-word sentences
            complex_punct_count / len(words) * 10  # Punctuation density
        )

        return max(0.0, min(complexity, 1.0))

    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        # Very basic language detection
        if re.search(r'[àâäéèêëïîôöùûüÿç]', text, re.IGNORECASE):
            return 'french'
        elif re.search(r'[äöüß]', text, re.IGNORECASE):
            return 'german'
        elif re.search(r'[ñáéíóúü]', text, re.IGNORECASE):
            return 'spanish'
        elif re.search(r'[а-яё]', text, re.IGNORECASE):
            return 'russian'
        else:
            return 'english'
    
    def _extract_location_info(self, highlight_text: str, full_content: str) -> str:
        """Extract location/page information for the highlight."""
        # Look for location indicators
        location_patterns = [
            r'Location (\d+)',
            r'Page (\d+)',
            r'Chapter (\d+)',
            r'Section (.+?)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, full_content)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_highlight_color(self, highlight_text: str, full_content: str) -> str:
        """Extract highlight color if specified."""
        # Readwise sometimes includes color information
        color_patterns = [
            r'Color: (\w+)',
            r'Highlight color: (\w+)'
        ]
        
        for pattern in color_patterns:
            match = re.search(pattern, full_content, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        # Default color
        return "yellow"
    
    def _extract_highlight_tags(self, highlight_text: str, full_content: str) -> List[str]:
        """Extract tags specific to this highlight."""
        tags = []
        
        # Look for hashtags in the highlight or nearby text
        hashtag_pattern = r'#(\w+)'
        matches = re.findall(hashtag_pattern, highlight_text)
        tags.extend(matches)
        
        return tags
    
    async def import_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Import highlights from a Readwise markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return await self.parse_markdown(content)
            
        except Exception as e:
            logger.error(f"Error importing from file {file_path}: {str(e)}")
            raise
    
    def validate_readwise_format(self, content: str) -> bool:
        """Validate that the content appears to be a Readwise export."""
        # Check for common Readwise export patterns
        indicators = [
            r'## .+',  # Book titles
            r'> .+',   # Blockquoted highlights
            r'Author: .+',  # Author information
            r'URL: .+'  # Source URLs
        ]
        
        matches = 0
        for pattern in indicators:
            if re.search(pattern, content, re.MULTILINE):
                matches += 1
        
        # If we find at least 2 indicators, it's likely a Readwise export
        return matches >= 2

    async def watch_readwise_folder(self, folder_path: str):
        """Watch Readwise folder for new markdown files."""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class ReadwiseHandler(FileSystemEventHandler):
            def __init__(self, importer):
                self.importer = importer

            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith('.md'):
                    logger.info(f"New Readwise file detected: {event.src_path}")
                    asyncio.create_task(self.importer.import_from_file(event.src_path))

            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith('.md'):
                    logger.info(f"Readwise file updated: {event.src_path}")
                    asyncio.create_task(self.importer.import_from_file(event.src_path))

        observer = Observer()
        observer.schedule(ReadwiseHandler(self), folder_path, recursive=True)
        observer.start()
        logger.info(f"Started watching Readwise folder: {folder_path}")
        return observer

    async def import_from_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """Import all Readwise markdown files from a folder."""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")

        all_highlights = []
        md_files = list(folder.rglob("*.md"))

        logger.info(f"Found {len(md_files)} markdown files in {folder_path}")

        for md_file in md_files:
            try:
                highlights = await self.import_from_file(str(md_file))
                all_highlights.extend(highlights)
                logger.info(f"Imported {len(highlights)} highlights from {md_file.name}")
            except Exception as e:
                logger.error(f"Error importing {md_file}: {e}")

        logger.info(f"Total imported: {len(all_highlights)} highlights from {len(md_files)} files")
        return all_highlights
