"""
Main search engine combining all components
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from tqdm import tqdm

from metadata_extractors import MetadataExtractor
from companion_finder import CompanionDocFinder
from companion_extractor import CompanionDocExtractor
from archive_handler import ArchiveAwareIndexer
from embedding_generator import CachedEmbeddingGenerator
from vector_index import VectorIndex
from file_validator import FileValidator
import config


class FAIRSearchEngine:
    """Complete FAIR data discovery search engine"""
    
    def __init__(self, load_existing: bool = True):
        """
        Initialize search engine
        
        Args:
            load_existing: Try to load existing index
        """
        # Initialize components
        self.metadata_extractor = MetadataExtractor()
        self.companion_finder = CompanionDocFinder()
        self.companion_extractor = CompanionDocExtractor()
        self.embedding_generator = CachedEmbeddingGenerator()
        self.validator = FileValidator()
        
        # Initialize or load index
        if load_existing and config.FAISS_INDEX_FILE.exists():
            print("Loading existing index...")
            self.vector_index = VectorIndex.load()
        else:
            print("Creating new index...")
            embedding_dim = self.embedding_generator.get_embedding_dim()
            self.vector_index = VectorIndex(embedding_dim)
    
    def index_file(self, filepath: Path, 
                   validate: bool = True,
                   include_companions: bool = True) -> Dict[str, Any]:
        """Index a single file"""
        filepath = Path(filepath)
        
        # Validate file
        if validate:
            is_valid, message = self._quick_validate(filepath)
            if not is_valid:
                return {'error': message, 'filepath': str(filepath)}
        
        # Extract metadata
        metadata = self.metadata_extractor.extract(filepath)
        
        if 'error' in metadata:
            return metadata
        
        # Find and extract companion docs
        if include_companions:
            companions = self.companion_finder.find_companions(filepath)
            companion_data = self._extract_companions(companions)
            metadata['companion_docs'] = companion_data
            
            # Create summary for search
            companion_text = self.companion_extractor.create_companion_summary(
                companion_data
            )
        else:
            companion_text = ""
        
        # Create searchable text
        base_text = self.metadata_extractor.create_searchable_text(metadata)
        searchable_text = f"{base_text} {companion_text}"
        
        # Generate embedding
        embedding = self.embedding_generator.encode_single(searchable_text)
        
        # Add to index
        self.vector_index.add(
            embedding.reshape(1, -1),
            [metadata]
        )
        
        return {
            'success': True,
            'filepath': str(filepath),
            'searchable_text_length': len(searchable_text)
        }
    
    def index_directory(self, directory: Path,
                       validate: bool = True,
                       include_companions: bool = True,
                       extract_archives: bool = True,
                       show_progress: bool = True) -> Dict[str, Any]:
        """Index all files in directory"""
        directory = Path(directory)
        
        # Use archive-aware indexer
        indexer = ArchiveAwareIndexer(
            self.metadata_extractor,
            self.companion_finder if include_companions else None
        )
        
        # Get all files
        results = indexer.index_path(directory, extract_archives)
        
        # Process each file
        indexed_count = 0
        error_count = 0
        
        iterator = results['indexed_files']
        if show_progress:
            iterator = tqdm(iterator, desc="Indexing files")
        
        for metadata in iterator:
            try:
                # Extract companion info if present
                companion_text = ""
                if 'companions' in metadata:
                    companion_data = self._extract_companions_from_paths(
                        metadata['companions']
                    )
                    companion_text = self.companion_extractor.create_companion_summary(
                        companion_data
                    )
                
                # Create searchable text
                base_text = self.metadata_extractor.create_searchable_text(metadata)
                searchable_text = f"{base_text} {companion_text}"
                
                # Generate embedding
                embedding = self.embedding_generator.encode_single(searchable_text)
                
                # Add to index
                self.vector_index.add(
                    embedding.reshape(1, -1),
                    [metadata]
                )
                
                indexed_count += 1
            
            except Exception as e:
                error_count += 1
                results['errors'].append({
                    'filepath': metadata.get('filepath', 'unknown'),
                    'error': str(e)
                })
        
        return {
            'success': True,
            'indexed': indexed_count,
            'errors': error_count,
            'archives_processed': len(results['archives_processed']),
            'details': results
        }
    
    def search(self, query: str, 
               top_k: int = config.DEFAULT_TOP_K,
               threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Search for datasets using natural language query"""
        # Generate query embedding
        query_embedding = self.embedding_generator.encode_single(query)
        
        # Search index
        results = self.vector_index.search(query_embedding, top_k, threshold)
        
        return results
    
    def find_similar(self, filepath: Path, 
                    top_k: int = config.DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        """Find similar datasets to a given file"""
        # Get metadata and create searchable text
        metadata = self.metadata_extractor.extract(filepath)
        searchable_text = self.metadata_extractor.create_searchable_text(metadata)
        
        # Search
        return self.search(searchable_text, top_k)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        index_stats = self.vector_index.get_stats()
        
        return {
            **index_stats,
            'model': self.embedding_generator.model_name,
            'cache_size': len(self.embedding_generator.cache)
        }
    
    def save(self):
        """Save index to disk"""
        self.vector_index.save()
        self.embedding_generator._save_cache()
    
    def _quick_validate(self, filepath: Path) -> tuple:
        """Quick validation wrapper"""
        from file_validator import quick_validate
        return quick_validate(filepath)
    
    def _extract_companions(self, companions: Dict[str, List[Path]]) -> List[Dict]:
        """Extract content from companion documents"""
        companion_data = []
        
        for readme_path in companions.get('readmes', [])[:3]:  # Limit
            try:
                data = self.companion_extractor.extract_readme(readme_path)
                companion_data.append(data)
            except:
                pass
        
        for citation_path in companions.get('citations', [])[:2]:
            try:
                data = self.companion_extractor.extract_citation_info(citation_path)
                companion_data.append(data)
            except:
                pass
        
        for script_path in companions.get('scripts', [])[:2]:
            try:
                data = self.companion_extractor.extract_script_metadata(script_path)
                companion_data.append(data)
            except:
                pass
        
        return companion_data
    
    def _extract_companions_from_paths(self, companion_paths: Dict[str, List[str]]) -> List[Dict]:
        """Extract companions from path strings"""
        companions = {
            key: [Path(p) for p in paths]
            for key, paths in companion_paths.items()
        }
        return self._extract_companions(companions)
