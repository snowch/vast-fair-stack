"""
Metadata extraction for NetCDF, HDF5, and GRIB files
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
import warnings
from utils import clean_text, extract_filename_metadata

warnings.filterwarnings('ignore')


class NetCDFExtractor:
    """Extract metadata from NetCDF files"""
    
    def extract(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata from NetCDF file"""
        try:
            import netCDF4
        except ImportError:
            return {'error': 'netCDF4 not installed'}
        
        metadata = {
            'filepath': str(filepath),
            'format': 'NetCDF',
            'file_size': filepath.stat().st_size,
        }
        
        try:
            with netCDF4.Dataset(filepath, 'r') as ds:
                # Global attributes
                metadata['global_attributes'] = {
                    attr: str(ds.getncattr(attr)) 
                    for attr in ds.ncattrs()
                }
                
                # Dimensions
                metadata['dimensions'] = {
                    dim: len(ds.dimensions[dim]) 
                    for dim in ds.dimensions
                }
                
                # Variables
                variables = {}
                for var_name in ds.variables:
                    var = ds.variables[var_name]
                    var_info = {
                        'dimensions': var.dimensions,
                        'shape': var.shape,
                        'dtype': str(var.dtype),
                        'attributes': {
                            attr: str(var.getncattr(attr)) 
                            for attr in var.ncattrs()
                        }
                    }
                    variables[var_name] = var_info
                
                metadata['variables'] = variables
                metadata['num_variables'] = len(variables)
                
                # Extract common metadata
                metadata['title'] = metadata['global_attributes'].get('title', '')
                metadata['institution'] = metadata['global_attributes'].get('institution', '')
                metadata['source'] = metadata['global_attributes'].get('source', '')
                metadata['history'] = metadata['global_attributes'].get('history', '')
                metadata['references'] = metadata['global_attributes'].get('references', '')
                metadata['comment'] = metadata['global_attributes'].get('comment', '')
                
                # Conventions
                metadata['conventions'] = metadata['global_attributes'].get('Conventions', '')
                
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata


