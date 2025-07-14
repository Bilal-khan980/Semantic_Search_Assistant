"""
Search engine that combines vector similarity search with additional ranking factors.
Handles query processing, result ranking, and highlight prioritization.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SearchEngine:
    """Advanced search engine with multiple ranking factors."""
    
    def __init__(self, vector_store, config):
        self.vector_store = vector_store
        self.config = config
    
    async def search(self, query: str, limit: int = 20, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform comprehensive search with multiple ranking factors."""
        
        # Preprocess query
        processed_query = self._preprocess_query(query)
        
        # Get vector similarity results
        search_multiplier = self.config.get('search.initial_search_multiplier', 2)
        threshold_multiplier = self.config.get('search.initial_threshold_multiplier', 0.8)
        
        vector_results = await self.vector_store.search(
            processed_query, 
            limit=limit * search_multiplier,
            similarity_threshold=similarity_threshold * threshold_multiplier
        )
        
        # Apply additional ranking factors
        ranked_results = await self._rerank_results(vector_results, query)
        
        # Apply final filtering and limit
        final_results = self._apply_final_filters(ranked_results, similarity_threshold)
        
        return final_results[:limit]
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess the search query for better results."""
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Get abbreviations from config
        abbreviations = self.config.get('search.abbreviations', {})
        
        if abbreviations:
            words = query.lower().split()
            expanded_words = []
            
            for word in words:
                if word in abbreviations:
                    expanded_words.append(abbreviations[word])
                else:
                    expanded_words.append(word)
            
            return ' '.join(expanded_words)
        
        return query
    
    async def _rerank_results(self, results: List[Dict[str, Any]], original_query: str) -> List[Dict[str, Any]]:
        """Apply additional ranking factors to reorder results."""
        
        # Get ranking weights from configuration
        weights = self.config.get('search.ranking_weights', {})
        
        for result in results:
            # Start with vector similarity score
            base_score = result['similarity']
            
            # Apply various ranking factors
            readwise_boost = self._calculate_readwise_boost(result)
            highlight_boost = self._calculate_highlight_boost(result)
            recency_boost = self._calculate_recency_boost(result)
            keyword_boost = self._calculate_keyword_boost(result, original_query)
            length_penalty = self._calculate_length_penalty(result)
            source_boost = self._calculate_source_boost(result)
            
            # Combine all factors using configurable weights
            final_score = (
                base_score * weights.get('base_similarity', 1.0) +
                readwise_boost * weights.get('readwise_boost', 0.0) +
                highlight_boost * weights.get('highlight_boost', 0.0) +
                recency_boost * weights.get('recency_boost', 0.0) +
                keyword_boost * weights.get('keyword_boost', 0.0) +
                length_penalty * weights.get('length_penalty', 0.0) +
                source_boost * weights.get('source_boost', 0.0)
            )
            
            result['final_score'] = final_score
            result['ranking_factors'] = {
                'base_similarity': base_score,
                'readwise_boost': readwise_boost,
                'highlight_boost': highlight_boost,
                'recency_boost': recency_boost,
                'keyword_boost': keyword_boost,
                'length_penalty': length_penalty,
                'source_boost': source_boost
            }
        
        # Sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results
    
    def _calculate_readwise_boost(self, result: Dict[str, Any]) -> float:
        """Calculate boost for Readwise highlights."""
        if not result.get('is_readwise', False):
            return 0.0
        
        readwise_config = self.config.get('readwise', {})
        boost = readwise_config.get('priority_boost', 0.0)
        
        # Additional boost for highlights with notes
        if result.get('metadata', {}).get('note', ''):
            boost += readwise_config.get('note_boost', 0.0)
        
        # Boost for certain highlight colors
        color = result.get('highlight_color', '').lower()
        color_boosts = readwise_config.get('color_boosts', {})
        boost += color_boosts.get(color, 0.0)
        
        return boost

    def _calculate_highlight_boost(self, result: Dict[str, Any]) -> float:
        """Calculate boost for PDF highlights and annotations."""
        metadata = result.get('metadata', {})
        boost = 0.0

        # Get highlight configuration
        highlight_config = self.config.get('search.highlight_boosts', {})

        # Boost for PDF highlights
        highlights = metadata.get('highlights', [])
        if highlights:
            base_highlight_boost = highlight_config.get('base_highlight_boost', 0.2)
            boost += base_highlight_boost

            # Additional boost based on highlight color
            color_boosts = highlight_config.get('color_boosts', {
                'yellow': 0.1,
                'red': 0.3,
                'green': 0.2,
                'blue': 0.15,
                'orange': 0.25,
                'pink': 0.1
            })

            for highlight in highlights:
                color_category = highlight.get('color_category', 'default')
                boost += color_boosts.get(color_category, 0.0)

                # Extra boost for highlights with content
                if highlight.get('highlighted_text'):
                    boost += highlight_config.get('text_highlight_boost', 0.1)

        # Boost for PDF annotations (notes, comments)
        annotations = metadata.get('annotations', [])
        if annotations:
            annotation_boost = highlight_config.get('annotation_boost', 0.15)
            boost += annotation_boost * min(len(annotations), 3)  # Cap at 3 annotations

            # Extra boost for annotations with content
            for annotation in annotations:
                if annotation.get('content'):
                    boost += highlight_config.get('content_annotation_boost', 0.1)

        # Boost for content that comes from highlighted text
        if result.get('content', '').strip() and any(
            highlight.get('highlighted_text', '').strip() in result.get('content', '')
            for highlight in highlights
        ):
            boost += highlight_config.get('highlighted_content_boost', 0.3)

        # Maximum highlight boost cap
        max_highlight_boost = highlight_config.get('max_highlight_boost', 1.0)
        return min(boost, max_highlight_boost)

    def _calculate_recency_boost(self, result: Dict[str, Any]) -> float:
        """Calculate boost based on content recency."""
        if not self.config.get('search.boost_recent', False):
            return 0.0
        
        try:
            created_at = result.get('created_at')
            if not created_at:
                return 0.0
            
            # Parse datetime
            if isinstance(created_at, str):
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_date = created_at
        
            # Calculate days since creation
            days_old = (datetime.now() - created_date.replace(tzinfo=None)).days
        
            # Get recency configuration
            recency_config = self.config.get('search.recency_boosts', {})
        
            # Apply boosts based on configurable time periods
            for period_key in sorted(recency_config.keys()):
                if period_key.endswith('_days'):
                    boost_key = period_key.replace('_days', '_boost')
                    if days_old <= recency_config.get(period_key, float('inf')):
                        return recency_config.get(boost_key, 0.0)
        
            return 0.0
        
        except Exception:
            return 0.0
    
    def _calculate_keyword_boost(self, result: Dict[str, Any], query: str) -> float:
        """Calculate boost for exact keyword matches."""
        content = result.get('content', '').lower()
        query_words = query.lower().split()
        
        # Get keyword matching configuration
        keyword_config = self.config.get('search.keyword_matching', {})
        min_word_length = keyword_config.get('min_word_length', 0)
        exact_word_boost = keyword_config.get('exact_word_boost', 0.0)
        phrase_match_boost = keyword_config.get('phrase_match_boost', 0.0)
        max_boost = keyword_config.get('max_keyword_boost', 0.0)
        
        boost = 0.0
        
        for word in query_words:
            if len(word) >= min_word_length:
                # Exact word match
                if re.search(r'\b' + re.escape(word) + r'\b', content):
                    boost += exact_word_boost
    
        # Phrase match (if query has multiple words)
        if len(query_words) > 1 and query.lower() in content:
            boost += phrase_match_boost
    
        return min(boost, max_boost) if max_boost > 0 else boost
    
    def _calculate_length_penalty(self, result: Dict[str, Any]) -> float:
        """Calculate penalty/boost based on content length."""
        content = result.get('content', '')
        length = len(content)
        
        # Get length preferences from configuration
        length_config = self.config.get('search.length_preferences', {})
        
        # Check each length range in config
        for range_name, range_config in length_config.items():
            if isinstance(range_config, dict):
                min_length = range_config.get('min', 0)
                max_length = range_config.get('max', float('inf'))
                boost = range_config.get('boost', 0.0)
                
                if min_length <= length <= max_length:
                    return boost
        
        return 0.0
    
    def _calculate_source_boost(self, result: Dict[str, Any]) -> float:
        """Calculate boost based on source reliability/importance."""
        source = result.get('source', '').lower()
        boost = 0.0
        
        # Get configurable source preferences from config
        source_boosts = self.config.get('search.source_boosts', {})
        
        # Check file extensions
        extensions = source_boosts.get('extensions', {})
        for ext, ext_boost in extensions.items():
            if ext in source:
                boost += ext_boost
        
        # Check source patterns
        patterns = source_boosts.get('patterns', {})
        for pattern, pattern_boost in patterns.items():
            if pattern in source:
                boost += pattern_boost
        
        # Boost for Readwise content
        if result.get('is_readwise', False):
            boost += source_boosts.get('readwise_boost', 0.0)
        
        # Additional boost based on metadata
        metadata = result.get('metadata', {})
        metadata_boosts = source_boosts.get('metadata_boosts', {})
        
        # Boost if highlight has personal notes
        if metadata.get('note', '').strip():
            boost += metadata_boosts.get('note_boost', 0.0)
        
        # Boost based on number of tags
        tags_count = len(metadata.get('tags', []))
        if tags_count > 0:
            tag_boost_per_tag = metadata_boosts.get('tag_boost_per_tag', 0.0)
            max_tag_boost = metadata_boosts.get('max_tag_boost', 0.0)
            tag_boost = min(tags_count * tag_boost_per_tag, max_tag_boost) if max_tag_boost > 0 else tags_count * tag_boost_per_tag
            boost += tag_boost
    
        return boost
    
    def _apply_final_filters(self, results: List[Dict[str, Any]], similarity_threshold: float) -> List[Dict[str, Any]]:
        """Apply final filtering and cleanup with deduplication."""
        filtered_results = []
        seen_content_hashes = set()

        for result in results:
            # Convert final_score to percentage (0-100) for display
            score_percentage = result['final_score'] * 100

            # Apply a more reasonable minimum score threshold
            # Most good matches are in the 20-40% range, so use 15% as minimum
            min_score_threshold = 15.0

            # Only show results with score > 15%
            if score_percentage <= min_score_threshold:
                continue

            # Update the result with percentage score for display
            result['score'] = score_percentage

            # Create content hash for deduplication
            content = result.get('content', '').strip().lower()
            content_hash = hash(content)

            # Skip duplicates
            if content_hash in seen_content_hashes:
                continue
            seen_content_hashes.add(content_hash)

            # Add display-friendly fields
            result['display_title'] = self._generate_display_title(result)
            result['display_snippet'] = self._generate_display_snippet(result)
            result['highlight_terms'] = self._extract_highlight_terms(result)

            filtered_results.append(result)
        
        return filtered_results
    
    def _generate_display_title(self, result: Dict[str, Any]) -> str:
        """Generate a user-friendly title for the result."""
        if result.get('is_readwise', False):
            metadata = result.get('metadata', {})
            book = metadata.get('book', self.config.get('display.unknown_book_title', 'Unknown Book'))
            author = metadata.get('author', '')
            
            title_format = self.config.get('display.readwise_title_format', '{book}')
            if author and '{author}' in title_format:
                return title_format.format(book=book, author=author)
            else:
                return title_format.format(book=book)
        else:
            # For regular documents, use filename
            source = result.get('source', '')
            if source:
                # Get filename (handle both / and \)
                filename = source.split('/')[-1].split('\\')[-1]
                return filename
            else:
                return self.config.get('display.unknown_document_title', 'Document')
    
    def _generate_display_snippet(self, result: Dict[str, Any]) -> str:
        """Generate a display snippet with context."""
        content = result.get('content', '')
        
        # Get snippet configuration
        snippet_config = self.config.get('display.snippet', {})
        max_length = snippet_config.get('max_length', 200)
        sentence_break_threshold = snippet_config.get('sentence_break_threshold', 0.7)
        space_break_threshold = snippet_config.get('space_break_threshold', 0.8)
        ellipsis = snippet_config.get('ellipsis', '...')
        
        if len(content) <= max_length:
            return content
        
        # Try to find a good breaking point
        snippet = content[:max_length]
        last_sentence = snippet.rfind('.')
        last_space = snippet.rfind(' ')
        
        if last_sentence > max_length * sentence_break_threshold:
            return snippet[:last_sentence + 1]
        elif last_space > max_length * space_break_threshold:
            return snippet[:last_space] + ellipsis
        else:
            return snippet + ellipsis
    
    def _extract_highlight_terms(self, result: Dict[str, Any]) -> List[str]:
        """Extract terms that should be highlighted in the UI."""
        # This would be used by the frontend to highlight matching terms
        return []
    
    async def get_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on indexed content."""
        suggestions = []
        
        suggestion_config = self.config.get('search.suggestions', {})
        min_query_length = suggestion_config.get('min_query_length', 2)
        max_suggestions = suggestion_config.get('max_suggestions', 5)
        
        if len(partial_query) < min_query_length:
            return suggestions
        
        try:
            # Get actual terms from indexed content
            suggestions = await self._get_content_based_suggestions(partial_query)
            
            # Fallback to configuration-based suggestions if no content matches
            if not suggestions:
                suggestions = self._get_config_based_suggestions(partial_query)
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return []

    async def _get_content_based_suggestions(self, partial_query: str) -> List[str]:
        """Get suggestions based on actual indexed content."""
        suggestions = set()
        
        try:
            suggestion_config = self.config.get('search.suggestions', {})
            sample_limit = suggestion_config.get('sample_limit', 50)
            sample_threshold = suggestion_config.get('sample_threshold', 0.3)
            min_word_length = suggestion_config.get('min_word_length', 3)
            
            # Get a sample of documents to extract common terms
            sample_results = await self.vector_store.search(
                partial_query, 
                limit=sample_limit, 
                similarity_threshold=sample_threshold
            )
            
            # Extract relevant terms from content
            for result in sample_results:
                content = result.get('content', '').lower()
                words = re.findall(r'\b\w{' + str(min_word_length) + ',}\b', content)
                
                # Find words that start with the partial query
                matching_words = [
                    word for word in words 
                    if word.startswith(partial_query.lower()) and len(word) > len(partial_query)
                ]
                
                suggestions.update(matching_words)
                
                # Also check metadata for relevant terms
                metadata = result.get('metadata', {})
                for key, value in metadata.items():
                    if isinstance(value, str) and value.lower().startswith(partial_query.lower()):
                        suggestions.add(value.lower())
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and item.lower().startswith(partial_query.lower()):
                                suggestions.add(item.lower())
        
            return sorted(list(suggestions))
            
        except Exception as e:
            logger.error(f"Error getting content-based suggestions: {str(e)}")
            return []

    def _get_config_based_suggestions(self, partial_query: str) -> List[str]:
        """Get suggestions from configuration as fallback."""
        # Get suggestions from config
        configured_terms = self.config.get('search.suggestion_terms', [])
        
        # Filter terms that match the partial query
        matching_terms = [
            term for term in configured_terms
            if term.lower().startswith(partial_query.lower())
        ]
        
        return matching_terms

    async def learn_from_search(self, query: str, selected_result_id: str = None):
        """Learn from user search behavior to improve suggestions."""
        if not self.config.get('search.enable_learning', False):
            return
            
        try:
            # Store search query for future suggestions
            await self._store_search_query(query)
            
            # If user selected a result, boost similar content
            if selected_result_id:
                await self._boost_similar_content(selected_result_id)
                
        except Exception as e:
            logger.error(f"Error learning from search: {str(e)}")

    async def _store_search_query(self, query: str):
        """Store search query to build suggestion vocabulary."""
        learning_config = self.config.get('search.learning', {})
        min_term_length = learning_config.get('min_term_length', 3)
        
        # Extract meaningful terms from the query
        terms = re.findall(r'\b\w{' + str(min_term_length) + ',}\b', query.lower())
        
        # Get current suggestion terms
        current_terms = set(self.config.get('search.suggestion_terms', []))
        
        # Add new terms
        new_terms = [term for term in terms if term not in current_terms]
        if new_terms:
            updated_terms = list(current_terms) + new_terms
            self.config.set('search.suggestion_terms', updated_terms)
            logger.info(f"Added {len(new_terms)} new suggestion terms")

    async def _boost_similar_content(self, result_id: str):
        """Boost content similar to what user selected."""
        # This could be implemented to adjust ranking weights
        # based on user behavior patterns
        pass

    def update_ranking_weights(self, new_weights: Dict[str, float]):
        """Allow dynamic updating of ranking weights."""
        current_weights = self.config.get('search.ranking_weights', {})
        current_weights.update(new_weights)
        self.config.set('search.ranking_weights', current_weights)
        logger.info("Updated ranking weights")

    def get_current_config(self) -> Dict[str, Any]:
        """Get current search configuration for debugging/tuning."""
        return {
            'ranking_weights': self.config.get('search.ranking_weights', {}),
            'source_boosts': self.config.get('search.source_boosts', {}),
            'recency_boosts': self.config.get('search.recency_boosts', {}),
            'length_preferences': self.config.get('search.length_preferences', {}),
            'keyword_matching': self.config.get('search.keyword_matching', {}),
            'suggestion_terms_count': len(self.config.get('search.suggestion_terms', []))
        }

    def _generate_display_title(self, result: Dict[str, Any]) -> str:
        """Generate a display-friendly title for the result."""
        if result.get('is_readwise'):
            return result.get('metadata', {}).get('book', 'Readwise Highlight')
        else:
            source = result.get('source', '')
            # Extract filename from path
            if '/' in source:
                return source.split('/')[-1]
            elif '\\' in source:
                return source.split('\\')[-1]
            return source

    def _generate_display_snippet(self, result: Dict[str, Any]) -> str:
        """Generate a display snippet with highlighted terms."""
        content = result.get('content', '')
        # Limit to first 200 characters for display
        if len(content) > 200:
            content = content[:200] + '...'
        return content

    def _extract_highlight_terms(self, result: Dict[str, Any]) -> List[str]:
        """Extract terms that should be highlighted in the result."""
        # This could be enhanced to identify which terms matched
        # For now, return empty list
        return []

    def _has_keyword_overlap(self, result: Dict[str, Any], top_result: Dict[str, Any] = None) -> bool:
        """Check if result has meaningful keyword overlap with query or top result."""
        final_score = result.get('final_score', 0)

        # For very low scores (< 40%), be very strict
        if final_score < 0.4:
            return False

        # For medium scores (40-50%), require some validation
        if final_score < 0.1:
            # If there's a much better result, this one is probably not relevant
            if top_result and top_result.get('final_score', 0) > final_score + 0.15:
                return False

        return True

    async def get_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query."""
        try:
            if not partial_query or len(partial_query.strip()) < 2:
                return []

            # Get recent search terms from vector store
            # This is a simplified implementation - in production you'd want to store search history
            suggestions = []

            # Add some common search patterns based on the partial query
            query_lower = partial_query.lower().strip()

            # Common search suggestions based on content
            common_suggestions = [
                f"{query_lower} definition",
                f"{query_lower} example",
                f"{query_lower} explanation",
                f"what is {query_lower}",
                f"how to {query_lower}",
                f"{query_lower} benefits",
                f"{query_lower} process",
                f"{query_lower} method"
            ]

            # Filter suggestions that make sense
            for suggestion in common_suggestions:
                if len(suggestion) > len(partial_query) and suggestion.startswith(query_lower):
                    suggestions.append(suggestion)

            # Try to get actual content-based suggestions by doing a quick search
            try:
                search_results = await self.vector_store.search(
                    partial_query,
                    limit=5,
                    similarity_threshold=0.3
                )

                # Extract key terms from search results
                for result in search_results:
                    content = result.get('content', '')
                    # Extract meaningful phrases that contain the query
                    words = content.lower().split()
                    for i, word in enumerate(words):
                        if query_lower in word and i < len(words) - 2:
                            phrase = ' '.join(words[i:i+3])
                            if phrase not in suggestions and len(phrase) > len(partial_query):
                                suggestions.append(phrase)

            except Exception as e:
                logger.debug(f"Error getting content-based suggestions: {e}")

            # Remove duplicates and limit results
            unique_suggestions = list(dict.fromkeys(suggestions))
            return unique_suggestions[:limit]

        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
