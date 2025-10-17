"""
Configuration settings for FAIR Scientific Data Discovery System
"""
from pathlib import Path
from typing import Dict, List

# Paths
BASE_DIR = Path(__file__).parent
GENERATED_DIR = BASE_DIR.parent / "generated"  # All generated files go here
INDEX_DIR = GENERATED_DIR / "indexes"
CACHE_DIR = GENERATED_DIR / "cache"
TEMP_DIR = GENERATED_DIR / "temp"

# Create directories
GENERATED_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Index files

# Embedding model

# Search settings
DEFAULT_TOP_K = 10

# File type magic bytes
MAGIC_BYTES: Dict[str, List[bytes]] = {
    'netcdf': [b'CDF\x01', b'CDF\x02', b'\x89HDF\r\n\x1a\n'],
    'hdf5': [b'\x89HDF\r\n\x1a\n'],
    'grib': [b'GRIB'],
    'html': [b'<!DOCTYPE', b'<html', b'<HTML'],
    'xml': [b'<?xml'],
    'pdf': [b'%PDF'],
    'zip': [b'PK\x03\x04', b'PK\x05\x06'],
    'tar': [b'ustar\x00', b'ustar\x20\x20\x00'],
    'gzip': [b'\x1f\x8b']
}

# Supported file extensions
SCIENTIFIC_DATA_EXTENSIONS = {'.nc', '.nc4', '.hdf', '.hdf5', '.h5', '.grb', '.grb2', '.grib', '.grib2'}
ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2'}
COMPANION_DOC_EXTENSIONS = {'.txt', '.md', '.pdf', '.rst', '.doc', '.docx'}
SCRIPT_EXTENSIONS = {'.py', '.r', '.m', '.ipynb', '.sh', '.bash'}

# Companion document patterns
README_PATTERNS = ['readme*', 'README*', 'ReadMe*']
CITATION_PATTERNS = ['citation*', 'CITATION*', 'references*', 'doi*', 'paper*']
DOCUMENTATION_PATTERNS = ['*documentation*', '*manual*', '*guide*', 'data_dictionary*']

# LLM settings (optional)
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434"

# Processing settings
BATCH_SIZE = 100
MAX_WORKERS = 4
PROGRESS_BAR = True

# Validation settings
MIN_FILE_SIZE = 100  # bytes
MAX_HEADER_BYTES = 1024  # bytes to read for validation
