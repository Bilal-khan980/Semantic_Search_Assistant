"""
Configuration management for the document processing backend.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager with default settings."""
    
    DEFAULT_CONFIG = {
        "embedding": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu",
            "batch_size": 32
        },
        "chunking": {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "separators": ["\n\n", "\n", " ", ""]
        },
        "vector_store": {
            "db_path": "./data/vector_db",
            "table_name": "documents",
            "similarity_threshold": 0.7
        },
        "processing": {
            "max_file_size_mb": 100,
            "supported_extensions": [".pdf", ".docx", ".md", ".txt"],
            "extract_highlights": True
        },
        "readwise": {
            "preserve_formatting": True,
            "extract_metadata": True,
            "priority_boost": 0.0,
            "note_boost": 0.0,
            "color_boosts": {}
        },
        "search": {
            "max_results": 50,
            "min_similarity": 0.5,
            "boost_recent": False,
            "initial_search_multiplier": 2,
            "initial_threshold_multiplier": 0.8,
            "enable_learning": False,
            "abbreviations": {},
            "ranking_weights": {
                "base_similarity": 1.0,
                "readwise_boost": 0.0,
                "highlight_boost": 0.3,
                "recency_boost": 0.0,
                "keyword_boost": 0.0,
                "length_penalty": 0.0,
                "source_boost": 0.0
            },
            "source_boosts": {
                "extensions": {},
                "patterns": {},
                "readwise_boost": 0.0,
                "metadata_boosts": {
                    "note_boost": 0.0,
                    "tag_boost_per_tag": 0.0,
                    "max_tag_boost": 0.0
                }
            },
            "recency_boosts": {},
            "length_preferences": {},
            "keyword_matching": {
                "min_word_length": 0,
                "exact_word_boost": 0.0,
                "phrase_match_boost": 0.0,
                "max_keyword_boost": 0.0
            },
            "highlight_boosts": {
                "base_highlight_boost": 0.2,
                "annotation_boost": 0.15,
                "text_highlight_boost": 0.1,
                "content_annotation_boost": 0.1,
                "highlighted_content_boost": 0.3,
                "max_highlight_boost": 1.0,
                "color_boosts": {
                    "yellow": 0.1,
                    "red": 0.3,
                    "green": 0.2,
                    "blue": 0.15,
                    "orange": 0.25,
                    "pink": 0.1,
                    "default": 0.05
                }
            },
            "suggestions": {
                "min_query_length": 2,
                "max_suggestions": 5,
                "sample_limit": 50,
                "sample_threshold": 0.3,
                "min_word_length": 3
            },
            "learning": {
                "min_term_length": 3
            },
            "suggestion_terms": []
        },
        "display": {
            "unknown_book_title": "Unknown Book",
            "unknown_document_title": "Document",
            "readwise_title_format": "{book}",
            "snippet": {
                "max_length": 200,
                "sentence_break_threshold": 0.7,
                "space_break_threshold": 0.8,
                "ellipsis": "..."
            }
        }
    }
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file, creating default if not exists."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    self._merge_config(self.config, user_config)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
        else:
            self.save_config()
    
    def save_config(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]):
        """Recursively merge configuration dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'embedding.model_name')."""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self.save_config()
    
    @property
    def embedding_model(self) -> str:
        return self.get('embedding.model_name')
    
    @property
    def chunk_size(self) -> int:
        return self.get('chunking.chunk_size')
    
    @property
    def chunk_overlap(self) -> int:
        return self.get('chunking.chunk_overlap')
    
    @property
    def db_path(self) -> str:
        return self.get('vector_store.db_path')
    
    @property
    def supported_extensions(self) -> list:
        return self.get('processing.supported_extensions')

    def to_dict(self) -> dict:
        """Convert config to dictionary format."""
        return self.config.copy()
