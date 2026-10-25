import os

from llm_client import LLMClient
from agent import Agent
from repair_agent import RepairAgent
from tools import dispatcher
from tool_schemas import TOOLS_SCHEMA


client = LLMClient(
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_MODEL")
)

agent = Agent(
    client,
    dispatcher,
    TOOLS_SCHEMA
)

repair_agent = RepairAgent(
    agent,
    dispatcher
)

result = repair_agent.repair(
    "python -m unittest test_app.py"
)

print("\nFINAL RESULT:")
print(result)