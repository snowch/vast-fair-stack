"""
File validation using magic bytes and content inspection
"""
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import config
from utils import format_size


class FileValidator:
    """Validate scientific data files"""
    
    def __init__(self):
        self.magic_bytes = config.MAGIC_BYTES
    
    def check_file_signature(self, filepath: Path) -> Dict:
        """Check file signature against known magic bytes"""
        result = {
            'filepath': str(filepath),
            'exists': filepath.exists(),
            'size': filepath.stat().st_size if filepath.exists() else 0,
            'size_formatted': None,
            'detected_type': None,
            'expected_type': None,
            'is_valid': False,
            'issues': []
        }
        
        if not result['exists']:
            result['issues'].append("File does not exist")
            return result
        
        result['size_formatted'] = format_size(result['size'])
        
        # Check minimum size
        if result['size'] < config.MIN_FILE_SIZE:
            result['issues'].append(f"File too small ({result['size']} bytes)")
            return result
        
        # Expected type from extension
        ext = filepath.suffix.lower()
        if ext in ['.nc', '.nc4']:
            result['expected_type'] = 'netcdf'
        elif ext in ['.hdf', '.hdf5', '.h5']:
            result['expected_type'] = 'hdf5'
        elif ext in ['.grb', '.grb2', '.grib', '.grib2']:
            result['expected_type'] = 'grib'
        
        # Read header
        try:
            with open(filepath, 'rb') as f:
                header = f.read(config.MAX_HEADER_BYTES)
        except Exception as e:
            result['issues'].append(f"Cannot read file: {e}")
            return result
        
        # Check magic bytes
        detected_types = []
        for file_type, signatures in self.magic_bytes.items():
            for signature in signatures:
                if header.startswith(signature):
                    detected_types.append(file_type)
                    break
        
        if detected_types:
            result['detected_type'] = detected_types[0]
        
        # Validation logic
        if result['detected_type'] == 'html':
            result['issues'].append("File is HTML (likely download error page)")
        elif result['detected_type'] == 'xml':
            result['issues'].append("File is XML (check if error response)")
        elif result['expected_type'] and result['detected_type']:
            # For NetCDF/HDF5, both might be detected (NetCDF uses HDF5)
            if result['expected_type'] == 'netcdf' and result['detected_type'] in ['netcdf', 'hdf5']:
                result['is_valid'] = True
            elif result['expected_type'] == 'hdf5' and result['detected_type'] == 'hdf5':
                result['is_valid'] = True
            elif result['expected_type'] == 'grib' and result['detected_type'] == 'grib':
                result['is_valid'] = True
            else:
                result['issues'].append(
                    f"Type mismatch: expected {result['expected_type']}, "
                    f"detected {result['detected_type']}"
                )
        elif result['expected_type'] and not result['detected_type']:
            result['issues'].append(f"Cannot detect valid {result['expected_type']} signature")
        elif not result['expected_type']:
            result['is_valid'] = bool(result['detected_type'])
            if not result['is_valid']:
                result['issues'].append("Unknown file type")
        
        return result
    
    def validate_directory(self, directory: Path, 
                          extensions: Optional[List[str]] = None) -> Dict:
        """Validate all scientific data files in directory"""
        if extensions is None:
            extensions = list(config.SCIENTIFIC_DATA_EXTENSIONS)
        
        files = []
        for ext in extensions:
            files.extend(directory.rglob(f"*{ext}"))
        
        results = {
            'directory': str(directory),
            'total_files': len(files),
            'valid': [],
            'invalid': [],
            'issues_summary': {}
        }
        
        for filepath in files:
            validation = self.check_file_signature(filepath)
            
            if validation['is_valid']:
                results['valid'].append(validation)
            else:
                results['invalid'].append(validation)
                
                # Summarize issues
                for issue in validation['issues']:
                    results['issues_summary'][issue] = \
                        results['issues_summary'].get(issue, 0) + 1
        
        return results
    
    def inspect_file_contents(self, filepath: Path, 
                             num_bytes: int = 512) -> str:
        """Inspect file contents for debugging"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read(num_bytes)
            
            # Show as hex and try to decode as text
            hex_view = ' '.join(f'{b:02x}' for b in data[:64])
            
            try:
                text_view = data.decode('utf-8', errors='replace')[:200]
            except:
                text_view = "(cannot decode as text)"
            
            return f"Hex (first 64 bytes):\n{hex_view}\n\nText preview:\n{text_view}"
        except Exception as e:
            return f"Error reading file: {e}"
    
    def suggest_fixes(self, validation_result: Dict) -> List[str]:
        """Suggest fixes for validation issues"""
        suggestions = []
        
        if not validation_result['is_valid']:
            issues = validation_result.get('issues', [])
            
            for issue in issues:
                if 'HTML' in issue or 'download error' in issue:
                    suggestions.append(
                        "Re-download the file. The URL may have returned an error page."
                    )
                elif 'Type mismatch' in issue:
                    suggestions.append(
                        "Rename file with correct extension or verify file source."
                    )
                elif 'too small' in issue:
                    suggestions.append(
                        "File appears truncated. Try re-downloading."
                    )
                elif 'Cannot detect' in issue:
                    suggestions.append(
                        "File may be corrupted. Verify with file provider."
                    )
        
        return list(set(suggestions))  # Remove duplicates


def quick_validate(filepath: Path) -> Tuple[bool, str]:
    """Quick validation check returning (is_valid, message)"""
    validator = FileValidator()
    result = validator.check_file_signature(filepath)
    
    if result['is_valid']:
        return True, f"Valid {result['detected_type']} file"
    else:
        issues = "; ".join(result['issues'])
        return False, f"Invalid: {issues}"
