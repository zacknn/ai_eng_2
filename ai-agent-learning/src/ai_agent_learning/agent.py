from dotenv import load_dotenv
load_dotenv()
from .spinner import Spinner
import json
import inspect
from typing import Callable, get_type_hints
from .tools import get_current_time, calculate, search_wikipedia , get_weather
from openai import OpenAI
import os
from .memory import *


# =============================================================================
# PART 1: TOOL REGISTRY
# =============================================================================

TOOL_REGISTRY: dict[str, Callable] = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "search_wikipedia": search_wikipedia,
    "get_weather": get_weather,
}

# =============================================================================
# PART 2: BUILD TOOL SCHEMAS (This tells the LLM what tools exist)
# =============================================================================

def build_tool_schema(func: Callable) -> dict:
    """
    Convert a Python function into an OpenAI tool schema.
    The LLM reads this JSON to decide which tool to call.
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    properties = {}
    required = []
    
    for name, param in sig.parameters.items():
        param_type = type_hints.get(name, str)
        
        # Map Python types to JSON schema types
        json_type = "string"
        if param_type == int:
            json_type = "integer"
        elif param_type == float:
            json_type = "number"
        elif param_type == bool:
            json_type = "boolean"
            
        properties[name] = {
            "type": json_type,
            "description": f"Parameter: {name}"
        }
        
        # If no default value, it's required
        if param.default == inspect.Parameter.empty:
            required.append(name)
    
    # Use first line of docstring as description
    doc = func.__doc__ or f"Function {func.__name__}"
    description = doc.strip().split("\n")[0].strip()
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }


# Build schemas once
TOOLS_SCHEMA = [build_tool_schema(fn) for fn in TOOL_REGISTRY.values()]

# =============================================================================
# PART 3: LLM CLIENT
# =============================================================================

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Export your Groq API key before starting the agent."
    )

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)

# =============================================================================
# PART 4: THE AGENT LOOP 
# =============================================================================

def run_agent(user_message: str, max_steps: int = 5) -> str:
    """
    The core loop:
      1. Send message + history to LLM
      2. Check if LLM wants a tool call
      3. If YES: run the tool, append result, go back to step 1
      4. If NO: return the answer
    """
    
    past_messages = load_memory()
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant with access to tools. "
                "You remember past conversations with the user. "
                "When a user's question requires real-time data, calculations, or "
                "external knowledge, you MUST use the appropriate tool. "
                "Do not guess. Do not use prior knowledge when a tool is available."
            )
        }
    ]
    messages.extend(past_messages[-20:])
    
    messages.append({"role": "user", "content": user_message})
    
    for step in range(max_steps):
        spinner = Spinner(f"Step {step + 1}")
        spinner.start()
        
        try:
            # STEP 1: Call the LLM WITH the tools
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=TOOLS_SCHEMA,        
                tool_choice="auto",        # Let the LLM decide
            )
        except Exception as e:
            return f"Error calling the model: {e}"
        finally:
            spinner.stop()
        
        assistant_message = response.choices[0].message
        
        # STEP 2: Check if LLM wants a tool
        # If no tool_calls, the LLM is done answering
        if not assistant_message.tool_calls:
            return assistant_message.content
        
        # STEP 3: LLM wants tools. Add its request to history first.
        messages.append(assistant_message)
        
        # Execute each requested tool
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            print(f" Tool called: {tool_name}({tool_args})")
            
            # Look up and run the function
            if tool_name in TOOL_REGISTRY:
                func = TOOL_REGISTRY[tool_name]
                try:
                    result = func(**tool_args)
                except Exception as e:
                    result = f"Error executing {tool_name}: {str(e)}"
            else:
                result = f"Error: Unknown tool '{tool_name}'"
            
            print(f"Result: {result}")
            
            # STEP 4: Feed the result back to the LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
        # Loop goes back to Step 1. The LLM now sees the tool results.
    
    return "Max steps reached without a final answer."


# =============================================================================
# PART 5: CLI
# =============================================================================

if __name__ == "__main__":
    print(" Agent Ready — Type 'exit' to quit")
    print("Examples:")
    print('  "What time is it in Tokyo?"')
    print('  "What is 145 times 23?"')
    print('  "Who invented the lightbulb?"')
    print()
    
    try:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break

            answer = run_agent(user_input)
            print(f"\n Agent: {answer}\n")
    except KeyboardInterrupt:
        print("\nGoodbye!")