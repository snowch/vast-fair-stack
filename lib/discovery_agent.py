"""
Discovery Agent - Intelligent companion document discovery
Goes beyond pattern matching to reason about document relevance
"""
from pathlib import Path
from typing import Dict, Any, List
import re
from agent_framework import BaseAgent, AgentTool, AgentDecision
import config


class DiscoveryAgent(BaseAgent):
    """Agent that discovers and evaluates companion documents"""
    
    SYSTEM_PROMPT = """You are an expert at discovering documentation for scientific datasets.

Your job: Find companion documents (READMEs, citations, scripts) and evaluate their relevance.

Unlike simple pattern matching, you REASON about:
- Is this README actually about THIS dataset, or just a generic project README?
- Is this script used to process THIS data, or unrelated code?
- Does this citation document actually describe THIS dataset?
- Should we trust this documentation?

You have tools to:
- Find candidate documents in the directory
- Preview document contents (first lines)
- Check if documents mention the data file or related terms
- Evaluate document quality and relevance

Work methodically:
1. Find potential companion files
2. Preview their contents
3. Assess relevance to the specific data file
4. Make decisions about what to include
5. Extract key information from relevant docs

Output format:
For tools: USE_TOOL: tool_name
          PARAMS: {"filepath": "path"}

For decisions: DECISION: RELEVANT or NOT_RELEVANT or UNCERTAIN
              CONFIDENCE: 0.0-1.0
              REASONING: Why you made this decision

Be conservative - better to mark uncertain than include irrelevant docs."""

    def __init__(self, ollama_client):
        super().__init__("DiscoveryAgent", self.SYSTEM_PROMPT, ollama_client)
        self.current_data_file = None
        self.tool_results = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register discovery tools"""
        
        def find_candidate_documents(filepath: str) -> dict:
            """Find potential companion documents in same directory"""
            data_path = Path(filepath)
            data_dir = data_path.parent
            
            candidates = {
                "readmes": [],
                "citations": [],
                "scripts": [],
                "documentation": []
            }
            
            # Find README files
            for pattern in config.README_PATTERNS:
                candidates["readmes"].extend([
                    str(f) for f in data_dir.glob(pattern)
                ])
            
            # Find citation files
            for pattern in config.CITATION_PATTERNS:
                candidates["citations"].extend([
                    str(f) for f in data_dir.glob(pattern)
                ])
            
            # Find documentation
            for pattern in config.DOCUMENTATION_PATTERNS:
                candidates["documentation"].extend([
                    str(f) for f in data_dir.glob(pattern)
                ])
            
            # Find scripts (filter out system files)
            for ext in config.SCRIPT_EXTENSIONS:
                found = data_dir.glob(f"*{ext}")
                for f in found:
                    # Skip numbered notebooks and system files
                    if not self._is_system_file(f):
                        candidates["scripts"].append(str(f))
            
            # Remove duplicates
            for key in candidates:
                candidates[key] = list(set(candidates[key]))
            
            total = sum(len(v) for v in candidates.values())
            
            return {
                "total_candidates": total,
                "readmes": candidates["readmes"],
                "citations": candidates["citations"],
                "scripts": candidates["scripts"],
                "documentation": candidates["documentation"]
            }
        
        self.register_tool(AgentTool(
            name="find_candidate_documents",
            description="Find potential companion documents in directory",
            function=find_candidate_documents,
            required_params=["filepath"]
        ))
        
        def preview_document(document_path: str, num_lines: int = 20) -> dict:
            """Read first N lines of a document"""
            try:
                path = Path(document_path)
                
                if not path.exists():
                    return {"error": "File not found"}
                
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(path, 'r', encoding=encoding) as f:
                            lines = [f.readline() for _ in range(num_lines)]
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    return {"error": "Could not decode file"}
                
                preview = ''.join(lines)
                
                return {
                    "filename": path.name,
                    "size_bytes": path.stat().st_size,
                    "preview": preview,
                    "total_lines": len(lines)
                }
            except Exception as e:
                return {"error": str(e)}
        
        self.register_tool(AgentTool(
            name="preview_document",
            description="Read first lines of a document to assess relevance",
            function=preview_document,
            required_params=["document_path"]
        ))
        
        def check_mentions(document_path: str, search_terms: List[str]) -> dict:
            """Check if document mentions specific terms"""
            try:
                path = Path(document_path)
                
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                
                mentions = {}
                for term in search_terms:
                    term_lower = term.lower()
                    count = content.count(term_lower)
                    mentions[term] = count
                
                total_mentions = sum(mentions.values())
                
                return {
                    "document": path.name,
                    "mentions": mentions,
                    "total_mentions": total_mentions,
                    "has_matches": total_mentions > 0
                }
            except Exception as e:
                return {"error": str(e)}
        
        self.register_tool(AgentTool(
            name="check_mentions",
            description="Check if document mentions data file name or variables",
            function=check_mentions,
            required_params=["document_path", "search_terms"]
        ))
        
        def extract_metadata_from_doc(document_path: str) -> dict:
            """Extract key metadata from document"""
            try:
                path = Path(document_path)
                
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                metadata = {
                    "filename": path.name,
                    "type": self._classify_document(path, content)
                }
                
                # Extract common patterns
                
                # DOI
                doi_match = re.search(r'10\.\d{4,}/[^\s]+', content)
                if doi_match:
                    metadata["doi"] = doi_match.group(0)
                
                # Email
                email_match = re.search(r'[\w\.-]+@[\w\.-]+', content)
                if email_match:
                    metadata["email"] = email_match.group(0)
                
                # Version
                version_match = re.search(r'version:?\s*(\S+)', content, re.IGNORECASE)
                if version_match:
                    metadata["version"] = version_match.group(1)
                
                # Date
                date_match = re.search(r'\b(20\d{2}[-/]\d{2}[-/]\d{2})\b', content)
                if date_match:
                    metadata["date"] = date_match.group(1)
                
                # Institution
                institution_patterns = [
                    r'institution:?\s*([^\n]+)',
                    r'organization:?\s*([^\n]+)',
                    r'university of ([^\n]+)',
                ]
                for pattern in institution_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        metadata["institution"] = match.group(1).strip()
                        break
                
                return metadata
            except Exception as e:
                return {"error": str(e)}
        
        self.register_tool(AgentTool(
            name="extract_metadata_from_doc",
            description="Extract key information (DOI, email, version, etc) from document",
            function=extract_metadata_from_doc,
            required_params=["document_path"]
        ))
    
    def _is_system_file(self, filepath: Path) -> bool:
        """Check if file is a system file (not a companion)"""
        name = filepath.name.lower()
        
        # Numbered notebooks
        if name.endswith('.ipynb') and re.match(r'^\d{2}_', name):
            return True
        
        # System scripts
        system_scripts = {
            'setup.sh', 'setup.py', 'install.sh', 'run.sh',
            'run_jupyterlab.sh', 'test.py', 'tests.py',
            '__init__.py', 'conftest.py'
        }
        if name in system_scripts:
            return True
        
        # In system directories
        excluded_dirs = {'lib', 'src', 'tests', 'docs', '.git', '__pycache__'}
        if any(excluded in filepath.parts for excluded in excluded_dirs):
            return True
        
        return False
    
    def _classify_document(self, path: Path, content: str) -> str:
        """Classify document type"""
        name_lower = path.name.lower()
        content_lower = content.lower()
        
        if 'readme' in name_lower:
            return 'readme'
        elif any(x in name_lower for x in ['citation', 'cite', 'reference']):
            return 'citation'
        elif path.suffix in ['.py', '.r', '.m', '.sh']:
            return 'script'
        elif any(x in content_lower for x in ['doi:', 'cite as:', 'citation:']):
            return 'citation'
        else:
            return 'documentation'
    
    def execute_tool(self, tool_name: str, params: Dict) -> Any:
        """Execute tool with parameter validation"""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        
        # Auto-fix missing filepath
        if "filepath" in tool.required_params and "filepath" not in params:
            if self.current_data_file:
                params["filepath"] = self.current_data_file
        
        # Filter invalid parameters
        valid_params = {}
        for param_name, param_value in params.items():
            if param_name in tool.required_params:
                valid_params[param_name] = param_value
            else:
                print(f"  [Ignored] Invalid parameter '{param_name}' for {tool_name}")
        
        # Check cache
        cache_key = f"{tool_name}:{str(valid_params)}"
        if cache_key in self.tool_results:
            print(f"[{self.name}] Using cached result for {tool_name}")
            return self.tool_results[cache_key]
        
        # Execute
        try:
            result = tool.execute(**valid_params)
            self.tool_results[cache_key] = result
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def discover_companions(self, data_filepath: str) -> dict:
        """Main discovery workflow"""
        self.current_data_file = data_filepath
        self.tool_results = {}
        
        data_path = Path(data_filepath)
        
        initial_prompt = f"""Discover companion documents for: {data_path.name}

Your task:
1. Find candidate documents in the directory
2. Preview promising documents
3. Check if they actually relate to THIS specific dataset
4. Assess relevance and quality
5. Extract key information from relevant docs

Start by finding candidates.

Data file info to help you:
- Name: {data_path.name}
- Stem: {data_path.stem}
- Could look for mentions of these terms in documents

Begin with find_candidate_documents tool."""
        
        decision = self.reason_and_act(
            initial_prompt, 
            {"filepath": data_filepath}
        )
        
        # Parse discovered companions from tool results
        discovered = {
            "relevant_companions": [],
            "uncertain": [],
            "not_relevant": [],
            "total_examined": 0
        }
        
        # Extract from tool results
        for key, result in self.tool_results.items():
            if "preview_document" in key:
                discovered["total_examined"] += 1
        
        return {
            "success": True,
            "data_file": data_filepath,
            "discovered": discovered,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "processing_time": decision.processing_time,
            "thoughts": decision.thoughts
        }