"""
Shared utility functions
"""
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from datetime import datetime


def compute_file_hash(filepath: Path, algorithm: str = 'md5') -> str:
    """Compute hash of file for deduplication"""
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def safe_get_nested(data: Dict, keys: List[str], default: Any = None) -> Any:
    """Safely get nested dictionary value"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        else:
            return default
    return data if data != {} else default


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_timestamp(timestamp: Optional[float] = None) -> str:
    """Format timestamp as ISO string"""
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    return datetime.fromtimestamp(timestamp).isoformat()


def truncate_string(s: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate string to max length"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """Clean text for embedding generation"""
    if not text:
        return ""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove special characters that don't help with search
    text = text.replace('\x00', ' ')
    return text.strip()


def extract_filename_metadata(filepath: Path) -> Dict[str, Any]:
    """Extract metadata from filename patterns"""
    metadata = {}
    name = filepath.stem
    
    # Look for common patterns
    import re
    
    # Date patterns (YYYYMMDD, YYYY-MM-DD, etc.)
    date_patterns = [
        r'(\d{4})(\d{2})(\d{2})',
        r'(\d{4})-(\d{2})-(\d{2})',
        r'(\d{4})_(\d{2})_(\d{2})'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, name)
        if match:
            metadata['date_from_filename'] = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            break
    
    # Version patterns (v1, v2.0, version_3, etc.)
    version_match = re.search(r'v(?:ersion)?[_\-]?(\d+(?:\.\d+)?)', name, re.IGNORECASE)
    if version_match:
        metadata['version'] = version_match.group(1)
    
    # Common variable abbreviations
    var_hints = {
        'sst': 'sea_surface_temperature',
        'ssh': 'sea_surface_height',
        'sss': 'sea_surface_salinity',
        'temp': 'temperature',
        'sal': 'salinity',
        'wind': 'wind_speed',
        'precip': 'precipitation',
        'press': 'pressure'
    }
    
    name_lower = name.lower()
    for abbr, full_name in var_hints.items():
        if abbr in name_lower:
            metadata.setdefault('variables_hint', []).append(full_name)
    
    return metadata


def pretty_print_dict(data: Dict, indent: int = 2, max_depth: int = 3, 
                      current_depth: int = 0) -> str:
    """Pretty print dictionary with depth limit"""
    if current_depth >= max_depth:
        return str(data)
    
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            if current_depth < max_depth - 1:
                nested = pretty_print_dict(value, indent, max_depth, current_depth + 1)
                lines.append(f"{' ' * (indent * current_depth)}{key}:")
                lines.append(nested)
            else:
                lines.append(f"{' ' * (indent * current_depth)}{key}: {{...}}")
        elif isinstance(value, (list, tuple)):
            if len(value) > 5:
                lines.append(f"{' ' * (indent * current_depth)}{key}: [{len(value)} items]")
            else:
                lines.append(f"{' ' * (indent * current_depth)}{key}: {value}")
        else:
            lines.append(f"{' ' * (indent * current_depth)}{key}: {value}")
    
    return '\n'.join(lines)


def merge_metadata(base: Dict, additional: Dict, prefix: Optional[str] = None) -> Dict:
    """Merge additional metadata into base, optionally with prefix"""
    result = base.copy()
    
    for key, value in additional.items():
        new_key = f"{prefix}_{key}" if prefix else key
        
        if new_key in result:
            # Handle conflicts
            if isinstance(result[new_key], list) and not isinstance(value, list):
                result[new_key].append(value)
            elif not isinstance(result[new_key], list) and isinstance(value, list):
                result[new_key] = [result[new_key]] + value
            elif isinstance(result[new_key], list) and isinstance(value, list):
                result[new_key].extend(value)
            else:
                result[f"{new_key}_additional"] = value
        else:
            result[new_key] = value
    
    return result


def save_json(data: Any, filepath: Path, indent: int = 2) -> None:
    """Save data as JSON"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(filepath: Path) -> Any:
    """Load data from JSON"""
    with open(filepath, 'r') as f:
        return json.load(f)
