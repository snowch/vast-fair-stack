"""
Metadata Enrichment Agent - Autonomous metadata improvement
REVISED: Uses a Python-based orchestration loop for reliability.
"""
from pathlib import Path
from typing import Dict, Any
import netCDF4
import numpy as np
from agent_framework import BaseAgent, AgentTool, AgentDecision
from metadata_extractors import MetadataExtractor
import time

class MetadataEnrichmentAgent(BaseAgent):
    """Agent that enriches minimal metadata using a reliable, orchestrated workflow."""
    
    SYSTEM_PROMPT = """You are an expert scientific data curator. Your task is to analyze metadata and provide concise, factual interpretations based on the tools provided. When asked to use a tool for a specific variable, focus only on that task. When asked to summarize, use all the information provided to create a final, comprehensive reasoning statement."""

    def __init__(self, ollama_client):
        super().__init__("EnrichmentAgent", self.SYSTEM_PROMPT, ollama_client)
        self.current_filepath = None
        self.tool_results = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register enrichment tools"""
        
        def get_structure(filepath: str) -> dict:
            extractor = MetadataExtractor()
            metadata = extractor.extract(Path(filepath))
            return {
                "variables": list(metadata.get("variables", {}).keys()),
            }
        
        self.register_tool(AgentTool(
            name="get_structure",
            description="Get the list of variables from a file.",
            function=get_structure,
            required_params=["filepath"]
        ))
        
        def domain_knowledge_lookup(term: str) -> dict:
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
            if term_lower in knowledge_base:
                return knowledge_base[term_lower]
            return {"found": False, "suggestion": "unknown abbreviation"}
        
        self.register_tool(AgentTool(
            name="domain_knowledge_lookup",
            description="Look up scientific abbreviation meanings",
            function=domain_knowledge_lookup,
            required_params=["term"]
        ))

    def _enrich_single_variable(self, variable_name: str):
        """Uses the LLM to look up a single variable."""
        prompt = f"Use the `domain_knowledge_lookup` tool to find the meaning of the variable '{variable_name}'."
        
        response = self.think(prompt)
        parsed = self.parse_llm_response(response)
        
        if parsed.get("type") == "tool_call" and parsed.get("tool_name") == "domain_knowledge_lookup":
            params = parsed.get("params", {})
            tool_result = self.tools["domain_knowledge_lookup"].execute(**params)
            
            # Store the result with a key that includes the variable name
            cache_key = f"domain_knowledge_lookup:{variable_name}"
            self.tool_results[cache_key] = tool_result
            print(f"  ✓ Decoded '{variable_name}': {tool_result.get('full', 'Unknown')}")
        else:
            print(f"  ✗ Failed to decode '{variable_name}'")

    def enrich_file(self, filepath: str) -> dict:
        """Main enrichment workflow using Python orchestration."""
        self.current_filepath = filepath
        self.tool_results = {}
        start_time = time.time()
        
        print(f"\n[{self.name}] Starting orchestrated enrichment for: {filepath}")
        print("=" * 60)
        
        # Step 1: Get the list of variables using the tool directly
        print(f"[{self.name}] Step 1: Getting file structure...")
        structure = self.tools["get_structure"].execute(filepath=filepath)
        all_variables = structure.get("variables", [])
        
        # Filter out coordinate variables
        coord_vars = {'time', 'lat', 'lon', 'x', 'y', 'z', 't'}
        variables_to_enrich = [v for v in all_variables if v not in coord_vars]
        
        print(f"  > Found {len(variables_to_enrich)} variables to enrich: {variables_to_enrich}")
        
        # Step 2: Loop through variables and enrich each one
        print(f"\n[{self.name}] Step 2: Decoding each variable...")
        for var_name in variables_to_enrich:
            self._enrich_single_variable(var_name)
            
        # Step 3: Ask the LLM for a final summary
        print(f"\n[{self.name}] Step 3: Generating final summary...")
        summary_prompt = f"""
        Based on the following decoded variables, provide a final reasoning for the dataset's domain and purpose.

        Decoded Variables:
        {self.tool_results}

        Provide your reasoning in the standard format:
        DECISION: ENRICHED
        CONFIDENCE: 0.9
        REASONING: [Your summary here]
        """
        
        final_response = self.think(summary_prompt)
        parsed_final = self.parse_llm_response(final_response)
        
        # Final result assembly
        enriched_metadata = {
            "variables_decoded": {},
            "inferred_domain": None,
            "confidence": parsed_final.get("confidence", 0.85)
        }
        
        for key, result in self.tool_results.items():
            if "domain_knowledge_lookup" in key and result.get("found", True) is not False:
                var_name = key.split(":", 1)[1]
                enriched_metadata["variables_decoded"][var_name] = {
                    "full_name": result.get("full"),
                    "units": result.get("units"),
                    "domain": result.get("domain")
                }
                # Infer domain from the first variable with a domain
                if not enriched_metadata["inferred_domain"] and result.get("domain"):
                    enriched_metadata["inferred_domain"] = result.get("domain")

        return {
            "success": True,
            "confidence": parsed_final.get("confidence", 0.85),
            "reasoning": parsed_final.get("reasoning", "Enrichment complete."),
            "enriched_metadata": enriched_metadata,
            "processing_time": time.time() - start_time,
            "thoughts": [] 
        }