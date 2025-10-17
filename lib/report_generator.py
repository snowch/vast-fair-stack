# In lib/report_generator.py
from ollama_client import OllamaClient
from pathlib import Path
import datetime
import json

class LLMReportGenerator:
    """
    Uses an LLM to generate a comprehensive curation report.
    """
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client

    def generate_report(self, mystery_file: Path, quality_result: dict, discovery_result: dict, enrichment_result: dict) -> str:
        """
        Generates a curation report using an LLM.
        """
        prompt = self._create_report_prompt(mystery_file, quality_result, discovery_result, enrichment_result)
        
        print("🤖 Generating report with LLM... (this may take a moment)")
        
        # Call the LLM to generate the report
        raw_report = self.ollama.generate(prompt, temperature=0.5)
        
        # Clean the LLM's response to ensure it's valid Markdown
        start_index = raw_report.find("#")
        if start_index != -1:
            # Slice the string from the first '#' character onwards
            cleaned_report = raw_report[start_index:]
            return cleaned_report
        else:
            # Return the raw report if no markdown header is found
            return raw_report

    def _create_report_prompt(self, mystery_file: Path, quality_result: dict, discovery_result: dict, enrichment_result: dict) -> str:
        """
        Creates a detailed prompt for the LLM to generate the report.
        """
        # (The rest of this method stays the same, but I'll add a final instruction to the prompt)
        file_name = mystery_file.name
        folder_path = mystery_file.parent
        file_size_mb = mystery_file.stat().st_size / (1024 * 1024)
        
        quality_confidence = quality_result.confidence
        
        relevant_docs = [Path(doc['path']).name for doc in discovery_result.get('relevant_companions', [])]
        
        enriched_metadata = enrichment_result.get('enriched_metadata', {})
        variable_details = enriched_metadata.get('variables_decoded', {})
        
        # Construct the prompt
        prompt = f"""
        You are an expert data curator. Your task is to generate a comprehensive, human-readable curation report in Markdown format for a scientific dataset.

        Here is the information gathered by our multi-agent system:

        **1. File Information:**
        - Filename: {file_name}
        - Folder Path: {folder_path}
        - Size: {file_size_mb:.2f} MB

        **2. Quality Assessment:**
        - The file has been validated and accepted with a confidence score of {quality_confidence:.2f}/1.0. It appears to be a valid and uncorrupted scientific data file.

        **3. Companion Documents:**
        - The following relevant companion documents were discovered: {', '.join(relevant_docs)}

        **4. Metadata Enrichment:**
        - The Enrichment Agent analyzed the file and decoded the following variables:
        {json.dumps(variable_details, indent=2)}

        **Your Task:**

        Based on all the information above, please generate a full curation report in Markdown format. The report should be similar in style and structure to the example in `docs/folder_metadata_example.md`. It should include:
        - An Executive Summary.
        - A "Key Findings" section with bullet points.
        - A "Dataset Inventory" section detailing the primary data file and its variables.
        - A summary of the companion documents.
        - A section on "Semantic Enrichment" that discusses the inferred scientific context.

        Please make sure the report is well-structured and professional.
        **IMPORTANT: Respond ONLY with the Markdown content. Do not add any introductory or concluding sentences.**
        """
        return prompt