"""
Generate embeddings using sentence-transformers (local)
"""
import numpy as np
from typing import List, Union, Optional
import config


class EmbeddingGenerator:
    """Generate embeddings using local sentence-transformer model"""
    
    def __init__(self, model_name: Optional[str] = None, device: str = 'cpu'):
        """
        Initialize embedding generator
        
        Args:
            model_name: Name of sentence-transformer model
            device: 'cpu' or 'cuda'
        """
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.device = device
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence-transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        print(f"Model loaded. Embedding dimension: {self.get_embedding_dim()}")
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()
    
    def encode(self, texts: Union[str, List[str]], 
               batch_size: int = 32,
               show_progress: bool = False) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True  # Important for cosine similarity
        )
        
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text (convenience method)"""
        return self.encode(text)[0]


class CachedEmbeddingGenerator(EmbeddingGenerator):
    """Embedding generator with caching"""
    
    def __init__(self, model_name: Optional[str] = None, device: str = 'cpu',
                 cache_dir: Optional[str] = None):
        super().__init__(model_name, device)
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        self.cache = {}
        self._load_cache()
    
    def _get_cache_path(self):
        """Get path to cache file"""
        return self.cache_dir / "embedding_cache.pkl"
    
    def _load_cache(self):
        """Load cache from disk"""
        cache_path = self._get_cache_path()
        if cache_path.exists():
            try:
                import pickle
                with open(cache_path, 'rb') as f:
                    self.cache = pickle.load(f)
                print(f"Loaded embedding cache: {len(self.cache)} entries")
            except Exception as e:
                print(f"Could not load cache: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk"""
        cache_path = self._get_cache_path()
        try:
            import pickle
            with open(cache_path, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"Could not save cache: {e}")
    
    def encode(self, texts: Union[str, List[str]], 
               batch_size: int = 32,
               show_progress: bool = False,
               use_cache: bool = True) -> np.ndarray:
        """Encode with caching support"""
        if isinstance(texts, str):
            texts = [texts]
        
        if not use_cache:
            return super().encode(texts, batch_size, show_progress)
        
        # Check cache
        embeddings = []
        texts_to_encode = []
        cache_indices = []
        
        for i, text in enumerate(texts):
            if text in self.cache:
                embeddings.append(self.cache[text])
                cache_indices.append(i)
            else:
                texts_to_encode.append(text)
        
        # Encode uncached texts
        if texts_to_encode:
            new_embeddings = super().encode(texts_to_encode, batch_size, show_progress)
            
            # Update cache
            for text, embedding in zip(texts_to_encode, new_embeddings):
                self.cache[text] = embedding
            
            # Merge results
            result = np.zeros((len(texts), self.get_embedding_dim()))
            result[cache_indices] = np.array(embeddings)
            
            non_cache_indices = [i for i in range(len(texts)) if i not in cache_indices]
            result[non_cache_indices] = new_embeddings
            
            # Save cache periodically
            if len(texts_to_encode) > 10:
                self._save_cache()
            
            return result
        else:
            return np.array(embeddings)
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache = {}
        cache_path = self._get_cache_path()
        if cache_path.exists():
            cache_path.unlink()
