"""
Metadata Enrichment Agent - Autonomous metadata improvement
"""
from pathlib import Path
from typing import Dict, Any
import netCDF4
import numpy as np
from agent_framework import BaseAgent, AgentTool, AgentDecision
from metadata_extractors import MetadataExtractor


class MetadataEnrichmentAgent(BaseAgent):
    """Agent that enriches minimal metadata using reasoning and domain knowledge"""
    
    SYSTEM_PROMPT = """You are an expert scientific data curator with deep knowledge across domains.

Your job: Take files with poor metadata and enrich them to make data FAIR and discoverable.

You have tools to:
- Inspect file structure (dimensions, variables, data ranges)
- Decode common abbreviations (sst→sea surface temperature)
- Infer scientific domain from variable patterns
- Suggest appropriate units and descriptions

Work methodically:
1. Get basic structure (dimensions, variables)
2. Analyze variable names and patterns
3. Check data ranges to validate guesses
4. Infer domain and context
5. Generate enriched metadata

Output format:
For tools: USE_TOOL: tool_name
          PARAMS: {"filepath": "path"}

For final enrichment:
DECISION: ENRICHED
CONFIDENCE: 0.0-1.0
REASONING: Explanation of inferences

Be honest about uncertainty - flag guesses vs confident inferences."""

    def __init__(self, ollama_client):
        super().__init__("EnrichmentAgent", self.SYSTEM_PROMPT, ollama_client)
        self.current_filepath = None
        self.tool_results = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register enrichment tools"""
        
        def get_structure(filepath: str) -> dict:
            """Get file structure overview"""
            extractor = MetadataExtractor()
            metadata = extractor.extract(Path(filepath))
            
            return {
                "format": metadata.get("format"),
                "dimensions": metadata.get("dimensions", {}),
                "variables": list(metadata.get("variables", {}).keys()),
                "file_size_mb": round(metadata.get("file_size", 0) / (1024*1024), 2),
                "has_title": bool(metadata.get("title")),
                "has_institution": bool(metadata.get("institution"))
            }
        
        self.register_tool(AgentTool(
            name="get_structure",
            description="Get file structure (format, dimensions, variables)",
            function=get_structure,
            required_params=["filepath"]
        ))
        
        def analyze_variable(filepath: str, variable_name: str) -> dict:
            """Get statistics and info for a variable"""
            try:
                with netCDF4.Dataset(filepath, 'r') as ds:
                    if variable_name not in ds.variables:
                        return {"error": f"Variable {variable_name} not found"}
                    
                    var = ds.variables[variable_name]
                    data = var[:]
                    
                    # Handle masked arrays
                    if hasattr(data, 'compressed'):
                        data_clean = data.compressed()
                    else:
                        data_clean = data.flatten()
                    
                    # Sample if very large
                    if len(data_clean) > 100000:
                        data_clean = np.random.choice(data_clean, 100000, replace=False)
                    
                    return {
                        "name": variable_name,
                        "shape": var.shape,
                        "dtype": str(var.dtype),
                        "min": float(np.min(data_clean)),
                        "max": float(np.max(data_clean)),
                        "mean": float(np.mean(data_clean)),
                        "std": float(np.std(data_clean)),
                        "units": getattr(var, 'units', None),
                        "long_name": getattr(var, 'long_name', None)
                    }
            except Exception as e:
                return {"error": str(e)}
        
        self.register_tool(AgentTool(
            name="analyze_variable",
            description="Get statistics and range for a variable (helps decode meaning)",
            function=analyze_variable,
            required_params=["filepath", "variable_name"]
        ))
        
        def domain_knowledge_lookup(term: str) -> dict:
            """Look up common scientific abbreviations"""
            # Common abbreviations in scientific data
            knowledge_base = {
                "sst": {"full": "sea surface temperature", "units": "celsius or kelvin", "domain": "oceanography"},
                "sst_anom": {"full": "sea surface temperature anomaly", "units": "celsius", "domain": "oceanography/climate"},
                "chl": {"full": "chlorophyll concentration", "units": "mg/m^3", "domain": "ocean biology"},
                "chl_a": {"full": "chlorophyll-a concentration", "units": "mg/m^3", "domain": "ocean biology"},
                "ssh": {"full": "sea surface height", "units": "meters", "domain": "oceanography"},
                "sss": {"full": "sea surface salinity", "units": "psu", "domain": "oceanography"},
                "u10": {"full": "u-component of wind at 10m", "units": "m/s", "domain": "atmospheric science"},
                "v10": {"full": "v-component of wind at 10m", "units": "m/s", "domain": "atmospheric science"},
                "wspd": {"full": "wind speed", "units": "m/s", "domain": "meteorology"},
                "wdir": {"full": "wind direction", "units": "degrees", "domain": "meteorology"},
                "t2m": {"full": "temperature at 2 meters", "units": "kelvin", "domain": "meteorology"},
                "tp": {"full": "total precipitation", "units": "mm", "domain": "meteorology"},
                "precip": {"full": "precipitation", "units": "mm or kg/m^2", "domain": "meteorology"},
                "temp": {"full": "temperature", "units": "celsius or kelvin", "domain": "general"},
                "sal": {"full": "salinity", "units": "psu", "domain": "oceanography"},
                "press": {"full": "pressure", "units": "pascals or hPa", "domain": "general"},
                "rh": {"full": "relative humidity", "units": "percent", "domain": "meteorology"},
                "aod": {"full": "aerosol optical depth", "units": "dimensionless", "domain": "atmospheric science"},
            }
            
            term_lower = term.lower().strip()
            
            # Exact match
            if term_lower in knowledge_base:
                return knowledge_base[term_lower]
            
            # Partial matches
            for key, value in knowledge_base.items():
                if term_lower in key or key in term_lower:
                    return {**value, "match_type": "partial"}
            
            return {"found": False, "suggestion": "unknown abbreviation - may need manual review"}
        
        self.register_tool(AgentTool(
            name="domain_knowledge_lookup",
            description="Look up scientific abbreviation meanings",
            function=domain_knowledge_lookup,
            required_params=["term"]
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
        
        # Filter out invalid parameters (LLM sometimes invents them)
        valid_params = {}
        for param_name, param_value in params.items():
            if param_name in tool.required_params or param_name == "filepath":
                valid_params[param_name] = param_value
            else:
                print(f"  [Ignored] Invalid parameter '{param_name}' for {tool_name}")
        
        # Check if we already called this tool with same params
        cache_key = f"{tool_name}:{str(valid_params)}"
        if cache_key in self.tool_results:
            print(f"[{self.name}] Note: Already called {tool_name} with these params, using cached result")
            return self.tool_results[cache_key]
        
        # Execute tool with cleaned params
        try:
            result = tool.execute(**valid_params)
            self.tool_results[cache_key] = result
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def parse_llm_response(self, response: str) -> dict:
        """Parse LLM response for enrichment"""
        result = super().parse_llm_response(response)
        
        # Also check for enriched metadata in response
        if "ENRICHED" in response or "enriched" in response.lower():
            result["type"] = "decision"
            result["decision"] = "ENRICHED"
            
            # Try to extract confidence and reasoning
            if "CONFIDENCE:" in response:
                try:
                    conf_line = [l for l in response.split('\n') if 'CONFIDENCE:' in l][0]
                    result["confidence"] = float(conf_line.split(':')[1].strip())
                except:
                    result["confidence"] = 0.7
            
            if "REASONING:" in response:
                try:
                    reasoning_start = response.find("REASONING:") + 10
                    reasoning_text = response[reasoning_start:].strip()
                    result["reasoning"] = reasoning_text[:500]
                except:
                    result["reasoning"] = response[:200]
        
        return result
    
    def reason_and_act(self, initial_prompt: str, context: Dict = None) -> AgentDecision:
        """Simplified reasoning loop for enrichment"""
        import time
        start_time = time.time()
        thoughts = []
        step = 0
        
        current_prompt = initial_prompt
        
        print(f"\n[{self.name}] Starting enrichment...")
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
                
                print(f"[{self.name}] Using tool: {tool_name}")
                print(f"  Parameters: {params}")
                
                thought.tool_name = tool_name
                thought.tool_params = params
                
                result = self.execute_tool(tool_name, params)
                thought.result = result
                
                result_str = str(result)[:200]
                print(f"  Result: {result_str}")
                
                # Build next prompt
                if step >= 4:
                    current_prompt = f"""You've gathered: {len(self.tool_results)} pieces of information.

