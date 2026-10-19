import os

from dotenv import load_dotenv
from smolagents import OpenAIServerModel, ToolCallingAgent

from .prompt import *
from .runner import run_research
from .tools import fetch_page, get_search_results_as_string

load_dotenv()


api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Add it to your environment or .env file."
    )

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = ToolCallingAgent(
            tools=[get_search_results_as_string, fetch_page ] ,
            model=OpenAIServerModel(
                model_id="openai/gpt-oss-120b",
                api_base="https://api.groq.com/openai/v1",
                api_key=api_key,
            ),
            max_steps=8,
        )
    return _agent


def main() -> None:
    result = run_research("origins of the Linux kernel")
    
    print("\n--- SUMMARY ---")
    print(result.summary)
    
    print("\n--- STATS ---")
    print(f"Steps used: {result.steps_used}")
    print(f"Sources fetched: {len(result.sources)}")
    
    if result.errors:
        print("\n--- ERRORS / WARNINGS ---")
        for err in result.errors:
            print(f"- {err}")


if __name__ == "__main__":
    main()
