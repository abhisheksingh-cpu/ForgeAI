import os

from llm_client import LLMClient
from impact_analyzer import ImpactAnalyzer
from tools import dispatcher


client = LLMClient(
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_MODEL")
)

analyzer = ImpactAnalyzer(
    client,
    dispatcher
)



architecture_plan = """
{
    "project_type": "Full-Stack To-Do Application",
    "components": [
        {
            "name": "Frontend",
            "technology": "React"
        },
        {
            "name": "Backend",
            "technology": "FastAPI"
        },
        {
            "name": "Database",
            "technology": "PostgreSQL"
        }
    ]
}
"""


report = analyzer.analyze(
    "Add a due_date field to tasks in the To-Do application.",
    architecture_plan
)

print(
    report.model_dump_json(indent=2)
)
