import json

from impact import ImpactReport
from tools import list_files


class ImpactAnalyzer:
    """
    Determines which existing project files are likely to be
    affected by a requested change.
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def analyze(
        self,
        requirement: str,
        architecture_plan: str,
    ) -> ImpactReport:
        """
        Analyze the current project and identify potentially
        affected files.
        """

        if not requirement or not requirement.strip():
            raise ValueError(
                "Impact analysis requires a requirement."
            )

        files = list_files()

        # A completely new project may have no files yet.
        if not files:
            return ImpactReport(
                directly_affected=[],
                indirectly_affected=[],
            )

        # Keep the prompt bounded so large repositories do not
        # consume unnecessary LLM tokens.
        visible_files = files[:100]

        file_listing = "\n".join(
            f"- {path}"
            for path in visible_files
        )

        schema = ImpactReport.model_json_schema()

        schema["additionalProperties"] = False

        prompt = f"""
You are the impact-analysis component of ForgeAI.

Determine which existing files in the target project are likely
to be affected by the requested software change.

USER REQUIREMENT:
{requirement.strip()}

ARCHITECTURE PLAN:
{architecture_plan}

EXISTING PROJECT FILES:
{file_listing}

Rules:

1. Only identify files that are actually relevant to the request.

2. Put files that will probably need modification or replacement
   in directly_affected.

3. Put files that may need changes because they depend on the
   directly affected functionality in indirectly_affected.

4. Do not invent file paths that are not present in the project.

5. If no existing files need modification, return empty lists.

6. Keep the analysis concise.

7. Return only structured JSON matching the provided schema.
"""

        response = self.llm_client.generate(
            user_message=prompt,
            schema=schema,
            schema_name="impact_report",
        )

        try:
            data = json.loads(response)

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Impact analyzer returned invalid JSON."
            ) from exc

        return ImpactReport.model_validate(
            data
        )