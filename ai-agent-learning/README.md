# Lesson: How AI Agents Work (Tool-Using LLMs)

A complete walkthrough of the concepts, the architecture, and the code — from zero to a working agent. (created by ai)

---

## 📚 Table of Contents

1. [What Is an AI Agent?](#1-what-is-an-ai-agent)
2. [The Core Idea: LLMs Can't Do Everything](#2-the-core-idea-llms-cant-do-everything)
3. [The Function-Calling Pattern](#3-the-function-calling-pattern)
4. [The Agent Loop (The Heart of Everything)](#4-the-agent-loop-the-heart-of-everything)
5. [Anatomy of Our Agent](#5-anatomy-of-our-agent)
6. [Tool Schemas: Teaching the LLM What Exists](#6-tool-schemas-teaching-the-llm-what-exists)
7. [The Message History Format](#7-the-message-history-format)
8. [Memory: Making Agents Remember](#8-memory-making-agents-remember)
9. [Error Handling: Why It Matters More Than You Think](#9-error-handling-why-it-matters-more-than-you-think)
10. [Common Pitfalls & How to Avoid Them](#10-common-pitfalls--how-to-avoid-them)
11. [How to Build Your Own Agent — Step by Step](#11-how-to-build-your-own-agent--step-by-step)
12. [Where to Go Next](#12-where-to-go-next)

---

## 1. What Is an AI Agent?

An **AI agent** is a program where a Large Language Model (LLM) is given:

1. **A goal** — the user's request
2. **Tools** — functions it can call to affect the world or fetch data
3. **A loop** — the ability to keep thinking, acting, and observing until done

A plain chatbot just **talks**. An agent **acts**.

| Plain chatbot | Agent |
|---|---|
| "What's the weather in Tokyo?" → *"I don't have real-time data."* | "What's the weather in Tokyo?" → *calls `get_weather("Tokyo")`* → *"It's 24°C and clear."* |
| "What's 145 × 23?" → *"Approximately 3335."* (may hallucinate) | "What's 145 × 23?" → *calls `calculate("145*23")`* → *"3335."* (exact) |

The agent is **not smarter** than the chatbot. It just has **hands** — the ability to call functions.

---

## 2. The Core Idea: LLMs Can't Do Everything

An LLM is a **text prediction engine**. It's brilliant at language, reasoning, and patterns. But it has hard limits:

- ❌ It doesn't know the **current time** (its training data is frozen)
- ❌ It can't do **precise math** (it guesses at arithmetic)
- ❌ It can't fetch **live data** (weather, stock prices, news)
- ❌ It can't **take actions** (send emails, write files, query databases)

**The solution:** Give it tools. When the LLM needs something it can't do, it asks *your code* to do it.

The LLM becomes the **brain**. Your Python functions become the **hands**.

---

## 3. The Function-Calling Pattern

Here's the key trick. The LLM never runs code itself. It **emits a structured request** like:

```json
{
  "name": "get_weather",
  "arguments": { "city": "Tokyo" }
}
```

Your code reads that request, runs the real function, and sends the result back:

```json
{ "temperature": "24°C", "condition": "Clear sky" }
```

The LLM then uses that result to write its final answer.

### The Four-Step Cycle

```
  ┌─────────────────────────────────────────────┐
  │  1. LLM receives: user question + tool list │
  └────────────────────┬────────────────────────┘
                       ▼
  ┌─────────────────────────────────────────────┐
  │  2. LLM decides: "I need `get_weather`"     │
  │     → emits a tool_call                     │
  └────────────────────┬────────────────────────┘
                       ▼
  ┌─────────────────────────────────────────────┐
  │  3. YOUR CODE runs the function             │
  │     → gets "24°C, Clear sky"                │
  └────────────────────┬────────────────────────┘
                       ▼
  ┌─────────────────────────────────────────────┐
  │  4. Result goes back to LLM                 │
  │     → LLM writes: "It's 24°C and clear."    │
  └─────────────────────────────────────────────┘
```

This cycle is the **entire foundation** of every modern AI agent — ChatGPT plugins, Claude tools, Copilot, Cursor, Devin — all use this pattern.

---

## 4. The Agent Loop (The Heart of Everything)

The 4-step cycle above is wrapped in a **loop** because the LLM might need multiple tools, or might need to react to a tool's result.

```python
for step in range(max_steps):
    response = llm.chat(messages, tools=TOOLS_SCHEMA)
    
    if not response.tool_calls:
        return response.content        # ← Done! Final answer.
    
    for tool_call in response.tool_calls:
        result = run_tool(tool_call)   # ← Your code runs it
        messages.append({
            "role": "tool",
            "content": result
        })
    # Loop again — LLM now sees the result
```

### Why a loop?

Imagine asking: *"Compare the weather in Tokyo and Paris."*

- **Round 1:** LLM calls `get_weather("Tokyo")` → gets result
- **Round 2:** LLM calls `get_weather("Paris")` → gets result
- **Round 3:** LLM has both results → writes comparison

Without a loop, the LLM could only call one tool per question. The loop lets it **chain actions**.

### Why `max_steps`?

Safety net. If the LLM gets confused (e.g., keeps calling the same tool forever), the loop stops after N iterations. **Always include this.**

---

## 5. Anatomy of Our Agent

Our project has 4 files, each with a clear job:

```
┌─────────────────────────────────────────────────────┐
│  agent.py       ← The brain: loop, LLM client, CLI  │
├─────────────────────────────────────────────────────┤
│  tools.py       ← The hands: functions the LLM uses │
├─────────────────────────────────────────────────────┤
│  memory.py      ← The notebook: saves conversations │
├─────────────────────────────────────────────────────┤
│  spinner.py     ← The UX: loading animation         │
└─────────────────────────────────────────────────────┘
```

### Division of Responsibility

| File | Job | Analogy |
|---|---|---|
| `tools.py` | Defines what the agent *can do* | A toolbox |
| `agent.py` | Decides *when* to use tools and *how* to loop | A worker |
| `memory.py` | Remembers past conversations | A diary |
| `spinner.py` | Shows the user something is happening | A "loading..." sign |

**This separation is important.** You can add a new tool to `tools.py` without touching the agent loop. You can swap memory for a database without touching the tools. Each file has one clear job.

---

## 6. Tool Schemas: Teaching the LLM What Exists

The LLM has no idea what Python functions you've written. You have to **describe them in JSON**.

### What the LLM Sees

For each tool, the LLM gets a JSON schema:

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "City name, e.g. Tokyo"
        }
      },
      "required": ["city"]
    }
  }
}
```

The LLM reads this and thinks: *"There's a tool called `get_weather`, it takes a `city` string, and the description says it returns weather. I'll use it when the user asks about weather."*

### Generating Schemas Automatically

Writing JSON by hand is tedious and error-prone. In `agent.py`, we use Python's `inspect` module to **read the function's signature and docstring** and generate the schema:

```python
def build_tool_schema(func):
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    properties = {}
    required = []
    
    for name, param in sig.parameters.items():
        properties[name] = {
            "type": "string",     # simplified
            "description": f"Parameter: {name}"
        }
        if param.default == inspect.Parameter.empty:
            required.append(name)
    
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__.strip().split("\n")[0],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }
```

### 💡 Writing Good Docstrings Matters

The docstring **is** the LLM's instruction manual. Compare:

```python
def get_weather(city: str) -> str:
    """Get weather."""   # ❌ Vague. LLM won't know when to use this.
```

vs.

```python
def get_weather(city: str) -> str:
    """
    Get the current weather for a city.
    Use this when the user asks about weather, temperature, rain, or conditions.
    
    Args:
        city: City name, e.g. "Tokyo", "Paris", "New York"
    """
    # ✅ Clear. LLM knows exactly when and how to use this.
```

The first line becomes the **description**. The more specific you are, the better the LLM's decisions.

---

## 7. The Message History Format

The LLM doesn't remember anything between API calls. **You** maintain the conversation history and send it every time.

### The Four Message Roles

| Role | Who | Example |
|---|---|---|
| `system` | You (the developer) | "You are a helpful assistant with tools..." |
| `user` | The human | "What's the weather in Tokyo?" |
| `assistant` | The LLM | "Let me check." + tool_call for `get_weather` |
| `tool` | Your code | "24°C, Clear sky" |

### What a Full Exchange Looks Like

```python
messages = [
    {"role": "system",    "content": "You are a helpful assistant..."},
    {"role": "user",      "content": "What's the weather in Tokyo?"},
    {"role": "assistant", "content": None, "tool_calls": [
        {"id": "call_abc", "function": {"name": "get_weather", "arguments": '{"city":"Tokyo"}'}}
    ]},
    {"role": "tool",      "tool_call_id": "call_abc", "content": "24°C, Clear sky"},
    {"role": "assistant", "content": "It's 24°C and clear in Tokyo."},
]
```

### Key Rules

1. **You send the whole history every time.** The LLM has no memory of its own.
2. **`tool_call_id` links a tool result to its request.** This matters when the LLM calls multiple tools at once — each result must match its request.
3. **Assistant messages with `tool_calls` have `content=None`.** They're requests, not answers.
4. **Order matters.** `user → assistant(tool_call) → tool → assistant(answer)`.

---

## 8. Memory: Making Agents Remember

Without memory, every conversation starts from scratch. With memory, the agent can say *"Earlier you asked about Tokyo weather..."*

### How Our Memory Works

- Messages are saved to `conversation_memory.json`
- On the next run, `load_memory()` reads them back
- Only the last 20 messages are loaded (to save tokens and avoid context overflow)

```python
past_messages = load_memory()
messages = [system_prompt]
messages.extend(past_messages[-20:])
messages.append({"role": "user", "content": user_message})
```

### ⚠️ The Hidden Trap

Tool messages **must** have a matching `assistant.tool_calls` message before them. If you save tool messages but strip their parent tool_calls (like the original code did), the API will **reject your history** on the next load.

**Two valid strategies:**

**Strategy A — Simple:** Only save `user` and `assistant` text messages. Skip all tool plumbing. Memory stays clean, but the agent won't remember tool conversations.

**Strategy B — Complete:** Save everything, including `tool_calls` and `tool_call_id`. Memory is fully faithful, but the JSON is bigger.

For a learning project, **Strategy A** is fine.

### Token Limits

Every message costs **tokens** (money + context space). For long conversations:
- Load only the last N messages (we use 20)
- Or summarize old messages with the LLM itself
- Or use a vector database to retrieve only relevant history

---

## 9. Error Handling: Why It Matters More Than You Think

Tools fail. The LLM sends bad arguments. The network drops. **Agents must handle this gracefully.**

### The Rule: Return Errors as Strings, Don't Crash

```python
def calculate(expression: str) -> str:
    if not re.match(r'^[\d\s\.\+\-\*\/\(\)]+$', expression):
        return "Error: Invalid characters."   # ✅ LLM can read this
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"                  # ✅ LLM can read this
```

Why? Because the LLM **reads the error and adapts**:

```
LLM calls:  calculate("sqrt(16)")
Tool says:  "Error: Invalid characters."
LLM thinks: "Oh, sqrt isn't allowed. Let me try another way."
LLM calls:  calculate("16 ** 0.5")
Tool says:  "4.0"
LLM answers: "The answer is 4."
```

If the tool **crashes**, the whole agent dies and the user sees a stack trace. **Always return errors as strings.**

### The Second Layer: Parse Tool Args Safely

```python
try:
    tool_args = json.loads(tool_call.function.arguments)
    if not isinstance(tool_args, dict):
        raise ValueError("Must be a JSON object")
except (json.JSONDecodeError, ValueError) as e:
    result = f"Error: Invalid arguments: {e}"
    # send back to LLM, don't crash
```

The LLM occasionally emits malformed JSON. Defensive parsing keeps the agent alive.

---

## 10. Common Pitfalls & How to Avoid Them

| Pitfall | Symptom | Fix |
|---|---|---|
| **No `max_steps`** | Agent loops forever | Always cap the loop |
| **Bare `except:`** | Swallows Ctrl+C and system exits | Use `except Exception:` |
| **Crashing tools** | One error kills the whole agent | Return errors as strings |
| **Broken memory** | API rejects history on reload | Only save complete exchanges |
| **Vague docstrings** | LLM never uses your tool, or uses it wrong | Write specific first lines |
| **No `tool_choice` control** | LLM ignores tools entirely | Use `"auto"`, `"required"`, or force a specific tool |
| **Sending the whole history** | Costs grow, context overflows | Trim to last N messages |
| **Trusting the LLM's math** | Wrong answers with confidence | Give it a calculator tool |

---

## 11. How to Build Your Own Agent — Step by Step

### Step 1: Pick Your Tools (Start with 2–3)

Ask yourself: *"What does the LLM need that it can't do alone?"*

- Fetch live data (weather, stocks, news)
- Do precise computation (math, unit conversion)
- Query private data (your database, your files)
- Take actions (send email, create file, post to API)

### Step 2: Write the Functions

Keep them **small**, **single-purpose**, and **return strings**.

```python
def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """
    Convert a value between units.
    Use this when the user asks to convert between units like km, miles, kg, lb.
    """
    # ... implementation ...
    return f"{value} {from_unit} = {result} {to_unit}"
```

### Step 3: Write Good Docstrings

The docstring is **the most important part**. The LLM's decisions depend entirely on it.

- **First line:** What the tool does + when to use it
- **Args section:** Describe each parameter with examples
- **Be specific:** "temperature in Celsius" beats "the value"

### Step 4: Register the Tools

```python
TOOL_REGISTRY = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "get_weather": get_weather,
    "convert_units": convert_units,   # ← just add it here
}
```

### Step 5: Auto-Generate Schemas

Use `inspect` + `get_type_hints` (as shown in Section 6) to avoid hand-writing JSON.

### Step 6: Build the Agent Loop

```python
def run_agent(user_message, max_steps=5):
    messages = [system_prompt] + load_memory()[-20:] + [user_msg(user_message)]
    
    for step in range(max_steps):
        response = llm.chat(messages, tools=TOOLS_SCHEMA, tool_choice="auto")
        
        if not response.tool_calls:
            save_memory(messages + [assistant_msg(response.content)])
            return response.content
        
        messages.append(assistant_msg_with_tool_calls(response))
        
        for tool_call in response.tool_calls:
            result = safe_run(tool_call)   # parse args, run, catch errors
            messages.append(tool_result(tool_call.id, result))
    
    save_memory(messages)
    return "Max steps reached."
```

### Step 7: Add a CLI

```python
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("exit", "quit"):
        break
    print(f"Agent: {run_agent(user_input)}\n")
```

### Step 8: Test, Iterate, Improve

Try weird questions. Watch which tools the LLM picks. If it picks wrong, **improve the docstring** — that's almost always the fix.

---

## 12. Where to Go Next

Once you've mastered this basic agent, here are the natural next steps:

### 🔧 More Advanced Tools
- **Multi-argument tools** with complex schemas
- **Tools that call other tools** (composition)
- **Streaming tools** (long-running tasks)

### 🧠 Better Memory
- **Summarization:** Compress old messages with the LLM
- **Vector databases:** Retrieve only relevant history (RAG)
- **Per-user memory:** Different history for different users

### 🤖 Multi-Agent Systems
- **Planner + Executor:** One agent plans, another executes
- **Critic:** One agent generates, another critiques
- **Specialists:** Different agents for different domains

### 🛡️ Production Concerns
- **Rate limiting** on tool calls
- **Human approval** for dangerous actions (sending emails, spending money)
- **Logging** every tool call for debugging
- **Token budgeting** to control costs
- **Evaluation**: how do you know your agent is getting better?

### 📚 Frameworks to Explore
- **LangChain / LangGraph** — Agent orchestration
- **LlamaIndex** — RAG and data agents
- **OpenAI Assistants API** — Managed agent infrastructure
- **CrewAI / AutoGen** — Multi-agent collaboration

But honestly? **Build from scratch first** (like this project). You'll understand every layer. Frameworks make sense *after* you've felt the pain they solve.

---

## 🎯 The One-Sentence Summary

> **An AI agent is an LLM in a loop, given tools to call — where the LLM decides *what* to do, and your code decides *how* to do it.**

Everything else is details.

---

## 📋 Cheat Sheet

```
┌──────────────────────────────────────────────────────┐
│  THE AGENT RECIPE                                    │
├──────────────────────────────────────────────────────┤
│  1. Write tool functions (small, one job, str out)   │
│  2. Write great docstrings (LLM reads these)         │
│  3. Register tools in a dict                         │
│  4. Auto-generate JSON schemas from signatures       │
│  5. Build the loop:                                  │
│       send → check tool_calls → run → append → repeat│
│  6. Cap with max_steps                               │
│  7. Return errors as strings, never crash            │
│  8. Save/load conversation memory                    │
│  9. Wrap in a CLI                                    │
│ 10. Test, improve docstrings, repeat                 │
└──────────────────────────────────────────────────────┘
```

---

