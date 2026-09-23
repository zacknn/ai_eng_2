from pathlib import Path
import json 

MEMORY_FILE = Path("conversation_memory.json")

def load_memory() -> list[dict]:
    """Load past conversation messages from disk."""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(messages: list[dict]) -> None:
    """Save conversation messages to disk, skipping tool plumbing."""
    clean_messages = []
    for msg in messages:
        if not isinstance(msg, dict) and hasattr(msg, "model_dump"):
            msg = msg.model_dump()

        role = msg.get("role")
        # Skip system prompt, tool calls, and tool results
        if role in ("system", "tool"):
            continue
        # Skip assistant messages that are just tool-call requests
        if role == "assistant" and not msg.get("content"):
            continue
        clean_messages.append({
            "role": role,
            "content": msg.get("content"),
        })
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(clean_messages, f, indent=2)