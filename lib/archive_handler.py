"""
Handle compressed archives (.zip, .tar.gz, etc.)
"""
from pathlib import Path
from typing import Dict, List, Optional
import zipfile
import tarfile
import tempfile
import shutil
import config


class ArchiveHandler:
    """Handle extraction and processing of compressed archives"""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or config.TEMP_DIR
        self.temp_dir.mkdir(exist_ok=True)
        self._cleanup_dirs = []
    
    def is_archive(self, filepath: Path) -> bool:
        """Check if file is a supported archive"""
        return filepath.suffix.lower() in config.ARCHIVE_EXTENSIONS
    
    def extract_archive(self, archive_path: Path, 
                       extract_to: Optional[Path] = None) -> Path:
        """Extract archive to temporary directory"""
        archive_path = Path(archive_path)
        
        if extract_to is None:
            extract_to = Path(tempfile.mkdtemp(dir=self.temp_dir))
            self._cleanup_dirs.append(extract_to)
        else:
            extract_to = Path(extract_to)
            extract_to.mkdir(parents=True, exist_ok=True)
        
        ext = archive_path.suffix.lower()
        
        try:
            if ext == '.zip':
                self._extract_zip(archive_path, extract_to)
            elif ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']:
                self._extract_tar(archive_path, extract_to)
            else:
                raise ValueError(f"Unsupported archive format: {ext}")
        except Exception as e:
            raise RuntimeError(f"Failed to extract {archive_path}: {e}")
        
        return extract_to
    
    def _extract_zip(self, archive_path: Path, extract_to: Path):
        """Extract ZIP archive"""
        with zipfile.ZipFile(archive_path, 'r') as zf:
            # Security: check for path traversal
            for name in zf.namelist():
                if name.startswith('/') or '..' in name:
                    raise ValueError(f"Unsafe path in archive: {name}")
            
            zf.extractall(extract_to)
    
    def _extract_tar(self, archive_path: Path, extract_to: Path):
        """Extract TAR archive"""
        with tarfile.open(archive_path, 'r:*') as tf:
            # Security: check for path traversal
            for member in tf.getmembers():
                if member.name.startswith('/') or '..' in member.name:
                    raise ValueError(f"Unsafe path in archive: {member.name}")
            
            tf.extractall(extract_to)
    
    def find_data_files(self, directory: Path) -> List[Path]:
        """Find scientific data files in directory"""
        data_files = []
        
        for ext in config.SCIENTIFIC_DATA_EXTENSIONS:
            data_files.extend(directory.rglob(f"*{ext}"))
        
        return sorted(data_files)
    
    def get_archive_structure(self, archive_path: Path) -> Dict:
        """Get archive structure without extracting"""
        archive_path = Path(archive_path)
        ext = archive_path.suffix.lower()
        
        structure = {
            'archive_path': str(archive_path),
            'format': ext,
            'files': [],
            'data_files': [],
            'companion_files': [],
            'total_size': 0
        }
        
        try:
            if ext == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    for info in zf.filelist:
                        file_info = {
                            'name': info.filename,
                            'size': info.file_size,
                            'compressed_size': info.compress_size
                        }
                        structure['files'].append(file_info)
                        structure['total_size'] += info.file_size
                        
                        # Categorize
                        file_ext = Path(info.filename).suffix.lower()
                        if file_ext in config.SCIENTIFIC_DATA_EXTENSIONS:
                            structure['data_files'].append(info.filename)
                        elif file_ext in config.COMPANION_DOC_EXTENSIONS:
                            structure['companion_files'].append(info.filename)
            
            elif ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2']:
                with tarfile.open(archive_path, 'r:*') as tf:
                    for member in tf.getmembers():
                        if member.isfile():
                            file_info = {
                                'name': member.name,
                                'size': member.size
                            }
                            structure['files'].append(file_info)
                            structure['total_size'] += member.size
                            
                            # Categorize
                            file_ext = Path(member.name).suffix.lower()
                            if file_ext in config.SCIENTIFIC_DATA_EXTENSIONS:
                                structure['data_files'].append(member.name)
                            elif file_ext in config.COMPANION_DOC_EXTENSIONS:
                                structure['companion_files'].append(member.name)
        
        except Exception as e:
            structure['error'] = str(e)
        
        return structure
    
    def cleanup(self):
        """Clean up temporary extraction directories"""
        for temp_dir in self._cleanup_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        self._cleanup_dirs = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class ArchiveAwareIndexer:
    """Index scientific data with archive support"""
    
    def __init__(self, metadata_extractor, companion_finder=None):
        self.metadata_extractor = metadata_extractor
        self.companion_finder = companion_finder
        self.archive_handler = ArchiveHandler()
    
    def index_path(self, path: Path, extract_archives: bool = True) -> Dict:
        """Index a file or directory, handling archives"""
        path = Path(path)
        results = {
            'indexed_files': [],
            'errors': [],
            'archives_processed': []
        }
        
        if path.is_file():
            if self.archive_handler.is_archive(path) and extract_archives:
                self._index_archive(path, results)
            else:
                self._index_file(path, results)
        
        elif path.is_dir():
            self._index_directory(path, results, extract_archives)
        
        return results
    
    def _index_file(self, filepath: Path, results: Dict, 
                   archive_context: Optional[Dict] = None):
        """Index a single file"""
        try:
            metadata = self.metadata_extractor.extract(filepath)
            
            # Add archive context if from archive
            if archive_context:
                metadata['archive_context'] = archive_context
            
            # Find companions if available
            if self.companion_finder:
                companions = self.companion_finder.find_companions(filepath)
                metadata['companions'] = {
                    k: [str(f) for f in v] 
                    for k, v in companions.items()
                }
            
            results['indexed_files'].append(metadata)
        
        except Exception as e:
            results['errors'].append({
                'filepath': str(filepath),
                'error': str(e)
            })
    
    def _index_archive(self, archive_path: Path, results: Dict):
        """Extract and index files from archive"""
        with ArchiveHandler() as handler:
            try:
                # Extract
                extract_dir = handler.extract_archive(archive_path)
                
                # Find data files
                data_files = handler.find_data_files(extract_dir)
                
                # Index each file with archive context
                archive_context = {
                    'from_archive': archive_path.name,
                    'archive_path': str(archive_path)
                }
                
                for data_file in data_files:
                    # Add relative path within archive
                    rel_path = data_file.relative_to(extract_dir)
                    archive_context['relative_path'] = str(rel_path)
                    
                    self._index_file(data_file, results, archive_context)
                
                results['archives_processed'].append({
                    'archive': str(archive_path),
                    'files_found': len(data_files)
                })
            
            except Exception as e:
                results['errors'].append({
                    'archive': str(archive_path),
                    'error': str(e)
                })
    
    def _index_directory(self, directory: Path, results: Dict, 
                        extract_archives: bool):
        """Index all files in directory"""
        # Find archives
        archives = []
        for ext in config.ARCHIVE_EXTENSIONS:
            archives.extend(directory.rglob(f"*{ext}"))
        
        # Find data files
        data_files = []
        for ext in config.SCIENTIFIC_DATA_EXTENSIONS:
            data_files.extend(directory.rglob(f"*{ext}"))
        
        # Index archives
        if extract_archives:
            for archive in archives:
                self._index_archive(archive, results)
        
        # Index standalone data files
        for data_file in data_files:
            self._index_file(data_file, results)
