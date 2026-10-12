from smolagents import CodeAgent, OpenAIServerModel 
import os
from dotenv import load_dotenv
load_dotenv()
from .tools import *


# Initialize a model (using Hugging Face Inference API)
model = OpenAIServerModel(
    model_id="openai/gpt-oss-120b",
    api_base="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
)

# Create an agent 
agent = CodeAgent(tools=[get_search_results_as_string], model=model)

# Run the agent with a task
result = agent.run("Use get_search_results_as_string to research the "
    "history of Python. Inspect the search results before "
    "writing your answer. Include source URLs from the "
     "results, and do not invent citations.")
print(result)

