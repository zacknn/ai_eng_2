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
    """Save conversation messages to disk."""
    # Filter out tool_call details to keep file small
    clean_messages = []
    for msg in messages:
        clean_msg = {
            "role": msg.get("role"),
            "content": msg.get("content"),
        }
        # Keep tool_call_id for tool messages so context makes sense
        if "tool_call_id" in msg:
            clean_msg["tool_call_id"] = msg["tool_call_id"]
        clean_messages.append(clean_msg)
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(clean_messages, f, indent=2)