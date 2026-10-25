import os
from dotenv import load_dotenv
from llm_client import LLMClient
from models.task import EngineeringTask
from requirement_parser import RequirementParser

load_dotenv()

schema = EngineeringTask.model_json_schema()
schema["additionalProperties"] = False

client = LLMClient(
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_MODEL")
)

# response = client.generate(
#       "Build a REST API using Python and PostgreSQL.", schema
# )

# print(response)

parser = RequirementParser(client)

result = parser.parse(
    "Build a REST API using Python, FastAPI, and PostgreSQL with JWT authentication."
)

print(result)
print(type(result))
print(result.language)