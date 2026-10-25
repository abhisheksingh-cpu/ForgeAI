from models.task import EngineeringTask
import json

class RequirementParser:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def parse(self, requirement):
        schema = EngineeringTask.model_json_schema()
        schema["additionalProperties"] = False

        response = self.llm_client.generate(
            requirement,
            schema
        )
        print("LLM RESPONSE:", response)
        data = json.loads(response)
        return EngineeringTask.model_validate(data)

    