import json

from architecture import ArchitecturePlan


class ArchitecturePlanner:
    """
    Converts a natural-language software requirement into a
    structured architecture plan.
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def plan(self, requirement: str) -> ArchitecturePlan:
        """
        Generate and validate an architecture plan.
        """

        if not requirement or not requirement.strip():
            raise ValueError(
                "Architecture planning requires a requirement."
            )

        schema = ArchitecturePlan.model_json_schema()

        schema["additionalProperties"] = False

        prompt = f"""
You are the architecture planning component of ForgeAI.

Create a practical implementation plan for the following
software requirement.

USER REQUIREMENT:
{requirement.strip()}

Your response must follow the provided JSON schema exactly.

Planning rules:

1. Identify the actual type of application being requested.

2. Choose technologies appropriate for the requirement.

3. List the important project components.

4. List the files that should actually be created or modified.

5. Describe the high-level data flow.

6. List required dependencies.

7. Provide concrete implementation steps.

8. Prefer the smallest reasonable architecture.

9. Do not introduce unnecessary frameworks or services.

10. Do not invent features that were not requested.

11. The plan must be practical enough for an autonomous
    coding agent to execute.

Return only structured JSON.
"""

        response = self.llm_client.generate(
            user_message=prompt,
            schema=schema,
            schema_name="architecture_plan",
        )

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Architecture planner returned invalid JSON."
            ) from exc

        return ArchitecturePlan.model_validate(
            data
        )