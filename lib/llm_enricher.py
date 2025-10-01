"""
Optional LLM-based metadata enrichment using local Ollama
"""
from typing import Dict, Any, Optional, List
import json
import config


class LLMEnricher:
    """Enrich metadata using local LLM (Ollama)"""
    
    def __init__(self, model: str = config.OLLAMA_MODEL,
                 base_url: str = config.OLLAMA_URL):
        """
        Initialize LLM enricher
        
        Args:
            model: Ollama model name
            base_url: Ollama API URL
        """
        self.model = model
        self.base_url = base_url
        self._check_connection()
    
    def _check_connection(self):
        """Check if Ollama is running"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                print(f"Connected to Ollama at {self.base_url}")
            else:
                print(f"Warning: Could not connect to Ollama at {self.base_url}")
        except Exception as e:
            print(f"Warning: Ollama not available - {e}")
            print("Install with: curl -fsSL https://ollama.com/install.sh | sh")
    
    def enrich_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich metadata with LLM-derived information
        
        Args:
            metadata: Base metadata dictionary
            
        Returns:
            Enriched metadata dictionary
        """
        enriched = metadata.copy()
        
        # Create prompt
        prompt = self._create_enrichment_prompt(metadata)
        
        # Call LLM
        try:
            response = self._call_llm(prompt)
            derived_metadata = self._parse_response(response)
            
            # Add to metadata with 'llm_' prefix
            enriched['llm_enrichment'] = derived_metadata
            
        except Exception as e:
            enriched['llm_error'] = str(e)
        
        return enriched
    
    def _create_enrichment_prompt(self, metadata: Dict[str, Any]) -> str:
        """Create prompt for LLM enrichment"""
        # Extract key information
        filename = metadata.get('filename', 'unknown')
        variables = metadata.get('variables', {})
        institution = metadata.get('institution', '')
        title = metadata.get('title', '')
        
        var_names = list(variables.keys()) if isinstance(variables, dict) else variables
        
        prompt = f"""You are a scientific data metadata expert. Analyze this dataset and provide enriched metadata.

Dataset Information:
- Filename: {filename}
- Title: {title}
- Institution: {institution}
- Variables: {', '.join(var_names) if var_names else 'unknown'}

Please provide:
1. Scientific domain (e.g., oceanography, atmospheric science, climate)
2. Likely data source/institution (if not specified)
3. Variable descriptions (decode abbreviations)
4. Potential use cases
5. Data quality notes (if any concerns)

Respond in JSON format with these keys:
{{
  "domain": "...",
  "source_institution": "...",
  "variable_descriptions": {{"var": "description"}},
  "use_cases": ["..."],
  "quality_notes": "..."
}}

Keep responses concise and factual."""
        
        return prompt
    
    def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Call Ollama API"""
        import requests
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature
            },
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()['response']
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response"""
        try:
            # Try to find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback: return raw response
                return {'raw_response': response}
        except:
            return {'raw_response': response}
    
    def enrich_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich search results with summaries"""
        enriched_results = []
        
        for result in results:
            # Create short summary
            prompt = f"""Summarize this scientific dataset in 1-2 sentences:

Title: {result.get('title', 'N/A')}
Variables: {', '.join(list(result.get('variables', {}).keys())[:5])}
Institution: {result.get('institution', 'N/A')}

One sentence summary:"""
            
            try:
                summary = self._call_llm(prompt, temperature=0.3)
                result['llm_summary'] = summary.strip()
            except:
                pass
            
            enriched_results.append(result)
        
        return enriched_results


class DataInspector:
    """Inspect actual data values to enrich metadata"""
    
    @staticmethod
    def get_variable_statistics(filepath: str, variable_name: str) -> Dict[str, Any]:
        """Get statistics for a variable"""
        try:
            import netCDF4
            import numpy as np
            
            with netCDF4.Dataset(filepath, 'r') as ds:
                if variable_name not in ds.variables:
                    return {'error': f'Variable {variable_name} not found'}
                
                var = ds.variables[variable_name]
                data = var[:]
                
                # Handle masked arrays
                if hasattr(data, 'compressed'):
                    data = data.compressed()
                
                stats = {
                    'min': float(np.min(data)),
                    'max': float(np.max(data)),
                    'mean': float(np.mean(data)),
                    'std': float(np.std(data)),
                    'shape': var.shape,
                    'dtype': str(var.dtype)
                }
                
                return stats
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def check_temporal_coverage(filepath: str) -> Dict[str, Any]:
        """Check temporal coverage from time variable"""
        try:
            import netCDF4
            from datetime import datetime
            
            with netCDF4.Dataset(filepath, 'r') as ds:
                # Find time variable
                time_vars = ['time', 'Time', 'TIME', 't']
                time_var = None
                
                for tv in time_vars:
                    if tv in ds.variables:
                        time_var = ds.variables[tv]
                        break
                
                if time_var is None:
                    return {'error': 'No time variable found'}
                
                times = time_var[:]
                
                coverage = {
                    'start_index': 0,
                    'end_index': len(times) - 1,
                    'num_timesteps': len(times),
                    'units': getattr(time_var, 'units', 'unknown')
                }
                
                # Try to decode times
                try:
                    decoded_times = netCDF4.num2date(
                        times, 
                        time_var.units,
                        only_use_cftime_datetimes=False
                    )
                    coverage['start_date'] = str(decoded_times[0])
                    coverage['end_date'] = str(decoded_times[-1])
                except:
                    pass
                
                return coverage
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def check_spatial_coverage(filepath: str) -> Dict[str, Any]:
        """Check spatial coverage from lat/lon variables"""
        try:
            import netCDF4
            import numpy as np
            
            with netCDF4.Dataset(filepath, 'r') as ds:
                # Find lat/lon variables
                lat_vars = ['lat', 'latitude', 'LAT', 'Latitude']
                lon_vars = ['lon', 'longitude', 'LON', 'Longitude']
                
                lat_var = None
                lon_var = None
                
                for lv in lat_vars:
                    if lv in ds.variables:
                        lat_var = ds.variables[lv]
                        break
                
                for lv in lon_vars:
                    if lv in ds.variables:
                        lon_var = ds.variables[lv]
                        break
                
                if lat_var is None or lon_var is None:
                    return {'error': 'No lat/lon variables found'}
                
                lats = lat_var[:]
                lons = lon_var[:]
                
                coverage = {
                    'lat_min': float(np.min(lats)),
                    'lat_max': float(np.max(lats)),
                    'lon_min': float(np.min(lons)),
                    'lon_max': float(np.max(lons)),
                    'lat_resolution': float(np.mean(np.diff(lats))) if len(lats) > 1 else None,
                    'lon_resolution': float(np.mean(np.diff(lons))) if len(lons) > 1 else None
                }
                
                return coverage
        except Exception as e:
            return {'error': str(e)}
