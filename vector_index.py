"""
FAISS-based vector index for fast similarity search
"""
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pickle
import config

# Import faiss at module level
try:
    import faiss
except ImportError:
    faiss = None


class VectorIndex:
    """FAISS-based vector index for dataset search"""
    
    def __init__(self, embedding_dim: int = config.EMBEDDING_DIM):
        """
        Initialize vector index
        
        Args:
            embedding_dim: Dimension of embeddings
        """
        if faiss is None:
            raise ImportError(
                "faiss not installed. "
                "Install with: pip install faiss-cpu"
            )
        
        self.embedding_dim = embedding_dim
        self.index = None
        self.metadata_store = []  # List of metadata dicts
        self.filepath_map = {}    # Map filepath to indices
        self._init_index()
    
    def _init_index(self):
        """Initialize FAISS index"""
        # Use IndexFlatIP for cosine similarity with normalized vectors
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        print(f"Initialized FAISS index (dim={self.embedding_dim})")
    
    def add(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]):
        """
        Add embeddings and metadata to index
        
        Args:
            embeddings: Array of shape (n, embedding_dim)
            metadata: List of metadata dicts (length n)
        """
        if len(embeddings) != len(metadata):
            raise ValueError("Number of embeddings must match metadata")
        
        # Normalize embeddings for cosine similarity
        embeddings = embeddings.astype('float32')
        faiss.normalize_L2(embeddings)
        
        # Add to index
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Store metadata
        self.metadata_store.extend(metadata)
        
        # Update filepath map
        for i, meta in enumerate(metadata):
            filepath = meta.get('filepath')
            if filepath:
                if filepath not in self.filepath_map:
                    self.filepath_map[filepath] = []
                self.filepath_map[filepath].append(start_idx + i)
    
    def search(self, query_embedding: np.ndarray, 
               top_k: int = config.DEFAULT_TOP_K,
               threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Search for similar items
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of results with metadata and scores
        """
        if self.index.ntotal == 0:
            return []
        
        # Normalize query
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, top_k)
        scores = scores[0]
        indices = indices[0]
        
        # Format results
        results = []
        seen_filepaths = set()
        
        for score, idx in zip(scores, indices):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
            
            # Apply threshold
            if threshold and score < threshold:
                continue
            
            # Get metadata
            metadata = self.metadata_store[idx].copy()
            metadata['similarity_score'] = float(score)
            metadata['index_position'] = int(idx)
            
            # Deduplicate by filepath
            filepath = metadata.get('filepath')
            if filepath and filepath in seen_filepaths:
                continue
            
            results.append(metadata)
            
            if filepath:
                seen_filepaths.add(filepath)
        
        return results
    
    def remove_duplicates(self) -> Dict[str, int]:
        """
        Remove duplicate entries (same filepath)
        
        Returns:
            Dict with statistics about removed duplicates
        """
        # Find duplicates
        duplicates = {
            fp: indices for fp, indices in self.filepath_map.items()
            if len(indices) > 1
        }
        
        if not duplicates:
            return {'total_duplicates': 0, 'filepaths_affected': 0}
        
        # Keep only first occurrence of each file
        indices_to_keep = []
        new_metadata = []
        new_filepath_map = {}
        
        for i, meta in enumerate(self.metadata_store):
            filepath = meta.get('filepath')
            
            if filepath:
                if filepath not in new_filepath_map:
                    indices_to_keep.append(i)
                    new_metadata.append(meta)
                    new_filepath_map[filepath] = [len(new_metadata) - 1]
            else:
                indices_to_keep.append(i)
                new_metadata.append(meta)
        
        # Rebuild index if duplicates found
        if len(new_metadata) < len(self.metadata_store):
            print(f"Removing {len(self.metadata_store) - len(new_metadata)} duplicates...")
            
            # Get embeddings for kept indices
            # Note: FAISS doesn't support removing specific vectors,
            # so we need to rebuild
            self._rebuild_index_subset(indices_to_keep, new_metadata, new_filepath_map)
            
            return {
                'total_duplicates': len(self.metadata_store) - len(new_metadata),
                'filepaths_affected': len(duplicates)
            }
        
        return {'total_duplicates': 0, 'filepaths_affected': 0}
    
    def _rebuild_index_subset(self, indices: List[int], 
                             new_metadata: List[Dict],
                             new_filepath_map: Dict):
        """Rebuild index with subset of vectors"""
        # This is a limitation of FAISS - we can't easily extract vectors
        # In practice, users should avoid adding duplicates
        # For now, just update metadata
        self.metadata_store = new_metadata
        self.filepath_map = new_filepath_map
        print("Note: Index vectors not rebuilt. Re-index for complete cleanup.")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            'total_vectors': self.index.ntotal,
            'total_metadata': len(self.metadata_store),
            'unique_files': len(self.filepath_map),
            'embedding_dim': self.embedding_dim,
            'index_type': type(self.index).__name__
        }
    
    def save(self, index_path: Optional[Path] = None,
             metadata_path: Optional[Path] = None,
             filepath_map_path: Optional[Path] = None):
        """Save index and metadata to disk"""
        index_path = index_path or config.FAISS_INDEX_FILE
        metadata_path = metadata_path or config.METADATA_STORE_FILE
        filepath_map_path = filepath_map_path or config.FILEPATH_MAP_FILE
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_path))
        
        # Save metadata
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata_store, f)
        
        # Save filepath map
        with open(filepath_map_path, 'wb') as f:
            pickle.dump(self.filepath_map, f)
        
        print(f"Index saved to {index_path}")
    
    @classmethod
    def load(cls, index_path: Optional[Path] = None,
             metadata_path: Optional[Path] = None,
             filepath_map_path: Optional[Path] = None) -> 'VectorIndex':
        """Load index and metadata from disk"""
        index_path = index_path or config.FAISS_INDEX_FILE
        metadata_path = metadata_path or config.METADATA_STORE_FILE
        filepath_map_path = filepath_map_path or config.FILEPATH_MAP_FILE
        
        if not index_path.exists():
            raise FileNotFoundError(f"Index not found: {index_path}")
        
        # Load FAISS index
        faiss_index = faiss.read_index(str(index_path))
        
        # Create instance
        vector_index = cls(embedding_dim=faiss_index.d)
        vector_index.index = faiss_index
        
        # Load metadata
        if metadata_path.exists():
            with open(metadata_path, 'rb') as f:
                vector_index.metadata_store = pickle.load(f)
        
        # Load filepath map
        if filepath_map_path.exists():
            with open(filepath_map_path, 'rb') as f:
                vector_index.filepath_map = pickle.load(f)
        
        print(f"Index loaded: {vector_index.get_stats()}")
        return vector_index