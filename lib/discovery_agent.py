"""
Discovery Agent - SIMPLIFIED HYBRID VERSION
Uses deterministic logic + LLM only for final relevance decisions

Philosophy: Don't make the LLM do what code can do reliably.
"""
from pathlib import Path
from typing import Dict, Any, List
import re
from ollama_client import OllamaClient
import config


class DiscoveryAgent:
    """Simplified agent: code for searching, LLM for deciding"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def discover_companions(self, data_filepath: str) -> Dict:
        """
        Main discovery workflow - SIMPLIFIED VERSION
        
        Returns:
            Dict with discovered companions and reasoning
        """
        import time
        start_time = time.time()
        
        data_path = Path(data_filepath)
        data_dir = data_path.parent
        
        print(f"\n[SimpleDiscoveryAgent] Analyzing: {data_path.name}")
        print("=" * 60)
        
        # Step 1: Find candidates (DETERMINISTIC)
        print("\nStep 1: Finding candidate documents...")
        candidates = self._find_candidates(data_dir)
        
        print(f"Found {len(candidates)} candidate documents:")
        for doc in candidates:
            print(f"  - {doc.name}")
        
        if not candidates:
            return {
                "success": True,
                "data_file": data_filepath,
                "relevant_companions": [],
                "total_examined": 0,
                "reasoning": "No companion documents found in directory",
                "processing_time": time.time() - start_time
            }
        
        # Step 2: Evaluate each candidate (HYBRID)
        relevant = []
        uncertain = []
        not_relevant = []
        
        for doc in candidates:
            print(f"\nEvaluating: {doc.name}")
            
            # Quick heuristic filter
            mentions = self._check_file_mentions(doc, data_path)
            preview = self._preview_document(doc)
            
            print(f"  Mentions of '{data_path.stem}': {mentions}")
            print(f"  Preview length: {len(preview)} chars")
            
            # Strong signals - no LLM needed
            if mentions >= 3:
                print(f"  ✓ RELEVANT (strong signal: {mentions} mentions)")
                relevant.append({
                    "path": str(doc),
                    "reason": f"Mentions data file {mentions} times",
                    "confidence": 0.95
                })
                continue
            
            if mentions == 0 and "readme" not in doc.name.lower():
                print(f"  ✗ NOT RELEVANT (no mentions, not a README)")
                not_relevant.append({
                    "path": str(doc),
                    "reason": "No mentions of data file"
                })
                continue
            
            # Ambiguous case - use LLM
            print(f"  🤔 AMBIGUOUS - asking LLM...")
            decision = self._llm_decide_relevance(
                data_file=data_path.name,
                candidate_file=doc.name,
                preview=preview[:500],
                mentions=mentions
            )
            
            print(f"  LLM Decision: {decision['decision']} ({decision['confidence']:.2f})")
            
            if decision['decision'] == 'RELEVANT':
                relevant.append({
                    "path": str(doc),
                    "reason": decision['reasoning'],
                    "confidence": decision['confidence']
                })
            elif decision['decision'] == 'UNCERTAIN':
                uncertain.append({
                    "path": str(doc),
                    "reason": decision['reasoning'],
                    "confidence": decision['confidence']
                })
            else:
                not_relevant.append({
                    "path": str(doc),
                    "reason": decision['reasoning']
                })
        
        # Step 3: Summarize
        print("\n" + "=" * 60)
        print("DISCOVERY SUMMARY")
        print("=" * 60)
        print(f"Relevant: {len(relevant)}")
        print(f"Uncertain: {len(uncertain)}")
        print(f"Not relevant: {len(not_relevant)}")
        
        return {
            "success": True,
            "data_file": data_filepath,
            "relevant_companions": relevant,
            "uncertain_companions": uncertain,
            "not_relevant": not_relevant,
            "total_examined": len(candidates),
            "processing_time": time.time() - start_time
        }
    
    def _find_candidates(self, directory: Path) -> List[Path]:
        """Find potential companion documents (DETERMINISTIC)"""
        candidates = []
        
        # READMEs
        for pattern in config.README_PATTERNS:
            candidates.extend(directory.glob(pattern))
        
        # Citations
        for pattern in config.CITATION_PATTERNS:
            candidates.extend(directory.glob(pattern))
        
        # Documentation
        for pattern in config.DOCUMENTATION_PATTERNS:
            candidates.extend(directory.glob(pattern))
        
        # Scripts (filter out system files)
        for ext in config.SCRIPT_EXTENSIONS:
            for script in directory.glob(f"*{ext}"):
                if not self._is_system_file(script):
                    candidates.append(script)
        
        return list(set(candidates))  # Remove duplicates
    
    def _is_system_file(self, filepath: Path) -> bool:
        """Check if file is a system file"""
        name = filepath.name.lower()
        
        # Numbered notebooks
        if name.endswith('.ipynb') and re.match(r'^\d{2}_', name):
            return True
        
        # System scripts
        system_files = {
            'setup.sh', 'setup.py', 'install.sh', 'run.sh',
            'run_jupyterlab.sh', 'test.py', '__init__.py'
        }
        if name in system_files:
            return True
        
        # In system directories
        excluded_dirs = {'lib', 'src', 'tests', 'docs', '.git'}
        if any(excluded in filepath.parts for excluded in excluded_dirs):
            return True
        
        return False
    
    def _preview_document(self, filepath: Path, lines: int = 20) -> str:
        """Read first N lines of document (DETERMINISTIC)"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                preview_lines = [f.readline() for _ in range(lines)]
            return ''.join(preview_lines)
        except:
            return ""
    
    def _check_file_mentions(self, doc_path: Path, data_path: Path) -> int:
        """Count mentions of data file in document (DETERMINISTIC)"""
        try:
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
            # Check for file name (without extension)
            mentions = content.count(data_path.stem.lower())
            
            # Also check full filename
            mentions += content.count(data_path.name.lower())
            
            return mentions
        except:
            return 0
    
    def _llm_decide_relevance(self, data_file: str, candidate_file: str,
                             preview: str, mentions: int) -> Dict:
        """
        Use LLM for FINAL DECISION only (FOCUSED TASK)
        
        Much simpler than making LLM coordinate a whole workflow!
        """
        prompt = f"""Is this companion document relevant to the data file?

Data File: {data_file}
Candidate Document: {candidate_file}

Document Preview:
{preview}

File Mentions: {mentions}

Your task: Decide if this document describes or relates to the data file.

Answer in this format:
DECISION: RELEVANT or NOT_RELEVANT or UNCERTAIN
CONFIDENCE: 0.0-1.0
REASONING: One sentence explanation

Decision:"""

        try:
            response = self.ollama.generate(prompt, temperature=0.3)
            
            # Parse response
            decision = "UNCERTAIN"
            confidence = 0.5
            reasoning = response[:200]
            
            if "DECISION:" in response:
                for line in response.split('\n'):
                    if line.startswith('DECISION:'):
                        decision = line.split(':')[1].strip().upper()
                        if 'RELEVANT' in decision and 'NOT' not in decision:
                            decision = 'RELEVANT'
                        elif 'NOT' in decision:
                            decision = 'NOT_RELEVANT'
                        else:
                            decision = 'UNCERTAIN'
                    elif line.startswith('CONFIDENCE:'):
                        try:
                            confidence = float(line.split(':')[1].strip())
                        except:
                            pass
                    elif line.startswith('REASONING:'):
                        reasoning = line.split(':', 1)[1].strip()
            
            return {
                "decision": decision,
                "confidence": confidence,
                "reasoning": reasoning
            }
        
        except Exception as e:
            return {
                "decision": "UNCERTAIN",
                "confidence": 0.3,
                "reasoning": f"LLM error: {str(e)}"
            }


# Wrapper for compatibility with existing code
class DiscoveryAgent(SimpleDiscoveryAgent):
    """Alias for compatibility"""
    pass