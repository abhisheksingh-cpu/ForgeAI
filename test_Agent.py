import os

from agent import Agent
from llm_client import LLMClient
from tools import dispatcher
from tool_schemas import TOOLS_SCHEMA

import tools

print(tools.__file__)
print(hasattr(tools, "dispatcher"))

api_key = os.getenv("GROQ_API_KEY")
model = "openai/gpt-oss-120b"

llm_client = LLMClient(
    api_key,
    model
)

agent = Agent(
    llm_client,
    dispatcher,
    TOOLS_SCHEMA
)

agent.run(
    "Edit hello.py so that it prints Hello ForgeAI"
)
