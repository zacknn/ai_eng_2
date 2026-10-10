from smolagents import CodeAgent, OpenAIServerModel
import os
from dotenv import load_dotenv
load_dotenv()
# Initialize a model (using Hugging Face Inference API)
model = OpenAIServerModel(
    model_id="openai/gpt-oss-120b",
    api_base="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
)

# Create an agent with no tools
agent = CodeAgent(tools=[], model=model)

# Run the agent with a task
result = agent.run("Calculate the sum of numbers from 1 to 10")
print(result)