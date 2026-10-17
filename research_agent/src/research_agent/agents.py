import os

from dotenv import load_dotenv
from smolagents import CodeAgent, OpenAIServerModel, ToolCallingAgent

from .prompt import *
from .tools import fetch_page, get_search_results_as_string

load_dotenv()


api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Add it to your environment or .env file."
    )

#were gonna replace this with get agent
def build_agent() -> CodeAgent:
    model = OpenAIServerModel(
        model_id="openai/gpt-oss-120b",
        api_base="https://api.groq.com/openai/v1",
        api_key=api_key,
    )
    return CodeAgent(tools=[get_search_results_as_string, fetch_page], model=model)


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = ToolCallingAgent(
            tools=[get_search_results_as_string, fetch_page],
            model=OpenAIServerModel(
                model_id="openai/gpt-oss-120b",
                api_base="https://api.groq.com/openai/v1",
                api_key=api_key,
            ),
            max_steps=8,
        )


def main() -> None:
    agent = get_agent()
    result = agent.run(TASK)
    print(result)


if __name__ == "__main__":
    main()
