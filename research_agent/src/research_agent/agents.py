import os

from dotenv import load_dotenv
from smolagents import CodeAgent, OpenAIServerModel

from .tools import fetch_page, get_search_results_as_string


load_dotenv()


TASK = """
Research the history of Python (the programming language) and write a
short cited summary. Keep the WHOLE conversation under 6000 tokens.

Output format:
- Every response must be a Python code block wrapped in <code>...</code>.
- Do NOT write prose outside the code block.
- To "write down" a plan or notes, use print() inside a code block.

Follow these phases IN ORDER:

Phase 1 — Plan (1 step only).
  Print 3 short sub-questions. Keep them under 10 words each.

Phase 2 — Search (max 3 searches total).
  For each sub-question, call get_search_results_as_string with a
  2-6 word query. Use num_results=3. Do NOT answer yet.
  Wait 2 seconds between calls to avoid rate limits.

Phase 3 — Read (max 2 fetches total).
  Pick the 2 best URLs from all your search results (prefer wikipedia.org,
  python.org, .edu, .gov). Call fetch_page on them with max_chars=2000.

Phase 4 — Summarize.
  Write a 150-250 word summary. Every claim gets an inline marker [1] or [2].
  End with a numbered list of the URLs you actually fetched.

Rules:
- Only cite URLs returned by search AND fetched with fetch_page.
- Do not invent URLs, dates, or facts.
- Search queries must be 2-6 words, not sentences.
- If a search fails, try a shorter query ONCE, then move on.
- Do not exceed 6000 tokens. If close, stop and summarize with what you have.

When done, call final_answer(...) with the summary text.
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

