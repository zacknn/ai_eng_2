# Research Agent

A small command-line research agent built with [smolagents](https://github.com/huggingface/smolagents). Give it a topic and it searches the web, reads the most promising pages, and writes a short cited summary. It then checks that every URL it cited was actually fetched during the run.

```
topic -> search (x3) -> fetch best pages (x2) -> cited summary -> citation check
```

## Architecture

```
src/research_agent/
├── __init__.py        # exposes main()
├── __main__.py        # lets you run `python -m research_agent`
├── agents.py          # builds the ToolCallingAgent + Groq model, CLI entry point
├── prompt.py          # prompt templates (short / long / compare) and shared rules
├── runner.py          # runs the agent, collects sources/errors, verifies citations
├── researchresult.py  # ResearchResult dataclass
└── tools.py           # the tools the agent can call
```

**How a run works**

1. `agents.py` loads `GROQ_API_KEY` from `.env` and creates a single `ToolCallingAgent` (cached in `_agent`) backed by `openai/gpt-oss-120b` on Groq's OpenAI-compatible endpoint.
2. `runner.run_research(topic)` fills in the `short` prompt template and calls `agent.run(..., return_full_result=True)`, so the full step history is available afterwards.
3. The agent loops: each step it must call a tool. It searches, fetches pages, then calls `final_answer` with the summary.
4. `runner.py` walks the recorded steps and reads each tool's output:
   - `SOURCE: <url>` lines (written by `fetch_page`) become `result.sources`.
   - `ERROR: ...` lines become `result.errors`.
5. `verify_citations` compares the URLs cited in the summary against the URLs actually fetched. Any cited URL that was never fetched is reported as hallucinated.
6. Everything is returned as a `ResearchResult` (topic, summary, sources, steps used, errors).

## Setup

Requires Python 3.10+ (developed on 3.14) and [uv](https://docs.astral.sh/uv/).

```bash
# 1. install dependencies
uv sync

# 2. create your local env file and add your Groq key
cp .env.example .env
#    then edit .env:  GROQ_API_KEY=your_key_here

# 3. run
uv run python -m research_agent
```

Get a key at https://console.groq.com/keys.

Main dependencies: `smolagents`, `openai` (client for Groq's endpoint), `ddgs` (search), `httpx` (downloads), `trafilatura` (text extraction), `python-dotenv`.

### Keeping your API key out of Git

- `.env` is listed in `.gitignore`, so it is never committed.
- `.env.example` is committed and contains only a placeholder.
- If `.env` was ever committed, untrack it with `git rm --cached .env`, and **rotate the key** in the Groq console. Deleting it in a later commit does not remove it from history.

## Tools

| Tool | What it does |
|---|---|
| `get_search_results_as_string(query, num_results)` | Searches DuckDuckGo (via `ddgs`) and returns title, URL, domain, and snippet for each result. `num_results` is clamped to 1-10. Returns an `ERROR: ...` string on rate limits, timeouts, or empty results instead of raising. |
| `fetch_page(url, max_chars)` | Downloads a page with `httpx`, extracts the main text with `trafilatura`, truncates to `max_chars`, and returns `SOURCE: <url>` followed by the text. Returns `ERROR: ...` on bad URLs, HTTP errors, timeouts, or extraction failure. |
| `final_answer(answer)` | Built into smolagents. Calling it ends the run and returns the summary. |

The `SOURCE:` and `ERROR:` prefixes matter: `runner.py` parses them to track what was fetched and what failed. Tools return errors as strings so the model can react to them (retry with a shorter query, move on) instead of crashing the run.

## Prompt templates

`prompt.py` defines three templates sharing one `COMMON_RULES` block:

- `short`: 150-250 word cited summary (the only one wired into `run_research`)
- `long`: ~500 words, section per sub-question
- `compare`: 300-word comparison with a markdown table (uses `{topic_a}` / `{topic_b}`)

## Limitations

- **Search is fragile.** DuckDuckGo via `ddgs` times out or rate-limits regularly. In testing, 2 of 5 searches failed in one run, which eats into the step budget.
- **Shallow reading.** Only 2 pages are fetched, each truncated to 2,000 characters, so the summary is based on a small slice of each source.
- **No JavaScript.** `fetch_page` only sees server-rendered HTML; JS-heavy sites often fail extraction.
- **Citation check is string-level.** It confirms a cited URL was fetched, not that the page actually supports the claim next to it.
- **Model reliability.** `gpt-oss-120b` on Groq sometimes returns empty generations when a tool call is forced, and can use non-ASCII citation brackets (`【1】`) that the rules have to forbid.
- **Prompt rules are advisory.** "Search exactly 3 times" is a request, not an enforced constraint; the model can deviate.
- **Only `short` is wired up.** `long` and `compare` exist, but `run_research` always uses `short`, and `compare` needs a different `format()` call.
- **Hardcoded CLI topic.** `main()` always researches "origins of the Linux kernel"; there is no argument parsing yet.
- **No tests, no caching.** Every run hits the network again.

## What I learned

- **The agent type dictates the prompt.** `ToolCallingAgent` forces a tool call on every step (`tool_choice="required"`). A prompt that says "reply in plain text" or "write Python code" causes `Tool choice is required, but model did not call a tool`. Those instructions belong to `CodeAgent`.
- **Runs end only on `final_answer`.** A custom `submit_final_answer` tool is just another tool to smolagents, so the run kept going until it hit `max_steps`. Use the built-in `final_answer`.
- **Docstrings are the model's API docs.** smolagents shows each tool's docstring and signature to the model, so a default of 2 with a docstring saying 5 produces confusing behavior. Keep them in sync.
- **Budget steps for failures.** Searches fail. If `max_steps` equals the happy-path step count, one failed search leaves no room to answer.
- **Return errors, don't raise them.** Tools that return `ERROR: ...` strings let the model recover, and make failures easy to collect afterwards.
- **Verify, don't trust.** Programmatically comparing cited URLs to fetched URLs catches invented sources cheaply. Parsing step history also depends on the library's data shape (steps can be dicts, not objects), so inspect real output when something comes back empty.
- **Avoid side effects at import time.** A `time.sleep()` at module level runs once on import and rate-limits nothing; it belongs inside the function it protects.

## Ideas for next steps

- Take the topic and template from CLI arguments
- Wire up `long` and `compare`
- Retry with backoff in the search tool
- Fetch more pages with a larger per-page budget
- Check that cited claims actually appear in the fetched text