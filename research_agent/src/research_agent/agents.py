import os

from dotenv import load_dotenv
from smolagents import CodeAgent, OpenAIServerModel

from .tools import fetch_page, get_search_results_as_string


load_dotenv()


TASK = """
Research the history of Python (the programming language) and write a
cited summary.

Follow these phases IN ORDER:

Phase 1 — Plan.
  Write 3 to 5 sub-questions that together cover the topic. Examples:
  who created it, when, why, major version milestones, governance changes.
  Write them as text before doing anything else.

Phase 2 — Search.
  For each sub-question, call get_search_results_as_string with a focused
  query. Read the snippets carefully. Do NOT answer yet.

Phase 3 — Read sources.
  For the 2 most promising results per sub-question, call fetch_page on
  their URL to read the full content. Prefer authoritative domains
  (wikipedia.org, .gov, .edu, python.org, major news outlets). Skip
  obviously low-quality results.

Phase 4 — Write the summary.
  Combine what you learned into a coherent summary. Every factual claim
  must have an inline source marker like [1], [2]. At the end, list every
  URL you actually fetched, numbered to match the markers.

Phase 5 — Verify.
  Re-read your summary. For each citation [N], confirm the claim is
  supported by the fetched text for that source. Remove or fix any claim
  you cannot support. If a source's text was truncated, only cite what
  you actually read.

Hard rules:
  - Only cite URLs that came from get_search_results_as_string AND were
    fetched with fetch_page.
  - Do not invent URLs, dates, or facts.
  - If you could not find evidence for a sub-question, say so explicitly
    instead of guessing.

When done, call final_answer(...) with the full summary text.
"""


def build_agent() -> CodeAgent:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your environment or .env file.")

    model = OpenAIServerModel(
        model_id="openai/gpt-oss-120b",
        api_base="https://api.groq.com/openai/v1",
        api_key=api_key,
    )
    return CodeAgent(tools=[get_search_results_as_string, fetch_page], model=model)


def main() -> None:
    agent = build_agent()
    result = agent.run(TASK)
    print(result)


if __name__ == "__main__":
    main()

