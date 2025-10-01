"""
Ollama client for agent system
Handles communication with local Ollama instance
"""
import requests
import json
from typing import Dict, Any, Optional
import config


class OllamaClient:
    """Client for Ollama LLM API"""
    
    def __init__(self, 
                 model: str = config.OLLAMA_MODEL,
                 base_url: str = config.OLLAMA_URL,
                 timeout: int = 60):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Check connection
        self._check_connection()
    
    def _check_connection(self):
        """Verify Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                print(f"✓ Connected to Ollama at {self.base_url}")
                print(f"  Available models: {', '.join(model_names)}")
                
                if self.model not in model_names:
                    print(f"  ⚠️  Model '{self.model}' not found locally")
                    print(f"  Pull it with: ollama pull {self.model}")
            else:
                print(f"⚠️  Ollama responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to Ollama at {self.base_url}")
            print(f"   Error: {e}")
            print(f"   Start Ollama with: ollama serve")
            raise
    
    def generate(self, 
                prompt: str,
                system: Optional[str] = None,
                temperature: float = 0.7,
                stream: bool = False) -> str:
        """
        Generate text from prompt
        
        Args:
            prompt: The prompt to send
            system: System message (optional)
            temperature: Sampling temperature (0.0-1.0)
            stream: Whether to stream response
        
        Returns:
            Generated text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 1024  # Max tokens to generate
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
        
        except requests.exceptions.Timeout:
            return "ERROR: Ollama request timed out"
        except requests.exceptions.RequestException as e:
            return f"ERROR: Ollama request failed: {e}"
    
    def chat(self, 
            messages: list,
            temperature: float = 0.7) -> str:
        """
        Chat completion with conversation history
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            temperature: Sampling temperature
        
        Returns:
            Assistant's response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '')
        
        except requests.exceptions.RequestException as e:
            return f"ERROR: {e}"
    
    def generate_structured(self, 
                          prompt: str,
                          format_example: Dict) -> Dict:
        """
        Generate structured output (experimental)
        
        Args:
            prompt: Prompt with instructions to output JSON
            format_example: Example of expected structure
        
        Returns:
            Parsed JSON dict
        """
        full_prompt = f"""{prompt}

Output your response as valid JSON matching this structure:
{json.dumps(format_example, indent=2)}

Respond ONLY with the JSON, no other text.
"""
        
        response = self.generate(full_prompt, temperature=0.3)
        
        # Try to extract JSON
        try:
            # Look for JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"error": "No JSON found in response", "raw": response}
        
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": response}
    
    def test_model(self):
        """Test that model is working"""
        print(f"\nTesting model: {self.model}")
        print("=" * 60)
        
        test_prompt = "What is 2+2? Answer with just the number."
        print(f"Test prompt: {test_prompt}")
        
        response = self.generate(test_prompt, temperature=0.1)
        print(f"Response: {response}")
        
        if "4" in response:
            print("✓ Model is working!")
            return True
        else:
            print("⚠️  Unexpected response - model may not be working correctly")
            return False