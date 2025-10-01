"""
Extract and parse content from companion documents
"""
from pathlib import Path
from typing import Dict, Any, List
import re
from utils import clean_text, truncate_string


class CompanionDocExtractor:
    """Extract content from companion documents"""
    
    def extract_readme(self, filepath: Path, max_length: int = 5000) -> Dict[str, Any]:
        """Extract content from README file"""
        result = {
            'filepath': str(filepath),
            'type': 'readme',
            'content': None,
            'sections': {},
            'metadata': {}
        }
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                result['error'] = 'Could not decode file'
                return result
            
            result['content'] = content[:max_length]
            
            # Parse markdown/rst sections
            if filepath.suffix in ['.md', '.rst']:
                result['sections'] = self._parse_sections(content)
            
            # Extract metadata hints
            result['metadata'] = self._extract_readme_metadata(content)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def extract_citation_info(self, filepath: Path) -> Dict[str, Any]:
        """Extract citation information"""
        result = {
            'filepath': str(filepath),
            'type': 'citation',
            'doi': None,
            'authors': [],
            'title': None,
            'year': None,
            'journal': None,
            'url': None
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract DOI
            doi_match = re.search(r'10\.\d{4,}/[^\s]+', content)
            if doi_match:
                result['doi'] = doi_match.group(0)
            
            # Extract URLs
            url_match = re.search(r'https?://[^\s]+', content)
            if url_match:
                result['url'] = url_match.group(0)
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', content)
            if year_match:
                result['year'] = year_match.group(0)
            
            # Look for common citation patterns
            if 'author' in content.lower():
                # Simple author extraction
                author_section = re.search(
                    r'author[s]?:?\s*([^\n]+)', 
                    content, 
                    re.IGNORECASE
                )
                if author_section:
                    result['authors'] = [
                        a.strip() for a in author_section.group(1).split(',')
                    ]
            
            result['raw_content'] = content[:500]
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def extract_script_metadata(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata from processing scripts"""
        result = {
            'filepath': str(filepath),
            'type': 'script',
            'language': filepath.suffix[1:],
            'docstring': None,
            'comments': [],
            'imports': [],
            'metadata': {}
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract docstring (Python)
            if filepath.suffix == '.py':
                docstring_match = re.search(
                    r'"""(.*?)"""', 
                    content, 
                    re.DOTALL
                )
                if docstring_match:
                    result['docstring'] = docstring_match.group(1).strip()
                
                # Extract imports
                import_matches = re.findall(r'^import\s+(\S+)', content, re.MULTILINE)
                from_matches = re.findall(r'^from\s+(\S+)', content, re.MULTILINE)
                result['imports'] = import_matches + from_matches
            
            # Extract comments
            comment_pattern = r'#\s*(.+)$' if filepath.suffix in ['.py', '.r', '.sh'] else None
            if comment_pattern:
                comments = re.findall(comment_pattern, content, re.MULTILINE)
                # Keep meaningful comments (longer than 10 chars)
                result['comments'] = [
                    c.strip() for c in comments 
                    if len(c.strip()) > 10
                ][:20]  # Limit to first 20
            
            # Look for metadata in comments
            result['metadata'] = self._extract_script_metadata_hints(content)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown/rst sections"""
        sections = {}
        
        # Find headers
        header_pattern = r'^#+\s+(.+)$|^(.+)\n[=\-]+$'
        lines = content.split('\n')
        
        current_section = 'introduction'
        current_content = []
        
        for line in lines:
            match = re.match(r'^#+\s+(.+)$', line)
            if match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = match.group(1).lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_readme_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata hints from README content"""
        metadata = {}
        
        # Look for common patterns
        patterns = {
            'contact': r'contact:?\s*([^\n]+)',
            'email': r'[\w\.-]+@[\w\.-]+',
            'version': r'version:?\s*([^\n]+)',
            'license': r'license:?\s*([^\n]+)',
            'date': r'date:?\s*([^\n]+)',
            'institution': r'(?:institution|organization):?\s*([^\n]+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()
        
        return metadata
    
    def _extract_script_metadata_hints(self, content: str) -> Dict[str, Any]:
        """Extract metadata hints from script comments"""
        metadata = {}
        
        # Look for common patterns in comments
        patterns = {
            'author': r'(?:author|created by):?\s*([^\n]+)',
            'date': r'(?:date|created):?\s*(\d{4}-\d{2}-\d{2})',
            'version': r'version:?\s*([^\n]+)',
            'description': r'description:?\s*([^\n]+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()
        
        return metadata
    
    def create_companion_summary(self, companions_data: List[Dict]) -> str:
        """Create searchable text from companion documents"""
        text_parts = []
        
        for doc in companions_data:
            doc_type = doc.get('type', '')
            
            if doc_type == 'readme':
                # Add README content
                if doc.get('content'):
                    text_parts.append(clean_text(doc['content'][:1000]))
                
                # Add extracted metadata
                if doc.get('metadata'):
                    for key, value in doc['metadata'].items():
                        text_parts.append(f"{key}: {value}")
            
            elif doc_type == 'citation':
                # Add citation info
                if doc.get('doi'):
                    text_parts.append(f"DOI: {doc['doi']}")
                if doc.get('authors'):
                    text_parts.append(f"Authors: {', '.join(doc['authors'])}")
                if doc.get('title'):
                    text_parts.append(doc['title'])
            
            elif doc_type == 'script':
                # Add script docstring
                if doc.get('docstring'):
                    text_parts.append(clean_text(doc['docstring']))
                
                # Add meaningful comments
                if doc.get('comments'):
                    text_parts.extend(doc['comments'][:5])
        
        return ' '.join(text_parts)