Results so far: {list(self.tool_results.keys())}

Make your final DECISION now with enriched metadata."""
                else:
                    current_prompt = f"Tool {tool_name} returned: {result}\n\nContinue analysis or make decision."
                
            elif parsed["type"] == "decision":
                print(f"\n[{self.name}] Enrichment complete!")
                print(f"  Decision: {parsed['decision']}")
                print(f"  Confidence: {parsed.get('confidence', 0.7):.2f}")
                
                thoughts.append(thought)
                
                # Build summary of what was learned
                enrichment_summary = {
                    "variables_analyzed": [k.split(':')[1] for k in self.tool_results.keys() if 'analyze_variable' in k],
                    "lookups_performed": [k.split(':')[1] for k in self.tool_results.keys() if 'lookup' in k],
                    "tool_calls": len(self.tool_results)
                }
                
                return AgentDecision(
                    decision=parsed["decision"],
                    confidence=parsed.get("confidence", 0.7),
                    reasoning=parsed.get("reasoning", response[:300]),
                    thoughts=thoughts,
                    metadata={"enrichment_summary": enrichment_summary},
                    processing_time=time.time() - start_time
                )
            
            else:
                # Just thinking
                if step >= 5:
                    current_prompt = "You have enough information. Make your DECISION now."
                else:
                    current_prompt = "Continue. Use tools or make decision."
            
            thoughts.append(thought)
        
        # Max iterations - provide summary
        print(f"\n[{self.name}] Max iterations reached, summarizing findings...")
        
        summary = f"Analyzed {len(self.tool_results)} aspects of the file. "
        summary += "Enrichment partially complete but needs more iterations."
        
        return AgentDecision(
            decision="PARTIAL_ENRICHMENT",
            confidence=0.6,
            reasoning=summary,
            thoughts=thoughts,
            metadata={"note": "Reached iteration limit"},
            processing_time=time.time() - start_time
        )
    
    def enrich_file(self, filepath: str) -> dict:
        """Main enrichment workflow"""
        self.current_filepath = filepath
        self.tool_results = {}
        
        initial_prompt = f"""Enrich metadata for file: {filepath}

This file likely has minimal metadata. Your task:
1. Use get_structure to see dimensions and variables
2. Use domain_knowledge_lookup to decode variable abbreviations
3. Use analyze_variable to validate your interpretations with data ranges
4. Infer scientific domain and appropriate metadata
5. Provide DECISION: ENRICHED with your findings

Start with get_structure."""
        
        decision = self.reason_and_act(initial_prompt, {"filepath": filepath})
        
        # Extract enriched findings from tool results
        enriched_metadata = {
            "variables_decoded": {},
            "inferred_domain": None,
            "confidence": decision.confidence
        }
        
        # Parse tool results for enrichment
        for key, result in self.tool_results.items():
            if "domain_knowledge_lookup" in key and result.get("found", True):
                var_name = key.split("'term': '")[1].split("'")[0] if "'term':" in key else "unknown"
                enriched_metadata["variables_decoded"][var_name] = {
                    "full_name": result.get("full"),
                    "units": result.get("units"),
                    "domain": result.get("domain")
                }
        
        return {
            "success": decision.decision in ["ENRICHED", "PARTIAL_ENRICHMENT"],
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "enriched_metadata": enriched_metadata,
            "processing_time": decision.processing_time,
            "thoughts": decision.thoughts
        }