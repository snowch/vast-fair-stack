"""
Quality Assessment Agent - SIMPLIFIED VERSION
Removes duplicate detection, adds result summary to help small models
"""
from pathlib import Path
from typing import Dict, Any, List
from agent_framework import BaseAgent, AgentTool, AgentDecision
from file_validator import FileValidator


class QualityAssessmentAgent(BaseAgent):
    """Agent that reasons about data quality"""
    
    SYSTEM_PROMPT = """You are an expert at assessing scientific data file quality.

Your job: Determine if files are legitimate research data or errors (HTML pages, corrupted files, etc).

Work efficiently:
1. Check file info (size, extension)
2. Check signature (magic bytes vs extension)
3. If results match and look good → ACCEPT
4. If results show problems → REJECT
5. If unsure → inspect_content or MANUAL_REVIEW

Make decisions quickly - don't repeat tools unnecessarily.

Output format:
For tools: USE_TOOL: tool_name
          PARAMS: {"filepath": "path/to/file"}

For decisions: DECISION: ACCEPT or REJECT or MANUAL_REVIEW
              CONFIDENCE: 0.0-1.0
              REASONING: Brief explanation

Decisions:
- ACCEPT: Valid data file
- REJECT: HTML page, corrupted, or wrong format
- MANUAL_REVIEW: Unusual but might be valid"""

    def __init__(self, ollama_client):
        super().__init__("QualityAgent", self.SYSTEM_PROMPT, ollama_client)
        self.validator = FileValidator()
        self.current_filepath = None
        self.tool_results: Dict[str, Any] = {}  # Store results by tool name
        self._register_tools()
    
    def _register_tools(self):
        """Register quality assessment tools"""
        
        def check_signature(filepath: str) -> Dict:
            """Check magic bytes to identify file type"""
            result = self.validator.check_file_signature(Path(filepath))
            return {
                "expected_type": result.get("expected_type"),
                "detected_type": result.get("detected_type"),
                "is_valid": result.get("is_valid"),
                "issues": result.get("issues", []),
                "size": result.get("size_formatted")
            }
        
        self.register_tool(AgentTool(
            name="check_signature",
            description="Read magic bytes to identify file type",
            function=check_signature,
            required_params=["filepath"]
        ))
        
        def get_file_info(filepath: str) -> Dict:
            """Get basic file information"""
            path = Path(filepath)
            if not path.exists():
                return {"error": "File not found"}
            
            return {
                "filename": path.name,
                "extension": path.suffix,
                "size_bytes": path.stat().st_size,
                "size_mb": round(path.stat().st_size / (1024*1024), 2)
            }
        
        self.register_tool(AgentTool(
            name="get_file_info",
            description="Get filename, extension, size",
            function=get_file_info,
            required_params=["filepath"]
        ))
        
        def inspect_content(filepath: str) -> Dict:
            """Read first bytes to detect HTML/text"""
            path = Path(filepath)
            try:
                with open(path, 'rb') as f:
                    data = f.read(512)
                
                try:
                    text = data.decode('utf-8', errors='replace')[:200]
                    is_text = True
                except:
                    text = None
                    is_text = False
                
                has_html = False
                if is_text:
                    html_markers = ['<!DOCTYPE', '<html', '<HTML', '<head', '<body']
                    has_html = any(marker in text for marker in html_markers)
                
                return {
                    "appears_text": is_text,
                    "appears_html": has_html,
                    "sample_text": text if is_text else "(binary data)"
                }
            except Exception as e:
                return {"error": str(e)}
        
        self.register_tool(AgentTool(
            name="inspect_content",
            description="Sample file content to detect HTML",
            function=inspect_content,
            required_params=["filepath"]
        ))
    
    def execute_tool(self, tool_name: str, params: Dict) -> Any:
        """Execute tool with parameter validation and result storage"""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        
        # Auto-fix missing filepath
        if "filepath" in tool.required_params and "filepath" not in params:
            if self.current_filepath:
                params["filepath"] = self.current_filepath
            else:
                return {"error": "Missing filepath parameter"}
        
        # FILTER OUT INVALID PARAMETERS (the LLM sometimes invents them)
        valid_params = {}
        for param_name, param_value in params.items():
            if param_name in tool.required_params or param_name == "filepath":
                valid_params[param_name] = param_value
            else:
                print(f"  [Ignored] Invalid parameter '{param_name}' for {tool_name}")
        
        # Execute tool with cleaned params
        try:
            result = tool.execute(**valid_params)
            self.tool_results[tool_name] = result
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def get_results_summary(self) -> str:
        """Create summary of all tool results gathered so far"""
        if not self.tool_results:
            return "No results yet."
        
        summary = "Results gathered so far:\n"
        for tool_name, result in self.tool_results.items():
            summary += f"- {tool_name}: {result}\n"
        return summary
    
    def reason_and_act(self, initial_prompt: str, context: Dict = None) -> AgentDecision:
        """Simplified reasoning loop"""
        import time
        start_time = time.time()
        thoughts = []
        step = 0
        
        current_prompt = initial_prompt
        
        print(f"\n[{self.name}] Starting analysis...")
        print("=" * 60)
        
        while step < self.max_iterations:
            step += 1
            
            print(f"\n[{self.name}] Step {step}: Thinking...")
            response = self.think(current_prompt, context)
            
            parsed = self.parse_llm_response(response)
            
            from agent_framework import AgentThought
            thought = AgentThought(
                step_number=step,
                reasoning=response[:500],
                action=parsed["type"]
            )
            
            if parsed["type"] == "tool_call":
                tool_name = parsed["tool_name"]
                params = parsed["params"]
                
                # Check if we already have results for this tool
                if tool_name in self.tool_results:
                    print(f"[{self.name}] Note: Already called {tool_name}, using cached result")
                    result = self.tool_results[tool_name]
                else:
                    print(f"[{self.name}] Using tool: {tool_name}")
                    print(f"  Parameters: {params}")
                    result = self.execute_tool(tool_name, params)
                
                thought.tool_name = tool_name
                thought.tool_params = params
                thought.result = result
                
                result_str = str(result)[:200]
                print(f"  Result: {result_str}")
                
                # Build next prompt with context
                if step >= 3:
                    # After 3 steps, push for decision
                    current_prompt = f"""Previous result: {result}

{self.get_results_summary()}

You have enough information. Make your DECISION now (ACCEPT/REJECT/MANUAL_REVIEW)."""
                else:
                    current_prompt = f"""Result: {result}

{self.get_results_summary()}

What's next? Use another tool or make a decision."""
                
            elif parsed["type"] == "decision":
                print(f"\n[{self.name}] Decision reached!")
                print(f"  Decision: {parsed['decision']}")
                print(f"  Confidence: {parsed['confidence']:.2f}")
                
                thoughts.append(thought)
                
                return AgentDecision(
                    decision=parsed["decision"],
                    confidence=parsed["confidence"],
                    reasoning=parsed["reasoning"],
                    thoughts=thoughts,
                    processing_time=time.time() - start_time
                )
            
            else:
                # Just thinking - nudge toward action
                if step >= 4:
                    current_prompt = f"""{self.get_results_summary()}

Based on the results above, make your final DECISION now."""
                else:
                    current_prompt = "Continue. Use a tool or make a decision."
            
            thoughts.append(thought)
        
        # Max iterations - make decision based on what we have
        print(f"\n[{self.name}] Max iterations reached, analyzing results...")
        
        # Simple rule-based fallback
        if 'check_signature' in self.tool_results:
            sig_result = self.tool_results['check_signature']
            if sig_result.get('is_valid'):
                return AgentDecision(
                    decision="ACCEPT",
                    confidence=0.85,
                    reasoning="Signature check passed - file format is valid",
                    thoughts=thoughts,
                    processing_time=time.time() - start_time
                )
            else:
                return AgentDecision(
                    decision="REJECT",
                    confidence=0.85,
                    reasoning=f"Signature check failed: {sig_result.get('issues')}",
                    thoughts=thoughts,
                    processing_time=time.time() - start_time
                )
        
        return AgentDecision(
            decision="MANUAL_REVIEW",
            confidence=0.5,
            reasoning="Could not complete analysis - needs human review",
            thoughts=thoughts,
            processing_time=time.time() - start_time
        )
    
    def assess_file(self, filepath: str) -> AgentDecision:
        """Main entry point"""
        self.current_filepath = filepath
        self.tool_results = {}  # Reset for new file
        
        initial_prompt = f"""Assess file: {filepath}

Work step-by-step:
1. get_file_info to check size/extension
2. check_signature to verify format
3. Make DECISION (or inspect_content if suspicious)

Start with step 1. Include filepath in params."""
        
        context = {"filepath": filepath, "task": "quality_assessment"}
        decision = self.reason_and_act(initial_prompt, context)
        
        # Normalize decision
        valid_decisions = ["ACCEPT", "REJECT", "MANUAL_REVIEW"]
        if decision.decision not in valid_decisions:
            if "valid" in decision.reasoning.lower():
                decision.decision = "ACCEPT"
            elif "invalid" in decision.reasoning.lower():
                decision.decision = "REJECT"
            else:
                decision.decision = "MANUAL_REVIEW"
        
        return decision
    
    def quick_assess(self, filepath: str) -> tuple[bool, str]:
        """Quick assessment for compatibility"""
        decision = self.assess_file(filepath)
        is_valid = decision.decision == "ACCEPT"
        message = f"{decision.decision} ({decision.confidence:.2f}) - {decision.reasoning[:100]}"
        return is_valid, message