class HDF5Extractor:
    """Extract metadata from HDF5 files"""
    
    def extract(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata from HDF5 file"""
        try:
            import h5py
        except ImportError:
            return {'error': 'h5py not installed'}
        
        metadata = {
            'filepath': str(filepath),
            'format': 'HDF5',
            'file_size': filepath.stat().st_size,
        }
        
        try:
            with h5py.File(filepath, 'r') as f:
                # Root attributes
                metadata['root_attributes'] = {
                    key: self._convert_attr(f.attrs[key]) 
                    for key in f.attrs.keys()
                }
                
                # Recursively get structure
                structure = {}
                self._explore_group(f, structure)
                metadata['structure'] = structure
                
                # Count datasets
                num_datasets = self._count_datasets(structure)
                metadata['num_datasets'] = num_datasets
                
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    def _explore_group(self, group, structure: Dict, max_depth: int = 5, 
                       current_depth: int = 0):
        """Recursively explore HDF5 group structure"""
        if current_depth >= max_depth:
            return
        
        for key in group.keys():
            item = group[key]
            
            if hasattr(item, 'shape'):  # Dataset
                structure[key] = {
                    'type': 'dataset',
                    'shape': item.shape,
                    'dtype': str(item.dtype),
                    'attributes': {
                        attr: self._convert_attr(item.attrs[attr])
                        for attr in item.attrs.keys()
                    }
                }
            else:  # Group
                structure[key] = {
                    'type': 'group',
                    'attributes': {
                        attr: self._convert_attr(item.attrs[attr])
                        for attr in item.attrs.keys()
                    },
                    'contents': {}
                }
                self._explore_group(item, structure[key]['contents'], 
                                  max_depth, current_depth + 1)
    
    def _convert_attr(self, attr):
        """Convert HDF5 attribute to Python type"""
        try:
            if hasattr(attr, 'decode'):
                return attr.decode('utf-8')
            elif hasattr(attr, 'tolist'):
                return attr.tolist()
            else:
                return str(attr)
        except:
            return str(attr)
    
    def _count_datasets(self, structure: Dict) -> int:
        """Count total number of datasets"""
        count = 0
        for key, value in structure.items():
            if isinstance(value, dict):
                if value.get('type') == 'dataset':
                    count += 1
                elif 'contents' in value:
                    count += self._count_datasets(value['contents'])
        return count


class GRIBExtractor:
    """Extract metadata from GRIB files"""
    
    def extract(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata from GRIB file"""
        try:
            import pygrib
        except ImportError:
            return {'error': 'pygrib not installed'}
        
        metadata = {
            'filepath': str(filepath),
            'format': 'GRIB',
            'file_size': filepath.stat().st_size,
        }
        
        try:
            with pygrib.open(str(filepath)) as grbs:
                messages = []
                for grb in grbs:
                    msg_info = {
                        'name': grb.name,
                        'shortName': getattr(grb, 'shortName', ''),
                        'units': getattr(grb, 'units', ''),
                        'level': getattr(grb, 'level', ''),
                        'typeOfLevel': getattr(grb, 'typeOfLevel', ''),
                        'dataDate': getattr(grb, 'dataDate', ''),
                        'dataTime': getattr(grb, 'dataTime', ''),
                        'shape': grb.values.shape if hasattr(grb, 'values') else None,
                    }
                    messages.append(msg_info)
                
                metadata['messages'] = messages
                metadata['num_messages'] = len(messages)
                
                # Extract unique values
                metadata['variables'] = list(set(msg['name'] for msg in messages))
                metadata['levels'] = list(set(msg['level'] for msg in messages))
                
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata


class MetadataExtractor:
    """Unified metadata extractor for all formats"""
    
    def __init__(self):
        self.netcdf = NetCDFExtractor()
        self.hdf5 = HDF5Extractor()
        self.grib = GRIBExtractor()
    
    def extract(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata from any supported file"""
        filepath = Path(filepath)
        ext = filepath.suffix.lower()
        
        # Add filename-based metadata
        metadata = extract_filename_metadata(filepath)
        metadata['filename'] = filepath.name
        
        # Format-specific extraction
        if ext in ['.nc', '.nc4']:
            format_metadata = self.netcdf.extract(filepath)
        elif ext in ['.hdf', '.hdf5', '.h5']:
            format_metadata = self.hdf5.extract(filepath)
        elif ext in ['.grb', '.grb2', '.grib', '.grib2']:
            format_metadata = self.grib.extract(filepath)
        else:
            return {
                'error': f'Unsupported file extension: {ext}',
                'filepath': str(filepath)
            }
        
        # Merge
        metadata.update(format_metadata)
        
        return metadata
    
    def create_searchable_text(self, metadata: Dict[str, Any]) -> str:
        """Create searchable text representation from metadata"""
        text_parts = []
        
        # Filename (without extension)
        if 'filename' in metadata:
            text_parts.append(Path(metadata['filename']).stem.replace('_', ' '))
        
        # Format
        if 'format' in metadata:
            text_parts.append(f"Format: {metadata['format']}")
        
        # Title and description
        for key in ['title', 'description', 'comment', 'summary']:
            if key in metadata and metadata[key]:
                text_parts.append(clean_text(str(metadata[key])))
        
        # Institution and source
        for key in ['institution', 'source', 'creator']:
            if key in metadata and metadata[key]:
                text_parts.append(clean_text(str(metadata[key])))
        
        # Variables
        if 'variables' in metadata:
            if isinstance(metadata['variables'], dict):
                var_names = list(metadata['variables'].keys())
                text_parts.append(f"Variables: {', '.join(var_names)}")
                
                # Add variable descriptions
                for var_name, var_info in metadata['variables'].items():
                    if isinstance(var_info, dict):
                        var_attrs = var_info.get('attributes', {})
                        if 'long_name' in var_attrs:
                            text_parts.append(f"{var_name}: {var_attrs['long_name']}")
                        if 'standard_name' in var_attrs:
                            text_parts.append(f"{var_name}: {var_attrs['standard_name']}")
            elif isinstance(metadata['variables'], list):
                text_parts.append(f"Variables: {', '.join(metadata['variables'])}")
        
        # Dimensions
        if 'dimensions' in metadata:
            dim_info = ', '.join(f"{k}={v}" for k, v in metadata['dimensions'].items())
            text_parts.append(f"Dimensions: {dim_info}")
        
        # Global attributes
        if 'global_attributes' in metadata:
            for key, value in metadata['global_attributes'].items():
                if key.lower() not in ['history']:  # Skip verbose fields
                    text_parts.append(f"{key}: {clean_text(str(value))}")
        
        return ' '.join(text_parts)
