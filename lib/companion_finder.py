"""
Discover companion documentation files (READMEs, scripts, citations)
"""
from pathlib import Path
from typing import Dict, List, Optional
import config


class CompanionDocFinder:
    """Find companion documentation for scientific data files"""
    
    def __init__(self):
        self.readme_patterns = config.README_PATTERNS
        self.citation_patterns = config.CITATION_PATTERNS
        self.doc_patterns = config.DOCUMENTATION_PATTERNS
    
    def find_companions(self, data_filepath: Path, 
                       search_parent: bool = True,
                       search_siblings: bool = True) -> Dict[str, List[Path]]:
        """Find all companion documents for a data file"""
        companions = {
            'readmes': [],
            'citations': [],
            'documentation': [],
            'scripts': [],
            'related_data': []
        }
        
        data_filepath = Path(data_filepath)
        search_dirs = [data_filepath.parent]
        
        # Also search parent directory
        if search_parent and data_filepath.parent.parent:
            search_dirs.append(data_filepath.parent.parent)
        
        for search_dir in search_dirs:
            # Find READMEs
            for pattern in self.readme_patterns:
                companions['readmes'].extend(search_dir.glob(pattern))
            
            # Find citations
            for pattern in self.citation_patterns:
                companions['citations'].extend(search_dir.glob(pattern))
            
            # Find documentation
            for pattern in self.doc_patterns:
                companions['documentation'].extend(search_dir.glob(pattern))
            
            # Find scripts
            for ext in config.SCRIPT_EXTENSIONS:
                companions['scripts'].extend(search_dir.glob(f"*{ext}"))
        
        # Find related data files (same prefix)
        if search_siblings:
            companions['related_data'] = self._find_related_files(data_filepath)
        
        # Remove duplicates and the data file itself
        for key in companions:
            companions[key] = [
                f for f in set(companions[key]) 
                if f.resolve() != data_filepath.resolve()
            ]
        
        return companions
    
    def _find_related_files(self, filepath: Path) -> List[Path]:
        """Find files with same prefix (likely related)"""
        # Get base name without date/version suffixes
        import re
        base_name = filepath.stem
        
        # Remove common suffixes
        base_name = re.sub(r'[_\-](v?\d+\.?\d*)$', '', base_name)
        base_name = re.sub(r'[_\-]\d{8}$', '', base_name)
        base_name = re.sub(r'[_\-]\d{4}-\d{2}-\d{2}$', '', base_name)
        
        # Find files with similar names
        related = []
        for ext in config.SCIENTIFIC_DATA_EXTENSIONS:
            pattern = f"{base_name}*{ext}"
            related.extend(filepath.parent.glob(pattern))
        
        return related
    
    def find_directory_companions(self, directory: Path) -> Dict[str, List[Path]]:
        """Find all companion docs in a directory"""
        companions = {
            'readmes': [],
            'citations': [],
            'documentation': [],
            'scripts': []
        }
        
        directory = Path(directory)
        
        # Search directory and subdirectories
        for pattern in self.readme_patterns:
            companions['readmes'].extend(directory.rglob(pattern))
        
        for pattern in self.citation_patterns:
            companions['citations'].extend(directory.rglob(pattern))
        
        for pattern in self.doc_patterns:
            companions['documentation'].extend(directory.rglob(pattern))
        
        for ext in config.SCRIPT_EXTENSIONS:
            companions['scripts'].extend(directory.rglob(f"*{ext}"))
        
        # Remove duplicates
        for key in companions:
            companions[key] = list(set(companions[key]))
        
        return companions
    
    def get_companion_summary(self, companions: Dict[str, List[Path]]) -> str:
        """Create text summary of companion documents"""
        summary_parts = []
        
        for doc_type, files in companions.items():
            if files:
                summary_parts.append(
                    f"{doc_type.replace('_', ' ').title()}: "
                    f"{len(files)} file(s)"
                )
        
        return "; ".join(summary_parts) if summary_parts else "No companions found"
