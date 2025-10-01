"""
Discover companion documentation files (READMEs, scripts, citations)
- Fixed to avoid picking up system files and notebooks
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
                       search_parent: bool = False,
                       search_siblings: bool = True) -> Dict[str, List[Path]]:
        """
        Find all companion documents for a data file
        
        Args:
            data_filepath: Path to the data file
            search_parent: Search parent directory (disabled by default to avoid system files)
            search_siblings: Search for related data files
        """
        companions = {
            'readmes': [],
            'citations': [],
            'documentation': [],
            'scripts': [],
            'related_data': []
        }
        
        data_filepath = Path(data_filepath)
        data_dir = data_filepath.parent
        search_dirs = [data_dir]
        
        # Only search parent if it looks like a data directory
        # (not a project root with Python code)
        if search_parent and data_filepath.parent.parent:
            parent_dir = data_filepath.parent.parent
            # Don't search parent if it contains typical project files
            project_markers = ['setup.py', 'setup.sh', 'requirements.txt', '.git', 'lib', 'src']
            has_project_markers = any((parent_dir / marker).exists() for marker in project_markers)
            
            if not has_project_markers:
                search_dirs.append(parent_dir)
        
        for search_dir in search_dirs:
            # Find READMEs (only in data directory)
            for pattern in self.readme_patterns:
                found_files = search_dir.glob(pattern)
                companions['readmes'].extend(
                    f for f in found_files 
                    if self._is_likely_companion(f, data_dir)
                )
            
            # Find citations
            for pattern in self.citation_patterns:
                found_files = search_dir.glob(pattern)
                companions['citations'].extend(
                    f for f in found_files
                    if self._is_likely_companion(f, data_dir)
                )
            
            # Find documentation
            for pattern in self.doc_patterns:
                found_files = search_dir.glob(pattern)
                companions['documentation'].extend(
                    f for f in found_files
                    if self._is_likely_companion(f, data_dir)
                )
            
            # Find scripts (exclude system notebooks and setup scripts)
            for ext in config.SCRIPT_EXTENSIONS:
                found_files = search_dir.glob(f"*{ext}")
                # Filter out notebooks with numbered prefixes (00_, 01_, etc.)
                # and setup/system scripts
                companions['scripts'].extend(
                    f for f in found_files
                    if self._is_likely_companion(f, data_dir) and 
                    not self._is_system_file(f)
                )
        
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
    
    def _is_likely_companion(self, filepath: Path, data_dir: Path) -> bool:
        """Check if file is likely a companion to data (not system file)"""
        # Must be in same directory as data or immediate subdirectory
        try:
            filepath.relative_to(data_dir)
            return True
        except ValueError:
            # Not in data directory tree
            return False
    
    def _is_system_file(self, filepath: Path) -> bool:
        """Check if file is a system/project file (not a data companion)"""
        name = filepath.name.lower()
        
        # Exclude numbered notebooks (00_, 01_, 99_, etc.)
        if name.endswith('.ipynb'):
            import re
            if re.match(r'^\d{2}_', name):
                return True
        
        # Exclude common setup/system scripts
        system_scripts = {
            'setup.sh', 'setup.py', 'install.sh', 'run.sh',
            'run_jupyterlab.sh', 'test.py', 'tests.py',
            '__init__.py', 'conftest.py'
        }
        if name in system_scripts:
            return True
        
        # Exclude if in certain directories
        excluded_dirs = {'lib', 'src', 'tests', 'docs', '.git', '__pycache__'}
        if any(excluded in filepath.parts for excluded in excluded_dirs):
            return True
        
        return False
    
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
        
        # Search directory (NOT recursively to avoid picking up subdirectories)
        for pattern in self.readme_patterns:
            companions['readmes'].extend(directory.glob(pattern))
        
        for pattern in self.citation_patterns:
            companions['citations'].extend(directory.glob(pattern))
        
        for pattern in self.doc_patterns:
            companions['documentation'].extend(directory.glob(pattern))
        
        for ext in config.SCRIPT_EXTENSIONS:
            found_files = directory.glob(f"*{ext}")
            companions['scripts'].extend(
                f for f in found_files
                if not self._is_system_file(f)
            )
        
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