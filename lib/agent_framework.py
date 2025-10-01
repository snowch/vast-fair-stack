"""
Simple agent framework for FAIR data discovery
Designed for CPU-based Ollama, educational/demo purposes
"""
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
import json
import time


@dataclass
class AgentThought:
    """Captures one step of agent reasoning"""
    step_number: int
    reasoning: str
    action: str
    tool_name: Optional[str] = None
    tool_params: Optional[Dict] = None
    result: Any = None
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentDecision:
    """Final decision from agent"""
    decision: str
    confidence: float
    reasoning: str
    thoughts: List[AgentThought]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0


class AgentTool:
    """A tool that agents can use"""
    
    def __init__(self, name: str, description: str, 
                 function: Callable, required_params: List[str]):
        self.name = name
        self.description = description
        self.function = function
        self.required_params = required_params
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool with parameters"""
        # Validate required parameters
        for param in self.required_params:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter: {param}")
        
        return self.function(**kwargs)
    
    def to_dict(self) -> Dict:
        """Tool description for LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.required_params
        }


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name: str, system_prompt: str, ollama_client):
        self.name = name
        self.system_prompt = system_prompt
        self.ollama = ollama_client
        self.tools: Dict[str, AgentTool] = {}
        self.max_iterations = 10
        self.conversation_history = []
        
    def register_tool(self, tool: AgentTool):
        """Register a tool this agent can use"""
        self.tools[tool.name] = tool
        print(f"  [{self.name}] Registered tool: {tool.name}")
    
    def get_tools_description(self) -> str:
        """Format tools for LLM prompt"""
        if not self.tools:
            return "No tools available."
        
        tools_text = "Available tools:\n"
        for tool in self.tools.values():
            params = ", ".join(tool.required_params)
            tools_text += f"- {tool.name}({params}): {tool.description}\n"
        
        return tools_text
    
    def think(self, prompt: str, context: Dict = None) -> str:
        """Core reasoning with LLM"""
        # Build prompt with system context and tools
        full_prompt = f"{self.system_prompt}\n\n"
        full_prompt += self.get_tools_description()
        full_prompt += f"\n\nTask: {prompt}\n"
        
        if context:
            full_prompt += f"\nContext:\n{json.dumps(context, indent=2)}\n"
        
        full_prompt += """
Think step-by-step. You can use tools by writing:
USE_TOOL: tool_name
PARAMS: {"param1": "value1", "param2": "value2"}

Or make a final decision by writing:
DECISION: your_decision
CONFIDENCE: 0.0-1.0
REASONING: your reasoning
"""
        
        # Call Ollama
        response = self.ollama.generate(full_prompt)
        return response
    
    def parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response for tool calls or decisions"""
        result = {
            "type": "thought",  # or "tool_call" or "decision"
            "content": response
        }
        
        # Check for tool call
        if "USE_TOOL:" in response:
            try:
                lines = response.split('\n')
                tool_line = [l for l in lines if l.startswith('USE_TOOL:')][0]
                tool_name = tool_line.split(':')[1].strip()
                
                params_line = [l for l in lines if l.startswith('PARAMS:')][0]
                params_json = params_line.split('PARAMS:')[1].strip()
                params = json.loads(params_json)
                
                result["type"] = "tool_call"
                result["tool_name"] = tool_name
                result["params"] = params
            except:
                pass  # Failed to parse, treat as thought
        
        # Check for decision
        elif "DECISION:" in response:
            try:
                lines = response.split('\n')
                decision_line = [l for l in lines if l.startswith('DECISION:')][0]
                decision = decision_line.split(':')[1].strip()
                
                confidence_line = [l for l in lines if l.startswith('CONFIDENCE:')][0]
                confidence = float(confidence_line.split(':')[1].strip())
                
                reasoning_line = [l for l in lines if l.startswith('REASONING:')][0]
                reasoning = reasoning_line.split('REASONING:')[1].strip()
                
                result["type"] = "decision"
                result["decision"] = decision
                result["confidence"] = confidence
                result["reasoning"] = reasoning
            except:
                pass
        
        return result
    
    def execute_tool(self, tool_name: str, params: Dict) -> Any:
        """Execute a tool and capture result"""
        if tool_name not in self.tools:
            return f"ERROR: Tool '{tool_name}' not found"
        
        try:
            tool = self.tools[tool_name]
            result = tool.execute(**params)
            return result
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def reason_and_act(self, initial_prompt: str, 
                      context: Dict = None) -> AgentDecision:
        """Main reasoning loop with tool use"""
        start_time = time.time()
        thoughts = []
        step = 0
        
        current_prompt = initial_prompt
        
        print(f"\n[{self.name}] Starting analysis...")
        print("=" * 60)
        
        while step < self.max_iterations:
            step += 1
            
            # Agent thinks
            print(f"\n[{self.name}] Step {step}: Thinking...")
            response = self.think(current_prompt, context)
            
            # Parse response
            parsed = self.parse_llm_response(response)
            
            # Create thought record
            thought = AgentThought(
                step_number=step,
                reasoning=response,
                action=parsed["type"]
            )
            
            if parsed["type"] == "tool_call":
                # Execute tool
                tool_name = parsed["tool_name"]
                params = parsed["params"]
                
                print(f"[{self.name}] Using tool: {tool_name}")
                print(f"  Parameters: {params}")
                
                thought.tool_name = tool_name
                thought.tool_params = params
                
                result = self.execute_tool(tool_name, params)
                thought.result = result
                
                print(f"  Result: {str(result)[:200]}...")
                
                # Update prompt for next iteration
                current_prompt = f"Tool {tool_name} returned: {result}\n\nWhat's next?"
                
            elif parsed["type"] == "decision":
                # Final decision reached
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
                # Just thinking, continue
                print(f"[{self.name}] Reasoning: {response[:200]}...")
                current_prompt = "Continue your analysis."
            
            thoughts.append(thought)
        
        # Max iterations reached
        print(f"\n[{self.name}] Max iterations reached, making best decision...")
        
        return AgentDecision(
            decision="INCOMPLETE",
            confidence=0.3,
            reasoning="Analysis incomplete - reached iteration limit",
            thoughts=thoughts,
            processing_time=time.time() - start_time
        )