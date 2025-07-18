"""
Vector store implementation using LanceDB for local semantic search.
Handles embedding generation and vector similarity search.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import time

# Vector database
import lancedb
import pyarrow as pa

# Embedding model
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    """LanceDB-based vector store for document embeddings."""
    
    def __init__(self, config):
        self.config = config
        self.db = None
        self.table = None
        self.embedding_model = None
        self.embedding_dim = None
    
    async def initialize(self):
        """Initialize the vector store and embedding model."""
        # Initialize embedding model
        model_name = self.config.embedding_model
        logger.info(f"Loading embedding model: {model_name}")
        
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize LanceDB
        db_path = Path(self.config.db_path)
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.db = lancedb.connect(str(db_path))
        
        # Create or connect to table
        table_name = self.config.get('vector_store.table_name', 'documents')
        
        try:
            self.table = self.db.open_table(table_name)
            logger.info(f"Connected to existing table: {table_name}")
        except:
            # Create new table with sample data
            schema = self._create_schema()
            
            # Create table with empty data but proper schema
            # Use integer timestamp to avoid precision issues
            current_timestamp = int(time.time())
            
            sample_data = [{
                "id": "sample",
                "content": "sample content",
                "embedding": [0.0] * self.embedding_dim,
                "metadata": "{}",
                "source": "sample",
                "chunk_index": 0,
                "created_at": current_timestamp,
                "is_readwise": False,
                "highlight_color": ""
            }]
            
            self.table = self.db.create_table(table_name, data=sample_data, schema=schema)
            
            # Remove the sample data
            self.table.delete("id = 'sample'")
            
            logger.info(f"Created new table: {table_name}")
        
        logger.info("Vector store initialized successfully")
    
    def _create_schema(self):
        """Create the schema for the vector table."""
        return pa.schema([
            pa.field("id", pa.string()),
            pa.field("content", pa.string()),
            pa.field("embedding", pa.list_(pa.float32(), self.embedding_dim)),
            pa.field("metadata", pa.string()),  # JSON string
            pa.field("source", pa.string()),
            pa.field("chunk_index", pa.int32()),
            pa.field("created_at", pa.int64()),  # Use int64 for timestamp to avoid precision issues
            pa.field("is_readwise", pa.bool_()),
            pa.field("highlight_color", pa.string()),
        ])
    
    async def add_document(self, file_path: str, chunks: List) -> str:
        """Add document chunks to the vector store."""
        logger.info(f"add_document called with {len(chunks)} chunks, type: {type(chunks)}")
        if chunks:
            logger.info(f"First chunk type: {type(chunks[0])}")

        if not chunks:
            logger.info(f"No chunks to add for {file_path}")
            return None

        # Generate embeddings for all chunks
        try:
            texts = [chunk.content for chunk in chunks]
        except AttributeError as e:
            logger.error(f"Chunk object missing content attribute: {e}")
            logger.error(f"Chunk type: {type(chunks[0])}, Chunk: {chunks[0]}")
            raise
        embeddings = await self._generate_embeddings(texts)
        
        # Prepare data for insertion
        data = []
        document_id = f"doc_{hash(file_path)}_{int(time.time())}"
        current_timestamp = int(time.time())
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            logger.info(f"Processing chunk {i}: metadata type = {type(chunk.metadata)}, metadata = {chunk.metadata}")
            try:
                metadata_json = json.dumps(chunk.metadata)
            except Exception as e:
                logger.error(f"Failed to serialize metadata: {e}, metadata type: {type(chunk.metadata)}, metadata: {chunk.metadata}")
                raise

            data.append({
                "id": f"{document_id}_chunk_{i}",
                "content": chunk.content,
                "embedding": embedding.tolist(),
                "metadata": metadata_json,
                "source": file_path,
                "chunk_index": i,
                "created_at": current_timestamp,
                "is_readwise": False,
                "highlight_color": ""
            })
        
        # Insert into table
        self.table.add(data)
        
        logger.info(f"Added {len(chunks)} chunks for document: {Path(file_path).name}")
        return document_id
    
    async def add_readwise_highlight(self, highlight: Dict[str, Any]) -> str:
        """Add a Readwise highlight to the vector store."""
        text = highlight.get('text', '')
        if not text.strip():
            return None
        
        # Generate embedding
        embedding = await self._generate_embeddings([text])
        
        # Prepare highlight data
        highlight_id = f"readwise_{hash(text)}_{int(time.time())}"
        current_timestamp = int(time.time())
        
        data = [{
            "id": highlight_id,
            "content": text,
            "embedding": embedding[0].tolist(),
            "metadata": json.dumps({
                'book': highlight.get('book', ''),
                'author': highlight.get('author', ''),
                'location': highlight.get('location', ''),
                'note': highlight.get('note', ''),
                'tags': highlight.get('tags', []),
                'highlighted_at': highlight.get('highlighted_at', ''),
                'readwise_id': highlight.get('id', '')
            }),
            "source": f"{highlight.get('book', 'Unknown')} - {highlight.get('author', 'Unknown')}",
            "chunk_index": 0,
            "created_at": current_timestamp,
            "is_readwise": True,
            "highlight_color": highlight.get('color', 'yellow')
        }]
        
        self.table.add(data)
        
        logger.info(f"Added Readwise highlight from: {highlight.get('book', 'Unknown')}")
        return highlight_id
    
    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        # Run embedding generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, 
            self.embedding_model.encode, 
            texts
        )
        return embeddings
    
    async def search(self, query: str, limit: int = 20, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        # Check if table is empty
        try:
            count = self.table.count_rows()
            if count == 0:
                logger.info("No documents in vector store yet")
                return []
        except Exception as e:
            logger.warning(f"Could not check table count: {e}")
            return []
        
        # Generate query embedding
        query_embedding = await self._generate_embeddings([query])
        
        # Perform vector search
        try:
            results = (
                self.table
                .search(query_embedding[0])
                .limit(limit)
                .to_pandas()
            )
        except Exception as e:
            logger.error(f"Error performing vector search: {e}")
            return []
        
        # Filter by similarity threshold and format results
        formatted_results = []
        seen_content = set()  # Track content we've already seen

        for _, row in results.iterrows():
            # Calculate similarity score (LanceDB returns distance, convert to similarity)
            distance = row.get('_distance', float('inf'))
            similarity = 1 / (1 + distance) if distance != float('inf') else 0
            
            if similarity >= similarity_threshold:
                # Create a content hash for deduplication
                content = row['content']
                content_hash = hash(content.strip().lower())
                
                # Skip if we've seen this exact content before
                if content_hash in seen_content:
                    continue
                seen_content.add(content_hash)
                
                try:
                    metadata = json.loads(row['metadata'])
                except:
                    metadata = {}
                
                # Convert timestamp back to datetime for display
                created_at = datetime.fromtimestamp(row['created_at']) if row['created_at'] else datetime.now()
                
                result = {
                    'id': row['id'],
                    'content': content,
                    'source': row['source'],
                    'similarity': similarity,
                    'metadata': metadata,
                    'is_readwise': row['is_readwise'],
                    'highlight_color': row.get('highlight_color', ''),
                    'created_at': created_at
                }
                
                # Apply Readwise boost if configured
                if row['is_readwise'] and self.config.get('readwise.priority_boost', 0) > 0:
                    result['similarity'] += self.config.get('readwise.priority_boost')
                
                formatted_results.append(result)
        
        # Sort by similarity (descending)
        formatted_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return formatted_results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            # Get total count
            total_count = self.table.count_rows()
            
            if total_count == 0:
                return {
                    'total_chunks': 0,
                    'document_chunks': 0,
                    'readwise_highlights': 0,
                    'unique_sources': 0,
                    'embedding_model': self.config.embedding_model,
                    'embedding_dimension': self.embedding_dim
                }
            
            # Get counts by type
            df = self.table.to_pandas()
            readwise_count = len(df[df['is_readwise'] == True])
            document_count = len(df[df['is_readwise'] == False])
            
            # Get unique sources
            unique_sources = df['source'].nunique()
            
            return {
                'total_chunks': total_count,
                'document_chunks': document_count,
                'readwise_highlights': readwise_count,
                'unique_sources': unique_sources,
                'embedding_model': self.config.embedding_model,
                'embedding_dimension': self.embedding_dim
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {
                'total_chunks': 0,
                'document_chunks': 0,
                'readwise_highlights': 0,
                'unique_sources': 0,
                'embedding_model': self.config.embedding_model,
                'embedding_dimension': self.embedding_dim
            }
    
    async def delete_document(self, document_id: str):
        """Delete all chunks for a document."""
        try:
            self.table.delete(f"id LIKE '{document_id}%'")
            logger.info(f"Deleted document: {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")

    async def delete_by_source(self, source_path: str):
        """Delete all chunks for a specific source file."""
        try:
            if not self.table:
                logger.warning("No table available for deletion")
                return

            # Normalize path for comparison
            normalized_path = source_path.replace('\\', '/')

            # Check current count before deletion
            initial_count = self.table.count_rows()

            # Try different path formats to ensure we catch all variations
            delete_conditions = [
                f"source = '{source_path}'",
                f"source = '{normalized_path}'",
                f"source LIKE '%{Path(source_path).name}%'"
            ]

            deleted_count = 0
            for condition in delete_conditions:
                try:
                    # Check if any rows match this condition
                    df = self.table.search().where(condition).limit(10).to_pandas()
                    if not df.empty:
                        self.table.delete(condition)
                        deleted_count += len(df)
                        logger.info(f"🗑️ Deleted {len(df)} chunks with condition: {condition}")
                        break
                except Exception as e:
                    logger.debug(f"Delete condition failed: {condition} - {e}")
                    continue

            # Verify deletion
            final_count = self.table.count_rows()
            logger.info(f"🗑️ Deleted chunks for {source_path}: {initial_count} → {final_count} rows")

        except Exception as e:
            logger.error(f"Error deleting by source {source_path}: {e}")

    async def get_documents(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of documents with metadata."""
        try:
            if not self.table:
                return []

            # Get all documents
            df = self.table.to_pandas()

            if df.empty:
                return []

            # Group by source to get unique documents
            documents = []
            grouped = df.groupby('source')

            for source, group in grouped:
                doc_info = {
                    'id': group.iloc[0]['id'].split('_chunk_')[0],  # Remove chunk suffix
                    'source': source,
                    'title': group.iloc[0].get('title', source),
                    'chunks': len(group),
                    'is_readwise': group.iloc[0]['is_readwise'],
                    'created_at': group.iloc[0]['created_at'],
                    'file_size': group.iloc[0].get('file_size', 0),
                    'file_type': group.iloc[0].get('file_type', 'unknown')
                }
                documents.append(doc_info)

            # Sort by creation date (newest first)
            documents.sort(key=lambda x: x['created_at'], reverse=True)

            # Apply pagination
            start_idx = offset
            end_idx = offset + limit

            return documents[start_idx:end_idx]

        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []

    async def clear(self):
        """Clear all data from the vector store."""
        try:
            if self.table:
                # Drop the table and recreate it
                table_name = self.config.get('vector_store.table_name', 'documents')
                self.db.drop_table(table_name)

                # Recreate the table
                await self._create_table()

                logger.info("Vector store cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            raise

    async def add_single_document(self, content: str, metadata: Dict[str, Any]):
        """Add a single document to the vector store."""
        try:
            # Generate embedding
            embeddings = await self._generate_embeddings([content])
            embedding = embeddings[0]

            # Create document record
            doc_id = metadata.get('highlight_id', f"doc_{int(time.time() * 1000)}")

            record = {
                'id': doc_id,
                'content': content,
                'embedding': embedding,
                'source': metadata.get('source', 'unknown'),
                'title': metadata.get('book', metadata.get('title', 'Untitled')),
                'is_readwise': metadata.get('source_type') == 'readwise',
                'created_at': datetime.now().isoformat(),
                'file_size': len(content),
                'file_type': 'highlight' if metadata.get('source_type') == 'readwise' else 'document',
                'metadata': json.dumps(metadata)
            }

            # Add to table
            self.table.add([record])

            logger.info(f"Added document: {doc_id}")

        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise

    async def close(self):
        """Close the vector store connection."""
        if self.db:
            # LanceDB doesn't require explicit closing
            pass
        logger.info("Vector store closed")
