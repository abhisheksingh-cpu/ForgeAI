from architecture_planner import ArchitecturePlanner
from llm_client import LLMClient
import os


client = LLMClient(
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_MODEL")
)

planner = ArchitecturePlanner(client)

plan = planner.plan(
    "Build a simple full-stack To-Do application with React frontend, FastAPI backend, and PostgreSQL database."
)

print(plan.model_dump_json(indent=2))